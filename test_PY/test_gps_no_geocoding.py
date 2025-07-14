#!/usr/bin/env python3
"""
Test script for GPS functionality WITHOUT geocoding
"""

import sys
import os
sys.path.append('.')

from analyze_metadata import MetadataAnalyzer

def test_gps_analysis_no_geocoding():
    print("🧪 Testing GPS Analysis WITHOUT Geocoding")
    print("=" * 60)
    
    # Test directory
    test_dir = "test_photos"
    
    if not os.path.exists(test_dir):
        print(f"❌ Test directory '{test_dir}' not found. Run create_gps_test_files.py first.")
        return
    
    print(f"📁 Analyzing test directory: {test_dir}")
    print("ℹ️  Geocoding disabled - showing coordinates only")
    
    # Create analyzer WITHOUT geocoding
    analyzer = MetadataAnalyzer(test_dir, enable_geocoding=False)
    
    # Run analysis
    analyzer.analyze_directory()
    
    print("\n🎯 Test completed - should be much faster without geocoding!")

if __name__ == "__main__":
    test_gps_analysis_no_geocoding()
