#!/usr/bin/env python3
"""
Update existing database with enhanced product data
"""

import sys
import os
from datetime import datetime

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from enhanced_mock_generator import EnhancedMockDataGenerator
from database_service import DatabaseService

def update_database_with_enhanced_data():
    """Update the existing database with enhanced product data"""
    print("🚀 Updating Database with Enhanced Product Data")
    print("=" * 60)
    
    try:
        # Initialize services
        print("1. Initializing services...")
        generator = EnhancedMockDataGenerator()
        db_service = DatabaseService()
        
        # Get current database stats
        print("\n2. Current database statistics:")
        current_stats = db_service.get_database_stats()
        for key, value in current_stats.items():
            print(f"   {key}: {value}")
        
        # Generate enhanced products (same count as current)
        current_product_count = current_stats.get('total_products', 0)
        print(f"\n3. Generating {current_product_count} enhanced products...")
        enhanced_products = generator.generate_enhanced_products(current_product_count)
        
        if not enhanced_products:
            print("❌ No enhanced products generated. Exiting.")
            return
        
        # Update products in database
        print(f"\n4. Updating {len(enhanced_products)} products with enhanced data...")
        success_count = 0
        
        for i, product in enumerate(enhanced_products, 1):
            try:
                if db_service.insert_or_update_product(product):
                    success_count += 1
                
                # Progress indicator
                if i % 50 == 0:
                    print(f"   Progress: {i}/{len(enhanced_products)} products updated ({success_count} successful)")
                
            except Exception as e:
                print(f"   ❌ Error updating product {product.get('asin', 'Unknown')}: {str(e)}")
                continue
        
        print(f"\n✅ Successfully updated {success_count}/{len(enhanced_products)} products")
        
        # Get updated database statistics
        print("\n5. Updated database statistics:")
        updated_stats = db_service.get_database_stats()
        for key, value in updated_stats.items():
            print(f"   {key}: {value}")
        
        # Export to JSON
        print("\n6. Exporting enhanced data to JSON...")
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        filename = f"enhanced_products_{timestamp}.json"
        db_service.export_to_json(filename)
        
        print(f"\n🎉 Database update completed successfully!")
        print(f"   Products updated: {len(enhanced_products)}")
        print(f"   Products successfully updated: {success_count}")
        print(f"   Export file: {filename}")
        
        # Show sample enhanced products
        print(f"\n📋 Sample enhanced products from database:")
        sample_products = db_service.get_products(limit=5)
        for i, product in enumerate(sample_products, 1):
            print(f"   {i}. {product.get('title', 'Unknown')}")
            print(f"      Brand: {product.get('brand', 'Unknown')}")
            print(f"      Price: ${product.get('price', 'Unknown')}")
            if product.get('original_price'):
                print(f"      Original: ${product.get('original_price')} (Save {product.get('discount_percentage', 0)}%)")
            print(f"      Rating: {product.get('rating', 'Unknown')} ⭐")
            print(f"      Commission: ${product.get('estimated_commission', 'Unknown')}")
            print(f"      Prime: {'✅' if product.get('is_prime') else '❌'}")
            if product.get('deal_badges'):
                print(f"      Badges: {', '.join(product.get('deal_badges', []))}")
            print()
        
    except Exception as e:
        print(f"❌ Fatal error: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

def show_enhanced_product_details():
    """Show detailed information about enhanced products"""
    print("🔍 Enhanced Product Details")
    print("=" * 40)
    
    try:
        db_service = DatabaseService()
        
        # Get enhanced products
        products = db_service.get_products(limit=10)
        
        if not products:
            print("❌ No products found in database.")
            return
        
        print(f"📋 Found {len(products)} enhanced products:")
        print()
        
        for i, product in enumerate(products, 1):
            print(f"{i}. {product.get('title', 'Unknown')}")
            print(f"   Brand: {product.get('brand', 'Unknown')}")
            print(f"   Price: ${product.get('price', 'Unknown')}")
            if product.get('original_price'):
                print(f"   Original: ${product.get('original_price')} (Save {product.get('discount_percentage', 0)}%)")
            print(f"   Rating: {product.get('rating', 'Unknown')} ⭐ ({product.get('review_count', 0)} reviews)")
            print(f"   Commission: ${product.get('estimated_commission', 'Unknown')} ({product.get('commission_rate', 0)*100}%)")
            print(f"   Category: {', '.join(product.get('categories', []))}")
            print(f"   Prime: {'✅' if product.get('is_prime') else '❌'}")
            print(f"   Free Shipping: {'✅' if product.get('free_shipping') else '❌'}")
            if product.get('best_seller_rank'):
                print(f"   Best Seller Rank: #{product.get('best_seller_rank')}")
            if product.get('deal_badges'):
                print(f"   Badges: {', '.join(product.get('deal_badges', []))}")
            print(f"   Stock: {product.get('stock_status', 'Unknown')}")
            print(f"   Shipping Weight: {product.get('shipping_weight', 'Unknown')} lbs")
            print(f"   Package: {product.get('package_dimensions', 'Unknown')}")
            print(f"   Warranty: {product.get('warranty', 'Unknown')}")
            print(f"   Return: {product.get('return_policy', 'Unknown')}")
            print(f"   Age: {product.get('age_recommendation', 'Unknown')}")
            print(f"   Features: {', '.join(product.get('features', [])[:3])}...")
            print(f"   Tags: {', '.join(product.get('tags', [])[:5])}...")
            print()
        
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def main():
    """Main function"""
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "details":
            show_enhanced_product_details()
        elif command == "stats":
            # Show database statistics
            try:
                db_service = DatabaseService()
                stats = db_service.get_database_stats()
                print("📊 Enhanced Database Statistics:")
                print("=" * 40)
                for key, value in stats.items():
                    print(f"   {key}: {value}")
            except Exception as e:
                print(f"❌ Error: {e}")
        else:
            print(f"❌ Unknown command: {command}")
            print("Usage:")
            print("   python3 update_database_enhanced.py          # Update database with enhanced data")
            print("   python3 update_database_enhanced.py details # Show detailed product information")
            print("   python3 update_database_enhanced.py stats   # Show database statistics")
    else:
        # Default: update database with enhanced data
        update_database_with_enhanced_data()

if __name__ == "__main__":
    main()
