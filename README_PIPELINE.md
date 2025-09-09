# Automated Product Pipeline

## 🎯 **Complete Solution for Adding New Products**

The `AutomatedProductPipeline` provides a comprehensive, automated solution for adding new products from URL files. It handles everything from data extraction to scoring.

## 🚀 **What It Does**

### ✅ **Complete Automation**
1. **Reads URL files** (CSV, TXT, JSON formats)
2. **Extracts product data** from Amazon URLs
3. **Downloads images locally** in organized format
4. **Populates database** with complete product info
5. **Calculates scores** automatically
6. **Validates data quality** and completeness
7. **Handles duplicates** and errors gracefully

### ✅ **Smart Features**
- **Duplicate Detection**: Won't add same product twice
- **Rate Limiting**: Respects Amazon's servers
- **Error Handling**: Continues processing even if some URLs fail
- **Data Validation**: Ensures quality and completeness
- **Progress Tracking**: Shows real-time progress
- **Bot Detection**: Handles Amazon's anti-bot measures

## 📁 **Supported File Formats**

### **CSV Format** (Recommended)
```csv
url,commission_rate,notes
https://www.amazon.com/dp/B08M9SMVSG,5.0,High quality product
https://www.amazon.com/dp/B079TH5HL3,4.5,Popular item
```

### **TXT Format** (Simple)
```
https://www.amazon.com/dp/B08M9SMVSG
https://www.amazon.com/dp/B079TH5HL3
https://www.amazon.com/dp/B0DZT7NYRY
```

### **JSON Format** (Advanced)
```json
{
  "urls": [
    {
      "url": "https://www.amazon.com/dp/B08M9SMVSG",
      "commission_rate": "5.0",
      "notes": "High quality product"
    }
  ]
}
```

## 🛠️ **Usage**

### **Basic Usage**
```python
from automated_product_pipeline import AutomatedProductPipeline

# Create pipeline
pipeline = AutomatedProductPipeline()

# Process CSV file
results = pipeline.process_url_file("new_products.csv", "csv")

# Process TXT file
results = pipeline.process_url_file("urls.txt", "txt")

# Process JSON file
results = pipeline.process_url_file("products.json", "json")
```

### **Command Line Usage**
```bash
# Process a CSV file
python3 -c "
from automated_product_pipeline import AutomatedProductPipeline
pipeline = AutomatedProductPipeline()
results = pipeline.process_url_file('new_products.csv', 'csv')
print(f'Added {results[\"successful\"]} products')
"
```

## 📊 **What Gets Extracted**

### **Product Information**
- **Title**: Product name
- **Price**: Current price
- **Rating**: Customer rating (1-5 stars)
- **Review Count**: Number of reviews
- **Description**: Product description
- **ASIN**: Amazon product identifier
- **SKU**: Generated SKU (AMZ-{ASIN})

### **Images**
- **Primary Image**: Main product image
- **Additional Images**: All product images
- **Local Storage**: Saved in `/images/products/` directory
- **Format**: `{ASIN}.jpg`, `{ASIN}_1.jpg`, etc.

### **Database Integration**
- **Products Table**: Main product data
- **Platforms Table**: Amazon platform info
- **Product Platforms**: Product-platform relationships
- **Affiliate Links**: Commission rates and URLs
- **Scores**: Automatically calculated

## 🔧 **Configuration**

### **Rate Limiting**
```python
pipeline = AutomatedProductPipeline()
pipeline.request_delay = 3  # 3 seconds between requests
```

### **Custom Headers**
```python
pipeline.session.headers.update({
    'User-Agent': 'Your Custom User Agent'
})
```

## 📈 **Results & Monitoring**

### **Processing Results**
```python
results = {
    'total_urls': 10,
    'successful': 8,
    'failed': 1,
    'duplicates': 1,
    'errors': ['Failed to extract data from URL'],
    'products_added': [
        {
            'id': 39,
            'sku': 'AMZ-B08M9SMVSG',
            'title': 'Product Name',
            'url': 'https://amazon.com/dp/B08M9SMVSG'
        }
    ]
}
```

### **Real-time Progress**
```
🚀 Starting automated product pipeline...
📁 Processing file: new_products.csv
📋 Found 3 URLs to process

📦 Processing 1/3: https://www.amazon.com/dp/B08M9SMVSG
   ✅ Product saved with ID: 39

📦 Processing 2/3: https://www.amazon.com/dp/B079TH5HL3
   ⚠️  Duplicate product found, skipping

📦 Processing 3/3: https://www.amazon.com/dp/B0DZT7NYRY
   ✅ Product saved with ID: 40

📊 Calculating scores for 2 new products...
   ✅ Scores calculated for 2 products

🎉 Processing Complete!
📊 Summary:
   Total URLs: 3
   ✅ Successful: 2
   ❌ Failed: 0
   ⚠️  Duplicates: 1
```

## 🛡️ **Error Handling**

### **Common Issues & Solutions**
- **Bot Detection**: Automatically detected and skipped
- **Broken URLs**: Logged and skipped
- **Missing Data**: Validated and reported
- **Database Errors**: Rolled back automatically
- **Image Download Failures**: Continues with other images

### **Data Quality**
- **Required Fields**: Title, price, rating, review count, image
- **Validation**: Checks for missing data
- **Completeness**: Reports data quality issues
- **Fallbacks**: Uses alternative selectors for extraction

## 🎯 **Best Practices**

### **File Preparation**
1. **Clean URLs**: Ensure URLs are valid Amazon product pages
2. **Include Commission Rates**: Add commission rates for affiliate tracking
3. **Add Notes**: Include notes for product context
4. **Test Small Batches**: Start with 5-10 URLs to test

### **Processing**
1. **Run During Off-Peak**: Process during low-traffic hours
2. **Monitor Progress**: Watch for errors and adjust
3. **Check Results**: Verify data quality after processing
4. **Backup Database**: Always backup before large batches

## 🔄 **Integration with Existing System**

### **Works With**
- **Product Migration Manager**: Handles old/new products
- **Configurable Scoring System**: Calculates scores automatically
- **Database Schema**: Uses existing multi-platform schema
- **Image Organization**: Follows existing image structure

### **File Structure**
```
images/products/
├── 39.jpg, 39_1.jpg, 39_2.jpg    # New product images
├── 40.jpg, 40_1.jpg              # Another new product
└── ...                           # Existing products
```

## 🚀 **Quick Start**

1. **Create URL file** (CSV format recommended)
2. **Run pipeline**: `python3 automated_product_pipeline.py`
3. **Check results**: Review processing summary
4. **Verify data**: Check database and images
5. **Calculate scores**: Scores calculated automatically

The pipeline is now ready for production use! 🎉
