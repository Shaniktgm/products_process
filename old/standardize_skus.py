#!/usr/bin/env python3
"""
Script to standardize SKU formats in the database
Converts all SKUs to AMAZON-{ASIN} format
"""

import sqlite3
import re
from typing import Dict, List, Tuple

class SKUStandardizer:
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
        # Pattern to match Amazon ASIN in URL
        patterns = [
            r'/dp/([A-Z0-9]{10})',  # Standard Amazon URL format
            r'/product/([A-Z0-9]{10})',  # Alternative format
            r'asin=([A-Z0-9]{10})',  # ASIN parameter
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def get_products_with_non_standard_skus(self) -> List[Dict]:
        """Get products that don't have AMAZON-{ASIN} format SKUs"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT p.id, p.sku, p.title, al.affiliate_url
            FROM products p
            LEFT JOIN affiliate_links al ON p.id = al.product_id
            WHERE p.sku NOT LIKE 'AMAZON-%'
            ORDER BY p.id
        """)
        return [dict(row) for row in cursor.fetchall()]
    
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
    
    def update_product_sku(self, product_id: int, old_sku: str, new_sku: str):
        """Update product SKU"""
        cursor = self.conn.cursor()
        
        # Check if new SKU already exists
        cursor.execute("SELECT id FROM products WHERE sku = ? AND id != ?", (new_sku, product_id))
        if cursor.fetchone():
            print(f"   ⚠️  SKU {new_sku} already exists, skipping {old_sku}")
            return False
        
        # Update the SKU
        cursor.execute("UPDATE products SET sku = ? WHERE id = ?", (new_sku, product_id))
        self.conn.commit()
        
        print(f"   ✅ Updated SKU: {old_sku} → {new_sku}")
        return True
    
    def standardize_all_skus(self):
        """Standardize all SKUs to AMAZON-{ASIN} format"""
        print("🔄 Starting SKU standardization...")
        print("=" * 60)
        
        self.connect_database()
        
        try:
            # Get products with non-standard SKUs
            products = self.get_products_with_non_standard_skus()
            
            print(f"📊 Found {len(products)} products with non-standard SKUs")
            print("=" * 60)
            
            updated_count = 0
            skipped_count = 0
            
            for product in products:
                product_id = product['id']
                old_sku = product['sku']
                title = product['title']
                
                print(f"\n📦 Processing: {old_sku} - {title[:50]}...")
                
                # Find ASIN from affiliate links
                asin = self.find_asin_for_product(product_id)
                
                if asin:
                    new_sku = f"AMAZON-{asin}"
                    if self.update_product_sku(product_id, old_sku, new_sku):
                        updated_count += 1
                    else:
                        skipped_count += 1
                else:
                    print(f"   ❌ No Amazon ASIN found for {old_sku}")
                    skipped_count += 1
            
            print("\n" + "=" * 60)
            print("🎉 SKU STANDARDIZATION COMPLETE!")
            print("=" * 60)
            print(f"📊 Products updated: {updated_count}")
            print(f"📊 Products skipped: {skipped_count}")
            print(f"📊 Total processed: {len(products)}")
            
            # Show final SKU distribution
            self.show_sku_distribution()
            
        except Exception as e:
            print(f"❌ Standardization failed: {e}")
            raise
        finally:
            self.close_database()
    
    def show_sku_distribution(self):
        """Show the distribution of SKU formats after standardization"""
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
    db_path = "multi_platform_products.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    standardizer = SKUStandardizer(db_path)
    standardizer.standardize_all_skus()

if __name__ == "__main__":
    import os
    main()
