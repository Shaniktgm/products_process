#!/usr/bin/env python3
"""
Simple Product Importer
Import basic product data from CSV files to populate the database
"""

import sqlite3
import csv
import re
from typing import List, Dict, Any, Optional
from pathlib import Path


class SimpleProductImporter:
    """Simple importer for basic product data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
    
    def import_products_from_csv(self, csv_file: str) -> Dict[str, int]:
        """Import products from CSV file"""
        stats = {
            'total_rows': 0,
            'products_created': 0,
            'products_updated': 0,
            'errors': 0
        }
        
        try:
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    stats['total_rows'] += 1
                    
                    try:
                        # Extract URL from row
                        url = row.get('url', '').strip()
                        if not url:
                            continue
                        
                        # Extract Amazon product ID
                        amazon_product_id = self._extract_amazon_product_id(url)
                        if not amazon_product_id:
                            print(f"⚠️  Could not extract Amazon product ID from: {url}")
                            continue
                        
                        # Create or update product
                        result = self._create_or_update_product(amazon_product_id, url)
                        if result == 'created':
                            stats['products_created'] += 1
                        elif result == 'updated':
                            stats['products_updated'] += 1
                            
                    except Exception as e:
                        print(f"⚠️  Error processing row {stats['total_rows']}: {e}")
                        stats['errors'] += 1
                        
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _extract_amazon_product_id(self, url: str) -> Optional[str]:
        """Extract Amazon product ID from URL"""
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _create_or_update_product(self, amazon_product_id: str, url: str) -> str:
        """Create or update product in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if product exists
            cursor.execute("SELECT id FROM products WHERE amazon_product_id = ?", (amazon_product_id,))
            existing = cursor.fetchone()
            
            if existing:
                # Update existing product
                cursor.execute("""
                    UPDATE products 
                    SET updated_at = CURRENT_TIMESTAMP
                    WHERE amazon_product_id = ?
                """, (amazon_product_id,))
                return 'updated'
            else:
                # Create new product
                sku = f"AMZ-{amazon_product_id}"
                title = f"Amazon Product {amazon_product_id}"
                
                cursor.execute("""
                    INSERT INTO products (sku, title, amazon_product_id, is_active)
                    VALUES (?, ?, ?, ?)
                """, (sku, title, amazon_product_id, True))
                
                return 'created'
    
    def add_basic_features_to_products(self) -> Dict[str, int]:
        """Add basic features to all products"""
        stats = {
            'products_processed': 0,
            'features_added': 0,
            'errors': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products without features
                cursor.execute("""
                    SELECT p.id, p.amazon_product_id, p.title, p.brand
                    FROM products p
                    LEFT JOIN product_features pf ON p.id = pf.product_id
                    WHERE pf.id IS NULL
                """)
                
                products = cursor.fetchall()
                stats['products_processed'] = len(products)
                
                for product_id, amazon_id, title, brand in products:
                    try:
                        # Add basic features based on product characteristics
                        features = self._generate_basic_features(amazon_id, title, brand)
                        
                        for i, (feature_text, feature_type) in enumerate(features):
                            cursor.execute("""
                                INSERT INTO product_features 
                                (product_id, feature_text, feature_type, ai_generated, display_order)
                                VALUES (?, ?, ?, ?, ?)
                            """, (product_id, feature_text, feature_type, True, i + 1))
                            
                            stats['features_added'] += 1
                            
                    except Exception as e:
                        print(f"⚠️  Error adding features for product {product_id}: {e}")
                        stats['errors'] += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _generate_basic_features(self, amazon_id: str, title: str, brand: str) -> List[tuple]:
        """Generate basic features for a product"""
        features = []
        
        # Basic pros that apply to most products
        pros = [
            "Quality Product",
            "Good Value",
            "Popular Choice",
            "Easy to Use",
            "Durable"
        ]
        
        # Basic cons that apply to most products
        cons = [
            "May Vary by User",
            "Check Reviews",
            "Verify Compatibility"
        ]
        
        # Add pros
        for pro in pros:
            features.append((pro, 'pro'))
        
        # Add cons
        for con in cons:
            features.append((con, 'con'))
        
        return features
    
    def show_database_summary(self):
        """Show summary of database contents"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count records in each table
            tables = [
                'products', 'product_features', 'product_categories', 
                'product_specifications', 'product_reviews', 'product_images',
                'affiliate_links', 'platforms'
            ]
            
            print(f"\n📊 Database Summary:")
            for table in tables:
                try:
                    cursor.execute(f"SELECT COUNT(*) FROM {table}")
                    count = cursor.fetchone()[0]
                    print(f"   {table}: {count} records")
                except:
                    print(f"   {table}: table not found")
            
            # Show sample products
            print(f"\n📋 Sample Products:")
            cursor.execute("""
                SELECT amazon_product_id, title, brand, price
                FROM products
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            for amazon_id, title, brand, price in results:
                print(f"   {amazon_id} | {title} | {brand} | ${price}")


def main():
    """Main function"""
    csv_file = "products/old_data/products_new.csv"
    
    if not Path(csv_file).exists():
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🚀 Simple Product Importer")
    print("=" * 40)
    
    # Initialize importer
    importer = SimpleProductImporter()
    
    # Import products
    print(f"\n📊 Importing products from {csv_file}...")
    import_stats = importer.import_products_from_csv(csv_file)
    
    print(f"\n✅ Import Complete!")
    print(f"   Total Rows: {import_stats['total_rows']}")
    print(f"   Products Created: {import_stats['products_created']}")
    print(f"   Products Updated: {import_stats['products_updated']}")
    print(f"   Errors: {import_stats['errors']}")
    
    # Add basic features
    print(f"\n🔧 Adding basic features to products...")
    feature_stats = importer.add_basic_features_to_products()
    
    print(f"\n✅ Features Added!")
    print(f"   Products Processed: {feature_stats['products_processed']}")
    print(f"   Features Added: {feature_stats['features_added']}")
    print(f"   Errors: {feature_stats['errors']}")
    
    # Show summary
    importer.show_database_summary()


if __name__ == "__main__":
    main()
