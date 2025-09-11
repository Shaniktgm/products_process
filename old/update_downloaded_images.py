#!/usr/bin/env python3
"""
Update Downloaded Images Script
Updates database with local image paths for downloaded Webflow images
"""

import sqlite3
import json
from pathlib import Path

def update_downloaded_images():
    """Update database with local image paths for downloaded images"""
    
    # Products that had images downloaded
    products_to_update = [
        {'id': 2, 'images': ['2.webp', '2_1.jpeg', '2_2.jpeg', '2_3.jpeg', '2_4.jpeg', '2_5.jpeg']},
        {'id': 4, 'images': ['4.png']},
        {'id': 5, 'images': ['5.jpeg', '5_1.jpeg', '5_2.jpeg', '5_3.jpeg', '5_4.jpeg', '5_5.jpeg']},
        {'id': 6, 'images': ['6.jpeg', '6_1.jpeg', '6_2.jpeg', '6_3.jpeg', '6_4.jpeg', '6_5.jpeg']},
        {'id': 9, 'images': ['9.jpeg', '9_1.jpeg', '9_2.jpeg', '9_3.jpeg', '9_4.jpeg', '9_5.jpeg']}
    ]
    
    with sqlite3.connect("multi_platform_products.db") as conn:
        cursor = conn.cursor()
        
        for product in products_to_update:
            product_id = product['id']
            image_files = product['images']
            
            # Check which images actually exist
            existing_images = []
            for img_file in image_files:
                img_path = Path(f"images/products/{img_file}")
                if img_path.exists():
                    existing_images.append(f"/images/products/{img_file}")
            
            if existing_images:
                primary_image = existing_images[0]
                image_urls_json = json.dumps(existing_images)
                
                # Update database
                cursor.execute("""
                    UPDATE products 
                    SET primary_image_url = ?,
                        image_urls = ?,
                        updated_at = datetime('now')
                    WHERE id = ?
                """, (primary_image, image_urls_json, product_id))
                
                print(f"✅ Updated product {product_id}: {len(existing_images)} images")
                print(f"   Primary: {primary_image}")
            else:
                print(f"❌ No images found for product {product_id}")
        
        conn.commit()
        print(f"\n🎉 Database update complete!")

if __name__ == "__main__":
    update_downloaded_images()
