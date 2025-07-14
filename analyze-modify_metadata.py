#!/usr/bin/env python3
"""
Metadata Analysis & Modification Tool for Google Photos Processor
================================================================

This script analyzes JPEG, JPG, and MP4 files and provides advanced metadata modification capabilities.
It serves as both a verification tool and the primary geocoding/location writing tool.

Features:
- Comprehensive metadata analysis (dates, GPS, location info)
- GPS geocoding (coordinates → location names using OpenStreetMap API)
- Location information writing to EXIF metadata
- Detailed reporting and statistics
- Quality control for OneDrive upload preparation

Author: Stephan Alluchon
Purpose: Advanced metadata analysis and modification for photo processing workflow
"""

import os
import json
import time
import shutil
from datetime import datetime
from collections import defaultdict
import piexif
from PIL import Image
import subprocess
import sys
import requests
from typing import Optional, Tuple, Dict

class MetadataAnalyzerModifier:
    """
    Advanced metadata analyzer and modifier for photo processing workflow.
    
    This class provides comprehensive metadata analysis and modification capabilities:
    - GPS coordinate extraction and validation
    - Location geocoding using OpenStreetMap API
    - EXIF metadata writing and modification
    - Detailed reporting and statistics
    """
    def __init__(self, directory_path, enable_geocoding=False, write_gps_to_files=False):
        self.directory_path = directory_path
        self.enable_geocoding = enable_geocoding
        self.write_gps_to_files = write_gps_to_files
        self.stats = {
            'total_files': 0,
            'jpeg_files': 0,
            'mp4_files': 0,
            'files_with_exif_date': 0,
            'files_with_system_date': 0,
            'files_without_metadata': 0,
            'files_with_gps': 0,
            'files_with_location': 0,
            'files_gps_written': 0,
            'errors': 0
        }
        self.detailed_results = []
        # Cache pour éviter les appels répétés au service de géocodage
        self.location_cache = {}
        # Variables pour le suivi de la progression GPS
        self.gps_processed = 0
        self.total_gps_files = 0
        # Détecter le chemin vers ffprobe
        self.ffprobe_path = self._find_ffprobe()
        
    def _find_ffprobe(self):
        """Find ffprobe executable in common locations"""
        possible_paths = [
            'ffprobe',  # Si dans le PATH
            'ffprobe.exe',  # Si dans le PATH (Windows)
            r'C:\Program Files\ffmpeg\bin\ffprobe.exe',  # Installation standard
            r'C:\ffmpeg\bin\ffprobe.exe',  # Installation alternative
            r'C:\Program Files (x86)\ffmpeg\bin\ffprobe.exe',  # 32-bit
            os.path.join(os.path.expanduser('~'), 'ffmpeg', 'bin', 'ffprobe.exe'),  # User install
        ]
        
        for path in possible_paths:
            try:
                # Tester si l'exécutable fonctionne
                result = subprocess.run([path, '-version'], 
                                      capture_output=True, 
                                      text=True, 
                                      timeout=5)
                if result.returncode == 0:
                    return path
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                continue
        
        return None

    def extract_gps_coordinates(self, exif_data) -> Optional[Tuple[float, float]]:
        """Extract GPS coordinates from EXIF data"""
        try:
            if 'GPS' not in exif_data:
                return None
                
            gps_data = exif_data['GPS']
            
            # Vérifier la présence des coordonnées requises
            required_keys = [
                piexif.GPSIFD.GPSLatitude,
                piexif.GPSIFD.GPSLatitudeRef,
                piexif.GPSIFD.GPSLongitude,
                piexif.GPSIFD.GPSLongitudeRef
            ]
            
            if not all(key in gps_data for key in required_keys):
                return None
            
            # Extraire latitude
            lat_data = gps_data[piexif.GPSIFD.GPSLatitude]
            lat_ref = gps_data[piexif.GPSIFD.GPSLatitudeRef].decode('utf-8')
            
            # Convertir format GPS (degrés, minutes, secondes) en décimal
            lat = self.convert_gps_to_decimal(lat_data, lat_ref)
            
            # Extraire longitude
            lon_data = gps_data[piexif.GPSIFD.GPSLongitude]
            lon_ref = gps_data[piexif.GPSIFD.GPSLongitudeRef].decode('utf-8')
            
            lon = self.convert_gps_to_decimal(lon_data, lon_ref)
            
            return (lat, lon)
            
        except Exception as e:
            print(f"⚠️  GPS extraction error: {e}")
            return None
    
    def convert_gps_to_decimal(self, gps_coord, ref) -> float:
        """Convert GPS coordinates from DMS to decimal degrees"""
        try:
            # Les coordonnées GPS EXIF sont des fractions (numerator, denominator)
            # Convertir chaque composant en décimal
            degrees = gps_coord[0][0] / gps_coord[0][1] if gps_coord[0][1] != 0 else 0
            minutes = gps_coord[1][0] / gps_coord[1][1] if gps_coord[1][1] != 0 else 0
            seconds = gps_coord[2][0] / gps_coord[2][1] if gps_coord[2][1] != 0 else 0
            
            # Conversion en décimal
            decimal = degrees + (minutes / 60) + (seconds / 3600)
            
            # Appliquer la référence (N/S pour latitude, E/W pour longitude)
            if ref in ['S', 'W']:
                decimal = -decimal
                
            return decimal
            
        except (IndexError, ZeroDivisionError, TypeError) as e:
            print(f"⚠️  GPS coordinate conversion error: {e}")
            return 0.0
    
    def get_location_from_coordinates(self, lat: float, lon: float) -> Optional[Dict[str, str]]:
        """Get location information from GPS coordinates using reverse geocoding"""
        # Vérifier si le géocodage est activé
        if not self.enable_geocoding:
            return None
            
        # Afficher la progression
        if hasattr(self, 'gps_processed') and hasattr(self, 'total_gps_files') and self.total_gps_files > 0:
            self.gps_processed += 1
            print(f"\r🌍 Geocoding progress: [{self.gps_processed}/{self.total_gps_files}] {lat:.3f},{lon:.3f}", end='', flush=True)
            
        # Vérifier le cache d'abord (3 décimales = ~110m de précision)
        cache_key = f"{lat:.3f},{lon:.3f}"
        if cache_key in self.location_cache:
            cached_location = self.location_cache[cache_key]
            # Afficher la localisation depuis le cache dans la progression
            city = cached_location.get('city', '')
            country = cached_location.get('country', '')
            location_text = f"{city}, {country}" if city and country else country or city or "Unknown"
            print(f"\r🌍 Geocoding progress: [{self.gps_processed}/{self.total_gps_files}] {lat:.3f},{lon:.3f} → {location_text} (cached)", end='', flush=True)
            return cached_location
        
        try:
            # Utiliser l'API Nominatim d'OpenStreetMap (gratuite)
            url = "https://nominatim.openstreetmap.org/reverse"
            params = {
                'lat': lat,
                'lon': lon,
                'format': 'json',
                'addressdetails': 1,
                'zoom': 10,  # Niveau de détail
                'accept-language': 'fr,en'  # Préférence française puis anglaise
            }
            
            headers = {
                'User-Agent': 'Google-Photos-Processor/1.0 (contact@example.com)'
            }
            
            response = requests.get(url, params=params, headers=headers, timeout=5)
            
            if response.status_code == 200:
                data = response.json()
                
                if 'address' in data:
                    address = data['address']
                    location_info = {
                        'city': address.get('city', address.get('town', address.get('village', ''))),
                        'state': address.get('state', address.get('region', '')),
                        'country': address.get('country', ''),
                        'country_code': address.get('country_code', '').upper(),
                        'full_address': data.get('display_name', ''),
                        'coordinates': f"{lat:.6f},{lon:.6f}"
                    }
                    
                    # Mettre en cache
                    self.location_cache[cache_key] = location_info
                    
                    # Afficher la localisation trouvée dans la progression
                    city = location_info.get('city', '')
                    country = location_info.get('country', '')
                    location_text = f"{city}, {country}" if city and country else country or city or "Unknown"
                    print(f"\r🌍 Geocoding progress: [{self.gps_processed}/{self.total_gps_files}] {lat:.3f},{lon:.3f} → {location_text}", end='', flush=True)
                    
                    # Petit délai pour respecter les limites de l'API
                    time.sleep(1)
                    
                    # Nouvelle ligne à la fin du dernier traitement
                    if hasattr(self, 'gps_processed') and hasattr(self, 'total_gps_files') and self.gps_processed == self.total_gps_files:
                        print()  # Nouvelle ligne après le dernier fichier
                    
                    return location_info
                    
        except requests.RequestException as e:
            print(f"\r🌍 Geocoding progress: [{self.gps_processed}/{self.total_gps_files}] {lat:.3f},{lon:.3f} → API Error", end='', flush=True)
            print(f"⚠️  Geocoding API error: {e}")
        except Exception as e:
            print(f"\r🌍 Geocoding progress: [{self.gps_processed}/{self.total_gps_files}] {lat:.3f},{lon:.3f} → Error", end='', flush=True)
            print(f"⚠️  Location processing error: {e}")
            
        return None
        
    def analyze_image_metadata(self, file_path):
        """Analyze EXIF metadata of JPEG/JPG files"""
        result = {
            'file_path': file_path,
            'file_type': 'image',
            'has_exif_date': False,
            'exif_date': None,
            'has_system_date': False,
            'system_date': None,
            'has_gps': False,
            'gps_coordinates': None,
            'location_info': None,
            'file_size': 0,
            'error': None
        }
        
        try:
            # Get file system information
            stat = os.stat(file_path)
            result['file_size'] = stat.st_size
            result['system_date'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            result['has_system_date'] = True
            
            # Analyze EXIF data
            try:
                with Image.open(file_path) as img:
                    # Vérifier si le fichier a des données EXIF
                    exif_bytes = img.info.get('exif', b'')
                    
                    if not exif_bytes:
                        # Pas de données EXIF - c'est normal pour certains fichiers
                        pass
                    else:
                        try:
                            exif_data = piexif.load(exif_bytes)
                            
                            # Check for DateTimeOriginal
                            if piexif.ExifIFD.DateTimeOriginal in exif_data.get('Exif', {}):
                                date_bytes = exif_data['Exif'][piexif.ExifIFD.DateTimeOriginal]
                                result['exif_date'] = date_bytes.decode('utf-8')
                                result['has_exif_date'] = True
                            
                            # Check for other date fields if DateTimeOriginal not found
                            elif piexif.ExifIFD.DateTimeDigitized in exif_data.get('Exif', {}):
                                date_bytes = exif_data['Exif'][piexif.ExifIFD.DateTimeDigitized]
                                result['exif_date'] = date_bytes.decode('utf-8')
                                result['has_exif_date'] = True
                            
                            elif piexif.ImageIFD.DateTime in exif_data.get('0th', {}):
                                date_bytes = exif_data['0th'][piexif.ImageIFD.DateTime]
                                result['exif_date'] = date_bytes.decode('utf-8')
                                result['has_exif_date'] = True
                            
                            # Extract GPS coordinates
                            gps_coords = self.extract_gps_coordinates(exif_data)
                            if gps_coords:
                                result['has_gps'] = True
                                result['gps_coordinates'] = gps_coords
                                
                                # Check for existing location information
                                existing_location = self.extract_existing_location_info(exif_data)
                                if existing_location:
                                    # Parse existing location to create location_info dict
                                    location_parts = existing_location.split(', ')
                                    if len(location_parts) >= 2:
                                        result['location_info'] = {
                                            'city': location_parts[0].strip(),
                                            'country': location_parts[1].strip(),
                                            'full_address': existing_location,
                                            'coordinates': f"{gps_coords[0]:.6f},{gps_coords[1]:.6f}",
                                            'source': 'existing_exif'
                                        }
                                    else:
                                        result['location_info'] = {
                                            'city': '',
                                            'country': existing_location.strip(),
                                            'full_address': existing_location,
                                            'coordinates': f"{gps_coords[0]:.6f},{gps_coords[1]:.6f}",
                                            'source': 'existing_exif'
                                        }
                                # Note: location_info will be filled during geocoding phase if enabled and not already present
                                    
                        except (piexif.InvalidImageDataError, ValueError, KeyError) as e:
                            # Données EXIF corrompues ou format non supporté - pas une erreur critique
                            pass
                        except Exception as e:
                            result['error'] = f"EXIF parsing error: {str(e)}"
                        
            except Exception as e:
                result['error'] = f"EXIF reading error: {str(e)}"
                
        except Exception as e:
            result['error'] = f"File access error: {str(e)}"
            
        return result
    
    def analyze_video_metadata(self, file_path):
        """Analyze metadata of MP4 files using ffprobe if available"""
        result = {
            'file_path': file_path,
            'file_type': 'video',
            'has_exif_date': False,
            'exif_date': None,
            'has_system_date': False,
            'system_date': None,
            'has_gps': False,
            'gps_coordinates': None,
            'location_info': None,
            'file_size': 0,
            'error': None
        }
        
        try:
            # Get file system information
            stat = os.stat(file_path)
            result['file_size'] = stat.st_size
            result['system_date'] = datetime.fromtimestamp(stat.st_mtime).strftime('%Y-%m-%d %H:%M:%S')
            result['has_system_date'] = True
            
            # Try to get video metadata using ffprobe
            if self.ffprobe_path:
                try:
                    cmd = [
                        self.ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                        '-show_format', '-show_streams', file_path
                    ]
                    
                    process = subprocess.run(cmd, capture_output=True, text=True, timeout=10)
                    
                    if process.returncode == 0:
                        metadata = json.loads(process.stdout)
                        
                        # Check for creation_time in format
                        if 'format' in metadata and 'tags' in metadata['format']:
                            tags = metadata['format']['tags']
                            creation_time = tags.get('creation_time') or tags.get('date')
                            
                            if creation_time:
                                result['exif_date'] = creation_time
                                result['has_exif_date'] = True
                            
                            # Check for GPS coordinates in video metadata
                            location = tags.get('location')
                            if location:
                                gps_coords = self.parse_video_location(location)
                                if gps_coords:
                                    result['has_gps'] = True
                                    result['gps_coordinates'] = gps_coords
                                    # Note: location_info will be filled during geocoding phase if enabled
                        
                        # Check for creation_time in streams
                        if not result['has_exif_date'] and 'streams' in metadata:
                            for stream in metadata['streams']:
                                if 'tags' in stream:
                                    creation_time = stream['tags'].get('creation_time')
                                    if creation_time:
                                        result['exif_date'] = creation_time
                                        result['has_exif_date'] = True
                                        break
                    else:
                        result['error'] = "ffprobe analysis failed"
                        
                except subprocess.TimeoutExpired:
                    result['error'] = "ffprobe timeout"
                except Exception as e:
                    result['error'] = f"ffprobe error: {str(e)}"
            else:
                # ffprobe not found - this is normal, don't treat as error
                # Video files will be considered valid if they have system dates
                pass
                
        except Exception as e:
            result['error'] = f"File access error: {str(e)}"
            
        return result
    
    def parse_video_location(self, location_string: str) -> Optional[Tuple[float, float]]:
        """Parse location string from video metadata (e.g., '+37.7749-122.4194+000.000/')"""
        try:
            # Format typique: '+37.7749-122.4194+000.000/' or '37.7749,-122.4194'
            location_string = location_string.strip()
            
            if ',' in location_string:
                # Format simple: "latitude,longitude"
                parts = location_string.split(',')
                if len(parts) >= 2:
                    lat = float(parts[0].strip())
                    lon = float(parts[1].strip())
                    return (lat, lon)
            else:
                # Format complexe avec +/- : '+37.7749-122.4194+000.000/'
                # Utiliser regex pour extraire lat/lon
                import re
                pattern = r'([+-]?\d+\.?\d*)([+-]\d+\.?\d*)'
                match = re.search(pattern, location_string)
                if match:
                    lat = float(match.group(1))
                    lon = float(match.group(2))
                    return (lat, lon)
                    
        except (ValueError, IndexError, AttributeError) as e:
            print(f"⚠️  Video location parsing error: {e}")
            
        return None
    
    def analyze_directory(self):
        """Analyze all supported files in the directory"""
        print(f"🔍 Analyzing directory: {self.directory_path}")
        print("=" * 60)
        
        supported_extensions = {'.jpg', '.jpeg', '.mp4'}
        
        for root, dirs, files in os.walk(self.directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in supported_extensions:
                    self.stats['total_files'] += 1
                    
                    try:
                        if file_ext in ['.jpg', '.jpeg']:
                            self.stats['jpeg_files'] += 1
                            result = self.analyze_image_metadata(file_path)
                        elif file_ext == '.mp4':
                            self.stats['mp4_files'] += 1
                            result = self.analyze_video_metadata(file_path)
                        
                        self.detailed_results.append(result)
                        
                        # Update statistics
                        if result['has_exif_date']:
                            self.stats['files_with_exif_date'] += 1
                        if result['has_system_date']:
                            self.stats['files_with_system_date'] += 1
                        if result['has_gps']:
                            self.stats['files_with_gps'] += 1
                        # Note: files_with_location will be updated during geocoding phase
                        if not result['has_exif_date'] and not result['has_system_date']:
                            self.stats['files_without_metadata'] += 1
                        if result['error']:
                            self.stats['errors'] += 1
                            
                    except Exception as e:
                        self.stats['errors'] += 1
                        print(f"❌ Error processing {file_path}: {str(e)}")
        
        # Update statistics for location info (including existing ones)
        for result in self.detailed_results:
            if result.get('location_info'):
                self.stats['files_with_location'] += 1
        
        # Préparer la géolocalisation si activée
        if self.enable_geocoding:
            gps_files = [r for r in self.detailed_results if r['has_gps']]
            gps_files_needing_geocoding = [r for r in gps_files if not r.get('location_info')]
            
            self.total_gps_files = len(gps_files_needing_geocoding)
            self.gps_processed = 0
            
            if self.total_gps_files > 0:
                action_text = "writing GPS location lookup" if self.write_gps_to_files else "geocoding"
                existing_count = len(gps_files) - len(gps_files_needing_geocoding)
                print(f"\n🌍 Starting {action_text} for {self.total_gps_files} files...")
                if existing_count > 0:
                    print(f"   ({existing_count} files already have location information)")
                
                # Traiter seulement les fichiers GPS qui n'ont pas d'informations de localisation
                new_locations_found = 0
                for result in gps_files_needing_geocoding:
                    location_info = self.get_location_from_coordinates(
                        result['gps_coordinates'][0], 
                        result['gps_coordinates'][1]
                    )
                    if location_info:
                        location_info['source'] = 'api_geocoding'  # Mark as newly found
                        result['location_info'] = location_info
                        new_locations_found += 1
                        
                        # Écrire dans le fichier si demandé
                        if self.write_gps_to_files and result['file_type'] == 'image':
                            if self.write_location_to_exif(result['file_path'], location_info):
                                self.stats['files_gps_written'] += 1
                
                # Update total count after geocoding
                total_with_location = len([r for r in self.detailed_results if r.get('location_info')])
                completion_text = f"Found {new_locations_found} new location names (total: {total_with_location} files with location info)"
                if self.write_gps_to_files:
                    completion_text += f" and wrote GPS data to {self.stats['files_gps_written']} files"
                print(f"✅ {action_text.capitalize()} complete! {completion_text}.")
            else:
                existing_count = len(gps_files)
                if existing_count > 0:
                    print(f"\n✅ All {existing_count} GPS files already have location information!")
                else:
                    print(f"\n🌍 No GPS files found for geocoding.")
        
        self.print_summary()
        self.print_detailed_report()
    
    def print_summary(self):
        """Print analysis summary"""
        print("\n📊 ANALYSIS SUMMARY")
        print("=" * 60)
        print(f"Total files analyzed: {self.stats['total_files']}")
        print(f"  • JPEG/JPG files: {self.stats['jpeg_files']}")
        print(f"  • MP4 files: {self.stats['mp4_files']}")
        print(f"\nMetadata Status:")
        print(f"  ✅ Files with EXIF/metadata dates: {self.stats['files_with_exif_date']}")
        print(f"  📅 Files with only system dates: {self.stats['files_with_system_date'] - self.stats['files_with_exif_date']}")
        print(f"  🌍 Files with GPS coordinates: {self.stats['files_with_gps']}")
        print(f"  📍 Files with location names: {self.stats['files_with_location']}")
        if self.write_gps_to_files:
            print(f"  ✏️  Files with GPS data written: {self.stats['files_gps_written']}")
        print(f"  ❌ Files without any metadata: {self.stats['files_without_metadata']}")
        print(f"  ⚠️  Files with errors: {self.stats['errors']}")
        
        # Calculate percentages
        if self.stats['total_files'] > 0:
            exif_percentage = (self.stats['files_with_exif_date'] / self.stats['total_files']) * 100
            system_only_percentage = ((self.stats['files_with_system_date'] - self.stats['files_with_exif_date']) / self.stats['total_files']) * 100
            gps_percentage = (self.stats['files_with_gps'] / self.stats['total_files']) * 100
            location_percentage = (self.stats['files_with_location'] / self.stats['total_files']) * 100
            
            print(f"\nPercentages:")
            print(f"  📈 Files with EXIF dates: {exif_percentage:.1f}%")
            print(f"  📈 Files with system dates only: {system_only_percentage:.1f}%")
            print(f"  🌍 Files with GPS coordinates: {gps_percentage:.1f}%")
            print(f"  📍 Files with location names: {location_percentage:.1f}%")
            if self.write_gps_to_files:
                written_percentage = (self.stats['files_gps_written'] / self.stats['total_files']) * 100
                print(f"  ✏️  Files with GPS data written: {written_percentage:.1f}%")
        
        # Add synthesis section
        self.print_synthesis()
    
    def print_synthesis(self):
        """Print a clear synthesis of valid vs invalid files"""
        print("\n🎯 SYNTHESIS FOR ONEDRIVE UPLOAD")
        print("=" * 60)
        
        valid_files = self.stats['files_with_exif_date'] + (self.stats['files_with_system_date'] - self.stats['files_with_exif_date'])
        invalid_files = self.stats['files_without_metadata'] + self.stats['errors']
        
        print(f"✅ VALID FILES (ready for OneDrive): {valid_files}")
        print(f"   • With EXIF/metadata dates: {self.stats['files_with_exif_date']}")
        print(f"   • With system dates only: {self.stats['files_with_system_date'] - self.stats['files_with_exif_date']}")
        
        print(f"\n❌ INVALID FILES (need attention): {invalid_files}")
        print(f"   • Without any date metadata: {self.stats['files_without_metadata']}")
        print(f"   • With processing errors: {self.stats['errors']}")
        
        if self.stats['total_files'] > 0:
            valid_percentage = (valid_files / self.stats['total_files']) * 100
            invalid_percentage = (invalid_files / self.stats['total_files']) * 100
            
            print(f"\n📊 OVERALL STATUS:")
            print(f"   • Valid files: {valid_percentage:.1f}%")
            print(f"   • Invalid files: {invalid_percentage:.1f}%")
            
            if valid_percentage >= 95:
                print("   🎉 EXCELLENT: Your files are ready for OneDrive!")
            elif valid_percentage >= 80:
                print("   👍 GOOD: Most files are ready, few need attention")
            elif valid_percentage >= 60:
                print("   ⚠️  ATTENTION: Many files need metadata correction")
            else:
                print("   🚨 CRITICAL: Most files need processing before upload")
        
        # Video-specific analysis
        video_files = [r for r in self.detailed_results if r['file_type'] == 'video']
        if video_files:
            video_with_metadata = len([r for r in video_files if r['has_exif_date']])
            video_with_system_date = len([r for r in video_files if r['has_system_date'] and not r['has_exif_date']])
            video_without_metadata = len([r for r in video_files if not r['has_exif_date'] and not r['has_system_date']])
            
            print(f"\n🎬 MP4 VIDEO FILES ANALYSIS:")
            print(f"   • Total MP4 files: {len(video_files)}")
            print(f"   • With metadata dates: {video_with_metadata}")
            print(f"   • With system dates only: {video_with_system_date}")
            print(f"   • Without any dates: {video_without_metadata}")
            
            if len(video_files) > 0:
                video_valid_percentage = ((video_with_metadata + video_with_system_date) / len(video_files)) * 100
                print(f"   • Valid video files: {video_valid_percentage:.1f}%")
                
                if video_with_metadata == 0:
                    print("   ⚠️  Note: No video metadata found (ffprobe not available)")
                    print("   💡 Tip: Install FFmpeg for better video analysis")
        
        # GPS and Location analysis
        if self.stats['files_with_gps'] > 0:
            print(f"\n🌍 GPS & LOCATION ANALYSIS:")
            print(f"   • Files with GPS coordinates: {self.stats['files_with_gps']}")
            print(f"   • Files with location names: {self.stats['files_with_location']}")
            
            # Show top locations
            locations = {}
            for result in self.detailed_results:
                if result['location_info'] and 'city' in result['location_info']:
                    city = result['location_info']['city']
                    country = result['location_info']['country']
                    location_key = f"{city}, {country}" if city and country else country or city
                    if location_key:
                        locations[location_key] = locations.get(location_key, 0) + 1
            
            if locations:
                print(f"   • Top locations found:")
                sorted_locations = sorted(locations.items(), key=lambda x: x[1], reverse=True)
                for location, count in sorted_locations[:5]:  # Top 5
                    print(f"     - {location}: {count} files")
        else:
            print(f"\n🌍 GPS & LOCATION ANALYSIS:")
            print(f"   • No GPS coordinates found in any files")
            print(f"   💡 Tip: GPS data is mainly available in photos taken with smartphones")
            if not self.enable_geocoding:
                print(f"   ℹ️  Note: Geocoding (location names) was disabled for this analysis")
    
    def print_detailed_report(self):
        """Print detailed report of files without metadata"""
        files_without_metadata = [r for r in self.detailed_results if not r['has_exif_date']]
        files_with_errors = [r for r in self.detailed_results if r['error']]
        files_with_gps = [r for r in self.detailed_results if r['has_gps']]
        
        if files_without_metadata:
            print(f"\n⚠️  FILES WITHOUT EXIF/METADATA DATES ({len(files_without_metadata)} files):")
            print("-" * 60)
            for result in files_without_metadata:
                rel_path = os.path.relpath(result['file_path'], self.directory_path)
                print(f"  {result['file_type'].upper()}: {rel_path}")
                if result['system_date']:
                    print(f"    System date: {result['system_date']}")
                if result['gps_coordinates']:
                    print(f"    GPS: {result['gps_coordinates'][0]:.6f}, {result['gps_coordinates'][1]:.6f}")
                if result['location_info']:
                    city = result['location_info'].get('city', '')
                    country = result['location_info'].get('country', '')
                    location = f"{city}, {country}" if city and country else country or city
                    print(f"    Location: {location}")
                if result['error']:
                    print(f"    Error: {result['error']}")
                print()
        
        if files_with_errors:
            print(f"\n❌ FILES WITH ERRORS ({len(files_with_errors)} files):")
            print("-" * 60)
            for result in files_with_errors:
                rel_path = os.path.relpath(result['file_path'], self.directory_path)
                print(f"  {result['file_type'].upper()}: {rel_path}")
                print(f"    Error: {result['error']}")
                print()
        
        if files_with_gps:
            print(f"\n🌍 FILES WITH GPS COORDINATES ({len(files_with_gps)} files):")
            print("-" * 60)
            for result in files_with_gps[:10]:  # Show first 10 to avoid too much output
                rel_path = os.path.relpath(result['file_path'], self.directory_path)
                print(f"  {result['file_type'].upper()}: {rel_path}")
                if result['gps_coordinates']:
                    print(f"    GPS: {result['gps_coordinates'][0]:.6f}, {result['gps_coordinates'][1]:.6f}")
                if result['location_info']:
                    city = result['location_info'].get('city', '')
                    country = result['location_info'].get('country', '')
                    location = f"{city}, {country}" if city and country else country or city
                    print(f"    Location: {location}")
                print()
            
            if len(files_with_gps) > 10:
                print(f"    ... and {len(files_with_gps) - 10} more files with GPS data")
    
    def quick_gps_scan(self):
        """Quick scan to count files with GPS coordinates and existing location information"""
        print("🔍 Scanning for GPS coordinates and location information...")
        
        gps_file_count = 0
        location_info_count = 0
        total_supported_files = 0
        supported_extensions = {'.jpg', '.jpeg', '.mp4'}
        
        for root, dirs, files in os.walk(self.directory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_ext = os.path.splitext(file)[1].lower()
                
                if file_ext in supported_extensions:
                    total_supported_files += 1
                    
                    try:
                        if file_ext in ['.jpg', '.jpeg']:
                            # Quick EXIF check for GPS data and location info
                            with Image.open(file_path) as img:
                                exif_bytes = img.info.get('exif', b'')
                                if exif_bytes:
                                    exif_data = piexif.load(exif_bytes)
                                    
                                    # Check for GPS coordinates
                                    gps_coords = self.extract_gps_coordinates(exif_data)
                                    if gps_coords:
                                        gps_file_count += 1
                                    
                                    # Check for existing location information
                                    existing_location = self.extract_existing_location_info(exif_data)
                                    if existing_location:
                                        location_info_count += 1
                                        
                        elif file_ext == '.mp4':
                            # Quick video metadata check for GPS
                            if self.ffprobe_path:
                                try:
                                    cmd = [
                                        self.ffprobe_path, '-v', 'quiet', '-print_format', 'json',
                                        '-show_format', file_path
                                    ]
                                    process = subprocess.run(cmd, capture_output=True, text=True, timeout=5)
                                    if process.returncode == 0:
                                        metadata = json.loads(process.stdout)
                                        if 'format' in metadata and 'tags' in metadata['format']:
                                            tags = metadata['format']['tags']
                                            location = tags.get('location')
                                            if location:
                                                gps_coords = self.parse_video_location(location)
                                                if gps_coords:
                                                    gps_file_count += 1
                                except (subprocess.TimeoutExpired, Exception):
                                    pass
                    except Exception:
                        # Skip files that can't be processed
                        pass
        
        return gps_file_count, location_info_count, total_supported_files

    def export_report(self, output_file):
        """Export detailed report to JSON file"""
        # Ensure the output directory exists
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            try:
                os.makedirs(output_dir, exist_ok=True)
                print(f"📁 Created directory: {output_dir}")
            except Exception as e:
                print(f"❌ Error creating directory {output_dir}: {e}")
                # Fallback to current directory
                output_file = os.path.join(os.getcwd(), os.path.basename(output_file))
                print(f"📁 Using current directory: {output_file}")
        
        report_data = {
            'analysis_date': datetime.now().isoformat(),
            'directory_analyzed': self.directory_path,
            'statistics': self.stats,
            'detailed_results': self.detailed_results
        }
        
        try:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(report_data, f, indent=2, ensure_ascii=False)
            
            print(f"📄 Detailed report exported to: {output_file}")
            
            # Verify file was created
            if os.path.exists(output_file):
                file_size = os.path.getsize(output_file)
                print(f"✅ File created successfully ({file_size} bytes)")
            else:
                print("⚠️  Warning: File may not have been created properly")
                
        except Exception as e:
            print(f"❌ Error writing report file: {e}")
            print(f"💡 Tip: Check if you have write permissions in {os.path.dirname(output_file)}")
    
    def write_location_to_exif(self, file_path: str, location_info: Dict[str, str]) -> bool:
        """Write location information to EXIF metadata"""
        try:
            if not file_path.lower().endswith(('.jpg', '.jpeg')):
                return False  # Only support JPEG files for now
            
            # Read existing EXIF data
            with Image.open(file_path) as img:
                exif_bytes = img.info.get('exif', b'')
                
                if exif_bytes:
                    exif_data = piexif.load(exif_bytes)
                else:
                    # Create new EXIF data structure
                    exif_data = {'0th': {}, 'Exif': {}, 'GPS': {}, '1st': {}, 'thumbnail': None}
                
                # Add location information to EXIF
                # Use GPSAreaInformation field to store location name
                location_text = f"{location_info.get('city', '')}, {location_info.get('country', '')}"
                if location_text.strip(', '):
                    exif_data['GPS'][piexif.GPSIFD.GPSAreaInformation] = location_text.encode('utf-8')
                
                # Add coordinates if not already present
                if 'coordinates' in location_info:
                    coords = location_info['coordinates'].split(',')
                    if len(coords) == 2:
                        lat, lon = float(coords[0]), float(coords[1])
                        
                        # Convert to GPS format if not already present
                        if piexif.GPSIFD.GPSLatitude not in exif_data['GPS']:
                            lat_deg, lat_min, lat_sec = self.decimal_to_gps(abs(lat))
                            lon_deg, lon_min, lon_sec = self.decimal_to_gps(abs(lon))
                            
                            exif_data['GPS'][piexif.GPSIFD.GPSLatitude] = (
                                (lat_deg, 1), (lat_min, 1), (int(lat_sec * 10000), 10000)
                            )
                            exif_data['GPS'][piexif.GPSIFD.GPSLatitudeRef] = 'N' if lat >= 0 else 'S'
                            exif_data['GPS'][piexif.GPSIFD.GPSLongitude] = (
                                (lon_deg, 1), (lon_min, 1), (int(lon_sec * 10000), 10000)
                            )
                            exif_data['GPS'][piexif.GPSIFD.GPSLongitudeRef] = 'E' if lon >= 0 else 'W'
                
                # Write back to file
                exif_bytes = piexif.dump(exif_data)
                
                # Create a backup and write the new file
                backup_path = file_path + '.backup'
                shutil.copy2(file_path, backup_path)
                
                try:
                    img.save(file_path, exif=exif_bytes)
                    os.remove(backup_path)  # Remove backup if successful
                    return True
                except Exception as e:
                    # Restore backup if writing fails
                    if os.path.exists(backup_path):
                        shutil.move(backup_path, file_path)
                    raise e
                    
        except Exception as e:
            print(f"⚠️  Error writing location to {file_path}: {e}")
            return False
    
    def decimal_to_gps(self, decimal_degree: float) -> tuple:
        """Convert decimal degrees to GPS format (degrees, minutes, seconds)"""
        degrees = int(decimal_degree)
        minutes_float = (decimal_degree - degrees) * 60
        minutes = int(minutes_float)
        seconds = (minutes_float - minutes) * 60
        return degrees, minutes, seconds

    def extract_existing_location_info(self, exif_data) -> Optional[str]:
        """Extract existing location information from EXIF GPS data"""
        try:
            if 'GPS' not in exif_data:
                return None
                
            gps_data = exif_data['GPS']
            
            # Check for GPSAreaInformation field
            if piexif.GPSIFD.GPSAreaInformation in gps_data:
                location_bytes = gps_data[piexif.GPSIFD.GPSAreaInformation]
                if isinstance(location_bytes, bytes):
                    try:
                        location_text = location_bytes.decode('utf-8')
                        return location_text.strip() if location_text.strip() else None
                    except UnicodeDecodeError:
                        # Try other encodings if UTF-8 fails
                        try:
                            location_text = location_bytes.decode('latin-1')
                            return location_text.strip() if location_text.strip() else None
                        except:
                            pass
                elif isinstance(location_bytes, str):
                    return location_bytes.strip() if location_bytes.strip() else None
            
            return None
            
        except Exception as e:
            return None

def main():
    """Main function"""
    # Default directory from traitement_photos_2.py
    default_directory = "D:/Sauvegardephotos/GooglePhotos2"
    
    # Alternative test directory if default doesn't exist
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_directory = os.path.join(current_dir, "test_photos")
    
    print("� Google Photos Metadata Analyzer & Modifier")
    print("=" * 60)
    print("This tool analyzes and modifies JPEG, JPG, and MP4 files metadata.")
    print("Features: Date verification, GPS geocoding, location writing, detailed reporting.")
    print("Use this tool for advanced metadata operations after traitement_photos_2.py processing.\n")
    
    # Get directory to analyze
    directory = input(f"Directory to analyze [{default_directory}]: ").strip()
    if not directory:
        directory = default_directory
    
    # Check if directory exists, fallback to test directory
    if not os.path.exists(directory):
        if os.path.exists(test_directory):
            print(f"⚠️  Default directory '{directory}' not found.")
            print(f"Using test directory: {test_directory}")
            directory = test_directory
        else:
            print(f"❌ Error: Directory '{directory}' does not exist.")
            print(f"💡 Tip: Create some test photos in '{test_directory}' or specify an existing directory.")
            sys.exit(1)
    
    # Check if ffprobe is available
    ffprobe_available = False
    ffprobe_path = None
    
    # Create a temporary analyzer to check ffprobe availability
    temp_analyzer = MetadataAnalyzerModifier(".", enable_geocoding=False, write_gps_to_files=False)
    ffprobe_path = temp_analyzer.ffprobe_path
    
    if ffprobe_path:
        print(f"✅ ffprobe detected at: {ffprobe_path}")
        print("   Enhanced video metadata analysis enabled")
        ffprobe_available = True
    else:
        print("⚠️  ffprobe not found in common locations:")
        print("   - C:\\Program Files\\ffmpeg\\bin\\ffprobe.exe")
        print("   - C:\\ffmpeg\\bin\\ffprobe.exe")
        print("   - System PATH")
        print("   Video analysis will use system dates only")
        print("💡 Tip: Install FFmpeg from https://ffmpeg.org or add it to your PATH")
    
    print()
    
    # Quick scan to count GPS files before asking user
    print("🔍 Preliminary GPS scan...")
    temp_analyzer_gps = MetadataAnalyzerModifier(directory, enable_geocoding=False, write_gps_to_files=False)
    gps_file_count, location_info_count, total_files = temp_analyzer_gps.quick_gps_scan()
    
    print(f"📊 Found {total_files} supported files (.jpg, .jpeg, .mp4)")
    print(f"🌍 Found {gps_file_count} files with GPS coordinates")
    print(f"📍 Found {location_info_count} files with existing location information")
    
    # Calculate files that need geocoding (have GPS but no location info)
    files_needing_geocoding = gps_file_count - location_info_count
    if files_needing_geocoding < 0:
        files_needing_geocoding = 0  # Safety check
    
    # Ask if user wants to enable GPS location lookup
    enable_geocoding = False
    write_gps_to_files = False
    if files_needing_geocoding > 0:
        print(f"\n💡 GPS geocoding can convert coordinates to location names for {files_needing_geocoding} files.")
        print(f"   ({location_info_count} files already have location information)")
        print("⚠️  Note: This requires internet access and may be slower (1 second per file)")
        
        geocoding_choice = input(f"Enable GPS location lookup for {files_needing_geocoding} files? (y/n) [n]: ").strip().lower()
        enable_geocoding = geocoding_choice == 'y'
        
        if enable_geocoding:
            estimated_time = files_needing_geocoding * 1.2  # 1 second + overhead
            print(f"✅ GPS geocoding enabled - estimated time: {estimated_time:.0f} seconds")
            print("   Will convert coordinates to city/country names")
            
            # Ask if user wants to write GPS data to files
            write_choice = input(f"Write GPS location lookup to file metadata? (y/n) [n]: ").strip().lower()
            write_gps_to_files = write_choice == 'y'
            
            if write_gps_to_files:
                print("✅ GPS writing enabled - will write location names to EXIF metadata")
                print("⚠️  Note: This will modify your image files (backups will be created)")
            else:
                print("ℹ️  GPS writing disabled - will only display location names")
        else:
            print("ℹ️  GPS geocoding disabled - will show coordinates only")
    elif gps_file_count > 0:
        print(f"\n✅ All {gps_file_count} files with GPS coordinates already have location information!")
        print("ℹ️  No geocoding needed")
    else:
        print("ℹ️  No GPS coordinates found - geocoding not available")
    
    print()
    
    # Create analyzer and run analysis
    analyzer = MetadataAnalyzerModifier(directory, enable_geocoding=enable_geocoding, write_gps_to_files=write_gps_to_files)
    analyzer.analyze_directory()
    
    # Ask if user wants to export detailed report
    export_choice = input("\nExport detailed report to JSON file? (y/n): ").strip().lower()
    if export_choice == 'y':
        # Use current directory as fallback if default directory doesn't exist
        if os.path.exists(directory) and os.access(directory, os.W_OK):
            output_file = os.path.join(directory, f"metadata_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        else:
            output_file = os.path.join(os.getcwd(), f"metadata_analysis_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")
        
        analyzer.export_report(output_file)
    
    print("\n✅ Analysis complete!")

if __name__ == "__main__":
    main()
