#!/usr/bin/env python3
"""
Centralized Product Migration Manager
Handles old products (1-16) and new products (17-38) with proper data integrity
"""

import sqlite3
import json
import os
import requests
import time
from typing import List, Dict, Any, Optional
from pathlib import Path

class ProductMigrationManager:
    """Centralized manager for product data migration and integrity"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.images_dir = Path("images/products")
        self.images_dir.mkdir(exist_ok=True)
    
    def ensure_database_integrity(self):
        """Ensure database has proper schema and no NULL IDs"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Add original_vercel_urls column if it doesn't exist
            try:
                cursor.execute("ALTER TABLE products ADD COLUMN original_vercel_urls TEXT")
                print("✅ Added original_vercel_urls column")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Check for NULL IDs and fix them
            cursor.execute("SELECT COUNT(*) FROM products WHERE id IS NULL")
            null_count = cursor.fetchone()[0]
            
            if null_count > 0:
                print(f"🔧 Fixing {null_count} NULL IDs...")
                self._fix_null_ids(cursor)
            
            conn.commit()
    
    def _fix_null_ids(self, cursor):
        """Fix NULL IDs by assigning proper sequential IDs"""
        # Get max existing ID
        cursor.execute("SELECT MAX(id) FROM products WHERE id IS NOT NULL")
        max_id = cursor.fetchone()[0] or 0
        
        # Get products with NULL IDs
        cursor.execute("SELECT rowid, sku FROM products WHERE id IS NULL ORDER BY rowid")
        null_products = cursor.fetchall()
        
        for i, (rowid, sku) in enumerate(null_products):
            new_id = max_id + i + 1
            cursor.execute("UPDATE products SET id = ? WHERE rowid = ?", (new_id, rowid))
            print(f"   ✅ Assigned ID {new_id} to {sku}")
    
    def migrate_old_products(self):
        """Handle all old products (IDs 1-16) - download images, fix paths, ensure data integrity"""
        print("🔄 Migrating old products (IDs 1-16)...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get old products
            cursor.execute("""
                SELECT id, sku, title, primary_image_url, image_urls, original_vercel_urls
                FROM products 
                WHERE id BETWEEN 1 AND 16
                ORDER BY id
            """)
            
            old_products = cursor.fetchall()
            print(f"📋 Found {len(old_products)} old products to migrate")
            
            for product_id, sku, title, primary_url, image_urls_str, vercel_urls in old_products:
                print(f"\n📦 Processing {sku} (ID {product_id})...")
                
                # Download and save images locally
                local_images = self._download_webflow_images(product_id, sku, image_urls_str, vercel_urls, cursor)
                
                # Update database with local paths
                if local_images:
                    self._update_product_images(cursor, product_id, local_images, image_urls_str)
                    print(f"   ✅ Updated with {len(local_images)} local images")
                else:
                    print(f"   ⚠️  No images downloaded, keeping original URLs")
            
            conn.commit()
            print(f"\n🎉 Old products migration completed!")
    
    def _download_webflow_images(self, product_id: int, sku: str, image_urls_str: str, vercel_urls: str, cursor) -> List[str]:
        """Download Webflow images and save locally"""
        local_images = []
        
        # Get URLs to download
        urls_to_download = []
        
        # Try to get URLs from image_urls first
        if image_urls_str and 'vercel' in image_urls_str:
            urls_to_download = self._extract_urls_from_string(image_urls_str)
        
        # If no URLs in image_urls, try original_vercel_urls
        if not urls_to_download and vercel_urls:
            try:
                urls_to_download = json.loads(vercel_urls)
            except:
                urls_to_download = self._extract_urls_from_string(vercel_urls)
        
        if not urls_to_download:
            return local_images
        
        print(f"   📷 Found {len(urls_to_download)} images to download")
        
        # Store original URLs if not already stored
        if not vercel_urls:
            cursor.execute("""
                UPDATE products 
                SET original_vercel_urls = ? 
                WHERE id = ?
            """, (json.dumps(urls_to_download), product_id))
        
        # Download images
        for i, url in enumerate(urls_to_download):
            try:
                # Determine file extension
                ext = self._get_file_extension(url)
                
                # Create filename
                if i == 0:
                    filename = f"{product_id}{ext}"
                else:
                    filename = f"{product_id}_{i}{ext}"
                
                filepath = self.images_dir / filename
                
                # Download image
                print(f"   ⬇️  Downloading {filename}...")
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                local_images.append(f"/images/products/{filename}")
                print(f"   ✅ Saved {filename}")
                
                time.sleep(0.5)  # Be respectful
                
            except Exception as e:
                print(f"   ❌ Error downloading image {i}: {e}")
                continue
        
        return local_images
    
    def _extract_urls_from_string(self, url_string: str) -> List[str]:
        """Extract URLs from malformed JSON string"""
        urls = []
        if url_string:
            url_parts = url_string.split(',')
            for part in url_parts:
                url = part.strip().strip('"').strip(']').strip()
                if url.startswith('https://'):
                    urls.append(url)
        return urls
    
    def _get_file_extension(self, url: str) -> str:
        """Determine file extension from URL"""
        if '.webp' in url:
            return '.webp'
        elif '.png' in url:
            return '.png'
        elif '.jpeg' in url:
            return '.jpeg'
        else:
            return '.jpg'
    
    def _update_product_images(self, cursor, product_id: int, local_images: List[str], original_urls: str):
        """Update product with local image paths"""
        if not local_images:
            return
        
        # Update primary image URL
        primary_url = local_images[0]
        cursor.execute("""
            UPDATE products 
            SET primary_image_url = ? 
            WHERE id = ?
        """, (primary_url, product_id))
        
        # Update image_urls with local paths
        cursor.execute("""
            UPDATE products 
            SET image_urls = ? 
            WHERE id = ?
        """, (json.dumps(local_images), product_id))
    
    def process_new_products(self):
        """Handle all new products (IDs 17-38) - ensure proper IDs, image paths, and data integrity"""
        print("🔄 Processing new products (IDs 17-38)...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get new products
            cursor.execute("""
                SELECT id, sku, title, primary_image_url, image_urls
                FROM products 
                WHERE id BETWEEN 17 AND 38
                ORDER BY id
            """)
            
            new_products = cursor.fetchall()
            print(f"📋 Found {len(new_products)} new products to process")
            
            for product_id, sku, title, primary_url, image_urls_str in new_products:
                print(f"\n📦 Processing {sku} (ID {product_id})...")
                
                # Ensure proper image paths
                self._ensure_local_image_paths(cursor, product_id, sku, primary_url, image_urls_str)
                
                # Ensure all required fields are populated
                self._ensure_required_fields(cursor, product_id, sku, title)
            
            conn.commit()
            print(f"\n🎉 New products processing completed!")
    
    def _ensure_local_image_paths(self, cursor, product_id: int, sku: str, primary_url: str, image_urls_str: str):
        """Ensure new products have proper local image paths"""
        # Check if primary image exists locally
        if primary_url and primary_url.startswith('/images/products/'):
            expected_file = primary_url.replace('/images/products/', '')
            file_path = self.images_dir / expected_file
            
            if file_path.exists():
                print(f"   ✅ Primary image exists: {expected_file}")
            else:
                print(f"   ❌ Primary image missing: {expected_file}")
                # Try to find alternative image
                self._find_alternative_image(cursor, product_id, sku)
        else:
            print(f"   ⚠️  Primary image not local: {primary_url}")
            self._find_alternative_image(cursor, product_id, sku)
    
    def _find_alternative_image(self, cursor, product_id: int, sku: str):
        """Find alternative image for product"""
        # Look for images with this product ID
        for ext in ['.jpg', '.jpeg', '.png', '.webp']:
            for i in range(20):  # Check up to 20 images
                if i == 0:
                    filename = f"{product_id}{ext}"
                else:
                    filename = f"{product_id}_{i}{ext}"
                
                file_path = self.images_dir / filename
                if file_path.exists():
                    new_url = f"/images/products/{filename}"
                    cursor.execute("""
                        UPDATE products 
                        SET primary_image_url = ? 
                        WHERE id = ?
                    """, (new_url, product_id))
                    print(f"   ✅ Found alternative image: {filename}")
                    return
        
        print(f"   ❌ No alternative image found for {sku}")
    
    def _ensure_required_fields(self, cursor, product_id: int, sku: str, title: str):
        """Ensure all required fields are populated"""
        # Check for missing required fields
        cursor.execute("""
            SELECT 
                CASE WHEN sku IS NULL OR sku = '' THEN 1 ELSE 0 END as missing_sku,
                CASE WHEN title IS NULL OR title = '' THEN 1 ELSE 0 END as missing_title,
                CASE WHEN primary_image_url IS NULL OR primary_image_url = '' THEN 1 ELSE 0 END as missing_image
            FROM products WHERE id = ?
        """, (product_id,))
        
        missing_sku, missing_title, missing_image = cursor.fetchone()
        
        if missing_sku:
            print(f"   ⚠️  Missing SKU for product {product_id}")
        
        if missing_title:
            print(f"   ⚠️  Missing title for product {product_id}")
        
        if missing_image:
            print(f"   ⚠️  Missing primary image for product {product_id}")
        
        if not (missing_sku or missing_title or missing_image):
            print(f"   ✅ All required fields populated")
    
    def run_full_migration(self):
        """Run complete migration for all products"""
        print("🚀 Starting full product migration...")
        
        # Ensure database integrity
        self.ensure_database_integrity()
        
        # Migrate old products
        self.migrate_old_products()
        
        # Process new products
        self.process_new_products()
        
        # Final verification
        self._verify_migration()
        
        print("\n🎉 Full migration completed successfully!")
    
    def _verify_migration(self):
        """Verify migration results"""
        print("\n🔍 Verifying migration results...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check for NULL IDs
            cursor.execute("SELECT COUNT(*) FROM products WHERE id IS NULL")
            null_ids = cursor.fetchone()[0]
            
            # Check image status
            cursor.execute("""
                SELECT 
                    COUNT(*) as total_products,
                    COUNT(CASE WHEN primary_image_url LIKE '/images/products/%' THEN 1 END) as local_images,
                    COUNT(CASE WHEN primary_image_url LIKE '%vercel%' THEN 1 END) as vercel_images,
                    COUNT(CASE WHEN primary_image_url IS NULL OR primary_image_url = '' THEN 1 END) as missing_images
                FROM products
            """)
            
            total, local, vercel, missing = cursor.fetchone()
            
            print(f"📊 Migration Results:")
            print(f"   Total products: {total}")
            print(f"   Local images: {local}")
            print(f"   Vercel images: {vercel}")
            print(f"   Missing images: {missing}")
            print(f"   NULL IDs: {null_ids}")
            
            if null_ids == 0 and missing == 0:
                print("✅ Migration verification passed!")
            else:
                print("⚠️  Migration verification found issues")

if __name__ == "__main__":
    manager = ProductMigrationManager()
    manager.run_full_migration()
