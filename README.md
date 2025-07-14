# Google Photos to OneDrive Transfer Suite

A comprehensive Python solution for processing and analyzing your Google Photos exported files, with complete JSON metadata integration into EXIF data, designed for seamless OneDrive upload.

## 🎯 Purpose

This tool suite automates the processing of Google Photos exports in two specialized steps:
1. **Main Processing** (`traitement_photos_2.py`): Metadata integration and file organization
2. **Advanced Analysis & Modification** (`analyze-modify_metadata.py`): Quality control, geocoding, and metadata enhancement

## 🏗️ Architecture (Updated July 2025)

### 1. 🔧 Main Processor (`traitement_photos_2.py`)

The core processing tool that handles your exported Google Photos files.

#### 🌟 Key Features:
- **Complete EXIF integration** from JSON metadata files
- **Interactive duplicate management** with manual selection
- **Folder structure preservation** from original export
- **Flexible renaming options** with date prefixes
- **GPS coordinate import** from JSON to EXIF
- **Batch processing** for large photo collections

#### 📋 Processing Capabilities:
- **Temporal data**: Creation date/time from JSON
- **Geolocation**: GPS coordinates (latitude/longitude)
- **Descriptive info**: Title, description, keywords
- **Face recognition**: Names of identified people
- **File organization**: Maintains original folder structure

#### 🏷️ Renaming Options:
- **Optional renaming** with date prefix (YYYY-MM-DD)
- **Original names preservation** if preferred
- **Special character cleanup** in filenames
- **Automatic truncation** of overly long names

### 2. 📊 Advanced Analyzer & Modifier (`analyze-modify_metadata.py`)

Comprehensive analysis and modification tool for quality control and metadata enhancement.

#### 🌟 Advanced Features:
- **Complete metadata analysis** (dates, GPS, location info)
- **GPS geocoding** (coordinates → location names via OpenStreetMap API)
- **Location information writing** to EXIF metadata
- **Existing location detection** to avoid unnecessary API calls
- **Intelligent caching** for API optimization (3-decimal precision ~110m)
- **Detailed reporting** and statistics
- **JSON export** for detailed analysis

#### 🔍 Analysis Capabilities:
- **Recursive scanning** of all subdirectories
- **Automatic file counting** by type (.jpg, .jpeg, .mp4)
- **Photo/video ↔ JSON association** detection
- **Detailed reporting** of files with/without metadata
- **GPS verification** and optional geocoding
- **Complete processing statistics**

#### 📍 Geocoding Features:
- **OpenStreetMap integration** (free, no API key required)
- **Smart caching** to reduce API calls
- **Existing location detection** from EXIF data
- **Progress tracking** with real-time feedback
- **Batch processing** with rate limiting
- **Backup creation** before file modification

## 🚀 Quick Start

### Prerequisites
```bash
pip install -r requirements.txt
```

### Basic Workflow

1. **Main Processing**:
   ```bash
   python traitement_photos_2.py
   ```
   - Processes Google Photos exports
   - Integrates JSON metadata into EXIF
   - Imports GPS coordinates
   - Organizes files for OneDrive upload

2. **Advanced Analysis & Geocoding**:
   ```bash
   python analyze-modify_metadata.py
   ```
   - Analyzes metadata quality
   - Performs GPS geocoding (coordinates → location names)
   - Writes location information to EXIF
   - Generates detailed reports

## 📁 Supported File Types

- **Images**: `.jpg`, `.jpeg`
- **Videos**: `.mp4`
- **Metadata**: `.json`, `.supjson` (Google Photos formats)

## 🔧 Configuration

### Main Processor Settings
- **Source directory**: Google Photos export folder
- **Output directory**: Processed files destination
- **Renaming**: Optional date prefixes
- **GPS import**: Automatic from JSON files

### Analyzer Settings
- **Analysis scope**: Recursive directory scanning
- **Geocoding**: Optional location name lookup
- **EXIF writing**: Optional metadata modification
- **Reporting**: JSON export capabilities

## 📊 Output & Reports

### Processing Results
- **Organized file structure** ready for OneDrive
- **Complete EXIF metadata** with dates and GPS
- **Processing statistics** and error reports
- **Duplicate handling** reports

### Analysis Reports
- **Metadata quality assessment**
- **GPS coverage statistics**
- **Location information summary**
- **File validation results**
- **Detailed JSON reports** (optional)

## 🌍 GPS & Location Features

### GPS Coordinate Processing
- **Automatic import** from JSON metadata
- **EXIF GPS format** conversion (DMS format)
- **Coordinate validation** and error handling
- **Batch processing** for large collections

### Location Geocoding
- **OpenStreetMap integration** (free API)
- **City and country lookup** from coordinates
- **Intelligent caching** (3-decimal precision)
- **Existing location detection** to avoid redundant API calls
- **Progress tracking** with real-time feedback
- **Rate limiting** to respect API guidelines

## 🛠️ Technical Details

### Dependencies
- `Pillow` (PIL): Image processing
- `piexif`: EXIF metadata manipulation
- `requests`: HTTP requests for geocoding
- `json`: JSON metadata parsing
- `os`, `shutil`: File operations

### Error Handling
- **Graceful degradation** for missing metadata
- **Backup creation** before file modification
- **Comprehensive logging** of processing steps
- **Error recovery** and reporting

### Performance Optimizations
- **Batch processing** for large photo collections
- **Intelligent caching** for geocoding
- **Memory-efficient** file processing
- **Progress tracking** for long operations

## 🔄 Workflow Integration

### Recommended Process
1. **Export from Google Photos** (Download your data)
2. **Run main processor** (`traitement_photos_2.py`)
3. **Quality analysis** (`analyze-modify_metadata.py`)
4. **Optional geocoding** for location names
5. **Upload to OneDrive** (files ready with complete metadata)

### OneDrive Compatibility
- **Complete EXIF metadata** for proper organization
- **GPS coordinates** for location-based sorting
- **Creation dates** for timeline accuracy
- **Optimized file names** for cloud storage

## 📈 Recent Updates (July 2025)

### Architecture Improvements
- **Separated concerns**: Main processing vs. advanced analysis
- **Modular design**: Specialized tools for specific tasks
- **Enhanced geocoding**: Smart caching and existing location detection
- **Improved performance**: Optimized for large photo collections

### New Features
- **Existing location detection** in EXIF data
- **Smart geocoding** with 3-decimal precision caching
- **Enhanced progress tracking** with location names
- **Comprehensive error handling** and recovery

## 🧪 Testing

The `test_PY/` directory contains test scripts for:
- **Test file creation** with GPS metadata
- **Geocoding analysis validation**
- **Unit tests** for main functions
- **GPS analysis testing**

## 💡 Use Cases

✅ **Ideal for:**
- Long-term archiving of Google Photos
- Migration to other platforms/software
- Preserving metadata lost during exports
- Organization and cleanup of photo collections
- OneDrive migration with complete metadata

⚠️ **Limitations:**
- Requires Google Photos JSON files
- Sequential processing (no parallelization)
- Dependent on Google Photos export structure
- Internet required for geocoding features

## 🤝 Contributing

Feel free to contribute to this project by:
- **Reporting bugs** or issues
- **Suggesting improvements** or new features
- **Submitting pull requests** with enhancements
- **Improving documentation** or examples

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- **OpenStreetMap** for providing free geocoding services
- **Google Photos** for the export functionality
- **Python community** for excellent libraries and tools

---

*Last updated: July 2025*
*Author: Stephan Alluchon*
