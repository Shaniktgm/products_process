#!/usr/bin/env python3
"""
Verify that the actual affiliate links from CSV are being used
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

def verify_affiliate_links():
    """Verify affiliate links are from CSV data"""
    print("🔗 Verifying Affiliate Links from CSV Data")
    print("=" * 50)
    
    try:
        db = MultiPlatformDatabaseService("multi_platform_products.db")
        
        # Get all products
        products = db.get_products(limit=20)
        
        if not products:
            print("❌ No products found in database.")
            return
        
        print(f"Checking {len(products)} products for affiliate links:\n")
        
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['title']}")
            print(f"   Brand: {product['brand']}")
            print(f"   Price: ${product['price']}")
            
            if product.get('affiliate_links'):
                print(f"   Affiliate Links ({len(product['affiliate_links'])}):")
                for link in product['affiliate_links']:
                    print(f"     - {link['link_type']}: {link['affiliate_url']}")
                    print(f"       Commission: {link['commission_rate']*100}% (${link['estimated_commission']:.2f})")
            else:
                print("   ❌ No affiliate links found")
            
            print()
        
        # Show total affiliate links
        stats = db.get_database_stats()
        print(f"📊 Total Affiliate Links in Database: {stats['total_affiliate_links']}")
        
        # Show breakdown by link type
        print("\n🔗 Affiliate Link Breakdown:")
        link_types = {}
        for product in products:
            for link in product.get('affiliate_links', []):
                link_type = link['link_type']
                link_types[link_type] = link_types.get(link_type, 0) + 1
        
        for link_type, count in link_types.items():
            print(f"   - {link_type}: {count} links")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    verify_affiliate_links()
