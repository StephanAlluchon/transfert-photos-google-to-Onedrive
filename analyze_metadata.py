#!/usr/bin/env python3
"""
Metadata Analysis Script for Google Photos Processor
====================================================

This script analyzes JPEG, JPG, and MP4 files to verify the presence of creation date information.
It serves as a verification tool for the output of traitement_photos_2.py script.

Author: Stephan Alluchon
Purpose: Quality control and metadata verification for OneDrive upload preparation
"""

import os
import json
import time
from datetime import datetime
from collections import defaultdict
import piexif
from PIL import Image
import subprocess
import sys
import requests
from typing import Optional, Tuple, Dict

class MetadataAnalyzer:
    def __init__(self, directory_path, enable_geocoding=False):
        self.directory_path = directory_path
        self.enable_geocoding = enable_geocoding
        self.stats = {
            'total_files': 0,
            'jpeg_files': 0,
            'mp4_files': 0,
            'files_with_exif_date': 0,
            'files_with_system_date': 0,
            'files_without_metadata': 0,
            'files_with_gps': 0,
            'files_with_location': 0,
            'errors': 0
        }
        self.detailed_results = []
        # Cache pour éviter les appels répétés au service de géocodage
        self.location_cache = {}
        
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
            
        # Vérifier le cache d'abord
        cache_key = f"{lat:.4f},{lon:.4f}"
        if cache_key in self.location_cache:
            return self.location_cache[cache_key]
        
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
                    
                    # Petit délai pour respecter les limites de l'API
                    time.sleep(1)
                    
                    return location_info
                    
        except requests.RequestException as e:
            print(f"⚠️  Geocoding API error: {e}")
        except Exception as e:
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
                                
                                # Get location information
                                if self.enable_geocoding:
                                    location_info = self.get_location_from_coordinates(gps_coords[0], gps_coords[1])
                                    if location_info:
                                        result['location_info'] = location_info
                                    
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
            try:
                cmd = [
                    'ffprobe', '-v', 'quiet', '-print_format', 'json',
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
                                
                                # Get location information
                                if self.enable_geocoding:
                                    location_info = self.get_location_from_coordinates(gps_coords[0], gps_coords[1])
                                    if location_info:
                                        result['location_info'] = location_info
                    
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
            except FileNotFoundError:
                # ffprobe not installed - this is normal, don't treat as error
                # Video files will be considered valid if they have system dates
                pass
            except Exception as e:
                result['error'] = f"ffprobe error: {str(e)}"
                
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
                        if result['location_info']:
                            self.stats['files_with_location'] += 1
                        if not result['has_exif_date'] and not result['has_system_date']:
                            self.stats['files_without_metadata'] += 1
                        if result['error']:
                            self.stats['errors'] += 1
                            
                    except Exception as e:
                        self.stats['errors'] += 1
                        print(f"❌ Error processing {file_path}: {str(e)}")
        
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

def main():
    """Main function"""
    # Default directory from traitement_photos_2.py
    default_directory = "D:/Sauvegardephotos/GooglePhotos2"
    
    # Alternative test directory if default doesn't exist
    current_dir = os.path.dirname(os.path.abspath(__file__))
    test_directory = os.path.join(current_dir, "test_photos")
    
    print("🔍 Google Photos Metadata Analyzer")
    print("=" * 60)
    print("This script analyzes JPEG, JPG, and MP4 files to verify creation date metadata.")
    print("It serves as a quality control tool for the traitement_photos_2.py output.\n")
    
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
    try:
        subprocess.run(['ffprobe', '-version'], capture_output=True, check=True)
        print("✅ ffprobe detected - enhanced video metadata analysis enabled")
        ffprobe_available = True
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  ffprobe not found - video analysis will use system dates only")
        print("💡 Tip: Install FFmpeg from https://ffmpeg.org for better video analysis")
    
    print()
    
    # Ask if user wants to enable GPS location lookup
    geocoding_choice = input("Enable GPS location lookup (city/country names)? This may be slower (y/n) [n]: ").strip().lower()
    enable_geocoding = geocoding_choice == 'y'
    
    if enable_geocoding:
        print("✅ GPS geocoding enabled - will convert coordinates to location names")
    else:
        print("ℹ️  GPS geocoding disabled - will show coordinates only")
    
    print()
    
    # Create analyzer and run analysis
    analyzer = MetadataAnalyzer(directory, enable_geocoding=enable_geocoding)
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
