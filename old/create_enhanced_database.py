#!/usr/bin/env python3
"""
Create a new enhanced database with all the new fields
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_mock_generator import EnhancedMockDataGenerator

class EnhancedDatabaseService:
    """Enhanced database service with new schema"""
    
    def __init__(self, db_path: str = "enhanced_products.db"):
        """Initialize database connection"""
        self.db_path = db_path
        self.init_database()
    
    def init_database(self):
        """Initialize database tables with enhanced schema"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Create enhanced products table
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
                cursor.execute('CREATE INDEX IF NOT EXISTS idx_products_commission ON products (estimated_commission)')
                
                conn.commit()
                print(f"✅ Enhanced database initialized: {self.db_path}")
                
        except Exception as e:
            print(f"❌ Database initialization error: {str(e)}")
    
    def insert_product(self, product_data: Dict[str, Any]) -> bool:
        """Insert a product into the enhanced database"""
        try:
            import sqlite3
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert main product data
                cursor.execute('''
                    INSERT INTO products (
                        asin, title, brand, description, price, original_price, discount_percentage,
                        rating, review_count, image_url, availability, condition, is_prime, free_shipping,
                        affiliate_link, commission_rate, estimated_commission, best_seller_rank, upc, isbn,
                        search_timestamp, fetch_timestamp, stock_status, shipping_weight, package_dimensions,
                        warranty, return_policy, age_recommendation, ingredients, deal_badges
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
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
                    product_data.get('image_url'),
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
                
                # Insert features
                if product_data.get('features'):
                    for feature in product_data['features']:
                        cursor.execute('''
                            INSERT INTO product_features (product_id, feature_text)
                            VALUES (?, ?)
                        ''', (product_id, feature))
                
                # Insert categories
                if product_data.get('categories'):
                    for category in product_data['categories']:
                        if isinstance(category, dict):
                            category_id = category.get('id', '')
                            category_name = category.get('name', '')
                            is_root = category.get('is_root', False)
                        else:
                            category_id = ''
                            category_name = str(category)
                            is_root = False
                        
                        cursor.execute('''
                            INSERT INTO product_categories (product_id, category_id, category_name, is_root)
                            VALUES (?, ?, ?, ?)
                        ''', (product_id, category_id, category_name, is_root))
                
                # Insert tags
                if product_data.get('tags'):
                    for tag in product_data['tags']:
                        cursor.execute('''
                            INSERT INTO product_tags (product_id, tag)
                            VALUES (?, ?)
                        ''', (product_id, tag))
                
                conn.commit()
                print(f"✅ Inserted enhanced product: {product_data.get('title', 'Unknown')}")
                return True
                
        except Exception as e:
            print(f"❌ Database error: {str(e)}")
            return False
    
    def get_database_stats(self) -> Dict[str, Any]:
        """Get database statistics"""
        try:
            import sqlite3
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
                
                # Total estimated commission
                cursor.execute('SELECT SUM(estimated_commission) FROM products WHERE estimated_commission IS NOT NULL')
                total_commission = cursor.fetchone()[0]
                
                return {
                    'total_products': total_products,
                    'total_brands': total_brands,
                    'total_categories': total_categories,
                    'total_tags': total_tags,
                    'average_price': round(avg_price, 2) if avg_price else 0,
                    'average_rating': round(avg_rating, 2) if avg_rating else 0,
                    'total_estimated_commission': round(total_commission, 2) if total_commission else 0
                }
                
        except Exception as e:
            print(f"❌ Database stats error: {str(e)}")
            return {}
    
    def export_to_json(self, filename: str = "enhanced_products.json"):
        """Export all products to JSON file"""
        try:
            import sqlite3
            import json
            
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                cursor.execute('SELECT * FROM products ORDER BY created_at DESC')
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
                    
                    # Convert deal_badges from string back to list
                    if product.get('deal_badges'):
                        product['deal_badges'] = product['deal_badges'].split(',') if product['deal_badges'] else []
                    else:
                        product['deal_badges'] = []
                    
                    products.append(product)
                
                with open(filename, 'w', encoding='utf-8') as f:
                    json.dump(products, f, indent=2, ensure_ascii=False)
                
                print(f"✅ Exported {len(products)} enhanced products to {filename}")
                
        except Exception as e:
            print(f"❌ Export error: {str(e)}")

def create_enhanced_database(product_count: int = 500):
    """Create a new enhanced database with enhanced products"""
    print("🚀 Creating Enhanced Database with Enhanced Products")
    print("=" * 60)
    
    try:
        # Initialize enhanced database service
        print("1. Initializing enhanced database...")
        db_service = EnhancedDatabaseService()
        
        # Generate enhanced products
        print(f"\n2. Generating {product_count} enhanced products...")
        generator = EnhancedMockDataGenerator()
        enhanced_products = generator.generate_enhanced_products(product_count)
        
        if not enhanced_products:
            print("❌ No enhanced products generated. Exiting.")
            return
        
        # Insert products into enhanced database
        print(f"\n3. Inserting {len(enhanced_products)} enhanced products...")
        success_count = 0
        
        for i, product in enumerate(enhanced_products, 1):
            try:
                if db_service.insert_product(product):
                    success_count += 1
                
                # Progress indicator
                if i % 50 == 0:
                    print(f"   Progress: {i}/{len(enhanced_products)} products inserted ({success_count} successful)")
                
            except Exception as e:
                print(f"   ❌ Error inserting product {product.get('asin', 'Unknown')}: {str(e)}")
                continue
        
        print(f"\n✅ Successfully inserted {success_count}/{len(enhanced_products)} enhanced products")
        
        # Get database statistics
        print("\n4. Enhanced database statistics:")
        stats = db_service.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Export to JSON
        print("\n5. Exporting enhanced data to JSON...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_products_{timestamp}.json"
        db_service.export_to_json(filename)
        
        print(f"\n🎉 Enhanced database creation completed successfully!")
        print(f"   Products generated: {len(enhanced_products)}")
        print(f"   Products inserted: {success_count}")
        print(f"   Database file: {db_service.db_path}")
        print(f"   Export file: {filename}")
        
        # Show sample enhanced products
        print(f"\n📋 Sample enhanced products from database:")
        sample_products = enhanced_products[:5]
        for i, product in enumerate(sample_products, 1):
            print(f"   {i}. {product.get('title', 'Unknown')}")
            print(f"      Brand: {product.get('brand', 'Unknown')}")
            print(f"      Price: ${product.get('price', 'Unknown')}")
            if product.get('original_price'):
                print(f"      Original: ${product.get('original_price')} (Save {product.get('discount_percentage', 0)}%)")
            print(f"      Rating: {product.get('rating', 'Unknown')} ⭐")
            print(f"      Commission: ${product.get('estimated_commission', 'Unknown')}")
            print(f"      Prime: {'✅' if product.get('is_prime') else '❌'}")
            if product.get('deal_badges'):
                print(f"      Badges: {', '.join(product.get('deal_badges', []))}")
            print()
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def main():
    """Main function"""
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            create_enhanced_database(count)
        except ValueError:
            print("❌ Please provide a valid number of products")
            print("Usage: python3 create_enhanced_database.py [number]")
    else:
        # Default: create database with 500 enhanced products
        create_enhanced_database(500)

if __name__ == "__main__":
    main()
