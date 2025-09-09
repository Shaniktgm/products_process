#!/usr/bin/env python3
"""
Show populated products from the multi-platform database
"""

import sys
import os
import json

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

def show_products():
    """Show all populated products"""
    print("📋 Populated Products in Multi-Platform Database")
    print("=" * 60)
    
    try:
        db = MultiPlatformDatabaseService("multi_platform_products.db")
        
        # Get all products
        products = db.get_products(limit=20)
        
        if not products:
            print("❌ No products found in database.")
            return
        
        print(f"Found {len(products)} products:\n")
        
        for i, product in enumerate(products, 1):
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
            print(f"   Platforms: {len(product['platforms'])} platforms")
            print(f"   Affiliate Links: {len(product['affiliate_links'])} links")
            print(f"   Featured: {'✅' if product['is_featured'] else '❌'}")
            print(f"   Bestseller: {'✅' if product['is_bestseller'] else '❌'}")
            
            # Show sample features
            if product['features']:
                print(f"   Sample Features:")
                for feature in product['features'][:3]:
                    if isinstance(feature, dict):
                        print(f"     - {feature.get('text', feature.get('feature_text', ''))} ({feature.get('type', 'general')})")
                    else:
                        print(f"     - {feature}")
            
            # Show sample specifications
            if product['specifications']:
                print(f"   Sample Specifications:")
                for spec in product['specifications'][:3]:
                    print(f"     - {spec['spec_name']}: {spec['spec_value']}")
            
            print()
        
        # Show database statistics
        stats = db.get_database_stats()
        print("📊 Database Statistics:")
        print(f"   Total Products: {stats['total_products']}")
        print(f"   Total Platforms: {stats['total_platforms']}")
        print(f"   Total Platform Products: {stats['total_platform_products']}")
        print(f"   Total Affiliate Links: {stats['total_affiliate_links']}")
        print(f"   Average Price: ${stats['average_price']}")
        print(f"   Average Rating: {stats['average_rating']}")
        
        print("\n🏷️ Platform Breakdown:")
        for platform in stats['platform_breakdown']:
            print(f"   - {platform['display_name']}: {platform['product_count']} products")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    show_products()
