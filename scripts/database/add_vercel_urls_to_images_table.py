#!/usr/bin/env python3
"""
Script to add Vercel URLs to the product_images table
This script will:
1. Check existing local image files
2. Generate corresponding Vercel URLs
3. Update the product_images table with Vercel URLs
"""

import sqlite3
import os
from pathlib import Path
from typing import Dict, List, Any

class VercelUrlUpdater:
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.vercel_base_url = "https://oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com"
        self.local_images_dir = "images/products"
        
    def connect_database(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close_database(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def get_local_image_files(self) -> List[str]:
        """Get list of local image files"""
        if not os.path.exists(self.local_images_dir):
            return []
        
        image_files = []
        for file in os.listdir(self.local_images_dir):
            if file.lower().endswith(('.jpg', '.jpeg', '.png', '.webp')):
                image_files.append(file)
        
        return sorted(image_files)
    
    def generate_vercel_url(self, filename: str) -> str:
        """Generate Vercel URL for a local image file"""
        return f"{self.vercel_base_url}/{filename}"
    
    def get_product_images_data(self) -> List[Dict[str, Any]]:
        """Get all product images data from the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, product_id, original_url, local_path, vercel_url, is_primary, display_order
            FROM product_images
            ORDER BY product_id, display_order
        """)
        
        return [dict(row) for row in cursor.fetchall()]
    
    def update_vercel_urls(self):
        """Update Vercel URLs in the product_images table"""
        print("🔄 Adding Vercel URLs to product_images table...")
        print("=" * 60)
        
        self.connect_database()
        
        try:
            # Get local image files
            local_files = self.get_local_image_files()
            print(f"📁 Found {len(local_files)} local image files")
            
            # Get product images data
            product_images = self.get_product_images_data()
            print(f"📊 Found {len(product_images)} images in product_images table")
            
            # Create a mapping of local_path to filename
            local_path_to_filename = {}
            for file in local_files:
                # Extract the filename from local_path (e.g., "1.webp" from "/images/products/1.webp")
                local_path_to_filename[file] = file
            
            updated_count = 0
            added_count = 0
            
            print("\n🔄 Processing images...")
            
            for image in product_images:
                local_path = image['local_path']
                current_vercel_url = image['vercel_url']
                
                # Skip if already has Vercel URL
                if current_vercel_url:
                    continue
                
                # Extract filename from local_path
                if local_path:
                    filename = os.path.basename(local_path)
                    
                    # Check if we have this file locally
                    if filename in local_files:
                        vercel_url = self.generate_vercel_url(filename)
                        
                        # Update the database
                        cursor = self.conn.cursor()
                        cursor.execute("""
                            UPDATE product_images 
                            SET vercel_url = ?
                            WHERE id = ?
                        """, (vercel_url, image['id']))
                        
                        updated_count += 1
                        print(f"   ✅ Updated image {image['id']}: {filename} → {vercel_url}")
                    else:
                        print(f"   ⚠️  Local file not found: {filename}")
                else:
                    print(f"   ⚠️  No local_path for image {image['id']}")
            
            self.conn.commit()
            
            print("\n" + "=" * 60)
            print("🎉 VERCEL URL UPDATE COMPLETE!")
            print("=" * 60)
            print(f"📊 Images updated with Vercel URLs: {updated_count}")
            print(f"📊 Total images in table: {len(product_images)}")
            
            # Show final statistics
            self.show_final_statistics()
            
        except Exception as e:
            print(f"❌ Update failed: {e}")
            raise
        finally:
            self.close_database()
    
    def show_final_statistics(self):
        """Show final statistics of the update"""
        cursor = self.conn.cursor()
        
        # Count images with Vercel URLs
        cursor.execute("SELECT COUNT(*) FROM product_images WHERE vercel_url IS NOT NULL AND vercel_url != ''")
        with_vercel = cursor.fetchone()[0]
        
        # Count images without Vercel URLs
        cursor.execute("SELECT COUNT(*) FROM product_images WHERE vercel_url IS NULL OR vercel_url = ''")
        without_vercel = cursor.fetchone()[0]
        
        # Count primary images with Vercel URLs
        cursor.execute("SELECT COUNT(*) FROM product_images WHERE is_primary = 1 AND vercel_url IS NOT NULL AND vercel_url != ''")
        primary_with_vercel = cursor.fetchone()[0]
        
        print(f"\n📊 Final Statistics:")
        print(f"   Images with Vercel URLs: {with_vercel}")
        print(f"   Images without Vercel URLs: {without_vercel}")
        print(f"   Primary images with Vercel URLs: {primary_with_vercel}")
        
        # Show some examples
        cursor.execute("""
            SELECT local_path, vercel_url 
            FROM product_images 
            WHERE vercel_url IS NOT NULL 
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        if examples:
            print(f"\n📋 Example Vercel URLs:")
            for local_path, vercel_url in examples:
                print(f"   {local_path} → {vercel_url}")

def main():
    """Main function"""
    print("🚀 Adding Vercel URLs to product_images table")
    print("=" * 60)
    
    updater = VercelUrlUpdater()
    updater.update_vercel_urls()

if __name__ == "__main__":
    main()
