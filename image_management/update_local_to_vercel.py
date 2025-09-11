#!/usr/bin/env python3
"""
Update Local Image URLs to Vercel URLs
Updates all local /images/products/ URLs to use the same Vercel base URL
"""

import sqlite3
import json
from typing import Dict, List

class LocalToVercelUpdater:
    """Update local image URLs to Vercel URLs"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.vercel_base_url = "https://oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com"
    
    def update_local_to_vercel(self) -> Dict[str, int]:
        """Update all local image URLs to Vercel URLs"""
        
        print("🔄 Updating local image URLs to Vercel URLs...")
        print(f"📡 Vercel Base URL: {self.vercel_base_url}")
        
        results = {
            'total_products': 0,
            'updated_primary': 0,
            'updated_image_urls': 0,
            'errors': []
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products with local image URLs
                cursor.execute("""
                    SELECT id, sku, title, primary_image_url, image_urls
                    FROM products 
                    WHERE primary_image_url LIKE '/images/products/%'
                       OR image_urls LIKE '/images/products/%'
                    ORDER BY id
                """)
                
                products = cursor.fetchall()
                results['total_products'] = len(products)
                
                print(f"📊 Found {len(products)} products with local image URLs")
                
                for product_id, sku, title, primary_url, image_urls in products:
                    print(f"\n📦 Processing: {title[:50]}...")
                    
                    updated_primary = False
                    updated_image_urls = False
                    
                    # Update primary_image_url
                    if primary_url and primary_url.startswith('/images/products/'):
                        new_primary_url = f"{self.vercel_base_url}{primary_url}"
                        
                        cursor.execute("""
                            UPDATE products 
                            SET primary_image_url = ?, updated_at = datetime('now')
                            WHERE id = ?
                        """, (new_primary_url, product_id))
                        
                        updated_primary = True
                        print(f"   ✅ Updated primary image: {new_primary_url}")
                    
                    # Update image_urls JSON array
                    if image_urls:
                        try:
                            # Parse JSON array
                            if isinstance(image_urls, str):
                                urls_list = json.loads(image_urls)
                            else:
                                urls_list = image_urls
                            
                            # Update local URLs to Vercel URLs
                            updated_urls = []
                            for url in urls_list:
                                if url.startswith('/images/products/'):
                                    new_url = f"{self.vercel_base_url}{url}"
                                    updated_urls.append(new_url)
                                    print(f"   ✅ Updated image URL: {new_url}")
                                else:
                                    updated_urls.append(url)
                            
                            # Update database with new URLs
                            if updated_urls != urls_list:
                                cursor.execute("""
                                    UPDATE products 
                                    SET image_urls = ?, updated_at = datetime('now')
                                    WHERE id = ?
                                """, (json.dumps(updated_urls), product_id))
                                
                                updated_image_urls = True
                                
                        except (json.JSONDecodeError, TypeError) as e:
                            print(f"   ⚠️  Error parsing image_urls for product {product_id}: {e}")
                            results['errors'].append(f"Product {product_id}: JSON parse error")
                    
                    # Count updates
                    if updated_primary:
                        results['updated_primary'] += 1
                    if updated_image_urls:
                        results['updated_image_urls'] += 1
                
                conn.commit()
                print(f"\n✅ Database updated successfully!")
                
        except Exception as e:
            print(f"❌ Error updating database: {e}")
            results['errors'].append(f"Database error: {e}")
        
        return results
    
    def verify_updates(self) -> Dict[str, int]:
        """Verify the URL updates"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count products with local URLs (should be 0)
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE primary_image_url LIKE '/images/products/%'
                   OR image_urls LIKE '/images/products/%'
            """)
            local_count = cursor.fetchone()[0]
            
            # Count products with Vercel URLs
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE primary_image_url LIKE '%vercel%'
                   OR image_urls LIKE '%vercel%'
            """)
            vercel_count = cursor.fetchone()[0]
            
            # Count products with no image URLs
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE primary_image_url IS NULL OR primary_image_url = ''
            """)
            no_image_count = cursor.fetchone()[0]
            
            return {
                'local_urls': local_count,
                'vercel_urls': vercel_count,
                'no_images': no_image_count
            }
    
    def print_summary(self, results: Dict[str, int]):
        """Print update summary"""
        
        print(f"\n🎉 Local to Vercel URL Update Complete!")
        print(f"📊 Summary:")
        print(f"   Total products processed: {results['total_products']}")
        print(f"   Primary images updated: {results['updated_primary']}")
        print(f"   Image URL arrays updated: {results['updated_image_urls']}")
        
        if results['errors']:
            print(f"   Errors: {len(results['errors'])}")
            for error in results['errors'][:3]:  # Show first 3 errors
                print(f"     - {error}")
            if len(results['errors']) > 3:
                print(f"     ... and {len(results['errors']) - 3} more errors")
        
        # Verify results
        verification = self.verify_updates()
        print(f"\n🔍 Verification:")
        print(f"   Products with local URLs: {verification['local_urls']} (should be 0)")
        print(f"   Products with Vercel URLs: {verification['vercel_urls']}")
        print(f"   Products with no images: {verification['no_images']}")

def main():
    """Main function"""
    
    print("🚀 Local to Vercel URL Updater")
    print("Updating all local image URLs to use Vercel storage")
    print("=" * 60)
    
    updater = LocalToVercelUpdater()
    
    # Update URLs
    results = updater.update_local_to_vercel()
    
    # Print summary
    updater.print_summary(results)

if __name__ == "__main__":
    main()
