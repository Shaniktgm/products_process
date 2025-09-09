#!/usr/bin/env python3
"""
Download a specific product image from Amazon URL and update database
"""

import sqlite3
import requests
import os
from urllib.parse import urlparse
import time

def download_image_from_amazon(amazon_url, product_id, product_name):
    """Download image from Amazon URL and save locally"""
    
    # Create images directory if it doesn't exist
    images_dir = "downloaded_images"
    if not os.path.exists(images_dir):
        os.makedirs(images_dir)
        print(f"✅ Created directory: {images_dir}")
    
    try:
        # Get the Amazon page
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        print(f"📥 Fetching Amazon page: {amazon_url}")
        response = requests.get(amazon_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Look for the main product image in the HTML
        html_content = response.text
        
        # Find the main product image URL
        import re
        
        # Look for the main product image pattern
        image_patterns = [
            r'"hiRes":"([^"]*)"',  # High resolution image
            r'"large":"([^"]*)"',  # Large image
            r'"main":"([^"]*)"',   # Main image
            r'data-old-hires="([^"]*)"',  # Old hires attribute
            r'data-a-dynamic-image=\'[^\']*"([^"]*)"[^\']*\'',  # Dynamic image
        ]
        
        image_url = None
        for pattern in image_patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                image_url = matches[0]
                break
        
        if not image_url:
            print("❌ Could not find product image in Amazon page")
            return None
        
        # Clean up the image URL
        if image_url.startswith('//'):
            image_url = 'https:' + image_url
        elif image_url.startswith('/'):
            image_url = 'https://m.media-amazon.com' + image_url
        
        print(f"🖼️  Found image URL: {image_url}")
        
        # Download the image
        print(f"📥 Downloading image...")
        img_response = requests.get(image_url, headers=headers, timeout=30)
        img_response.raise_for_status()
        
        # Save the image
        filename = f"product_{product_id}.jpg"
        filepath = os.path.join(images_dir, filename)
        
        with open(filepath, 'wb') as f:
            f.write(img_response.content)
        
        print(f"✅ Downloaded image: {filepath}")
        return filepath
        
    except Exception as e:
        print(f"❌ Error downloading image: {e}")
        return None

def update_database_image_path(product_id, image_path):
    """Update database with new image path"""
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Update the primary_image_url
            cursor.execute("""
                UPDATE products 
                SET primary_image_url = ? 
                WHERE id = ?
            """, (image_path, product_id))
            
            conn.commit()
            print(f"✅ Updated database: Product {product_id} -> {image_path}")
            
    except Exception as e:
        print(f"❌ Error updating database: {e}")

def main():
    # Amazon URL for Signature Hemmed Sheet Set
    amazon_url = "https://www.amazon.com/BOLL-BRANCH-Signature-Hemmed-Sheet/dp/B0BHZSJ4QK?th=1&linkCode=ll1&tag=aehp-20&linkId=439c467d7cf692a24e5667e5bb9bed6e&language=en_US&ref_=as_li_ss_tl"
    
    # Product ID for Signature Hemmed Sheet Set - Queen, White
    product_id = 10
    product_name = "Signature Hemmed Sheet Set - Queen, White"
    
    print(f"🎯 Downloading image for: {product_name}")
    print(f"📦 Product ID: {product_id}")
    
    # Download the image
    image_path = download_image_from_amazon(amazon_url, product_id, product_name)
    
    if image_path:
        # Update database
        update_database_image_path(product_id, image_path)
        print(f"🎉 Successfully updated product {product_id} with new image!")
    else:
        print("❌ Failed to download image")

if __name__ == "__main__":
    main()
