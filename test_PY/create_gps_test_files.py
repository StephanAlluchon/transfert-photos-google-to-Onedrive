#!/usr/bin/env python3
"""
Create test files with GPS metadata for testing the analyze_metadata.py script
"""

import os
import json
from datetime import datetime
from PIL import Image
import piexif

def create_test_photo_with_gps(file_path, lat, lon, city_name):
    """Create a test JPEG file with GPS EXIF data"""
    
    # Create a simple test image
    img = Image.new('RGB', (800, 600), color='blue')
    
    # Create EXIF data with GPS coordinates
    exif_dict = {
        "0th": {
            piexif.ImageIFD.Make: "Test Camera",
            piexif.ImageIFD.Model: "GPS Test Model",
            piexif.ImageIFD.DateTime: "2023:07:15 14:30:00"
        },
        "Exif": {
            piexif.ExifIFD.DateTimeOriginal: "2023:07:15 14:30:00",
            piexif.ExifIFD.DateTimeDigitized: "2023:07:15 14:30:00"
        },
        "GPS": {}
    }
    
    # Convert decimal degrees to GPS format (degrees, minutes, seconds)
    def decimal_to_dms(decimal_degree):
        degrees = int(abs(decimal_degree))
        minutes_float = (abs(decimal_degree) - degrees) * 60
        minutes = int(minutes_float)
        seconds = int((minutes_float - minutes) * 60 * 100)  # * 100 pour la précision
        
        return [(degrees, 1), (minutes, 1), (seconds, 100)]
    
    # Latitude
    lat_dms = decimal_to_dms(lat)
    lat_ref = 'N' if lat >= 0 else 'S'
    
    # Longitude  
    lon_dms = decimal_to_dms(lon)
    lon_ref = 'E' if lon >= 0 else 'W'
    
    # Add GPS data to EXIF
    exif_dict["GPS"] = {
        piexif.GPSIFD.GPSVersionID: (2, 0, 0, 0),
        piexif.GPSIFD.GPSLatitudeRef: lat_ref,
        piexif.GPSIFD.GPSLatitude: lat_dms,
        piexif.GPSIFD.GPSLongitudeRef: lon_ref,
        piexif.GPSIFD.GPSLongitude: lon_dms,
        piexif.GPSIFD.GPSTimeStamp: [(14, 1), (30, 1), (0, 1)],
        piexif.GPSIFD.GPSDateStamp: "2023:07:15"
    }
    
    # Convert EXIF dict to bytes
    exif_bytes = piexif.dump(exif_dict)
    
    # Save image with EXIF data
    img.save(file_path, "JPEG", exif=exif_bytes, quality=95)
    
    print(f"✅ Created test photo: {os.path.basename(file_path)} ({city_name})")
    print(f"   GPS: {lat:.6f}, {lon:.6f}")

def create_test_video_metadata(file_path, lat, lon, city_name):
    """Create a test JSON metadata file for a video (simulating Google Photos format)"""
    
    metadata = {
        "title": f"Test Video - {city_name}",
        "description": f"Test video taken in {city_name}",
        "creationTime": {
            "timestamp": "1689428200",
            "formatted": "Jul 15, 2023, 2:30:00 PM UTC"
        },
        "geoData": {
            "latitude": lat,
            "longitude": lon,
            "altitude": 100.0,
            "latitudeSpan": 0.0,
            "longitudeSpan": 0.0
        },
        "geoDataExif": {
            "latitude": lat,
            "longitude": lon,
            "altitude": 100.0,
            "latitudeSpan": 0.0,
            "longitudeSpan": 0.0
        }
    }
    
    # Save metadata JSON
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, indent=2)
    
    print(f"✅ Created test video metadata: {os.path.basename(file_path)} ({city_name})")
    print(f"   GPS: {lat:.6f}, {lon:.6f}")

def main():
    # Create test_photos directory
    test_dir = "test_photos"
    os.makedirs(test_dir, exist_ok=True)
    
    print("🌍 Creating test files with GPS metadata...")
    print("=" * 60)
    
    # Test locations around the world
    test_locations = [
        (48.8566, 2.3522, "Paris, France"),       # Tour Eiffel
        (40.7589, -73.9851, "New York, USA"),     # Times Square  
        (35.6762, 139.6503, "Tokyo, Japan"),      # Tokyo
        (-33.8688, 151.2093, "Sydney, Australia"), # Sydney Opera House
        (51.5074, -0.1278, "London, UK"),         # London
        (41.9028, 12.4964, "Rome, Italy"),        # Colosseum
        (-22.9068, -43.1729, "Rio de Janeiro, Brazil"), # Christ the Redeemer
    ]
    
    # Create test photos with GPS
    for i, (lat, lon, city) in enumerate(test_locations):
        # Create photo
        photo_name = f"test_photo_{i+1}_{city.split(',')[0].replace(' ', '_').lower()}.jpg"
        photo_path = os.path.join(test_dir, photo_name)
        create_test_photo_with_gps(photo_path, lat, lon, city)
        
        # Create video metadata (simulating Google Photos format)
        json_name = f"test_video_{i+1}_{city.split(',')[0].replace(' ', '_').lower()}.mp4.json"
        json_path = os.path.join(test_dir, json_name)
        create_test_video_metadata(json_path, lat, lon, city)
    
    # Create a photo without GPS for comparison
    img_no_gps = Image.new('RGB', (800, 600), color='red')
    no_gps_path = os.path.join(test_dir, "test_photo_no_gps.jpg")
    img_no_gps.save(no_gps_path, "JPEG", quality=95)
    print(f"✅ Created test photo without GPS: {os.path.basename(no_gps_path)}")
    
    print(f"\n🎯 Test files created in '{test_dir}' directory")
    print(f"📊 Total files: {len(os.listdir(test_dir))}")
    print(f"💡 Run 'python analyze_metadata.py' and specify '{test_dir}' to test GPS features!")

if __name__ == "__main__":
    main()
