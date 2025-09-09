#!/usr/bin/env python3
"""
Populate database with mock dental products
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from mock_data_generator import MockDataGenerator
from database_service import DatabaseService

def populate_database(product_count: int = 500):
    """Populate the database with mock products"""
    print("🚀 Populating Database with Mock Dental Products")
    print("=" * 60)
    
    try:
        # Initialize services
        print("1. Initializing services...")
        generator = MockDataGenerator()
        db_service = DatabaseService()
        
        # Generate mock products
        print(f"\n2. Generating {product_count} mock products...")
        products = generator.generate_products(product_count)
        
        if not products:
            print("❌ No products generated. Exiting.")
            return
        
        # Store products in database
        print(f"\n3. Storing {len(products)} products in database...")
        success_count = 0
        
        for i, product in enumerate(products, 1):
            try:
                if db_service.insert_or_update_product(product):
                    success_count += 1
                
                # Progress indicator
                if i % 50 == 0:
                    print(f"   Progress: {i}/{len(products)} products processed ({success_count} successful)")
                
            except Exception as e:
                print(f"   ❌ Error storing product {product.get('asin', 'Unknown')}: {str(e)}")
                continue
        
        print(f"\n✅ Successfully stored {success_count}/{len(products)} products")
        
        # Get database statistics
        print("\n4. Database statistics:")
        stats = db_service.get_database_stats()
        for key, value in stats.items():
            print(f"   {key}: {value}")
        
        # Export to JSON
        print("\n5. Exporting to JSON...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"mock_products_{timestamp}.json"
        db_service.export_to_json(filename)
        
        print(f"\n🎉 Database population completed successfully!")
        print(f"   Products generated: {len(products)}")
        print(f"   Products stored: {success_count}")
        print(f"   Export file: {filename}")
        
        # Show sample products
        print(f"\n📋 Sample products from database:")
        sample_products = db_service.get_products(limit=5)
        for i, product in enumerate(sample_products, 1):
            print(f"   {i}. {product.get('title', 'Unknown')}")
            print(f"      Brand: {product.get('brand', 'Unknown')}")
            print(f"      Price: ${product.get('price', 'Unknown')}")
            print(f"      Rating: {product.get('rating', 'Unknown')} ⭐")
            print()
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def search_and_display_products():
    """Search and display products from the database"""
    print("🔍 Searching Products in Database")
    print("=" * 40)
    
    try:
        db_service = DatabaseService()
        
        # Get all products
        products = db_service.get_products(limit=20)
        
        if not products:
            print("❌ No products found in database. Run populate_mock_database.py first.")
            return
        
        print(f"📋 Found {len(products)} products:")
        print()
        
        for i, product in enumerate(products, 1):
            print(f"{i}. {product.get('title', 'Unknown')}")
            print(f"   Brand: {product.get('brand', 'Unknown')}")
            print(f"   Price: ${product.get('price', 'Unknown')}")
            print(f"   Rating: {product.get('rating', 'Unknown')} ⭐ ({product.get('review_count', 0)} reviews)")
            print(f"   Category: {', '.join(product.get('categories', []))}")
            print(f"   Tags: {', '.join(product.get('tags', [])[:5])}...")
            print()
        
        # Test search functionality
        print("🔍 Testing search functionality...")
        search_results = db_service.search_products("toothpaste", limit=5)
        print(f"   Search for 'toothpaste': {len(search_results)} results")
        
        search_results = db_service.search_products("whitening", limit=5)
        print(f"   Search for 'whitening': {len(search_results)} results")
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "search":
            search_and_display_products()
        elif command == "stats":
            # Show database statistics
            try:
                db_service = DatabaseService()
                stats = db_service.get_database_stats()
                print("📊 Database Statistics:")
                print("=" * 30)
                for key, value in stats.items():
                    print(f"   {key}: {value}")
            except Exception as e:
                print(f"❌ Error: {str(e)}")
        elif command.isdigit():
            # Populate with specific number of products
            count = int(command)
            populate_database(count)
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage:")
            print("   python3 populate_mock_database.py [number]  # Populate with N products")
            print("   python3 populate_mock_database.py search    # Search and display products")
            print("   python3 populate_mock_database.py stats     # Show database statistics")
    else:
        # Default: populate with 500 products
        populate_database(500)

if __name__ == "__main__":
    main()
