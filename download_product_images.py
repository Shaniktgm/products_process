#!/usr/bin/env python3
"""
Download all product images and save them locally
"""

import sqlite3
import requests
import os
from urllib.parse import urlparse
import time
from typing import List, Dict, Optional

def create_images_directory():
    """Create local images directory"""
    images_dir = "downloaded_images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        print(f"✅ Created directory: {images_dir}")
    return images_dir

def get_product_images():
    """Get all product images from database"""
    print("📸 Getting product images from database...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Get all products with their image URLs
            cursor.execute("""
                SELECT id, title, primary_image_url, image_urls
                FROM products 
                WHERE primary_image_url IS NOT NULL OR image_urls IS NOT NULL
            """)
            
            products = cursor.fetchall()
            print(f"   Found {len(products)} products with images")
            
            return products
            
    except Exception as e:
        print(f"❌ Error getting product images: {str(e)}")
        return []

def download_image(url: str, local_path: str) -> bool:
    """Download a single image"""
    try:
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        with open(local_path, 'wb') as f:
            f.write(response.content)
        
        return True
        
    except Exception as e:
        print(f"   ❌ Failed to download {url}: {str(e)}")
        return False

def get_file_extension(url: str) -> str:
    """Get file extension from URL"""
    parsed_url = urlparse(url)
    path = parsed_url.path
    
    # Get extension from path
    if '.' in path:
        return path.split('.')[-1].lower()
    
    # Default to jpg if no extension
    return 'jpg'

def sanitize_filename(filename: str) -> str:
    """Sanitize filename for filesystem"""
    # Remove or replace invalid characters
    invalid_chars = '<>:"/\\|?*'
    for char in invalid_chars:
        filename = filename.replace(char, '_')
    
    # Limit length
    if len(filename) > 100:
        filename = filename[:100]
    
    return filename

def add_local_path_column():
    """Add local_path column to products table"""
    print("🔧 Adding local_path column to products table...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Check if column already exists
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'local_image_path' not in columns:
                cursor.execute("ALTER TABLE products ADD COLUMN local_image_path TEXT")
                print("   ✅ Added local_image_path column")
            else:
                print("   ⚠️  local_image_path column already exists")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error adding column: {str(e)}")

def download_all_images():
    """Download all product images"""
    print("🔄 Starting image download process...")
    print("=" * 60)
    
    # Create images directory
    images_dir = create_images_directory()
    
    # Add local_path column
    add_local_path_column()
    
    # Get product images
    products = get_product_images()
    
    if not products:
        print("❌ No products with images found")
        return
    
    downloaded_count = 0
    failed_count = 0
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            for product_id, title, primary_image_url, image_urls in products:
                print(f"\n📦 Processing: {title[:50]}...")
                
                # Process primary image
                if primary_image_url:
                    local_path = download_single_image(
                        primary_image_url, 
                        product_id, 
                        title, 
                        images_dir, 
                        "primary"
                    )
                    
                    if local_path:
                        # Update database with local path
                        cursor.execute("""
                            UPDATE products 
                            SET local_image_path = ? 
                            WHERE id = ?
                        """, (local_path, product_id))
                        downloaded_count += 1
                    else:
                        failed_count += 1
                
                # Process additional images (if any)
                if image_urls:
                    # Parse image_urls (assuming it's a JSON string or comma-separated)
                    try:
                        import json
                        additional_urls = json.loads(image_urls)
                    except:
                        # If not JSON, try comma-separated
                        additional_urls = [url.strip() for url in image_urls.split(',') if url.strip()]
                    
                    for i, url in enumerate(additional_urls):
                        local_path = download_single_image(
                            url, 
                            product_id, 
                            title, 
                            images_dir, 
                            f"additional_{i+1}"
                        )
                        
                        if local_path:
                            downloaded_count += 1
                        else:
                            failed_count += 1
                
                # Small delay to be respectful to servers
                time.sleep(0.5)
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error during download process: {str(e)}")
    
    print(f"\n🎉 Download process completed!")
    print(f"   ✅ Successfully downloaded: {downloaded_count} images")
    print(f"   ❌ Failed downloads: {failed_count} images")
    print(f"   📁 Images saved to: {images_dir}/")

def download_single_image(url: str, product_id: int, title: str, images_dir: str, image_type: str) -> Optional[str]:
    """Download a single image and return local path"""
    try:
        # Create filename
        extension = get_file_extension(url)
        sanitized_title = sanitize_filename(title)
        filename = f"product_{product_id}_{image_type}_{sanitized_title}.{extension}"
        local_path = os.path.join(images_dir, filename)
        
        # Download image
        if download_image(url, local_path):
            print(f"   ✅ Downloaded: {filename}")
            return local_path
        else:
            return None
            
    except Exception as e:
        print(f"   ❌ Error processing {url}: {str(e)}")
        return None

def show_download_summary():
    """Show summary of downloaded images"""
    print("\n📊 Download Summary")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Count products with local images
            cursor.execute("SELECT COUNT(*) FROM products WHERE local_image_path IS NOT NULL")
            local_count = cursor.fetchone()[0]
            
            # Count total products
            cursor.execute("SELECT COUNT(*) FROM products")
            total_count = cursor.fetchone()[0]
            
            print(f"Products with local images: {local_count}/{total_count}")
            
            # Show some examples
            cursor.execute("""
                SELECT title, local_image_path 
                FROM products 
                WHERE local_image_path IS NOT NULL 
                LIMIT 5
            """)
            
            examples = cursor.fetchall()
            print("\nExample local paths:")
            for title, local_path in examples:
                print(f"   📁 {title[:30]}... → {local_path}")
            
    except Exception as e:
        print(f"❌ Error showing summary: {str(e)}")

def main():
    """Main function"""
    print("🖼️  Product Image Downloader")
    print("=" * 60)
    print("This will download all product images and save them locally")
    print("A 'local_image_path' column will be added to track file locations")
    print()
    
    # Confirm before starting
    response = input("Continue? (y/n): ").strip().lower()
    if response != 'y':
        print("❌ Download cancelled")
        return
    
    # Start download process
    download_all_images()
    
    # Show summary
    show_download_summary()
    
    print("\n💡 Next steps:")
    print("   • Images are saved in 'downloaded_images/' folder")
    print("   • Database now has 'local_image_path' column")
    print("   • You can upload these to Vercel or your preferred hosting")

if __name__ == "__main__":
    main()

