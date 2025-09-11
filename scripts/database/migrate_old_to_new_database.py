#!/usr/bin/env python3
"""
One-off script to migrate data from old database to new database
Fills in missing values and adds missing products
"""

import sqlite3
import json
import os
from pathlib import Path
from typing import Dict, List, Any, Optional

class DatabaseMigrator:
    def __init__(self, old_db_path: str, new_db_path: str):
        self.old_db_path = old_db_path
        self.new_db_path = new_db_path
        
    def connect_databases(self):
        """Connect to both databases"""
        self.old_conn = sqlite3.connect(self.old_db_path)
        self.old_conn.row_factory = sqlite3.Row
        self.new_conn = sqlite3.connect(self.new_db_path)
        self.new_conn.row_factory = sqlite3.Row
        
    def close_databases(self):
        """Close database connections"""
        if hasattr(self, 'old_conn'):
            self.old_conn.close()
        if hasattr(self, 'new_conn'):
            self.new_conn.close()
    
    def get_old_products(self) -> List[Dict[str, Any]]:
        """Get all products from old database"""
        cursor = self.old_conn.cursor()
        cursor.execute("""
            SELECT * FROM products
            ORDER BY id
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_new_products(self) -> List[Dict[str, Any]]:
        """Get all products from new database"""
        cursor = self.new_conn.cursor()
        cursor.execute("""
            SELECT * FROM products
            ORDER BY id
        """)
        return [dict(row) for row in cursor.fetchall()]
    
    def get_new_product_by_sku(self, sku: str) -> Optional[Dict[str, Any]]:
        """Get product from new database by SKU"""
        cursor = self.new_conn.cursor()
        cursor.execute("SELECT * FROM products WHERE sku = ?", (sku,))
        row = cursor.fetchone()
        return dict(row) if row else None
    
    def update_product_fields(self, product_id: int, updates: Dict[str, Any]):
        """Update specific fields in a product"""
        if not updates:
            return
            
        set_clauses = []
        values = []
        
        for field, value in updates.items():
            if value is not None and value != '':
                set_clauses.append(f"{field} = ?")
                values.append(value)
        
        if set_clauses:
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(set_clauses)} WHERE id = ?"
            
            cursor = self.new_conn.cursor()
            cursor.execute(query, values)
            self.new_conn.commit()
            print(f"   ✅ Updated product {product_id}: {', '.join(set_clauses)}")
    
    def insert_new_product(self, old_product: Dict[str, Any]) -> int:
        """Insert a new product from old database"""
        cursor = self.new_conn.cursor()
        
        # Map old product fields to new schema (only existing columns)
        new_product_data = {
            'sku': old_product['sku'],
            'title': old_product['title'],
            'brand': old_product.get('brand'),
            'description': old_product.get('description'),
            'short_description': old_product.get('short_description'),
            'slug': old_product.get('slug'),
            'price': old_product.get('price'),
            'currency': old_product.get('currency', 'USD'),
            'rating': old_product.get('rating'),
            'review_count': old_product.get('review_count'),
            'availability': old_product.get('availability'),
            'primary_image_url': old_product.get('primary_image_url'),
            'image_urls': old_product.get('image_urls'),
            'product_summary': old_product.get('product_summary'),
            'created_at': old_product.get('created_at'),
            'updated_at': old_product.get('updated_at')
        }
        
        # Remove None values
        new_product_data = {k: v for k, v in new_product_data.items() if v is not None}
        
        columns = list(new_product_data.keys())
        placeholders = ['?' for _ in columns]
        values = list(new_product_data.values())
        
        query = f"""
            INSERT INTO products ({', '.join(columns)})
            VALUES ({', '.join(placeholders)})
        """
        
        cursor.execute(query, values)
        product_id = cursor.lastrowid
        self.new_conn.commit()
        
        print(f"   ✅ Inserted new product: {old_product['sku']} (ID: {product_id})")
        return product_id
    
    def migrate_product_features(self, old_product_id: int, new_product_id: int):
        """Migrate product features from old to new database"""
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM product_features WHERE product_id = ?", (old_product_id,))
        old_features = [dict(row) for row in cursor.fetchall()]
        
        if not old_features:
            return
        
        new_cursor = self.new_conn.cursor()
        for feature in old_features:
            # Check if feature already exists
            new_cursor.execute("""
                SELECT id FROM product_features 
                WHERE product_id = ? AND feature_type = ? AND feature_text = ?
            """, (new_product_id, feature['feature_type'], feature['feature_text']))
            
            if not new_cursor.fetchone():
                new_cursor.execute("""
                    INSERT INTO product_features 
                    (product_id, feature_text, feature_type, display_order, category, importance, impact_score, ai_generated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_product_id,
                    feature['feature_text'],
                    feature['feature_type'],
                    feature.get('display_order', 0),
                    feature.get('category'),
                    feature.get('importance'),
                    feature.get('impact_score'),
                    feature.get('ai_generated', False)
                ))
        
        self.new_conn.commit()
        if old_features:
            print(f"   ✅ Migrated {len(old_features)} features")
    
    def migrate_product_specifications(self, old_product_id: int, new_product_id: int):
        """Migrate product specifications from old to new database"""
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM product_specifications WHERE product_id = ?", (old_product_id,))
        old_specs = [dict(row) for row in cursor.fetchall()]
        
        if not old_specs:
            return
        
        new_cursor = self.new_conn.cursor()
        for spec in old_specs:
            # Check if spec already exists
            new_cursor.execute("""
                SELECT id FROM product_specifications 
                WHERE product_id = ? AND spec_name = ? AND spec_value = ?
            """, (new_product_id, spec['spec_name'], spec['spec_value']))
            
            if not new_cursor.fetchone():
                new_cursor.execute("""
                    INSERT INTO product_specifications 
                    (product_id, spec_name, spec_value, spec_unit, display_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    new_product_id,
                    spec['spec_name'],
                    spec['spec_value'],
                    spec.get('spec_unit'),
                    spec.get('display_order', 0)
                ))
        
        self.new_conn.commit()
        if old_specs:
            print(f"   ✅ Migrated {len(old_specs)} specifications")
    
    def migrate_product_categories(self, old_product_id: int, new_product_id: int):
        """Migrate product categories from old to new database"""
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM product_categories WHERE product_id = ?", (old_product_id,))
        old_categories = [dict(row) for row in cursor.fetchall()]
        
        if not old_categories:
            return
        
        new_cursor = self.new_conn.cursor()
        for category in old_categories:
            # Check if category already exists
            new_cursor.execute("""
                SELECT id FROM product_categories 
                WHERE product_id = ? AND category_name = ?
            """, (new_product_id, category['category_name']))
            
            if not new_cursor.fetchone():
                new_cursor.execute("""
                    INSERT INTO product_categories 
                    (product_id, category_name, category_path, is_primary, display_order)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    new_product_id,
                    category['category_name'],
                    category.get('category_path'),
                    category.get('is_primary', False),
                    category.get('display_order', 0)
                ))
        
        self.new_conn.commit()
        if old_categories:
            print(f"   ✅ Migrated {len(old_categories)} categories")
    
    def migrate_affiliate_links(self, old_product_id: int, new_product_id: int):
        """Migrate affiliate links from old to new database"""
        cursor = self.old_conn.cursor()
        cursor.execute("SELECT * FROM affiliate_links WHERE product_id = ?", (old_product_id,))
        old_links = [dict(row) for row in cursor.fetchall()]
        
        if not old_links:
            return
        
        new_cursor = self.new_conn.cursor()
        for link in old_links:
            # Check if link already exists
            new_cursor.execute("""
                SELECT id FROM affiliate_links 
                WHERE product_id = ? AND affiliate_url = ?
            """, (new_product_id, link['affiliate_url']))
            
            if not new_cursor.fetchone():
                new_cursor.execute("""
                    INSERT INTO affiliate_links 
                    (product_id, platform_id, affiliate_url, link_type, commission_rate, estimated_commission, is_active, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    new_product_id,
                    link.get('platform_id', 1),  # Default to Amazon
                    link['affiliate_url'],
                    link.get('link_type', 'web'),
                    link.get('commission_rate'),
                    link.get('estimated_commission'),
                    link.get('is_active', True),
                    link.get('created_at'),
                    link.get('updated_at')
                ))
        
        self.new_conn.commit()
        if old_links:
            print(f"   ✅ Migrated {len(old_links)} affiliate links")
    
    def run_migration(self):
        """Run the complete migration process"""
        print("🔄 Starting database migration from old to new...")
        print("=" * 60)
        
        self.connect_databases()
        
        try:
            # Get all products from both databases
            old_products = self.get_old_products()
            new_products = self.get_new_products()
            
            print(f"📊 Old database: {len(old_products)} products")
            print(f"📊 New database: {len(new_products)} products")
            print("=" * 60)
            
            # Create a mapping of SKUs to new product IDs
            new_sku_map = {product['sku']: product['id'] for product in new_products}
            
            products_updated = 0
            products_added = 0
            features_migrated = 0
            specs_migrated = 0
            categories_migrated = 0
            links_migrated = 0
            
            for old_product in old_products:
                old_sku = old_product['sku']
                print(f"\n📦 Processing: {old_sku} - {old_product['title'][:50]}...")
                
                if old_sku in new_sku_map:
                    # Product exists in new database - update missing fields
                    new_product_id = new_sku_map[old_sku]
                    new_product = self.get_new_product_by_sku(old_sku)
                    
                    # Check what fields need updating (only existing columns)
                    updates = {}
                    for field in ['brand', 'description', 'short_description', 'price', 'rating', 'review_count', 'primary_image_url', 'image_urls', 'product_summary']:
                        if new_product.get(field) is None and old_product.get(field) is not None:
                            updates[field] = old_product[field]
                    
                    if updates:
                        self.update_product_fields(new_product_id, updates)
                        products_updated += 1
                    
                    # Migrate related data
                    self.migrate_product_features(old_product['id'], new_product_id)
                    self.migrate_product_specifications(old_product['id'], new_product_id)
                    self.migrate_product_categories(old_product['id'], new_product_id)
                    self.migrate_affiliate_links(old_product['id'], new_product_id)
                    
                else:
                    # Product doesn't exist in new database - add it
                    new_product_id = self.insert_new_product(old_product)
                    products_added += 1
                    
                    # Migrate related data
                    self.migrate_product_features(old_product['id'], new_product_id)
                    self.migrate_product_specifications(old_product['id'], new_product_id)
                    self.migrate_product_categories(old_product['id'], new_product_id)
                    self.migrate_affiliate_links(old_product['id'], new_product_id)
            
            print("\n" + "=" * 60)
            print("🎉 MIGRATION COMPLETE!")
            print("=" * 60)
            print(f"📊 Products updated: {products_updated}")
            print(f"📊 Products added: {products_added}")
            print(f"📊 Total products processed: {len(old_products)}")
            
            # Final count
            final_count = len(self.get_new_products())
            print(f"📊 Final product count in new database: {final_count}")
            
        except Exception as e:
            print(f"❌ Migration failed: {e}")
            raise
        finally:
            self.close_databases()

def main():
    """Main function"""
    old_db_path = "multi_platform_products_old.db"
    new_db_path = "multi_platform_products.db"
    
    if not os.path.exists(old_db_path):
        print(f"❌ Old database not found: {old_db_path}")
        return
    
    if not os.path.exists(new_db_path):
        print(f"❌ New database not found: {new_db_path}")
        return
    
    migrator = DatabaseMigrator(old_db_path, new_db_path)
    migrator.run_migration()

if __name__ == "__main__":
    main()
