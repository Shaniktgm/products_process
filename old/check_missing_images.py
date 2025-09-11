#!/usr/bin/env python3
"""
Check Missing Images Script
Shows which products need images uploaded to Vercel
"""

import sqlite3
import json
from typing import List, Dict

def check_missing_images():
    """Check which products need images uploaded to Vercel"""
    
    with sqlite3.connect("multi_platform_products.db") as conn:
        cursor = conn.cursor()
        
        # Get products with old Vercel URLs
        cursor.execute("""
            SELECT id, sku, title, primary_image_url, image_urls
            FROM products 
            WHERE primary_image_url LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
               OR image_urls LIKE '%oqc9lt7zlwlkp8e3.public.blob.vercel-storage.com%'
            ORDER BY id
        """)
        
        products = cursor.fetchall()
        
        print("🔍 Products with old Vercel URLs that need new images:")
        print("=" * 80)
        
        for product in products:
            product_id, sku, title, primary_url, image_urls_str = product
            
            print(f"\n📦 Product ID {product_id}: {sku}")
            print(f"   Title: {title[:60]}...")
            print(f"   Primary URL: {primary_url}")
            
            # Extract filenames from old Vercel URLs
            filenames = extract_filenames_from_vercel_urls(primary_url, image_urls_str)
            
            print(f"   📁 Images to upload to Vercel:")
            for i, filename in enumerate(filenames):
                print(f"      {i+1}. {filename}")
            
            print(f"   💡 Vercel URLs will be:")
            for i, filename in enumerate(filenames):
                print(f"      {i+1}. https://your-vercel-domain.com/images/products/{filename}")

def extract_filenames_from_vercel_urls(primary_url: str, image_urls_str: str) -> List[str]:
    """Extract filenames from old Vercel URLs"""
    
    filenames = []
    
    # Extract from primary URL
    if primary_url and 'vercel' in primary_url:
        filename = extract_filename_from_vercel_url(primary_url)
        if filename:
            filenames.append(filename)
    
    # Extract from image_urls
    if image_urls_str:
        try:
            # Try to parse as JSON
            image_urls = json.loads(image_urls_str)
        except:
            # If not JSON, extract URLs from string
            image_urls = extract_urls_from_string(image_urls_str)
        
        for url in image_urls:
            if 'vercel' in url:
                filename = extract_filename_from_vercel_url(url)
                if filename and filename not in filenames:
                    filenames.append(filename)
    
    return filenames

def extract_filename_from_vercel_url(url: str) -> str:
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
        return ""
    except:
        return ""

def extract_urls_from_string(url_string: str) -> List[str]:
    """Extract URLs from malformed JSON string"""
    urls = []
    if url_string:
        url_parts = url_string.split(',')
        for part in url_parts:
            url = part.strip().strip('"').strip(']').strip()
            if url.startswith('http'):
                urls.append(url)
    return urls

if __name__ == "__main__":
    check_missing_images()
