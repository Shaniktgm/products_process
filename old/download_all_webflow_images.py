#!/usr/bin/env python3
"""
Download ALL Webflow Images Script
Downloads all images from original Webflow CDN to stop paying for Webflow
"""

import sqlite3
import requests
import json
import time
from pathlib import Path
from typing import List, Dict, Optional
import subprocess
import re

class CompleteWebflowDownloader:
    """Download ALL images from Webflow CDN"""
    
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
    
    def get_all_webflow_urls_from_csv(self) -> Dict[int, List[str]]:
        """Get ALL Webflow URLs from the original CSV file"""
        
        print("🔄 Extracting Webflow URLs from original CSV...")
        
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
                        print(f"📋 Product {i}: {len(urls)} Webflow URLs - {product_name[:50]}...")
            
            print(f"✅ Found Webflow URLs for {len(webflow_urls)} products")
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
    
    def download_all_webflow_images(self) -> Dict[str, int]:
        """Download ALL Webflow images"""
        
        print("🚀 Starting complete Webflow image download...")
        print("This will download ALL images from Webflow CDN to stop paying for Webflow")
        
        # Get all Webflow URLs from CSV
        webflow_urls = self.get_all_webflow_urls_from_csv()
        
        if not webflow_urls:
            print("❌ No Webflow URLs found!")
            return {'error': 'No Webflow URLs found'}
        
        results = {
            'total_products': len(webflow_urls),
            'total_images': sum(len(urls) for urls in webflow_urls.values()),
            'successful_downloads': 0,
            'failed_downloads': 0,
            'products_processed': 0,
            'errors': []
        }
        
        print(f"📊 Total: {results['total_products']} products, {results['total_images']} images")
        
        # Download images for each product
        for product_id, urls in webflow_urls.items():
            print(f"\n📦 Processing Product {product_id}: {len(urls)} images")
            
            downloaded_images = []
            
            for i, url in enumerate(urls):
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
                    
                    # Skip if already exists
                    if filepath.exists():
                        print(f"   ⏭️  {filename} already exists, skipping")
                        downloaded_images.append(f"/images/products/{filename}")
                        results['successful_downloads'] += 1
                        continue
                    
                    # Download image
                    print(f"   ⬇️  Downloading {filename}...")
                    response = self.session.get(url, timeout=30)
                    response.raise_for_status()
                    
                    # Save image
                    with open(filepath, 'wb') as f:
                        f.write(response.content)
                    
                    downloaded_images.append(f"/images/products/{filename}")
                    results['successful_downloads'] += 1
                    print(f"   ✅ Saved {filename}")
                    
                    # Rate limiting
                    time.sleep(0.5)
                    
                except Exception as e:
                    print(f"   ❌ Error downloading image {i}: {e}")
                    results['failed_downloads'] += 1
                    results['errors'].append(f"Product {product_id}, image {i}: {e}")
                    continue
            
            results['products_processed'] += 1
            
            # Update database if we have images
            if downloaded_images:
                self._update_product_images(product_id, downloaded_images)
        
        return results
    
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
                print(f"   💾 Updated database for product {product_id}")
                return True
                
        except Exception as e:
            print(f"   ⚠️  Database error for product {product_id}: {e}")
            return False
    
    def print_summary(self, results: Dict[str, int]):
        """Print download summary"""
        
        print(f"\n🎉 Complete Webflow Image Download Finished!")
        print(f"📊 Summary:")
        print(f"   Total products: {results['total_products']}")
        print(f"   Total images: {results['total_images']}")
        print(f"   Successful downloads: {results['successful_downloads']}")
        print(f"   Failed downloads: {results['failed_downloads']}")
        print(f"   Products processed: {results['products_processed']}")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more errors")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Upload all images to Vercel")
        print(f"   2. Update database with new Vercel URLs")
        print(f"   3. Cancel Webflow subscription")
        print(f"   4. Enjoy cost savings! 💰")
    
    def get_upload_list(self) -> List[str]:
        """Get list of all images that need to be uploaded to Vercel"""
        
        image_files = []
        for img_file in self.images_dir.glob("*"):
            if img_file.is_file() and img_file.suffix.lower() in ['.jpg', '.jpeg', '.png', '.webp']:
                image_files.append(str(img_file))
        
        return sorted(image_files)

def main():
    """Main function"""
    downloader = CompleteWebflowDownloader()
    
    print("🚀 Complete Webflow Image Downloader")
    print("This will download ALL images from Webflow CDN to stop paying for Webflow")
    print("=" * 80)
    
    # Download all images
    results = downloader.download_all_webflow_images()
    
    # Print summary
    downloader.print_summary(results)
    
    # Show upload list
    upload_list = downloader.get_upload_list()
    print(f"\n📁 Images ready for Vercel upload ({len(upload_list)} files):")
    for img_file in upload_list[:10]:  # Show first 10
        print(f"   - {img_file}")
    if len(upload_list) > 10:
        print(f"   ... and {len(upload_list) - 10} more files")

if __name__ == "__main__":
    main()
