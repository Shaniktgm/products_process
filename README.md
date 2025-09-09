# Amazon Product Advertising API - Python Implementation

A robust Python implementation for collecting dental products from Amazon using the official Product Advertising API (PA-API) 5.0 SDK.

## 🚀 Features

- **Official Amazon SDK**: Uses `amazon-paapi5-python-sdk` for reliable API access
- **Comprehensive Data Collection**: Searches multiple dental categories
- **SQLite Database**: Stores products with features, categories, and tags
- **Rate Limiting**: Built-in throttling to respect Amazon's limits
- **Data Export**: JSON export functionality
- **Error Handling**: Robust error handling and logging

## 📋 Prerequisites

- Python 3.7 or higher
- Amazon Associates account with PA-API access
- Valid API credentials (Access Key, Secret Key, Partner Tag)

## 🛠️ Installation

### 1. Clone or navigate to the directory
```bash
cd python-amazon-api
```

### 2. Install dependencies
```bash
python3 -m pip install -r requirements.txt
```

### 3. Environment setup
**Option A: Interactive setup (recommended)**
```bash
python3 setup_env.py
```

**Option B: Manual setup**
```bash
cp env.example .env
# Edit .env with your actual credentials
```

**Required Environment Variables:**
- `PAAPI_ACCESS_KEY`: Your Amazon Access Key ID
- `PAAPI_SECRET_ACCESS_KEY`: Your Amazon Secret Access Key  
- `PAAPI_PARTNER_TAG`: Your Amazon Associate ID/Partner Tag

**Optional Environment Variables:**
- `PAAPI_REGION`: AWS region (default: us-east-1)
- `PAAPI_MARKETPLACE`: Amazon marketplace (default: www.amazon.com)
- `PAAPI_HOST`: API host (default: webservices.amazon.com)

## 🔐 Configuration

The setup script creates a `.env` file with your credentials:

```env
PAAPI_ACCESS_KEY=your_access_key_here
PAAPI_SECRET_ACCESS_KEY=your_secret_access_key_here
PAAPI_PARTNER_TAG=your_partner_tag_here
PAAPI_MARKETPLACE=www.amazon.com
DATABASE_PATH=amazon_products.db
```

**Important:** Never commit your actual credentials to version control. The `.env` file should be added to `.gitignore`.

## 📖 Usage

### Full Product Collection
Collect products from all dental categories:
```bash
python main.py
```

### Specific Search
Search for specific keywords:
```bash
python main.py toothpaste
python main.py "dental floss"
python main.py "teeth whitening"
```

### Individual Components

#### Test API Connection
```python
from simple_amazon_api import SimpleAmazonAPI

api = SimpleAmazonAPI()
api.test_api()
```

#### Search Products
```python
products = api.search_products("toothpaste", 10)
```

#### Search Dental Categories
```python
all_products = api.search_dental_categories()
```

#### Database Operations
```python
from database_service import DatabaseService

db = DatabaseService()

# Insert/update product
db.insert_or_update_product(product_data)

# Search products
results = db.search_products("toothpaste")

# Get database stats
stats = db.get_database_stats()

# Export to JSON
db.export_to_json("products.json")
```

## 🗄️ Database Schema

### Products Table
- `id`: Primary key
- `asin`: Amazon Standard Identification Number
- `title`: Product title
- `brand`: Product brand
- `description`: Product description
- `price`: Current price
- `original_price`: Original price (for discounts)
- `rating`: Customer rating (1-5)
- `review_count`: Number of reviews
- `image_url`: Product image URL
- `availability`: Product availability
- `condition`: Product condition
- `is_prime`: Prime eligibility
- `affiliate_link`: Affiliate link with tracking
- `upc`: Universal Product Code
- `isbn`: International Standard Book Number
- `search_timestamp`: When product was searched
- `fetch_timestamp`: When details were fetched
- `created_at`: Record creation time
- `updated_at`: Last update time

### Related Tables
- `product_features`: Product features/bullet points
- `product_categories`: Amazon browse categories
- `product_tags`: Generated tags for search/filtering

## 🔍 Dental Categories Searched

The system automatically searches these dental categories:
- Toothpaste
- Toothbrush
- Mouthwash
- Dental floss
- Oral probiotics
- Teeth whitening
- Dental care
- Oral hygiene
- Bad breath
- Gum health
- Sensitive teeth
- Dental tools

## 📊 Data Collection Process

1. **Initialize**: Set up API client and database
2. **Test Connection**: Verify API access
3. **Category Search**: Search each dental category
4. **Data Storage**: Store products in SQLite database
5. **Feature Extraction**: Extract and store product features
6. **Category Mapping**: Map Amazon browse categories
7. **Tag Generation**: Generate searchable tags
8. **Export**: Create JSON export with timestamp

## 🚦 Rate Limiting

- **Search Requests**: 1 request per second
- **Product Details**: 1 request per second
- **Built-in Delays**: Automatic throttling between requests
- **Error Handling**: Retry logic for rate limit errors

## 📁 Output Files

- `amazon_products.db`: SQLite database
- `amazon_products_YYYYMMDD_HHMMSS.json`: Timestamped JSON export
- `.env`: Environment configuration

## 🐛 Troubleshooting

### Common Issues

1. **Import Errors**
   ```bash
   pip install paapi5-python-sdk python-dotenv
   ```

2. **API Authentication Errors**
   - Verify credentials in `.env` file
   - Check Amazon Associates account status
   - Ensure PA-API access is approved

3. **Database Errors**
   - Check file permissions
   - Verify SQLite installation
   - Check disk space

4. **Rate Limiting**
   - Increase delays between requests
   - Check Amazon API quotas
   - Monitor error responses

### Debug Mode

Enable detailed logging by modifying the API service:
```python
# Add to amazon_api_service.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 🔄 Updating Products

The system automatically:
- Updates existing products by ASIN
- Adds new products
- Refreshes prices and availability
- Updates timestamps

## 📈 Performance

- **Typical Collection**: 200-500 products per run
- **Processing Speed**: ~10 products per second
- **Database Size**: ~1-5 MB for typical collection
- **Memory Usage**: Minimal (streaming processing)

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
- **Amazon API**: Contact Amazon Associates support
- **Python SDK**: Check [amazon-paapi5-python-sdk documentation](https://github.com/amzn/amazon-paapi5-python-sdk)
- **This Implementation**: Open an issue in the repository

## 🔗 Related Links

- [Amazon Product Advertising API](https://webservices.amazon.com/paapi5/documentation/)
- [Amazon Associates Program](https://affiliate-program.amazon.com/)
- [PA-API Python SDK](https://github.com/amzn/amazon-paapi5-python-sdk)
