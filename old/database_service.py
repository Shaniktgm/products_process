#!/usr/bin/env python3
"""
Database service for storing Amazon products
"""

import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any, Optional

class DatabaseService:
    """SQLite database service for Amazon products"""
    
    def __init__(self, db_path: str = "amazon_products.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create products table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS products (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        asin TEXT UNIQUE NOT NULL,
                        title TEXT NOT NULL,
                        brand TEXT,
                        description TEXT,
                        price REAL,
                        original_price REAL,
                        discount_percentage INTEGER,
                        rating REAL,
                        review_count INTEGER,
                        image_url TEXT,
                        availability TEXT,
                        condition TEXT,
                        is_prime BOOLEAN,
                        free_shipping BOOLEAN,
                        affiliate_link TEXT NOT NULL,
                        commission_rate REAL,
                        estimated_commission REAL,
                        best_seller_rank INTEGER,
                        upc TEXT,
                        isbn TEXT,
                        search_timestamp TEXT,
                        fetch_timestamp TEXT,
                        stock_status TEXT,
                        shipping_weight REAL,
                        package_dimensions TEXT,
                        warranty TEXT,
                        return_policy TEXT,
                        age_recommendation TEXT,
                        ingredients TEXT,
                        deal_badges TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
                
                # Create features table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_features (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        feature_text TEXT NOT NULL,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create categories table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_categories (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        category_id TEXT,
                        category_name TEXT NOT NULL,
                        is_root BOOLEAN,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create tags table
                cursor.execute('''
                    CREATE TABLE IF NOT EXISTS product_tags (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        product_id INTEGER,
                        tag TEXT NOT NULL,
                        FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                    )
                ''')
                
                # Create indexes for better performance
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_asin ON products (asin)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_brand ON products (brand)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_price ON products (price)')
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_rating ON products (rating)')
                
                conn.commit()
                print(f"✅ Database initialized: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Database initialization error: {str(e)}")
    
    def insert_or_update_product(self, product_data: Dict[str, Any]) -> bool:
        """Insert or update a product in the database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if product exists
                cursor.execute('SELECT id FROM products WHERE asin = ?', (product_data['asin'],))
                existing = cursor.fetchone()
                
                if existing:
                    # Update existing product
                    cursor.execute('''
                        UPDATE products SET
                            title = ?, brand = ?, description = ?, price = ?, original_price = ?,
                            discount_percentage = ?, rating = ?, review_count = ?, image_url = ?, availability = ?,
                            condition = ?, is_prime = ?, free_shipping = ?, affiliate_link = ?, commission_rate = ?,
                            estimated_commission = ?, best_seller_rank = ?, upc = ?, isbn = ?,
                            search_timestamp = ?, fetch_timestamp = ?, stock_status = ?, shipping_weight = ?,
                            package_dimensions = ?, warranty = ?, return_policy = ?, age_recommendation = ?,
                            ingredients = ?, deal_badges = ?, updated_at = CURRENT_TIMESTAMP
                        WHERE asin = ?
                    ''', (
                        product_data.get('title'),
                        product_data.get('brand'),
                        product_data.get('description', ''),
                        product_data.get('price'),
                        product_data.get('original_price'),
                        product_data.get('discount_percentage'),
                        product_data.get('rating'),
                        product_data.get('review_count'),
                        product_data.get('image'),
                        product_data.get('availability'),
                        product_data.get('condition'),
                        product_data.get('is_prime', False),
                        product_data.get('free_shipping', False),
                        product_data.get('affiliate_link'),
                        product_data.get('commission_rate'),
                        product_data.get('estimated_commission'),
                        product_data.get('best_seller_rank'),
                        product_data.get('upc', ''),
                        product_data.get('isbn', ''),
                        product_data.get('search_timestamp', ''),
                        product_data.get('fetch_timestamp', ''),
                        product_data.get('stock_status'),
                        product_data.get('shipping_weight'),
                        product_data.get('package_dimensions'),
                        product_data.get('warranty'),
                        product_data.get('return_policy'),
                        product_data.get('age_recommendation'),
                        product_data.get('ingredients'),
                        ','.join(product_data.get('deal_badges', [])) if product_data.get('deal_badges') else '',
                        product_data['asin']
                    ))
                    
                    product_id = existing[0]
                    print(f"🔄 Updated product: {product_data.get('title', 'Unknown')}")
                    
                else:
                    # Insert new product
                    cursor.execute('''
                        INSERT INTO products (
                            asin, title, brand, description, price, original_price, discount_percentage,
                            rating, review_count, image_url, availability, condition, is_prime, free_shipping,
                            affiliate_link, commission_rate, estimated_commission, best_seller_rank, upc, isbn,
                            search_timestamp, fetch_timestamp, stock_status, shipping_weight, package_dimensions,
                            warranty, return_policy, age_recommendation, ingredients, deal_badges
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        product_data['asin'],
                        product_data.get('title'),
                        product_data.get('brand'),
                        product_data.get('description', ''),
                        product_data.get('price'),
                        product_data.get('original_price'),
                        product_data.get('discount_percentage'),
                        product_data.get('rating'),
                        product_data.get('review_count'),
                        product_data.get('image'),
                        product_data.get('availability'),
                        product_data.get('condition'),
                        product_data.get('is_prime', False),
                        product_data.get('free_shipping', False),
                        product_data.get('affiliate_link'),
                        product_data.get('commission_rate'),
                        product_data.get('estimated_commission'),
                        product_data.get('best_seller_rank'),
                        product_data.get('upc', ''),
                        product_data.get('isbn', ''),
                        product_data.get('search_timestamp', ''),
                        product_data.get('fetch_timestamp', ''),
                        product_data.get('stock_status'),
                        product_data.get('shipping_weight'),
                        product_data.get('package_dimensions'),
                        product_data.get('warranty'),
                        product_data.get('return_policy'),
                        product_data.get('age_recommendation'),
                        product_data.get('ingredients'),
                        ','.join(product_data.get('deal_badges', [])) if product_data.get('deal_badges') else ''
                    ))
                    
                    product_id = cursor.lastrowid
                    print(f"✅ Inserted new product: {product_data.get('title', 'Unknown')}")
                
                # Insert/update features
                if product_data.get('features'):
                    # Remove old features
                    cursor.execute('DELETE FROM product_features WHERE product_id = ?', (product_id,))
                    
                    # Insert new features
                    for feature in product_data['features']:
                        cursor.execute('''
                            INSERT INTO product_features (product_id, feature_text)
                            VALUES (?, ?)
                        ''', (product_id, feature))
                
                # Insert/update categories
                if product_data.get('categories'):
                    # Remove old categories
                    cursor.execute('DELETE FROM product_categories WHERE product_id = ?', (product_id,))
                    
                    # Insert new categories
                    for category in product_data['categories']:
                        if isinstance(category, dict):
                            # Category is a dictionary with id, name, is_root
                            category_id = category.get('id', '')
                            category_name = category.get('name', '')
                            is_root = category.get('is_root', False)
                        else:
                            # Category is a simple string
                            category_id = ''
                            category_name = str(category)
                            is_root = False
                        
                        cursor.execute('''
                            INSERT INTO product_categories (product_id, category_id, category_name, is_root)
                            VALUES (?, ?, ?, ?)
                        ''', (product_id, category_id, category_name, is_root))
                
                # Generate and insert tags
                self._generate_and_insert_tags(cursor, product_id, product_data)
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return False
    
    def _generate_and_insert_tags(self, cursor, product_id: int, product_data: Dict[str, Any]):
        """Generate tags from product data and insert them"""
        try:
            # Remove old tags
            cursor.execute('DELETE FROM product_tags WHERE product_id = ?', (product_id,))
            
            tags = set()
            
            # Add brand as tag
            if product_data.get('brand'):
                tags.add(product_data['brand'].lower().replace(' ', '-'))
            
            # Add category names as tags
            if product_data.get('categories'):
                for category in product_data['categories']:
                    if isinstance(category, dict):
                        category_name = category.get('name', '')
                    else:
                        category_name = str(category)
                    
                    if category_name:
                        tags.add(category_name.lower().replace(' ', '-'))
            
            # Add condition as tag
            if product_data.get('condition'):
                tags.add(product_data['condition'].lower().replace(' ', '-'))
            
            # Add availability as tag
            if product_data.get('availability'):
                tags.add(product_data['availability'].lower().replace(' ', '-'))
            
            # Add prime status as tag
            if product_data.get('is_prime'):
                tags.add('prime')
            
            # Insert tags
            for tag in tags:
                cursor.execute('''
                    INSERT INTO product_tags (product_id, tag)
                    VALUES (?, ?)
                ''', (product_id, tag))
                
        except Exception as e:
            print(f"❌ Tag generation error: {str(e)}")
    
    def get_products(self, limit: int = 50, offset: int = 0) -> List[Dict[str, Any]]:
        """Get products from database with pagination"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('''
                    SELECT * FROM products 
                    ORDER BY created_at DESC 
                    LIMIT ? OFFSET ?
                ''', (limit, offset))
                
                rows = cursor.fetchall()
                products = []
                
                for row in rows:
                    product = dict(row)
                    
                    # Get features
                    cursor.execute('SELECT feature_text FROM product_features WHERE product_id = ?', (row['id'],))
                    product['features'] = [feature[0] for feature in cursor.fetchall()]
                    
                    # Get categories
                    cursor.execute('SELECT category_name FROM product_categories WHERE product_id = ?', (row['id'],))
                    product['categories'] = [category[0] for category in cursor.fetchall()]
                    
                    # Get tags
                    cursor.execute('SELECT tag FROM product_tags WHERE product_id = ?', (row['id'],))
                    product['tags'] = [tag[0] for tag in cursor.fetchall()]
                    
                    products.append(product)
                
                return products
                
        except Exception as e:
            print(f"❌ Database query error: {str(e)}")
            return []
    
    def search_products(self, query: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Search products by title, brand, or tags"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                search_query = f"%{query}%"
                
                cursor.execute('''
                    SELECT DISTINCT p.* FROM products p
                    LEFT JOIN product_features pf ON p.id = pf.product_id
                    LEFT JOIN product_tags pt ON p.id = pt.product_id
                    WHERE p.title LIKE ? OR p.brand LIKE ? OR pf.feature_text LIKE ? OR pt.tag LIKE ?
                    ORDER BY p.rating DESC, p.review_count DESC
                    LIMIT ?
                ''', (search_query, search_query, search_query, search_query, limit))
                
                rows = cursor.fetchall()
                products = []
                
                for row in rows:
                    product = dict(row)
                    
                    # Get features
                    cursor.execute('SELECT feature_text FROM product_features WHERE product_id = ?', (row['id'],))
                    product['features'] = [feature[0] for feature in cursor.fetchall()]
                    
                    # Get categories
                    cursor.execute('SELECT category_name FROM product_categories WHERE product_id = ?', (row['id'],))
                    product['categories'] = [category[0] for category in cursor.fetchall()]
                    
                    # Get tags
                    cursor.execute('SELECT tag FROM product_tags WHERE product_id = ?', (row['id'],))
                    product['tags'] = [tag[0] for tag in cursor.fetchall()]
                    
                    products.append(product)
                
                return products
                
        except Exception as e:
            print(f"❌ Database search error: {str(e)}")
            return []
    
    def get_product_by_asin(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get a specific product by ASIN"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM products WHERE asin = ?', (asin,))
                row = cursor.fetchone()
                
                if not row:
                    return None
                
                product = dict(row)
                
                # Get features
                cursor.execute('SELECT feature_text FROM product_features WHERE product_id = ?', (row['id'],))
                product['features'] = [feature[0] for feature in cursor.fetchall()]
                
                # Get categories
                cursor.execute('SELECT category_name FROM product_categories WHERE product_id = ?', (row['id'],))
                product['categories'] = [category[0] for category in cursor.fetchall()]
                
                # Get tags
                cursor.execute('SELECT tag FROM product_tags WHERE product_id = ?', (row['id'],))
                product['tags'] = [tag[0] for tag in cursor.fetchall()]
                
                return product
                
        except Exception as e:
            print(f"❌ Database query error: {str(e)}")
            return None
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count products
                cursor.execute('SELECT COUNT(*) FROM products')
                total_products = cursor.fetchone()[0]
                
                # Count brands
                cursor.execute('SELECT COUNT(DISTINCT brand) FROM products WHERE brand IS NOT NULL')
                total_brands = cursor.fetchone()[0]
                
                # Count categories
                cursor.execute('SELECT COUNT(DISTINCT category_name) FROM product_categories')
                total_categories = cursor.fetchone()[0]
                
                # Count tags
                cursor.execute('SELECT COUNT(DISTINCT tag) FROM product_tags')
                total_tags = cursor.fetchone()[0]
                
                # Average price
                cursor.execute('SELECT AVG(price) FROM products WHERE price IS NOT NULL')
                avg_price = cursor.fetchone()[0]
                
                # Average rating
                cursor.execute('SELECT AVG(rating) FROM products WHERE rating IS NOT NULL')
                avg_rating = cursor.fetchone()[0]
                
                return {
                    'total_products': total_products,
                    'total_brands': total_brands,
                    'total_categories': total_categories,
                    'total_tags': total_tags,
                    'average_price': round(avg_price, 2) if avg_price else 0,
                    'average_rating': round(avg_rating, 2) if avg_rating else 0
                }
                
        except Exception as e:
            print(f"❌ Database stats error: {str(e)}")
            return {}
    
    def export_to_json(self, filename: str = "amazon_products.json"):
        """Export all products to JSON file"""
        try:
            products = self.get_products(limit=10000)  # Get all products
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            
            print(f"✅ Exported {len(products)} products to {filename}")
            
        except Exception as e:
            print(f"❌ Export error: {str(e)}")

if __name__ == "__main__":
    # Test database service
    db = DatabaseService()
    
    # Get database stats
    stats = db.get_database_stats()
    print("📊 Database Statistics:")
    for key, value in stats.items():
        print(f"   {key}: {value}")
