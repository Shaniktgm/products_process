# 📁 Project Structure - Clean & Organized

## 🎯 **Organized by Theme**

The project has been cleaned up and organized into logical folders by functionality:

### 📁 **CORE** (6 files) - Essential System Files
- `configurable_scoring_system.py` - Product scoring system
- `enhanced_automated_pipeline.py` - **Main pipeline** for processing new products
- `enhanced_pros_cons_system.py` - Enhanced pros/cons with categories and scores
- `generate_product_summaries.py` - One-sentence product summaries
- `multi_platform_database.py` - Database schema and operations
- `scoring_config.json` - Scoring configuration

### 📁 **IMAGE_MANAGEMENT** (2 files) - Current Image Tools Only
- `update_local_to_vercel.py` - Update local URLs to Vercel URLs
- `upload_to_vercel.py` - Upload images to Vercel blob storage

### 📁 **DATABASE** (2 files) - SQL Scripts
- `add_summary_field.sql` - Add product_summary column
- `fix_downloaded_images.sql` - Fix image URLs for specific products

### 📁 **DOCUMENTATION** (6 files) - Current Documentation
- `MULTI_PLATFORM_SCHEMA.md` - Database schema documentation
- `PRODUCT_SUMMARY_SYSTEM.md` - Product summary system guide
- `README_ENHANCED_PIPELINE.md` - Enhanced pipeline documentation
- `README_ENHANCED_PROS_CONS.md` - Enhanced pros/cons system guide
- `README_PIPELINE.md` - Legacy pipeline documentation
- `vercel_upload_guide.md` - Vercel upload instructions

### 📁 **EXAMPLES** (4 files) - Templates & Samples
- `env.example` - Environment variables template
- `example_new_products.csv` - Sample CSV with product URLs
- `product_template.json` - Product data template
- `test_new_urls.csv` - Test URLs for pipeline

### 📁 **OLD** (11 files) - Legacy & Completed Scripts
- `amazon_products.db` - Old Amazon database
- `check_missing_images.py` - Legacy image checker
- `download_all_webflow_images.py` - **COMPLETED** Webflow migration
- `download_webflow_images.py` - Legacy Webflow downloader
- `enhanced_products.db` - Old enhanced database
- `sample_multi_platform.db` - Sample database
- `update_downloaded_images.py` - Legacy image updater
- `update_vercel_urls.py` - Legacy Vercel updater
- `README_MIGRATION.md` - Legacy migration docs
- `WEBFLOW_IMAGES_SUMMARY.md` - **COMPLETED** Webflow summary
- `WEBFLOW_MIGRATION_COMPLETE.md` - **COMPLETED** Webflow migration

## 🚀 **Main Entry Points**

### **For New Products**
```python
from core.enhanced_automated_pipeline import EnhancedAutomatedPipeline

pipeline = EnhancedAutomatedPipeline()
results = pipeline.process_url_file_enhanced('new_products.csv', 'csv')
```

### **For Image Management**
```python
from image_management.upload_to_vercel import VercelBlobUploader
from image_management.update_local_to_vercel import LocalToVercelUpdater

# Upload images
uploader = VercelBlobUploader()
uploader.upload_all_images()

# Update URLs
updater = LocalToVercelUpdater()
updater.update_local_to_vercel()
```

### **For Database Operations**
```python
from core.multi_platform_database import MultiPlatformDatabaseService

db = MultiPlatformDatabaseService()
products = db.get_products()
```

## 📊 **Cleanup Summary**

### **Before Cleanup**
- **Scattered files** in root directory
- **7 scripts** in image management (too many)
- **Mixed legacy and current** files
- **Hard to navigate** structure

### **After Cleanup**
- **Organized by theme** (core, image_management, database, etc.)
- **2 essential scripts** in image management
- **11 legacy files** moved to 'old' folder
- **Clear separation** of current vs legacy code

## 🎯 **Benefits**

1. **Easy Navigation**: Find files by functionality
2. **Clear Separation**: Current vs legacy code
3. **Reduced Clutter**: Only essential files in main folders
4. **Better Maintenance**: Organized structure for future development
5. **Focused Development**: Work with relevant files only

## 🔧 **Usage Guidelines**

- **Use CORE** for main system functionality
- **Use IMAGE_MANAGEMENT** for current image operations
- **Use DATABASE** for SQL scripts and migrations
- **Use DOCUMENTATION** for current guides and references
- **Use EXAMPLES** for templates and samples
- **Check OLD** for legacy code and completed tasks

**The project is now clean, organized, and easy to navigate!** 🎉
