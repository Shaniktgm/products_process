#!/usr/bin/env python3
"""
Show only the new products added from products_three_rows
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

def show_new_products():
    """Show only the new products from three rows"""
    print("🆕 New Products Added from Products Three Rows")
    print("=" * 50)
    
    try:
        db = MultiPlatformDatabaseService("multi_platform_products.db")
        
        # Get all products
        products = db.get_products(limit=20)
        
        if not products:
            print("❌ No products found in database.")
            return
        
        # Filter for products with THREE- SKU
        new_products = [p for p in products if p['sku'].startswith('THREE-')]
        
        print(f"Found {len(new_products)} new products:\n")
        
        for i, product in enumerate(new_products, 1):
            print(f"{i}. {product['title']}")
            print(f"   Brand: {product['brand']}")
            print(f"   SKU: {product['sku']}")
            print(f"   Price: ${product['price']}")
            if product.get('original_price'):
                print(f"   Original: ${product['original_price']} (Save {product.get('discount_percentage', 0)}%)")
            print(f"   Rating: {product['rating']} ⭐ ({product['review_count']} reviews)")
            print(f"   Material: {product['material']}")
            print(f"   Size: {product['size']}")
            print(f"   Color: {product['color']}")
            print(f"   Weight: {product['weight']} lbs")
            print(f"   Categories: {', '.join([cat['category_name'] for cat in product['categories']])}")
            print(f"   Tags: {', '.join(product['tags'][:5])}...")
            print(f"   Features: {len(product['features'])} features")
            print(f"   Specifications: {len(product['specifications'])} specs")
            print(f"   Featured: {'✅' if product['is_featured'] else '❌'}")
            print(f"   Bestseller: {'✅' if product['is_bestseller'] else '❌'}")
            
            # Show affiliate links
            if product.get('affiliate_links'):
                print(f"   Affiliate Links:")
                for link in product['affiliate_links']:
                    print(f"     - {link['link_type']}: {link['affiliate_url'][:80]}...")
                    print(f"       Commission: {link['commission_rate']*100}% (${link['estimated_commission']:.2f})")
            
            print()
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    show_new_products()
