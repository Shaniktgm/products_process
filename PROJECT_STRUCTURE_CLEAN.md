# Product Data Generator - Clean Project Structure

## 📁 Directory Structure

```
product-data-generator/
├── core/                           # Core pipeline and database modules
│   ├── enhanced_automated_pipeline.py    # Main pipeline with statistics
│   ├── generate_product_summaries.py     # Product summary generation
│   ├── enhanced_pros_cons_system.py      # Enhanced pros/cons system
│   ├── multi_platform_database.py        # Database schema and operations
│   ├── configurable_scoring_system.py    # Product scoring system
│   └── scoring_config.json               # Scoring configuration
│
├── image_management/               # Image handling and Vercel upload
│   ├── upload_to_vercel.py              # Vercel blob upload functionality
│   └── update_local_to_vercel.py        # Local to Vercel URL updates
│
├── database/                       # Database migration scripts
│   ├── add_summary_field.sql            # Add product summary field
│   └── fix_downloaded_images.sql        # Fix image path issues
│
├── documentation/                  # Project documentation
│   ├── MULTI_PLATFORM_SCHEMA.md         # Database schema documentation
│   ├── PRODUCT_SUMMARY_SYSTEM.md        # Summary system documentation
│   ├── README_ENHANCED_PIPELINE.md      # Pipeline documentation
│   ├── README_ENHANCED_PROS_CONS.md     # Pros/cons system documentation
│   ├── README_PIPELINE.md               # General pipeline docs
│   └── vercel_upload_guide.md           # Vercel upload guide
│
├── examples/                       # Example files and templates
│   ├── env.example                      # Environment variables template
│   ├── example_new_products.csv         # Example product URLs
│   ├── product_template.json            # Product data template
│   └── test_new_urls.csv                # Test URLs
│
├── products/                       # Product data files
│   ├── old_data/                        # Legacy product data
│   └── product_affilate_links.csv       # Current affiliate links
│
├── old/                           # Legacy and deprecated files
│   ├── *.py                            # Old scripts and modules
│   ├── *.db                            # Old database files
│   └── *.md                            # Old documentation
│
├── images/                        # Product images (gitignored)
│   ├── products/                       # Current product images
│   └── products_old/                   # Legacy product images
│
├── .gitignore                     # Git ignore rules
├── README.md                      # Main project documentation
├── requirements.txt               # Python dependencies
└── PROJECT_STRUCTURE_CLEAN.md    # This file
```

## 🚀 Core Components

### Enhanced Automated Pipeline
- **File**: `core/enhanced_automated_pipeline.py`
- **Purpose**: Main pipeline for processing product URLs
- **Features**: 
  - Two-pass data extraction
  - Affiliate URL validation
  - Duplicate SKU handling
  - Comprehensive statistics tracking
  - Image processing and Vercel upload

### Product Summary System
- **File**: `core/generate_product_summaries.py`
- **Purpose**: Generate concise product summaries
- **Features**:
  - Uses all available product data
  - Material and feature extraction
  - Quality indicators and value assessment

### Enhanced Pros/Cons System
- **File**: `core/enhanced_pros_cons_system.py`
- **Purpose**: Categorize and enhance product features
- **Features**:
  - 15 feature categories
  - Importance levels and impact scoring
  - AI-powered analysis

### Database System
- **File**: `core/multi_platform_database.py`
- **Purpose**: Database schema and operations
- **Features**:
  - Multi-platform support
  - Product images table
  - Affiliate links tracking
  - Comprehensive product data

## 📊 Key Features

1. **Comprehensive Statistics**: Real-time performance monitoring
2. **Two-Pass Extraction**: Improved data quality
3. **Affiliate Validation**: Support for multiple affiliate types
4. **Image Management**: Local storage and Vercel upload
5. **Duplicate Handling**: Multiple affiliate links per product
6. **Enhanced Summaries**: AI-powered product descriptions

## 🔧 Usage

```bash
# Process new product URLs
python3 -c "
from core.enhanced_automated_pipeline import EnhancedAutomatedPipeline
pipeline = EnhancedAutomatedPipeline()
results = pipeline.process_url_file_enhanced('products/product_affilate_links.csv')
"

# Generate product summaries
python3 core/generate_product_summaries.py

# Upload images to Vercel
python3 image_management/upload_to_vercel.py
```

## 📝 Notes

- Database files (`*.db`) are gitignored
- Image directories are gitignored
- Test files are gitignored
- Legacy files are moved to `old/` directory
- All core functionality is in the `core/` directory
