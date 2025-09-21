# Separated Product Pipeline

The product pipeline has been reorganized into two distinct phases for better clarity and maintainability.

## 🏗️ Architecture

### Phase 1: Data Collection (`phase1_data_collection.py`)
**Purpose**: Scrape product data from Amazon using affiliate links

**What it does**:
- 📋 Processes CSV file with affiliate links
- 🔗 Converts affiliate links to direct product URLs (respects Amazon's terms)
- ⏳ Implements rate limiting (3 seconds between requests)
- 🕷️ Scrapes product details from Amazon:
  - Title, description, price, rating, review count
  - Brand, images, specifications
- 💾 Stores raw product data in database
- 🖼️ Downloads and saves product images locally

**Key Features**:
- ✅ Uses direct product URLs (not affiliate links) for scraping
- ✅ Respectful rate limiting to avoid being blocked
- ✅ Handles duplicate products gracefully
- ✅ Comprehensive error handling and statistics

### Phase 2: Content Generation (`phase2_content_generation.py`)
**Purpose**: Generate enhanced content from scraped product data

**What it does**:
- ✨ Generates smart, product-specific pros and cons
- 🎨 Creates pretty titles (max 8 words with fabric details)
- 📝 Generates Martha Stewart-style product summaries
- 🔍 Extracts missing fields from existing data
- 📂 Assigns product categories

**Key Features**:
- ✅ AI-powered content generation
- ✅ Product-specific insights (not generic)
- ✅ Elegant, readable summaries
- ✅ Comprehensive field extraction

## 🚀 Usage

### Run Complete Pipeline (Both Phases)
```bash
python run_complete_pipeline.py --csv products/product_affilate_links.csv
```

### Run Phase 1 Only (Data Collection)
```bash
python run_complete_pipeline.py --phase 1 --csv products/product_affilate_links.csv
```

### Run Phase 2 Only (Content Generation)
```bash
python run_complete_pipeline.py --phase 2
```

### Run Individual Phases Directly
```bash
# Phase 1 only
python phase1_data_collection.py

# Phase 2 only  
python phase2_content_generation.py
```

## 📊 Pipeline Flow

```
CSV with Affiliate Links
           ↓
    Phase 1: Data Collection
           ↓
    Raw Product Data in DB
           ↓
    Phase 2: Content Generation
           ↓
    Enhanced Product Data
```

## 🔧 Configuration

### Rate Limiting
- **Default**: 3 seconds between requests
- **Configurable**: Modify `self.request_delay` in `DataCollectionPipeline`
- **Purpose**: Be respectful to Amazon's servers

### Database
- **Default**: `multi_platform_products.db`
- **Configurable**: Pass `db_path` parameter to any pipeline class

### CSV Format
Expected CSV columns:
- `affiliate_url`: Amazon affiliate link

## 📈 Statistics

Both phases provide comprehensive statistics:

### Phase 1 Stats
- `processed`: Number of affiliate links processed
- `products_created`: New products added to database
- `products_updated`: Products with data extracted
- `images_downloaded`: Images saved locally
- `errors`: Number of errors encountered

### Phase 2 Stats
- `pros_cons_generated`: Smart features created
- `pretty_titles_generated`: Pretty titles created
- `summaries_generated`: Product summaries created
- `fields_extracted`: Missing fields extracted
- `categories_assigned`: Products categorized

## 🛡️ Error Handling

- **Graceful degradation**: Pipeline continues even if individual products fail
- **Comprehensive logging**: Detailed error messages and statistics
- **User control**: Option to stop between phases if Phase 1 has many errors
- **Retry logic**: Built into individual components

## 🔄 Benefits of Separation

1. **Clarity**: Each phase has a single, clear responsibility
2. **Flexibility**: Run phases independently as needed
3. **Debugging**: Easier to identify issues in specific phases
4. **Maintenance**: Simpler to update individual components
5. **Testing**: Can test each phase in isolation
6. **Rate Limiting**: Clear separation of external API calls vs. internal processing

## 📁 File Structure

```
├── phase1_data_collection.py      # Phase 1: Data Collection
├── phase2_content_generation.py   # Phase 2: Content Generation  
├── run_complete_pipeline.py       # Main orchestrator
├── main_pipeline.py              # Legacy unified pipeline (deprecated)
└── README_SEPARATED_PIPELINE.md  # This documentation
```

## 🚨 Important Notes

- **Affiliate Links**: Phase 1 converts affiliate links to direct product URLs before scraping
- **Rate Limiting**: Always respect Amazon's servers with appropriate delays
- **Data Dependencies**: Phase 2 requires Phase 1 to have run first (or existing data in DB)
- **Legacy Support**: Original `main_pipeline.py` still works but is deprecated
