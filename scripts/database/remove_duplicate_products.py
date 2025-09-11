#!/usr/bin/env python3
"""
Script to remove duplicate products with non-standard SKUs
Keeps the products with AMAZON-{ASIN} format and removes duplicates
"""

import sqlite3
import re
from typing import Dict, List, Tuple

class DuplicateRemover:
    def __init__(self, db_path: str):
        self.db_path = db_path
        
    def connect_database(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close_database(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def extract_asin_from_url(self, url: str) -> str:
        """Extract Amazon ASIN from URL"""
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
    
    def find_asin_for_product(self, product_id: int) -> str:
        """Find the Amazon ASIN for a product from its affiliate links"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT affiliate_url FROM affiliate_links 
            WHERE product_id = ? AND affiliate_url LIKE '%amazon%'
        """, (product_id,))
        
        urls = [row[0] for row in cursor.fetchall()]
        
        for url in urls:
            asin = self.extract_asin_from_url(url)
            if asin:
                return asin
        
        return None
    
    def get_duplicate_products(self) -> List[Dict]:
        """Get products that are duplicates of existing AMAZON-{ASIN} products"""
        cursor = self.conn.cursor()
        
        # Get all products with non-standard SKUs
        cursor.execute("""
            SELECT id, sku, title FROM products 
            WHERE sku NOT LIKE 'AMAZON-%'
            ORDER BY id
        """)
        
        non_standard_products = [dict(row) for row in cursor.fetchall()]
        duplicates = []
        
        for product in non_standard_products:
            product_id = product['id']
            asin = self.find_asin_for_product(product_id)
            
            if asin:
                # Check if there's already a product with AMAZON-{ASIN} format
                cursor.execute("""
                    SELECT id, sku, title FROM products 
                    WHERE sku = ?
                """, (f"AMAZON-{asin}",))
                
                existing_product = cursor.fetchone()
                if existing_product:
                    duplicates.append({
                        'duplicate_id': product_id,
                        'duplicate_sku': product['sku'],
                        'duplicate_title': product['title'],
                        'existing_id': existing_product['id'],
                        'existing_sku': existing_product['sku'],
                        'existing_title': existing_product['title'],
                        'asin': asin
                    })
        
        return duplicates
    
    def merge_affiliate_links(self, duplicate_id: int, existing_id: int):
        """Merge affiliate links from duplicate to existing product"""
        cursor = self.conn.cursor()
        
        # Get affiliate links from duplicate product
        cursor.execute("""
            SELECT affiliate_url, link_type, commission_rate, estimated_commission, is_active
            FROM affiliate_links WHERE product_id = ?
        """, (duplicate_id,))
        
        duplicate_links = cursor.fetchall()
        
        # Get existing affiliate links
        cursor.execute("""
            SELECT affiliate_url FROM affiliate_links WHERE product_id = ?
        """, (existing_id,))
        
        existing_urls = {row[0] for row in cursor.fetchall()}
        
        # Add new affiliate links that don't already exist
        added_count = 0
        for link in duplicate_links:
            if link[0] not in existing_urls:
                cursor.execute("""
                    INSERT INTO affiliate_links 
                    (product_id, platform_id, affiliate_url, link_type, commission_rate, estimated_commission, is_active)
                    VALUES (?, 1, ?, ?, ?, ?, ?)
                """, (existing_id, link[0], link[1], link[2], link[3], link[4]))
                added_count += 1
        
        self.conn.commit()
        return added_count
    
    def merge_product_features(self, duplicate_id: int, existing_id: int):
        """Merge product features from duplicate to existing product"""
        cursor = self.conn.cursor()
        
        # Get features from duplicate product
        cursor.execute("""
            SELECT feature_text, feature_type, display_order, category, importance, impact_score, ai_generated
            FROM product_features WHERE product_id = ?
        """, (duplicate_id,))
        
        duplicate_features = cursor.fetchall()
        
        # Get existing features
        cursor.execute("""
            SELECT feature_text, feature_type FROM product_features WHERE product_id = ?
        """, (existing_id,))
        
        existing_features = {(row[0], row[1]) for row in cursor.fetchall()}
        
        # Add new features that don't already exist
        added_count = 0
        for feature in duplicate_features:
            if (feature[0], feature[1]) not in existing_features:
                cursor.execute("""
                    INSERT INTO product_features 
                    (product_id, feature_text, feature_type, display_order, category, importance, impact_score, ai_generated)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (existing_id, feature[0], feature[1], feature[2], feature[3], feature[4], feature[5], feature[6]))
                added_count += 1
        
        self.conn.commit()
        return added_count
    
    def delete_duplicate_product(self, product_id: int):
        """Delete a duplicate product and all its related data"""
        cursor = self.conn.cursor()
        
        # Delete related data (foreign key constraints will handle this)
        cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))
        self.conn.commit()
    
    def remove_duplicates(self):
        """Remove duplicate products and merge their data"""
        print("🔄 Starting duplicate product removal...")
        print("=" * 60)
        
        self.connect_database()
        
        try:
            # Find duplicate products
            duplicates = self.get_duplicate_products()
            
            print(f"📊 Found {len(duplicates)} duplicate products to remove")
            print("=" * 60)
            
            removed_count = 0
            merged_links = 0
            merged_features = 0
            
            for duplicate in duplicates:
                duplicate_id = duplicate['duplicate_id']
                existing_id = duplicate['existing_id']
                duplicate_sku = duplicate['duplicate_sku']
                existing_sku = duplicate['existing_sku']
                
                print(f"\n📦 Processing duplicate: {duplicate_sku}")
                print(f"   → Merging with: {existing_sku}")
                
                # Merge affiliate links
                links_added = self.merge_affiliate_links(duplicate_id, existing_id)
                if links_added > 0:
                    print(f"   ✅ Merged {links_added} affiliate links")
                    merged_links += links_added
                
                # Merge product features
                features_added = self.merge_product_features(duplicate_id, existing_id)
                if features_added > 0:
                    print(f"   ✅ Merged {features_added} product features")
                    merged_features += features_added
                
                # Delete duplicate product
                self.delete_duplicate_product(duplicate_id)
                print(f"   ✅ Removed duplicate product")
                removed_count += 1
            
            print("\n" + "=" * 60)
            print("🎉 DUPLICATE REMOVAL COMPLETE!")
            print("=" * 60)
            print(f"📊 Products removed: {removed_count}")
            print(f"📊 Affiliate links merged: {merged_links}")
            print(f"📊 Product features merged: {merged_features}")
            
            # Show final product count
            cursor = self.conn.cursor()
            cursor.execute("SELECT COUNT(*) FROM products")
            final_count = cursor.fetchone()[0]
            print(f"📊 Final product count: {final_count}")
            
            # Show final SKU distribution
            self.show_sku_distribution()
            
        except Exception as e:
            print(f"❌ Duplicate removal failed: {e}")
            raise
        finally:
            self.close_database()
    
    def show_sku_distribution(self):
        """Show the distribution of SKU formats after cleanup"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN sku LIKE 'AMAZON-%' THEN 'AMAZON-{ASIN}'
                    ELSE 'Other'
                END as sku_format,
                COUNT(*) as count
            FROM products 
            GROUP BY sku_format
            ORDER BY count DESC
        """)
        
        print("\n📊 Final SKU Distribution:")
        for row in cursor.fetchall():
            print(f"   {row[0]}: {row[1]} products")

def main():
    """Main function"""
    import os
    db_path = "multi_platform_products.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    remover = DuplicateRemover(db_path)
    remover.remove_duplicates()

if __name__ == "__main__":
    main()
