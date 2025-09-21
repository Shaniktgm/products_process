# Product Data Generator - Clean Structure

## 📁 Project Structure

```
product-data-generator/
├── main_pipeline.py              # 🚀 Main unified pipeline (A-Z)
├── requirements.txt              # Python dependencies
├── README.md                     # Main project documentation
├── README_UNIFIED_PIPELINE.md    # Pipeline documentation
├── README_CLEAN_STRUCTURE.md     # This file
│
├── core/                         # 🧠 Core processing modules
│   ├── configurable_scoring_system.py
│   ├── dynamic_pros_cons_generator.py
│   ├── enhanced_pros_cons_system.py
│   ├── generate_product_summaries.py
│   └── scoring_config.json
│
├── scripts/                      # 🔧 Utility scripts
│   ├── database/                 # Database management scripts
│   │   ├── add_display_columns.py
│   │   ├── add_vercel_urls_to_images_table.py
│   │   ├── cleanup_redundant_image_columns.py
│   │   ├── migrate_old_to_new_database.py
│   │   ├── populate_display_columns.py
│   │   ├── remove_duplicate_products.py
│   │   └── remove_unused_score_columns.py
│   │
│   ├── utilities/                # General utility scripts
│   │   ├── simple_product_importer.py
│   │   ├── standardize_skus.py
│   │   ├── test_sku_generation.py
│   │   └── update_pretty_titles.py
│   │
│   └── legacy/                   # Legacy/deprecated scripts
│       ├── enhanced_automated_pipeline.py
│       ├── improved_enhanced_pros_cons.py
│       ├── multi_platform_database.py
│       ├── replace_with_structured_pros_cons.py
│       └── scoring_config.json.backup
│
├── database/                     # 📊 Database schemas and migrations
│   ├── add_summary_field.sql
│   └── fix_downloaded_images.sql
│
├── documentation/                # 📚 Documentation
│   ├── MULTI_PLATFORM_SCHEMA.md
│   ├── PRODUCT_SUMMARY_SYSTEM.md
│   ├── README_ENHANCED_PIPELINE.md
│   ├── README_ENHANCED_PROS_CONS.md
│   ├── README_PIPELINE.md
│   └── vercel_upload_guide.md
│
├── examples/                     # 📝 Example files and templates
│   ├── env.example
│   ├── example_new_products.csv
│   ├── product_template.json
│   └── test_new_urls.csv
│
├── image_management/             # 🖼️ Image handling utilities
│   ├── update_local_to_vercel.py
│   └── upload_to_vercel.py
│
├── images/                       # 📸 Product images
│   ├── products/                 # Current product images
│   └── products_old/             # Legacy images
│
├── products/                     # 📦 Product data files
│   ├── old_data/                 # Historical product data
│   └── product_affilate_links.csv # Main affiliate links file
│
├── old/                          # 🗄️ Legacy files (archived)
│   └── [various legacy files]
│
└── multi_platform_products.db    # 🗃️ Main SQLite database
```

## 🚀 Quick Start

### Run the Complete Pipeline
```bash
python3 main_pipeline.py
```

This single command will:
1. Process affiliate links from CSV
2. Extract product details from Amazon URLs
3. Download product images
4. Generate enhanced pros/cons
5. Create Martha Stewart-style summaries
6. Calculate product scores
7. Generate pretty titles

## 📋 Script Categories

### 🧠 Core Modules (`core/`)
- **Essential processing modules** used by the main pipeline
- **Do not run directly** - called by main_pipeline.py
- Contains: scoring, pros/cons generation, summaries

### 🔧 Database Scripts (`scripts/database/`)
- **Database management and maintenance**
- Run individually as needed for specific tasks
- Examples: adding columns, cleaning data, migrations

### 🛠️ Utility Scripts (`scripts/utilities/`)
- **General purpose utilities**
- Run individually for specific tasks
- Examples: SKU standardization, title updates

### 🗄️ Legacy Scripts (`scripts/legacy/`)
- **Deprecated or old versions**
- **Do not use** - kept for reference only
- Will be removed in future versions

## 🎯 Main Entry Points

### 1. Main Pipeline (Recommended)
```bash
python3 main_pipeline.py
```
**Use this for:** Complete A-Z processing of all products

### 2. Database Scripts (As Needed)
```bash
python3 scripts/database/add_display_columns.py
python3 scripts/database/cleanup_redundant_image_columns.py
```
**Use these for:** Specific database maintenance tasks

### 3. Utility Scripts (As Needed)
```bash
python3 scripts/utilities/standardize_skus.py
python3 scripts/utilities/update_pretty_titles.py
```
**Use these for:** Specific utility tasks

## 📊 Data Flow

```
CSV Files → main_pipeline.py → Core Modules → Database
    ↓              ↓              ↓           ↓
Affiliate    Product        Enhanced    SQLite DB
Links        Extraction     Content     + Images
```

## 🔧 Configuration

- **Main Config**: `core/scoring_config.json`
- **Database**: `multi_platform_products.db`
- **Images**: `images/products/`
- **Input**: `products/product_affilate_links.csv`

## 📈 Benefits of Clean Structure

1. **Single Entry Point**: `main_pipeline.py` handles everything
2. **Organized Scripts**: Clear categorization by purpose
3. **No Redundancy**: Removed duplicate functionality
4. **Easy Maintenance**: Scripts grouped by function
5. **Clear Documentation**: Each folder has a specific purpose
6. **Legacy Separation**: Old scripts preserved but separated

## 🚫 What NOT to Use

- ❌ Scripts in `scripts/legacy/` (deprecated)
- ❌ Scripts in `old/` folder (archived)
- ❌ Individual core modules (use main_pipeline.py instead)
- ❌ Multiple pipeline scripts (use main_pipeline.py only)

## ✅ What TO Use

- ✅ `main_pipeline.py` for complete processing
- ✅ `scripts/database/` for database maintenance
- ✅ `scripts/utilities/` for specific tasks
- ✅ `core/` modules (automatically used by main pipeline)

## 🎉 Result

**One clean, organized codebase with a single entry point that handles everything A-Z!**
