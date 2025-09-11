# Product Data Generator

A comprehensive Python system for processing product URLs, extracting data, and managing product information with advanced features like AI-powered summaries, enhanced pros/cons, and automated image management.

## 🚀 Features

- **Enhanced Automated Pipeline**: Two-pass data extraction with comprehensive statistics
- **Product Summary Generation**: AI-powered concise product summaries using all available data
- **Enhanced Pros/Cons System**: Categorized features with importance levels and impact scoring
- **Multi-Platform Support**: Handles Amazon, Levana, and other affiliate platforms
- **Image Management**: Local storage and Vercel CDN integration
- **Duplicate Handling**: Multiple affiliate links per product
- **Comprehensive Statistics**: Real-time performance monitoring and success rates
- **Database Management**: SQLite with multi-platform schema

## 📋 Prerequisites

- Python 3.7 or higher
- Valid affiliate URLs (Amazon, Levana, etc.)
- Vercel account (optional, for image hosting)

## 🛠️ Installation

### 1. Clone the repository
```bash
git clone <repository-url>
cd product-data-generator
```

### 2. Install dependencies
```bash
pip install -r requirements.txt
```

### 3. Environment setup
```bash
cp examples/env.example .env
# Edit .env with your Vercel token (optional)
```

## 📖 Usage

### Process Product URLs
```python
from core.enhanced_automated_pipeline import EnhancedAutomatedPipeline

# Initialize pipeline
pipeline = EnhancedAutomatedPipeline()

# Process URLs from CSV file
results = pipeline.process_url_file_enhanced('products/product_affilate_links.csv')
```

### Generate Product Summaries
```python
from core.generate_product_summaries import ProductSummaryGenerator

generator = ProductSummaryGenerator()
results = generator.generate_all_summaries()
```

### Upload Images to Vercel
```python
from image_management.upload_to_vercel import VercelBlobUploader

uploader = VercelBlobUploader(vercel_token="your_token")
results = uploader.upload_all_images()
```

## 🗄️ Database Schema

### Products Table
- `id`: Primary key
- `sku`: Product SKU (generated from URL)
- `title`: Product title
- `description`: Product description
- `price`: Current price
- `rating`: Customer rating (1-5)
- `review_count`: Number of reviews
- `brand`: Product brand
- `primary_image_url`: Primary image URL
- `image_urls`: JSON array of all image URLs
- `product_summary`: AI-generated summary
- `original_vercel_urls`: JSON array of original Vercel URLs
- `created_at`: Record creation time
- `updated_at`: Last update time

### Related Tables
- `product_features`: Enhanced pros/cons with categories
- `product_specifications`: Product specifications
- `product_categories`: Product categories
- `product_images`: Image metadata and URLs
- `affiliate_links`: Multiple affiliate links per product
- `platforms`: Supported platforms (Amazon, Levana, etc.)

## 🔧 Core Components

### Enhanced Automated Pipeline
- **Two-pass extraction**: Initial extraction + enhanced fallback
- **Affiliate validation**: Validates URLs and detects platform types
- **Duplicate handling**: Adds multiple affiliate links to existing products
- **Statistics tracking**: Comprehensive performance monitoring
- **Image processing**: Downloads and manages product images

### Product Summary System
- **Smart extraction**: Uses title, description, features, and specifications
- **Material detection**: Identifies cotton, bamboo, linen, etc.
- **Feature recognition**: Detects cooling, breathable, luxury features
- **Quality indicators**: Incorporates ratings, reviews, and price context
- **Concise format**: One-sentence summaries optimized for readability

### Enhanced Pros/Cons System
- **15 categories**: Quality, comfort, durability, care, etc.
- **5 importance levels**: Critical to minor
- **Impact scoring**: Numerical impact assessment
- **AI analysis**: Intelligent feature categorization
- **Confidence scoring**: Quality assessment of analysis

## 📊 Statistics & Monitoring

The pipeline provides comprehensive statistics:

- **Performance Metrics**: Request times, extraction times, database operations
- **Success Rates**: Overall and platform-specific success rates
- **Error Analysis**: Categorized error tracking and retry counts
- **Data Quality**: Quality scores and validation results
- **Throughput**: Requests per second and processing speed

## 🖼️ Image Management

- **Local Storage**: Images saved with product ID naming (e.g., `1.webp`, `1_1.webp`)
- **Vercel Integration**: Automatic upload to Vercel CDN
- **Metadata Tracking**: Image dimensions, file size, and type
- **Primary Image**: Automatic primary image selection
- **URL Updates**: Database updates with Vercel URLs

## 🔍 Supported Platforms

- **Amazon**: Direct Amazon affiliate links
- **Levana**: Third-party affiliate service
- **Amazon Associates**: Official Amazon Associates links
- **Custom**: Extensible for other platforms

## 📁 Project Structure

```
product-data-generator/
├── core/                           # Core pipeline modules
│   ├── enhanced_automated_pipeline.py
│   ├── generate_product_summaries.py
│   ├── enhanced_pros_cons_system.py
│   ├── multi_platform_database.py
│   └── configurable_scoring_system.py
├── image_management/               # Image handling
├── database/                       # Migration scripts
├── documentation/                  # Project documentation
├── examples/                       # Example files
├── products/                       # Product data files
└── old/                           # Legacy files
```

## 🚦 Rate Limiting

- **Request Delay**: 2 seconds between requests
- **Session Management**: Persistent connections for efficiency
- **Error Handling**: Retry logic with exponential backoff
- **Statistics Tracking**: Monitor rate limiting effectiveness

## 📈 Performance

- **Typical Processing**: 2-5 seconds per URL
- **Success Rate**: 90%+ for valid affiliate URLs
- **Data Quality**: High-quality extraction with two-pass strategy
- **Memory Usage**: Efficient streaming processing
- **Database Size**: Optimized schema with proper indexing

## 🔄 Data Flow

1. **URL Validation**: Check affiliate URL validity
2. **First Pass**: Initial data extraction
3. **Validation**: Assess data quality
4. **Second Pass**: Enhanced extraction if needed
5. **Database Insert**: Store product and related data
6. **Image Processing**: Download and save images
7. **Summary Generation**: Create AI-powered summary
8. **Pros/Cons Enhancement**: Categorize and score features
9. **Statistics Update**: Track performance metrics

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install -r requirements.txt
   ```

2. **Database Errors**
   - Check file permissions
   - Verify SQLite installation
   - Check disk space

3. **Image Download Failures**
   - Check network connectivity
   - Verify image URL validity
   - Check disk space for images

4. **Vercel Upload Issues**
   - Verify Vercel token
   - Check Vercel account status
   - Monitor API rate limits

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License.

## 🆘 Support

For issues related to:
- **Pipeline Processing**: Check the documentation in `documentation/`
- **Database Issues**: Review schema in `core/multi_platform_database.py`
- **Image Management**: See `image_management/` directory
- **General Issues**: Open an issue in the repository