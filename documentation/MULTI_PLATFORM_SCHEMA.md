# Multi-Platform Product Catalog Database Schema

## Overview

This document describes the new multi-platform database schema designed to support products from Amazon, D2C brands, and other e-commerce platforms. The schema is flexible, scalable, and platform-agnostic while maintaining support for platform-specific features.

## Key Features

- **Platform Agnostic**: Supports Amazon, D2C, Walmart, Target, Etsy, Shopify, and custom platforms
- **Flexible Affiliate System**: Multiple affiliate links per product with platform-specific commission rates
- **Comprehensive Product Data**: Rich product information including specifications, features, and media
- **SEO Optimized**: Built-in support for slugs, meta data, and search optimization
- **Performance Optimized**: Proper indexing and relational design
- **Migration Ready**: Tools to migrate existing Amazon-focused data

## Database Schema

### Core Tables

#### 1. `platforms` Table
Stores information about different e-commerce platforms.

```sql
CREATE TABLE platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name TEXT UNIQUE NOT NULL,           -- 'amazon', 'd2c', 'walmart', etc.
    display_name TEXT NOT NULL,          -- 'Amazon', 'Direct-to-Consumer', etc.
    base_url TEXT,                       -- Platform's base URL
    api_endpoint TEXT,                   -- API endpoint for data fetching
    commission_rate REAL DEFAULT 0.0,    -- Default commission rate
    is_active BOOLEAN DEFAULT TRUE,      -- Platform status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

**Default Platforms:**
- Amazon (4% commission)
- Direct-to-Consumer (10% commission)
- Walmart (3% commission)
- Target (5% commission)
- Etsy (8% commission)
- Shopify Store (12% commission)
- Other Platform (5% commission)

#### 2. `products` Table
Main product catalog with platform-agnostic fields.

```sql
CREATE TABLE products (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    sku TEXT UNIQUE NOT NULL,            -- Universal SKU
    title TEXT NOT NULL,                 -- Product title
    brand TEXT,                          -- Product brand
    description TEXT,                    -- Full description
    short_description TEXT,              -- Brief description
    slug TEXT UNIQUE,                    -- URL-friendly identifier
    
    -- Pricing
    price REAL,                          -- Current price
    original_price REAL,                 -- Original price
    discount_percentage INTEGER,         -- Discount percentage
    currency TEXT DEFAULT 'USD',         -- Currency code
    
    -- Ratings & Reviews
    rating REAL,                         -- Average rating (0-5)
    review_count INTEGER,                -- Number of reviews
    
    -- Media
    primary_image_url TEXT,              -- Main product image
    image_urls TEXT,                     -- JSON array of image URLs
    video_urls TEXT,                     -- JSON array of video URLs
    
    -- Availability
    availability TEXT,                   -- Stock availability
    stock_status TEXT,                   -- Detailed stock info
    stock_quantity INTEGER,              -- Available quantity
    
    -- Product Details
    condition TEXT,                      -- Product condition
    warranty TEXT,                       -- Warranty information
    return_policy TEXT,                  -- Return policy
    shipping_info TEXT,                  -- Shipping details
    age_recommendation TEXT,             -- Age recommendations
    ingredients TEXT,                    -- Product ingredients
    
    -- Physical Properties
    weight REAL,                         -- Product weight
    dimensions TEXT,                     -- JSON: {"length": 10, "width": 5, "height": 2}
    color TEXT,                          -- Product color
    material TEXT,                       -- Material composition
    size TEXT,                           -- Product size
    
    -- SEO & Marketing
    meta_title TEXT,                     -- SEO title
    meta_description TEXT,               -- SEO description
    tags TEXT,                           -- JSON array of tags
    deal_badges TEXT,                    -- JSON array of badges
    
    -- Status
    is_active BOOLEAN DEFAULT TRUE,      -- Product status
    is_featured BOOLEAN DEFAULT FALSE,   -- Featured product
    is_bestseller BOOLEAN DEFAULT FALSE, -- Bestseller status
    
    -- Timestamps
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### 3. `product_platforms` Table
Links products to specific platforms with platform-specific data.

```sql
CREATE TABLE product_platforms (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,                  -- Reference to products table
    platform_id INTEGER,                 -- Reference to platforms table
    platform_sku TEXT,                   -- Platform-specific SKU (ASIN, etc.)
    platform_url TEXT,                   -- Product URL on platform
    platform_price REAL,                 -- Price on this platform
    platform_availability TEXT,          -- Availability on platform
    platform_rating REAL,                -- Rating on platform
    platform_review_count INTEGER,       -- Review count on platform
    platform_specific_data TEXT,         -- JSON for platform-specific fields
    is_primary BOOLEAN DEFAULT FALSE,    -- Primary platform for this product
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE,
    UNIQUE(product_id, platform_id)
);
```

**Platform-Specific Data Examples:**
- **Amazon**: `{"is_prime": true, "best_seller_rank": 1234, "free_shipping": true}`
- **D2C**: `{"direct_shipping": true, "customization_available": true, "sustainability_score": 8.5}`
- **Walmart**: `{"pickup_available": true, "walmart_plus_eligible": true}`
- **Etsy**: `{"handmade": true, "vintage": false, "customizable": true}`

#### 4. `affiliate_links` Table
Manages affiliate links for different platforms and link types.

```sql
CREATE TABLE affiliate_links (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,                  -- Reference to products table
    platform_id INTEGER,                 -- Reference to platforms table
    link_type TEXT NOT NULL,             -- 'web', 'mobile', 'desktop'
    affiliate_url TEXT NOT NULL,         -- Affiliate URL
    commission_rate REAL,                -- Commission rate for this link
    estimated_commission REAL,           -- Estimated commission amount
    is_active BOOLEAN DEFAULT TRUE,      -- Link status
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE
);
```

### Supporting Tables

#### 5. `product_features` Table
Stores product features and specifications.

```sql
CREATE TABLE product_features (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,                  -- Reference to products table
    feature_text TEXT NOT NULL,          -- Feature description
    feature_type TEXT DEFAULT 'general', -- 'pro', 'con', 'specification', 'general'
    display_order INTEGER DEFAULT 0,     -- Display order
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);
```

#### 6. `product_categories` Table
Product categorization system.

```sql
CREATE TABLE product_categories (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,                  -- Reference to products table
    category_name TEXT NOT NULL,         -- Category name
    category_path TEXT,                  -- Full category hierarchy
    is_primary BOOLEAN DEFAULT FALSE,    -- Primary category
    display_order INTEGER DEFAULT 0,     -- Display order
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);
```

#### 7. `product_specifications` Table
Detailed product specifications.

```sql
CREATE TABLE product_specifications (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,                  -- Reference to products table
    spec_name TEXT NOT NULL,             -- Specification name
    spec_value TEXT NOT NULL,            -- Specification value
    spec_unit TEXT,                      -- Unit of measurement
    display_order INTEGER DEFAULT 0,     -- Display order
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
);
```

#### 8. `product_reviews` Table
Aggregated product reviews from different platforms.

```sql
CREATE TABLE product_reviews (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    product_id INTEGER,                  -- Reference to products table
    platform_id INTEGER,                 -- Reference to platforms table
    review_text TEXT,                    -- Review content
    rating INTEGER,                      -- Review rating (1-5)
    reviewer_name TEXT,                  -- Reviewer name
    review_date TEXT,                    -- Review date
    is_verified BOOLEAN DEFAULT FALSE,   -- Verified purchase
    helpful_votes INTEGER DEFAULT 0,     -- Helpful votes
    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
    FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE
);
```

## Usage Examples

### Adding a Product from Multiple Platforms

```python
from multi_platform_database import MultiPlatformDatabaseService

db = MultiPlatformDatabaseService()

# Product data with multiple platforms
product_data = {
    'sku': 'UNI-001',
    'title': 'Wireless Bluetooth Headphones',
    'brand': 'TechBrand',
    'description': 'High-quality wireless headphones...',
    'slug': 'techbrand-wireless-bluetooth-headphones',
    'price': 99.99,
    'original_price': 149.99,
    'discount_percentage': 33,
    'currency': 'USD',
    'rating': 4.5,
    'review_count': 1250,
    'primary_image_url': 'https://example.com/headphones.jpg',
    'image_urls': ['https://example.com/headphones-1.jpg', 'https://example.com/headphones-2.jpg'],
    'availability': 'In Stock',
    'stock_status': 'Available',
    'condition': 'New',
    'warranty': '2 Years',
    'return_policy': '30 Days',
    'weight': 0.5,
    'dimensions': {'length': 8, 'width': 6, 'height': 2},
    'color': 'Black',
    'material': 'Plastic',
    'size': 'One Size',
    'tags': ['electronics', 'audio', 'wireless'],
    'deal_badges': ['Best Seller', 'Sale'],
    'is_active': True,
    'is_featured': True,
    'is_bestseller': True,
    'features': [
        {'text': '30-hour battery life', 'type': 'pro'},
        {'text': 'Noise cancellation', 'type': 'pro'},
        {'text': 'Premium sound quality', 'type': 'pro'}
    ],
    'categories': ['Electronics', 'Audio'],
    'specifications': {
        'Battery Life': '30 hours',
        'Connectivity': 'Bluetooth 5.0',
        'Range': '30 feet',
        'Weight': '0.5 lbs'
    },
    'platforms': [
        {
            'platform_id': 1,  # Amazon
            'platform_sku': 'B08XYZ123',
            'platform_url': 'https://amazon.com/dp/B08XYZ123',
            'platform_price': 99.99,
            'platform_availability': 'In Stock',
            'platform_rating': 4.5,
            'platform_review_count': 1250,
            'platform_specific_data': {
                'is_prime': True,
                'best_seller_rank': 1234,
                'free_shipping': True
            },
            'is_primary': True
        },
        {
            'platform_id': 2,  # D2C
            'platform_sku': 'TB-WH-001',
            'platform_url': 'https://techbrand.com/headphones',
            'platform_price': 89.99,
            'platform_availability': 'In Stock',
            'platform_rating': 4.7,
            'platform_review_count': 89,
            'platform_specific_data': {
                'direct_shipping': True,
                'customization_available': True,
                'sustainability_score': 8.5
            },
            'is_primary': False
        }
    ],
    'affiliate_links': [
        {
            'platform_id': 1,  # Amazon
            'link_type': 'web',
            'affiliate_url': 'https://amazon.com/dp/B08XYZ123?tag=yourtag',
            'commission_rate': 0.04,
            'estimated_commission': 4.00
        },
        {
            'platform_id': 2,  # D2C
            'link_type': 'web',
            'affiliate_url': 'https://techbrand.com/headphones?ref=yourref',
            'commission_rate': 0.10,
            'estimated_commission': 9.00
        }
    ]
}

# Insert the product
product_id = db.insert_product(product_data)
```

### Querying Products by Platform

```python
# Get all Amazon products
amazon_products = db.get_products(platform='amazon', limit=20)

# Get all D2C products
d2c_products = db.get_products(platform='d2c', limit=20)

# Get all products (all platforms)
all_products = db.get_products(limit=50)
```

### Getting Database Statistics

```python
stats = db.get_database_stats()
print(f"Total products: {stats['total_products']}")
print(f"Total platforms: {stats['total_platforms']}")
print("Platform breakdown:")
for platform in stats['platform_breakdown']:
    print(f"  - {platform['display_name']}: {platform['product_count']} products")
```

## Migration from Existing Schema

### Migrating Amazon Products Database

```bash
# Migrate from amazon_products.db
python3 migrate_to_multi_platform.py amazon_products.db

# Migrate from enhanced_products.db
python3 migrate_to_multi_platform.py enhanced_products.db

# Migrate both databases
python3 migrate_to_multi_platform.py
```

### Migration Process

1. **Data Conversion**: Converts Amazon-specific fields to platform-agnostic format
2. **Platform Mapping**: Maps existing data to Amazon platform in new schema
3. **Relationship Creation**: Creates proper relationships between products, platforms, and affiliate links
4. **Data Validation**: Ensures data integrity during migration

## Benefits of Multi-Platform Schema

### 1. **Scalability**
- Easy to add new platforms without schema changes
- Supports unlimited products per platform
- Flexible affiliate link management

### 2. **Platform Independence**
- Not tied to Amazon-specific fields
- Supports D2C brands and custom platforms
- Platform-specific data stored in JSON fields

### 3. **Better Affiliate Management**
- Multiple affiliate links per product
- Platform-specific commission rates
- Link type differentiation (web, mobile, desktop)

### 4. **Enhanced SEO**
- Built-in slug support
- Meta title and description fields
- Structured data for better search visibility

### 5. **Rich Product Data**
- Comprehensive specifications
- Multiple image and video support
- Detailed categorization system

### 6. **Performance Optimization**
- Proper indexing on key fields
- Efficient querying with platform filtering
- Optimized for large product catalogs

## Best Practices

### 1. **SKU Management**
- Use consistent SKU format: `PLATFORM-XXXXXX`
- Ensure SKUs are unique across all platforms
- Include platform prefix for easy identification

### 2. **Platform Data**
- Store platform-specific data in JSON format
- Use consistent field names across platforms
- Validate platform-specific data before insertion

### 3. **Affiliate Links**
- Always include commission rates
- Calculate estimated commissions
- Keep affiliate links active and updated

### 4. **Product Features**
- Use consistent feature types
- Order features by importance
- Include both pros and cons

### 5. **Categories**
- Use hierarchical category structure
- Mark primary categories
- Keep categories consistent across platforms

## File Structure

```
product-data-generator/
├── multi_platform_database.py          # Main database service
├── migrate_to_multi_platform.py        # Migration script
├── multi_platform_sample_data.py       # Sample data generator
├── MULTI_PLATFORM_SCHEMA.md           # This documentation
├── multi_platform_products.db         # New database file
└── sample_multi_platform.db           # Sample database
```

## Next Steps

1. **Test the Migration**: Run migration script on your existing data
2. **Validate Data**: Check that all data migrated correctly
3. **Update Application Code**: Modify your application to use the new schema
4. **Add New Platforms**: Use the platform management features to add D2C brands
5. **Optimize Queries**: Use platform filtering for better performance

This multi-platform schema provides a solid foundation for a scalable, flexible product catalog that can grow with your business needs while supporting multiple revenue streams through different platforms.
