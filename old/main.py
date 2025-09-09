#!/usr/bin/env python3
"""
Main script for Amazon Product Advertising API data collection
"""

import os
import sys
import time
from datetime import datetime
from dotenv import load_dotenv

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from simple_amazon_api import SimpleAmazonAPI
from database_service import DatabaseService

def main():
    """Main function to collect and store Amazon products"""
    print("🚀 Amazon Product Data Collection")
    print("=" * 50)

    # Load environment variables
    load_dotenv()

    try:
        # Initialize services
        print("\n1. Initializing services...")
        api_service = SimpleAmazonAPI()
        db_service = DatabaseService()

        # Test API connection
        print("\n2. Testing API connection...")
        api_service.test_api()

        # Collect products from all dental categories
        print("\n3. Collecting products from dental categories...")
        products = api_service.search_dental_categories()

        if not products:
            print("❌ No products found. Exiting.")
            return

        # Store products in database
        print(f"\n4. Storing {len(products)} products in database...")
        success_count = 0

        for i, product in enumerate(products, 1):
            try:
                if db_service.insert_or_update_product(product):
                    success_count += 1

                # Progress indicator
                if i % 10 == 0:
                    print(f"   Progress: {i}/{len(products)} products processed")

                # Rate limiting
                time.sleep(0.1)

            except Exception as e:
                print(f"❌ Error storing product {product.get('asin', 'Unknown')}: {str(e)}")
                continue

        print(f"\n✅ Successfully stored {success_count}/{len(products)} products")

        # Get database statistics
        print("\n5. Database statistics:")
        stats = db_service.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")

        # Export to JSON
        print("\n6. Exporting to JSON...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"amazon_products_{timestamp}.json"
        db_service.export_to_json(filename)

        print(f"\n🎉 Data collection completed successfully!")
        print(f"   Products collected: {len(products)}")
        print(f"   Products stored: {success_count}")
        print(f"   Export file: {filename}")

    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def search_and_store_specific(keywords: str, item_count: int = 20):
    """Search for specific keywords and store results"""
    print(f"🔍 Searching for: {keywords}")
    print("=" * 50)

    try:
        # Initialize services
        api_service = SimpleAmazonAPI()
        db_service = DatabaseService()

        # Search for products
        products = api_service.search_products(keywords, item_count)

        if not products:
            print("❌ No products found.")
            return

        # Store products
        print(f"\n📦 Storing {len(products)} products...")
        success_count = 0

        for product in products:
            if db_service.insert_or_update_product(product):
                success_count += 1

        print(f"✅ Stored {success_count}/{len(products)} products")

        # Show some results
        print(f"\n📋 Sample products:")
        for i, product in enumerate(products[:3], 1):
            print(f"   {i}. {product.get('title', 'Unknown')}")
            print(f"      ASIN: {product.get('asin', 'Unknown')}")
            print(f"      Price: ${product.get('price', 'Unknown')}")
            print(f"      Brand: {product.get('brand', 'Unknown')}")
            print()

    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Search for specific keywords
        keywords = " ".join(sys.argv[1:])
        search_and_store_specific(keywords)
    else:
        # Full collection
        main()
