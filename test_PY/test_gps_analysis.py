#!/usr/bin/env python3
"""
Test script for GPS functionality
"""

import sys
import os
sys.path.append('.')

from analyze_metadata import MetadataAnalyzer

def test_gps_analysis():
    print("🧪 Testing GPS Analysis Functionality")
    print("=" * 60)
    
    # Test directory
    test_dir = "test_photos"
    
    if not os.path.exists(test_dir):
        print(f"❌ Test directory '{test_dir}' not found. Run create_gps_test_files.py first.")
        return
    
    # Create analyzer with geocoding enabled for testing
    analyzer = MetadataAnalyzer(test_dir, enable_geocoding=True)
    
    # Disable API calls for testing (comment this line to test real API calls)
    # analyzer.get_location_from_coordinates = lambda lat, lon: {"city": "Test City", "country": "Test Country"}
    
    print(f"📁 Analyzing test directory: {test_dir}")
    
    # Run analysis
    analyzer.analyze_directory()
    
    print("\n🎯 Test completed!")

if __name__ == "__main__":
    test_gps_analysis()
