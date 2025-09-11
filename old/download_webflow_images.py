#!/usr/bin/env python3
"""
Download Webflow Images Script
Downloads images from original Webflow CDN URLs for products with missing images
"""

import sqlite3
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import re

class WebflowImageDownloader:
    """Download images from Webflow CDN for products with missing images"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.images_dir = Path("images/products")
        self.images_dir.mkdir(exist_ok=True)
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'image/webp,image/apng,image/*,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
        })
    
    def get_products_with_missing_images(self) -> List[Dict]:
        """Get products that need images (have old Vercel URLs)"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT id, sku, title, primary_image_url, image_urls, original_vercel_urls
                FROM products 
                WHERE primary_image_url LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
                   OR image_urls LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
                ORDER BY id
            """)
            
            products = []
            for row in cursor.fetchall():
                products.append({
                    'id': row[0],
                    'sku': row[1],
                    'title': row[2],
                    'primary_image_url': row[3],
                    'image_urls': row[4],
                    'original_vercel_urls': row[5]
                })
            
            return products
    
    def get_webflow_urls_from_csv(self) -> Dict[int, List[str]]:
        """Get Webflow URLs from the original CSV file"""
        
        # Get the CSV content from git
        import subprocess
        
        try:
            result = subprocess.run([
                'git', 'show', '79210cd:old/sheets_filtered_products.csv'
            ], capture_output=True, text=True, check=True)
            
            csv_content = result.stdout
            lines = csv_content.strip().split('\n')
            
            # Parse CSV
            webflow_urls = {}
            headers = lines[0].split(',')
            
            for i, line in enumerate(lines[1:], 1):  # Skip header
                if not line.strip():
                    continue
                
                # Simple CSV parsing (handle commas in quoted fields)
                fields = self._parse_csv_line(line)
                
                if len(fields) >= 4:
                    product_name = fields[0]
                    primary_image = fields[3]  # Product Image column
                    multi_images = fields[4] if len(fields) > 4 else ""  # Multi Image column
                    
                    # Extract Webflow URLs
                    urls = []
                    
                    # Primary image
                    if primary_image and 'cdn.prod.website-files.com' in primary_image:
                        urls.append(primary_image)
                    
                    # Multi images
                    if multi_images and 'cdn.prod.website-files.com' in multi_images:
                        # Split by semicolon and clean up
                        multi_urls = multi_images.split(';')
                        for url in multi_urls:
                            url = url.strip()
                            if 'cdn.prod.website-files.com' in url:
                                urls.append(url)
                    
                    if urls:
                        webflow_urls[i] = urls
                        print(f"📋 Found {len(urls)} Webflow URLs for product {i}: {product_name[:50]}...")
            
            return webflow_urls
            
        except Exception as e:
            print(f"❌ Error reading CSV from git: {e}")
            return {}
    
    def _parse_csv_line(self, line: str) -> List[str]:
        """Simple CSV line parser that handles quoted fields"""
        fields = []
        current_field = ""
        in_quotes = False
        
        i = 0
        while i < len(line):
            char = line[i]
            
            if char == '"':
                if in_quotes and i + 1 < len(line) and line[i + 1] == '"':
                    # Escaped quote
                    current_field += '"'
                    i += 2
                else:
                    # Toggle quote state
                    in_quotes = not in_quotes
                    i += 1
            elif char == ',' and not in_quotes:
                # Field separator
                fields.append(current_field)
                current_field = ""
                i += 1
            else:
                current_field += char
                i += 1
        
        # Add the last field
        fields.append(current_field)
        
        return fields
    
    def download_webflow_images(self) -> Dict[str, int]:
        """Download Webflow images for products with missing images"""
        
        print("🔄 Starting Webflow image download...")
        
        # Get products that need images
        products = self.get_products_with_missing_images()
        print(f"📋 Found {len(products)} products with missing images")
        
        # Get Webflow URLs from CSV
        webflow_urls = self.get_webflow_urls_from_csv()
        print(f"📋 Found Webflow URLs for {len(webflow_urls)} products")
        
        results = {
            'total_products': len(products),
            'successful_downloads': 0,
            'failed_downloads': 0,
            'products_updated': 0,
            'errors': []
        }
        
        for product in products:
            product_id = product['id']
            sku = product['sku']
            title = product['title'][:50] + "..." if len(product['title']) > 50 else product['title']
            
            print(f"\n📦 Processing {sku} (ID {product_id}): {title}")
            
            # Get Webflow URLs for this product
            if product_id in webflow_urls:
                webflow_urls_for_product = webflow_urls[product_id]
                print(f"   📷 Found {len(webflow_urls_for_product)} Webflow URLs")
                
                # Download images
                downloaded_images = self._download_images_for_product(
                    product_id, webflow_urls_for_product
                )
                
                if downloaded_images:
                    # Update database
                    success = self._update_product_images(product_id, downloaded_images)
                    if success:
                        results['products_updated'] += 1
                        results['successful_downloads'] += len(downloaded_images)
                        print(f"   ✅ Downloaded {len(downloaded_images)} images and updated database")
                    else:
                        results['failed_downloads'] += len(downloaded_images)
                        results['errors'].append(f"Database update failed for product {product_id}")
                else:
                    results['failed_downloads'] += len(webflow_urls_for_product)
                    results['errors'].append(f"No images downloaded for product {product_id}")
            else:
                print(f"   ⚠️  No Webflow URLs found for this product")
                results['errors'].append(f"No Webflow URLs found for product {product_id}")
        
        return results
    
    def _download_images_for_product(self, product_id: int, webflow_urls: List[str]) -> List[str]:
        """Download images for a specific product"""
        
        downloaded_images = []
        
        for i, url in enumerate(webflow_urls):
            try:
                # Clean URL
                url = url.strip()
                if not url:
                    continue
                
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
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                downloaded_images.append(f"/images/products/{filename}")
                print(f"   ✅ Saved {filename}")
                
                # Rate limiting
                time.sleep(0.5)
                
            except Exception as e:
                print(f"   ❌ Error downloading image {i}: {e}")
                continue
        
        return downloaded_images
    
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
    
    def _update_product_images(self, product_id: int, local_images: List[str]) -> bool:
        """Update product with local image paths"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Update primary image URL
                primary_url = local_images[0]
                cursor.execute("""
                    UPDATE products 
                    SET primary_image_url = ?,
                        image_urls = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (primary_url, json.dumps(local_images), product_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return False
    
    def print_summary(self, results: Dict[str, int]):
        """Print download summary"""
        
        print(f"\n🎉 Webflow Image Download Complete!")
        print(f"📊 Summary:")
        print(f"   Total products processed: {results['total_products']}")
        print(f"   Successful downloads: {results['successful_downloads']}")
        print(f"   Failed downloads: {results['failed_downloads']}")
        print(f"   Products updated: {results['products_updated']}")
        
        if results['errors']:
            print(f"\n❌ Errors:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more errors")

def main():
    """Main function"""
    downloader = WebflowImageDownloader()
    
    print("🚀 Webflow Image Downloader")
    print("This will download images from the original Webflow CDN for products with missing images.")
    
    # Download images
    results = downloader.download_webflow_images()
    
    # Print summary
    downloader.print_summary(results)

if __name__ == "__main__":
    main()
