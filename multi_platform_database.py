#!/usr/bin/env python3
"""
Multi-Platform Database Service
Supports Amazon, D2C brands, and other e-commerce platforms
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional
from enum import Enum

class PlatformType(Enum):
    AMAZON = "amazon"
    D2C = "d2c"  # Direct-to-Consumer
    WALMART = "walmart"
    TARGET = "target"
    ETSY = "etsy"
    SHOPIFY = "shopify"
    WOOCOMMERCE = "woocommerce"
    OTHER = "other"

class MultiPlatformDatabaseService:
    """Multi-platform database service for product catalog"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize multi-platform database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create platforms table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS platforms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        name TEXT UNIQUE NOT NULL,
                        display_name TEXT NOT NULL,
                        base_url TEXT,
                        api_endpoint TEXT,
                        commission_rate REAL DEFAULT 0.0,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create products table (platform-agnostic)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        sku TEXT UNIQUE NOT NULL,  -- Universal SKU
                        title TEXT NOT NULL,
                        brand TEXT,
                        description TEXT,
                        short_description TEXT,
                        slug TEXT UNIQUE,  -- URL-friendly identifier
                        
                        -- Pricing
                        price REAL,
                        original_price REAL,
                        discount_percentage INTEGER,
                        currency TEXT DEFAULT 'USD',
                        
                        -- Ratings & Reviews
                        rating REAL,
                        review_count INTEGER,
                        
                        -- Media
                        primary_image_url TEXT,
                        image_urls TEXT,  -- JSON array of image URLs
                        video_urls TEXT,  -- JSON array of video URLs
                        
                        -- Availability
                        availability TEXT,
                        stock_status TEXT,
                        stock_quantity INTEGER,
                        
                        -- Product Details
                        condition TEXT,
                        warranty TEXT,
                        return_policy TEXT,
                        shipping_info TEXT,
                        age_recommendation TEXT,
                        ingredients TEXT,
                        
                        -- Physical Properties
                        weight REAL,
                        dimensions TEXT,  -- JSON: {"length": 10, "width": 5, "height": 2}
                        color TEXT,
                        material TEXT,
                        size TEXT,
                        
                        -- SEO & Marketing
                        meta_title TEXT,
                        meta_description TEXT,
                        tags TEXT,  -- JSON array
                        deal_badges TEXT,  -- JSON array
                        
                        -- Status
                        is_active BOOLEAN DEFAULT TRUE,
                        is_featured BOOLEAN DEFAULT FALSE,
                        is_bestseller BOOLEAN DEFAULT FALSE,
                        
                        -- Timestamps
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create product_platforms table (many-to-many relationship)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_platforms (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        product_id INTEGER NOT NULL,
                        platform_id INTEGER NOT NULL,
                        platform_sku TEXT,  -- Platform-specific SKU (ASIN for Amazon, etc.)
                        platform_url TEXT,
                        platform_price REAL,
                        platform_availability TEXT,
                        platform_rating REAL,
                        platform_review_count INTEGER,
                        platform_specific_data TEXT,  -- JSON for platform-specific fields
                        is_primary BOOLEAN DEFAULT FALSE,  -- Primary platform for this product
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                        FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE,
                        UNIQUE(product_id, platform_id)
                    )
                ''')
                
                # Create affiliate_links table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS affiliate_links (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        product_id INTEGER NOT NULL,
                        platform_id INTEGER NOT NULL,
                        link_type TEXT NOT NULL,  -- 'web', 'mobile', 'desktop'
                        affiliate_url TEXT NOT NULL,
                        commission_rate REAL,
                        estimated_commission REAL,
                        is_active BOOLEAN DEFAULT TRUE,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                        FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create product_features table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_features (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        product_id INTEGER NOT NULL,
                        feature_text TEXT NOT NULL,
                        feature_type TEXT DEFAULT 'general',  -- 'pro', 'con', 'specification', 'general'
                        display_order INTEGER DEFAULT 0,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create product_categories table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        product_id INTEGER NOT NULL,
                        category_name TEXT NOT NULL,
                        category_path TEXT,  -- Full category hierarchy
                        is_primary BOOLEAN DEFAULT FALSE,
                        display_order INTEGER DEFAULT 0,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create product_specifications table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_specifications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        product_id INTEGER NOT NULL,
                        spec_name TEXT NOT NULL,
                        spec_value TEXT NOT NULL,
                        spec_unit TEXT,  -- 'inches', 'lbs', 'count', etc.
                        display_order INTEGER DEFAULT 0,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create product_reviews table (aggregated reviews)
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_reviews (
                        id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                        product_id INTEGER NOT NULL,
                        platform_id INTEGER NOT NULL,
                        review_text TEXT,
                        rating INTEGER,
                        reviewer_name TEXT,
                        review_date TEXT,
                        is_verified BOOLEAN DEFAULT FALSE,
                        helpful_votes INTEGER DEFAULT 0,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                        FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_sku ON products (sku)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_slug ON products (slug)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products (brand)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_price ON products (price)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_rating ON products (rating)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_active ON products (is_active)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_featured ON products (is_featured)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_platforms_product ON product_platforms (product_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_product_platforms_platform ON product_platforms (platform_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_affiliate_links_product ON affiliate_links (product_id)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_affiliate_links_platform ON affiliate_links (platform_id)')
                
                # Insert default platforms
                self._insert_default_platforms(cursor)
                
                conn.commit()
                print(f"✅ Multi-platform database initialized: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Database initialization error: {str(e)}")
    
    def _insert_default_platforms(self, cursor):
        """Insert default platforms"""
        default_platforms = [
            ('amazon', 'Amazon', 'https://amazon.com', None, 0.04, True),
            ('d2c', 'Direct-to-Consumer', None, None, 0.10, True),
            ('walmart', 'Walmart', 'https://walmart.com', None, 0.03, True),
            ('target', 'Target', 'https://target.com', None, 0.05, True),
            ('etsy', 'Etsy', 'https://etsy.com', None, 0.08, True),
            ('shopify', 'Shopify Store', None, None, 0.12, True),
            ('other', 'Other Platform', None, None, 0.05, True)
        ]
        
        for platform in default_platforms:
            cursor.execute('''
                INSERT OR IGNORE INTO platforms (name, display_name, base_url, api_endpoint, commission_rate, is_active)
                VALUES (?, ?, ?, ?, ?, ?)
            ''', platform)
    
    def add_platform(self, name: str, display_name: str, base_url: str = None, 
                    api_endpoint: str = None, commission_rate: float = 0.05) -> bool:
        """Add a new platform"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO platforms (name, display_name, base_url, api_endpoint, commission_rate)
                    VALUES (?, ?, ?, ?, ?)
                ''', (name, display_name, base_url, api_endpoint, commission_rate))
                conn.commit()
                print(f"✅ Added platform: {display_name}")
                return True
        except Exception as e:
            print(f"❌ Error adding platform: {str(e)}")
            return False
    
    def insert_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """Insert a new product with multi-platform support"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert main product data
                cursor.execute('''
                    INSERT INTO products (
                        sku, title, brand, description, short_description, slug,
                        price, original_price, discount_percentage, currency,
                        rating, review_count,
                        primary_image_url, image_urls, video_urls,
                        availability, stock_status, stock_quantity,
                        condition, warranty, return_policy, shipping_info,
                        age_recommendation, ingredients,
                        weight, dimensions, color, material, size,
                        meta_title, meta_description, tags, deal_badges,
                        is_active, is_featured, is_bestseller
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_data['sku'],
                    product_data.get('title'),
                    product_data.get('brand'),
                    product_data.get('description', ''),
                    product_data.get('short_description', ''),
                    product_data.get('slug'),
                    product_data.get('price'),
                    product_data.get('original_price'),
                    product_data.get('discount_percentage'),
                    product_data.get('currency', 'USD'),
                    product_data.get('rating'),
                    product_data.get('review_count'),
                    product_data.get('primary_image_url'),
                    json.dumps(product_data.get('image_urls', [])),
                    json.dumps(product_data.get('video_urls', [])),
                    product_data.get('availability'),
                    product_data.get('stock_status'),
                    product_data.get('stock_quantity'),
                    product_data.get('condition'),
                    product_data.get('warranty'),
                    product_data.get('return_policy'),
                    product_data.get('shipping_info'),
                    product_data.get('age_recommendation'),
                    product_data.get('ingredients'),
                    product_data.get('weight'),
                    json.dumps(product_data.get('dimensions', {})),
                    product_data.get('color'),
                    product_data.get('material'),
                    product_data.get('size'),
                    product_data.get('meta_title'),
                    product_data.get('meta_description'),
                    json.dumps(product_data.get('tags', [])),
                    json.dumps(product_data.get('deal_badges', [])),
                    product_data.get('is_active', True),
                    product_data.get('is_featured', False),
                    product_data.get('is_bestseller', False)
                ))
                
                product_id = cursor.lastrowid
                
                # Insert platform-specific data
                if product_data.get('platforms'):
                    for platform_data in product_data['platforms']:
                        self._insert_product_platform(cursor, product_id, platform_data)
                
                # Insert affiliate links
                if product_data.get('affiliate_links'):
                    for affiliate_data in product_data['affiliate_links']:
                        self._insert_affiliate_link(cursor, product_id, affiliate_data)
                
                # Insert features
                if product_data.get('features'):
                    for i, feature in enumerate(product_data['features']):
                        feature_type = 'general'
                        if isinstance(feature, dict):
                            feature_text = feature.get('text', '')
                            feature_type = feature.get('type', 'general')
                        else:
                            feature_text = str(feature)
                        
                        cursor.execute('''
                            INSERT INTO product_features (product_id, feature_text, feature_type, display_order)
                            VALUES (?, ?, ?, ?)
                        ''', (product_id, feature_text, feature_type, i))
                
                # Insert categories
                if product_data.get('categories'):
                    for i, category in enumerate(product_data['categories']):
                        is_primary = i == 0  # First category is primary
                        cursor.execute('''
                            INSERT INTO product_categories (product_id, category_name, is_primary, display_order)
                            VALUES (?, ?, ?, ?)
                        ''', (product_id, category, is_primary, i))
                
                # Insert specifications
                if product_data.get('specifications'):
                    for i, (spec_name, spec_value) in enumerate(product_data['specifications'].items()):
                        cursor.execute('''
                            INSERT INTO product_specifications (product_id, spec_name, spec_value, display_order)
                            VALUES (?, ?, ?, ?)
                        ''', (product_id, spec_name, spec_value, i))
                
                conn.commit()
                print(f"✅ Inserted product: {product_data.get('title', 'Unknown')}")
                return product_id
                
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return None
    
    def _insert_product_platform(self, cursor, product_id: int, platform_data: Dict[str, Any]):
        """Insert platform-specific product data"""
        cursor.execute('''
            INSERT INTO product_platforms (
                product_id, platform_id, platform_sku, platform_url,
                platform_price, platform_availability, platform_rating,
                platform_review_count, platform_specific_data, is_primary
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            platform_data['platform_id'],
            platform_data.get('platform_sku'),
            platform_data.get('platform_url'),
            platform_data.get('platform_price'),
            platform_data.get('platform_availability'),
            platform_data.get('platform_rating'),
            platform_data.get('platform_review_count'),
            json.dumps(platform_data.get('platform_specific_data', {})),
            platform_data.get('is_primary', False)
        ))
    
    def _insert_affiliate_link(self, cursor, product_id: int, affiliate_data: Dict[str, Any]):
        """Insert affiliate link data"""
        cursor.execute('''
            INSERT INTO affiliate_links (
                product_id, platform_id, link_type, affiliate_url,
                commission_rate, estimated_commission
            ) VALUES (?, ?, ?, ?, ?, ?)
        ''', (
            product_id,
            affiliate_data['platform_id'],
            affiliate_data.get('link_type', 'web'),
            affiliate_data['affiliate_url'],
            affiliate_data.get('commission_rate'),
            affiliate_data.get('estimated_commission')
        ))
    
    def get_products(self, platform: str = None, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get products with optional platform filtering"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                if platform:
                    cursor.execute('''
                        SELECT DISTINCT p.* FROM products p
                        JOIN product_platforms pp ON p.id = pp.product_id
                        JOIN platforms pl ON pp.platform_id = pl.id
                        WHERE pl.name = ? AND p.is_active = TRUE
                        ORDER BY p.created_at DESC
                        LIMIT ? OFFSET ?
                    ''', (platform, limit, offset))
                else:
                    cursor.execute('''
                        SELECT * FROM products 
                        WHERE is_active = TRUE
                        ORDER BY created_at DESC 
                        LIMIT ? OFFSET ?
                    ''', (limit, offset))
                
                rows = cursor.fetchall()
                products = []
                
                for row in rows:
                    product = dict(row)
                    product_id = row['id']
                    
                    # Get platform data
                    product['platforms'] = self._get_product_platforms(cursor, product_id)
                    
                    # Get affiliate links
                    product['affiliate_links'] = self._get_affiliate_links(cursor, product_id)
                    
                    # Get features
                    product['features'] = self._get_product_features(cursor, product_id)
                    
                    # Get categories
                    product['categories'] = self._get_product_categories(cursor, product_id)
                    
                    # Get specifications
                    product['specifications'] = self._get_product_specifications(cursor, product_id)
                    
                    # Parse JSON fields
                    product['image_urls'] = json.loads(product.get('image_urls', '[]'))
                    product['video_urls'] = json.loads(product.get('video_urls', '[]'))
                    product['tags'] = json.loads(product.get('tags', '[]'))
                    product['deal_badges'] = json.loads(product.get('deal_badges', '[]'))
                    product['dimensions'] = json.loads(product.get('dimensions', '{}'))
                    
                    products.append(product)
                
                return products
                
        except Exception as e:
            print(f"❌ Database query error: {str(e)}")
            return []
    
    def _get_product_platforms(self, cursor, product_id: int) -> List[Dict[str, Any]]:
        """Get platform data for a product"""
        cursor.execute('''
            SELECT pp.*, pl.name as platform_name, pl.display_name
            FROM product_platforms pp
            JOIN platforms pl ON pp.platform_id = pl.id
            WHERE pp.product_id = ?
        ''', (product_id,))
        
        platforms = []
        for row in cursor.fetchall():
            platform = dict(row)
            platform['platform_specific_data'] = json.loads(platform.get('platform_specific_data', '{}'))
            platforms.append(platform)
        
        return platforms
    
    def _get_affiliate_links(self, cursor, product_id: int) -> List[Dict[str, Any]]:
        """Get affiliate links for a product"""
        cursor.execute('''
            SELECT al.*, pl.name as platform_name
            FROM affiliate_links al
            JOIN platforms pl ON al.platform_id = pl.id
            WHERE al.product_id = ? AND al.is_active = TRUE
        ''', (product_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_product_features(self, cursor, product_id: int) -> List[Dict[str, Any]]:
        """Get features for a product"""
        cursor.execute('''
            SELECT feature_text, feature_type, display_order
            FROM product_features
            WHERE product_id = ?
            ORDER BY display_order
        ''', (product_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_product_categories(self, cursor, product_id: int) -> List[Dict[str, Any]]:
        """Get categories for a product"""
        cursor.execute('''
            SELECT category_name, is_primary, display_order
            FROM product_categories
            WHERE product_id = ?
            ORDER BY display_order
        ''', (product_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def _get_product_specifications(self, cursor, product_id: int) -> List[Dict[str, Any]]:
        """Get specifications for a product"""
        cursor.execute('''
            SELECT spec_name, spec_value, spec_unit, display_order
            FROM product_specifications
            WHERE product_id = ?
            ORDER BY display_order
        ''', (product_id,))
        
        return [dict(row) for row in cursor.fetchall()]
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get comprehensive database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Basic counts
                cursor.execute('SELECT COUNT(*) FROM products WHERE is_active = TRUE')
                total_products = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM platforms WHERE is_active = TRUE')
                total_platforms = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM product_platforms')
                total_platform_products = cursor.fetchone()[0]
                
                cursor.execute('SELECT COUNT(*) FROM affiliate_links WHERE is_active = TRUE')
                total_affiliate_links = cursor.fetchone()[0]
                
                # Platform breakdown
                cursor.execute('''
                    SELECT pl.display_name, COUNT(pp.product_id) as product_count
                    FROM platforms pl
                    LEFT JOIN product_platforms pp ON pl.id = pp.platform_id
                    WHERE pl.is_active = TRUE
                    GROUP BY pl.id, pl.display_name
                    ORDER BY product_count DESC
                ''')
                platform_breakdown = []
                for row in cursor.fetchall():
                    platform_breakdown.append({
                        'display_name': row[0],
                        'product_count': row[1]
                    })
                
                # Average metrics
                cursor.execute('SELECT AVG(price) FROM products WHERE price IS NOT NULL AND is_active = TRUE')
                avg_price = cursor.fetchone()[0]
                
                cursor.execute('SELECT AVG(rating) FROM products WHERE rating IS NOT NULL AND is_active = TRUE')
                avg_rating = cursor.fetchone()[0]
                
                return {
                    'total_products': total_products,
                    'total_platforms': total_platforms,
                    'total_platform_products': total_platform_products,
                    'total_affiliate_links': total_affiliate_links,
                    'platform_breakdown': platform_breakdown,
                    'average_price': round(avg_price, 2) if avg_price else 0,
                    'average_rating': round(avg_rating, 2) if avg_rating else 0
                }
                
        except Exception as e:
            print(f"❌ Database stats error: {str(e)}")
            return {}

if __name__ == "__main__":
    # Test multi-platform database service
    db = MultiPlatformDatabaseService()
    
    # Get database stats
    stats = db.get_database_stats()
    print("📊 Multi-Platform Database Statistics:")
    for key, value in stats.items():
        if key == 'platform_breakdown':
            print(f"   {key}:")
            for platform in value:
                print(f"     - {platform['display_name']}: {platform['product_count']} products")
        else:
            print(f"   {key}: {value}")
