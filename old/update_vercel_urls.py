#!/usr/bin/env python3
"""
Update Vercel URLs Script
Updates database with new Vercel URLs after uploading local images
"""

import sqlite3
import json
from typing import Dict, List, Optional

class VercelUrlUpdater:
    """Update database with new Vercel URLs"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
    
    def get_products_with_old_vercel_urls(self) -> List[Dict]:
        """Get products that still have old Vercel URLs"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, sku, title, primary_image_url, image_urls
                FROM products 
                WHERE primary_image_url LIKE '%vercel%' 
                   OR image_urls LIKE '%vercel%'
                ORDER BY id
            """)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'sku': row[1],
                    'title': row[2],
                    'primary_image_url': row[3],
                    'image_urls': row[4]
                })
            
            return products
    
    def update_product_vercel_urls(self, product_id: int, new_vercel_base_url: str) -> bool:
        """Update a product's URLs to use new Vercel base URL"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get current product data
                cursor.execute("""
                    SELECT primary_image_url, image_urls
                    FROM products 
                    WHERE id = ?
                """, (product_id,))
                
                result = cursor.fetchone()
                if not result:
                    print(f"❌ Product {product_id} not found")
                    return False
                
                old_primary_url = result[0]
                old_image_urls_str = result[1]
                
                # Determine file extension and create new URLs
                if old_primary_url and old_primary_url.startswith('/images/products/'):
                    # Extract filename from local path
                    filename = old_primary_url.split('/')[-1]
                    new_primary_url = f"{new_vercel_base_url}/images/products/{filename}"
                else:
                    # Extract filename from old Vercel URL
                    filename = self._extract_filename_from_vercel_url(old_primary_url)
                    if filename:
                        new_primary_url = f"{new_vercel_base_url}/images/products/{filename}"
                    else:
                        print(f"⚠️  Could not extract filename from {old_primary_url}")
                        return False
                
                # Update image_urls array
                new_image_urls = []
                if old_image_urls_str:
                    try:
                        # Try to parse as JSON
                        old_image_urls = json.loads(old_image_urls_str)
                    except:
                        # If not JSON, try to extract URLs from string
                        old_image_urls = self._extract_urls_from_string(old_image_urls_str)
                    
                    for old_url in old_image_urls:
                        if old_url.startswith('/images/products/'):
                            # Local path - just update base URL
                            filename = old_url.split('/')[-1]
                            new_url = f"{new_vercel_base_url}/images/products/{filename}"
                        elif 'vercel' in old_url:
                            # Old Vercel URL - extract filename and update
                            filename = self._extract_filename_from_vercel_url(old_url)
                            if filename:
                                new_url = f"{new_vercel_base_url}/images/products/{filename}"
                            else:
                                new_url = old_url  # Keep original if can't extract
                        else:
                            new_url = old_url  # Keep non-Vercel URLs as-is
                        
                        new_image_urls.append(new_url)
                
                # Update database
                cursor.execute("""
                    UPDATE products 
                    SET primary_image_url = ?, 
                        image_urls = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (new_primary_url, json.dumps(new_image_urls), product_id))
                
                conn.commit()
                
                print(f"✅ Updated product {product_id}:")
                print(f"   Primary: {new_primary_url}")
                print(f"   Images: {len(new_image_urls)} URLs updated")
                
                return True
                
        except Exception as e:
            print(f"❌ Error updating product {product_id}: {e}")
            return False
    
    def _extract_filename_from_vercel_url(self, url: str) -> Optional[str]:
        """Extract filename from old Vercel URL"""
        try:
            # Old Vercel URLs have format like:
            # https://oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com/6748046e1bab1a092ed95e30_673d6ea1ce546209494ddd46_Organic%20Cotton%20Sheet%20Set%20White.webp
            
            # Extract the last part after the last underscore
            parts = url.split('_')
            if len(parts) > 1:
                filename = parts[-1]
                # Clean up URL encoding
                filename = filename.replace('%20', ' ').replace('%26', '&')
                return filename
            return None
        except:
            return None
    
    def _extract_urls_from_string(self, url_string: str) -> List[str]:
        """Extract URLs from malformed JSON string"""
        urls = []
        if url_string:
            # Split by common separators
            url_parts = url_string.split(',')
            for part in url_parts:
                url = part.strip().strip('"').strip(']').strip()
                if url.startswith('http'):
                    urls.append(url)
        return urls
    
    def update_all_vercel_urls(self, new_vercel_base_url: str) -> Dict[str, int]:
        """Update all products with old Vercel URLs"""
        
        print(f"🔄 Updating all Vercel URLs to: {new_vercel_base_url}")
        
        products = self.get_products_with_old_vercel_urls()
        print(f"📋 Found {len(products)} products with old Vercel URLs")
        
        results = {
            'total': len(products),
            'successful': 0,
            'failed': 0,
            'errors': []
        }
        
        for product in products:
            product_id = product['id']
            sku = product['sku']
            title = product['title'][:50] + "..." if len(product['title']) > 50 else product['title']
            
            print(f"\n📦 Updating {sku} (ID {product_id}): {title}")
            
            success = self.update_product_vercel_urls(product_id, new_vercel_base_url)
            
            if success:
                results['successful'] += 1
            else:
                results['failed'] += 1
                results['errors'].append(f"Failed to update product {product_id}")
        
        return results
    
    def verify_vercel_urls(self) -> Dict[str, int]:
        """Verify which products still have old Vercel URLs"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count products with old Vercel URLs
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE primary_image_url LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
                   OR image_urls LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
            """)
            old_vercel_count = cursor.fetchone()[0]
            
            # Count products with new Vercel URLs
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE (primary_image_url LIKE '%vercel%' 
                   OR image_urls LIKE '%vercel%')
                   AND (primary_image_url NOT LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
                   AND image_urls NOT LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%')
            """)
            new_vercel_count = cursor.fetchone()[0]
            
            # Count products with local images
            cursor.execute("""
                SELECT COUNT(*) FROM products 
                WHERE primary_image_url LIKE '/images/products/%'
            """)
            local_count = cursor.fetchone()[0]
            
            return {
                'old_vercel': old_vercel_count,
                'new_vercel': new_vercel_count,
                'local': local_count
            }

def main():
    """Example usage"""
    updater = VercelUrlUpdater()
    
    # Check current status
    print("🔍 Current Vercel URL Status:")
    status = updater.verify_vercel_urls()
    print(f"   Old Vercel URLs: {status['old_vercel']}")
    print(f"   New Vercel URLs: {status['new_vercel']}")
    print(f"   Local Images: {status['local']}")
    
    # Show products that need updating
    products = updater.get_products_with_old_vercel_urls()
    print(f"\n📋 Products needing Vercel URL updates:")
    for product in products:
        print(f"   ID {product['id']}: {product['sku']} - {product['title'][:50]}...")
    
    print(f"\n🚀 To update URLs, run:")
    print(f"updater.update_all_vercel_urls('https://your-new-vercel-domain.com')")

if __name__ == "__main__":
    main()
