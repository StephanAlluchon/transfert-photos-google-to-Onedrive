#!/usr/bin/env python3
"""
Quick test script to demonstrate analyze_metadata.py functionality
"""

import os
import sys
from datetime import datetime

def run_analyzer_test():
    """Run the analyzer on current directory"""
    print("🔍 Testing Metadata Analyzer")
    print("=" * 50)
    
    # Import the analyzer
    sys.path.append(os.path.dirname(os.path.abspath(__file__)))
    from analyze_metadata import MetadataAnalyzer
    
    # Test on current directory
    current_dir = os.getcwd()
    analyzer = MetadataAnalyzer(current_dir)
    
    print(f"Analyzing current directory: {current_dir}")
    print()
    
    # Run analysis
    analyzer.analyze_directory()
    
    print("\n" + "=" * 50)
    print("✅ Test completed!")

if __name__ == "__main__":
    run_analyzer_test()
