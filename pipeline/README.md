# Organized Product Pipeline

This directory contains the organized two-phase product pipeline.

## 📁 Directory Structure

```
pipeline/
├── phase1_data_collection/          # Phase 1: Data Collection
│   ├── __init__.py
│   └── phase1_data_collection.py    # CSV processing & Amazon scraping
├── phase2_content_generation/       # Phase 2: Content Generation  
│   ├── __init__.py
│   └── phase2_content_generation.py # Pros/cons, titles, summaries
├── run_complete_pipeline.py         # Main orchestrator
├── __init__.py                      # Package initialization
└── README.md                        # This file
```

## 🚀 Usage

### From the pipeline directory:
```bash
cd pipeline
python run_complete_pipeline.py --help
```

### From the root directory:
```bash
python run_pipeline.py --help
```

### Run specific phases:
```bash
# Phase 1 only (data collection)
python run_complete_pipeline.py --phase 1 --csv products/product_affilate_links.csv

# Phase 2 only (content generation)
python run_complete_pipeline.py --phase 2

# Both phases
python run_complete_pipeline.py --csv products/product_affilate_links.csv
```

## 🔧 Phase Details

### Phase 1: Data Collection
- **Purpose**: Scrape product data from Amazon using affiliate links
- **Input**: CSV file with affiliate links
- **Output**: Raw product data in database
- **Key Features**: Rate limiting, direct URL conversion, image downloading

### Phase 2: Content Generation
- **Purpose**: Generate enhanced content from scraped data
- **Input**: Raw product data from database
- **Output**: Enhanced product data with pros/cons, titles, summaries
- **Key Features**: AI-powered content generation, smart field extraction

## 📊 Benefits of Organization

1. **Clear Separation**: Each phase has its own directory and responsibility
2. **Easy Maintenance**: Update individual phases without affecting others
3. **Flexible Execution**: Run phases independently or together
4. **Clean Imports**: Proper Python package structure
5. **Scalable**: Easy to add new phases or modify existing ones
