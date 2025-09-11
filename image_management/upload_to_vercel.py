#!/usr/bin/env python3
"""
Upload New Product Images to Vercel Blob Storage
Uploads only images for products with local URLs (new products)
"""

import os
import requests
import json
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional
import time

class VercelBlobUploader:
    """Upload images to Vercel Blob Storage"""
    
    def __init__(self, vercel_token: str = None, db_path: str = "multi_platform_products.db"):
        self.vercel_token = vercel_token or os.getenv('VERCEL_TOKEN')
        self.images_dir = Path("images/products")
        self.db_path = db_path
        self.uploaded_urls = {}
        
        if not self.vercel_token:
            print("❌ VERCEL_TOKEN environment variable not set!")
            print("Please set your Vercel token:")
            print("export VERCEL_TOKEN='your_vercel_token_here'")
            return
        
        # Vercel Blob API endpoint
        self.blob_api_url = "https://api.vercel.com/v1/blob"
        
        # Headers for Vercel API
        self.headers = {
            'Authorization': f'Bearer {self.vercel_token}',
            'Content-Type': 'application/json'
        }
    
    def upload_single_image(self, image_path: Path) -> Optional[str]:
        """Upload a single image to Vercel Blob Storage"""
        
        try:
            # Read image file
            with open(image_path, 'rb') as f:
                image_data = f.read()
            
            # Get filename
            filename = image_path.name
            
            # Create upload request
            upload_data = {
                'filename': filename,
                'contentType': self._get_content_type(image_path),
                'size': len(image_data)
            }
            
            # Get upload URL
            response = requests.post(
                f"{self.blob_api_url}",
                headers=self.headers,
                json=upload_data
            )
            
            if response.status_code != 200:
                print(f"   ❌ Failed to get upload URL for {filename}: {response.text}")
                return None
            
            upload_info = response.json()
            upload_url = upload_info['url']
            
            # Upload image data
            upload_response = requests.put(
                upload_url,
                data=image_data,
                headers={'Content-Type': upload_info['contentType']}
            )
            
            if upload_response.status_code == 200:
                blob_url = upload_info['url']
                print(f"   ✅ Uploaded {filename} -> {blob_url}")
                return blob_url
            else:
                print(f"   ❌ Failed to upload {filename}: {upload_response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Error uploading {image_path.name}: {e}")
            return None
    
    def _get_content_type(self, image_path: Path) -> str:
        """Get content type based on file extension"""
        ext = image_path.suffix.lower()
        content_types = {
            '.jpg': 'image/jpeg',
            '.jpeg': 'image/jpeg',
            '.png': 'image/png',
            '.webp': 'image/webp'
        }
        return content_types.get(ext, 'image/jpeg')
    
    def get_new_product_images(self) -> List[Path]:
        """Get only images for products that have local URLs (new products)"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get products with local image URLs
                cursor.execute("""
                    SELECT id, sku, primary_image_url, image_urls
                    FROM products 
                    WHERE primary_image_url LIKE '/images/products/%'
                       OR image_urls LIKE '/images/products/%'
                    ORDER BY id
                """)
                
                products = cursor.fetchall()
                image_files = []
                
                print(f"🔍 Found {len(products)} products with local image URLs")
                
                for product_id, sku, primary_url, image_urls in products:
                    # Get primary image
                    if primary_url and primary_url.startswith('/images/products/'):
                        filename = primary_url.split('/')[-1]
                        image_path = self.images_dir / filename
                        if image_path.exists():
                            image_files.append(image_path)
                            print(f"   📷 Product {product_id} ({sku}): {filename}")
                    
                    # Get additional images from JSON array
                    if image_urls:
                        try:
                            urls_list = json.loads(image_urls)
                            for url in urls_list:
                                if url.startswith('/images/products/'):
                                    filename = url.split('/')[-1]
                                    image_path = self.images_dir / filename
                                    if image_path.exists() and image_path not in image_files:
                                        image_files.append(image_path)
                        except (json.JSONDecodeError, TypeError):
                            continue
                
                return image_files
                
        except Exception as e:
            print(f"❌ Error getting new product images: {e}")
            return []
    
    def upload_new_product_images(self) -> Dict[str, any]:
        """Upload only new product images to Vercel Blob Storage"""
        
        if not self.vercel_token:
            return {'error': 'No Vercel token provided'}
        
        print("🚀 Starting Vercel Blob Upload for New Products...")
        print(f"📁 Uploading from: {self.images_dir}")
        
        # Get only images for products with local URLs (new products)
        image_files = self.get_new_product_images()
        
        if not image_files:
            print("✅ No new product images found to upload")
            return {
                'total_images': 0,
                'successful_uploads': 0,
                'failed_uploads': 0,
                'uploaded_urls': {},
                'errors': []
            }
        
        print(f"📊 Found {len(image_files)} new product images to upload")
        
        results = {
            'total_images': len(image_files),
            'successful_uploads': 0,
            'failed_uploads': 0,
            'uploaded_urls': {},
            'errors': []
        }
        
        # Upload each image
        for i, image_path in enumerate(image_files, 1):
            print(f"\n📤 [{i}/{len(image_files)}] Uploading {image_path.name}...")
            
            blob_url = self.upload_single_image(image_path)
            
            if blob_url:
                results['successful_uploads'] += 1
                results['uploaded_urls'][image_path.name] = blob_url
                self.uploaded_urls[image_path.name] = blob_url
            else:
                results['failed_uploads'] += 1
                results['errors'].append(f"Failed to upload {image_path.name}")
            
            # Rate limiting
            time.sleep(0.5)
        
        return results
    
    def save_upload_results(self, results: Dict[str, any]):
        """Save upload results to JSON file"""
        
        output_file = "vercel_upload_results.json"
        
        with open(output_file, 'w') as f:
            json.dump(results, f, indent=2)
        
        print(f"\n💾 Upload results saved to: {output_file}")
    
    def print_summary(self, results: Dict[str, any]):
        """Print upload summary"""
        
        print(f"\n🎉 Vercel Blob Upload Complete!")
        print(f"📊 Summary:")
        print(f"   Total images: {results['total_images']}")
        print(f"   Successful uploads: {results['successful_uploads']}")
        print(f"   Failed uploads: {results['failed_uploads']}")
        print(f"   Success rate: {(results['successful_uploads']/results['total_images']*100):.1f}%")
        
        if results['errors']:
            print(f"\n❌ Errors ({len(results['errors'])}):")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more errors")
        
        print(f"\n💡 Next Steps:")
        print(f"   1. Check vercel_upload_results.json for all URLs")
        print(f"   2. Update database with new Vercel URLs")
        print(f"   3. Cancel Webflow subscription")
        print(f"   4. Enjoy cost savings! 💰")

def main():
    """Main function"""
    
    print("🚀 Vercel Blob Uploader for New Products")
    print("Uploading only new product images to sheets-website-blob")
    print("=" * 60)
    
    # Check for Vercel token
    vercel_token = os.getenv('VERCEL_TOKEN')
    if not vercel_token:
        print("❌ VERCEL_TOKEN environment variable not set!")
        print("\nTo get your Vercel token:")
        print("1. Go to https://vercel.com/account/tokens")
        print("2. Create a new token")
        print("3. Set it as environment variable:")
        print("   export VERCEL_TOKEN='your_token_here'")
        print("4. Run this script again")
        return
    
    # Initialize uploader
    uploader = VercelBlobUploader(vercel_token)
    
    # Upload only new product images
    results = uploader.upload_new_product_images()
    
    if 'error' in results:
        print(f"❌ Error: {results['error']}")
        return
    
    # Save results
    uploader.save_upload_results(results)
    
    # Print summary
    uploader.print_summary(results)

if __name__ == "__main__":
    main()
