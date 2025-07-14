#!/usr/bin/env python3
"""
Test script for analyze_metadata.py
Creates sample files to demonstrate the analyzer functionality
"""

import os
from datetime import datetime
from PIL import Image
import piexif

def create_test_files():
    """Create test files for analysis"""
    test_dir = "test_photos"
    os.makedirs(test_dir, exist_ok=True)
    
    # Create a simple JPEG with EXIF data
    img = Image.new('RGB', (100, 100), color='red')
    
    # Create EXIF data
    exif_dict = {"0th": {}, "Exif": {}, "GPS": {}, "1st": {}, "thumbnail": None}
    
    # Add date to EXIF
    date_string = "2023:12:15 14:30:00"
    exif_dict["Exif"][piexif.ExifIFD.DateTimeOriginal] = date_string.encode('utf-8')
    exif_dict["Exif"][piexif.ExifIFD.DateTimeDigitized] = date_string.encode('utf-8')
    exif_dict["0th"][piexif.ImageIFD.DateTime] = date_string.encode('utf-8')
    
    # Save image with EXIF
    exif_bytes = piexif.dump(exif_dict)
    img.save(os.path.join(test_dir, "test_with_exif.jpg"), exif=exif_bytes)
    
    # Create a simple JPEG without EXIF
    img.save(os.path.join(test_dir, "test_without_exif.jpg"))
    
    # Create a simple text file (to be ignored)
    with open(os.path.join(test_dir, "readme.txt"), "w") as f:
        f.write("Test files created for metadata analysis")
    
    print(f"✅ Test files created in '{test_dir}':")
    print("  - test_with_exif.jpg (with EXIF date)")
    print("  - test_without_exif.jpg (without EXIF date)")
    print("  - readme.txt (will be ignored)")
    print()

if __name__ == "__main__":
    create_test_files()
