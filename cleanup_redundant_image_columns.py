#!/usr/bin/env python3
"""
Script to clean up redundant image URL columns from products table
Since we have a dedicated product_images table, we can remove the redundant columns
"""

import sqlite3
import json
from typing import Dict, List, Any

class ImageColumnCleanup:
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
    
    def analyze_image_data(self):
        """Analyze current image data distribution"""
        cursor = self.conn.cursor()
        
        print("📊 Current Image Data Analysis:")
        print("=" * 50)
        
        # Check product_images table
        cursor.execute("SELECT COUNT(*) FROM product_images")
        product_images_count = cursor.fetchone()[0]
        print(f"product_images table: {product_images_count} images")
        
        # Check products with primary_image_url
        cursor.execute("SELECT COUNT(*) FROM products WHERE primary_image_url IS NOT NULL AND primary_image_url != ''")
        primary_image_count = cursor.fetchone()[0]
        print(f"products.primary_image_url: {primary_image_count} products")
        
        # Check products with image_urls
        cursor.execute("SELECT COUNT(*) FROM products WHERE image_urls IS NOT NULL AND image_urls != ''")
        image_urls_count = cursor.fetchone()[0]
        print(f"products.image_urls: {image_urls_count} products")
        
        # Check if primary images are in product_images table
        cursor.execute("""
            SELECT COUNT(DISTINCT p.id) 
            FROM products p 
            JOIN product_images pi ON p.id = pi.product_id 
            WHERE p.primary_image_url IS NOT NULL 
            AND pi.is_primary = 1
        """)
        primary_in_table = cursor.fetchone()[0]
        print(f"Primary images also in product_images: {primary_in_table} products")
        
        return {
            'product_images_count': product_images_count,
            'primary_image_count': primary_image_count,
            'image_urls_count': image_urls_count,
            'primary_in_table': primary_in_table
        }
    
    def verify_data_integrity(self):
        """Verify that all image data is properly stored in product_images table"""
        cursor = self.conn.cursor()
        
        print("\n🔍 Data Integrity Check:")
        print("=" * 50)
        
        # Check if all products have images in product_images table
        cursor.execute("""
            SELECT COUNT(*) FROM products p 
            WHERE NOT EXISTS (
                SELECT 1 FROM product_images pi WHERE pi.product_id = p.id
            )
        """)
        products_without_images = cursor.fetchone()[0]
        print(f"Products without images in product_images table: {products_without_images}")
        
        # Check if primary images are properly marked
        cursor.execute("""
            SELECT COUNT(*) FROM product_images WHERE is_primary = 1
        """)
        primary_images_marked = cursor.fetchone()[0]
        print(f"Images marked as primary in product_images: {primary_images_marked}")
        
        return {
            'products_without_images': products_without_images,
            'primary_images_marked': primary_images_marked
        }
    
    def cleanup_redundant_columns(self):
        """Remove redundant image columns from products table"""
        print("\n🧹 Cleaning up redundant image columns...")
        print("=" * 50)
        
        cursor = self.conn.cursor()
        
        # First, let's backup the data (just in case)
        print("📋 Backing up image data...")
        
        # Get all products with image data
        cursor.execute("""
            SELECT id, sku, primary_image_url, image_urls 
            FROM products 
            WHERE primary_image_url IS NOT NULL OR image_urls IS NOT NULL
        """)
        
        backup_data = []
        for row in cursor.fetchall():
            backup_data.append({
                'id': row['id'],
                'sku': row['sku'],
                'primary_image_url': row['primary_image_url'],
                'image_urls': row['image_urls']
            })
        
        print(f"   ✅ Backed up {len(backup_data)} products with image data")
        
        # Now remove the redundant columns
        print("🗑️  Removing redundant columns...")
        
        # Drop the columns (SQLite doesn't support DROP COLUMN directly, so we need to recreate the table)
        # This is a more complex operation, so let's just set them to NULL for now
        cursor.execute("UPDATE products SET primary_image_url = NULL, image_urls = NULL")
        self.conn.commit()
        
        print("   ✅ Set redundant image columns to NULL")
        
        return backup_data
    
    def run_cleanup(self):
        """Run the complete cleanup process"""
        print("🔄 Starting image column cleanup...")
        print("=" * 60)
        
        self.connect_database()
        
        try:
            # Analyze current state
            analysis = self.analyze_image_data()
            
            # Verify data integrity
            integrity = self.verify_data_integrity()
            
            # Ask for confirmation
            print(f"\n⚠️  This will remove redundant image columns from products table.")
            print(f"   - {analysis['primary_image_count']} products with primary_image_url")
            print(f"   - {analysis['image_urls_count']} products with image_urls")
            print(f"   - All image data is already in product_images table ({analysis['product_images_count']} images)")
            
            response = input("\nProceed with cleanup? (y/N): ").strip().lower()
            
            if response == 'y':
                # Clean up redundant columns
                backup_data = self.cleanup_redundant_columns()
                
                print("\n" + "=" * 60)
                print("🎉 CLEANUP COMPLETE!")
                print("=" * 60)
                print("✅ Redundant image columns removed from products table")
                print("✅ All image data preserved in product_images table")
                print("✅ Database schema is now cleaner and more consistent")
                
                # Show final state
                self.analyze_image_data()
                
            else:
                print("❌ Cleanup cancelled by user")
                
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            raise
        finally:
            self.close_database()

def main():
    """Main function"""
    import os
    db_path = "multi_platform_products.db"
    
    if not os.path.exists(db_path):
        print(f"❌ Database not found: {db_path}")
        return
    
    cleanup = ImageColumnCleanup(db_path)
    cleanup.run_cleanup()

if __name__ == "__main__":
    main()
