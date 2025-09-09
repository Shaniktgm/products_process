#!/usr/bin/env python3
"""
Simple test script for Amazon API
"""

import sys
import os

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def test_basic_functionality():
    """Test basic API functionality"""
    print("🧪 Testing Amazon API Basic Functionality")
    print("=" * 50)
    
    try:
                       # Test imports
               print("1. Testing imports...")
               from simple_amazon_api import SimpleAmazonAPI
               from database_service import DatabaseService
               print("   ✅ All modules imported successfully")

               # Test API initialization
               print("\n2. Testing API initialization...")
               api = SimpleAmazonAPI()
               print("   ✅ API service initialized")
        
        # Test database initialization
        print("\n3. Testing database initialization...")
        db = DatabaseService()
        print("   ✅ Database service initialized")
        
        # Test basic search
        print("\n4. Testing basic search...")
        products = api.search_dental_products("toothpaste", 2)
        
        if products:
            print(f"   ✅ Found {len(products)} products")
            for i, product in enumerate(products, 1):
                print(f"      {i}. {product.get('title', 'Unknown')[:50]}...")
                print(f"         ASIN: {product.get('asin', 'Unknown')}")
                print(f"         Price: ${product.get('price', 'Unknown')}")
        else:
            print("   ❌ No products found")
        
        # Test database storage
        if products:
            print("\n5. Testing database storage...")
            success_count = 0
            for product in products:
                if db.insert_or_update_product(product):
                    success_count += 1
            
            print(f"   ✅ Stored {success_count}/{len(products)} products")
        
        # Test database stats
        print("\n6. Testing database stats...")
        stats = db.get_database_stats()
        print("   📊 Database Statistics:")
        for key, value in stats.items():
            print(f"      {key}: {value}")
        
        print("\n🎉 Basic functionality test completed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

def test_specific_search():
    """Test specific search functionality"""
    print("\n🔍 Testing Specific Search")
    print("=" * 30)
    
    try:
        from amazon_api_service import AmazonAPIService
        
        api = AmazonAPIService()
        
        # Test different search terms
        search_terms = ["toothbrush", "mouthwash", "dental floss"]
        
        for term in search_terms:
            print(f"\n   Searching for: {term}")
            products = api.search_dental_products(term, 1)
            
            if products:
                product = products[0]
                print(f"      ✅ Found: {product.get('title', 'Unknown')[:60]}...")
                print(f"         Brand: {product.get('brand', 'Unknown')}")
                print(f"         Price: ${product.get('price', 'Unknown')}")
            else:
                print(f"      ❌ No products found for: {term}")
        
        print("\n✅ Specific search test completed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Specific search test failed: {str(e)}")
        return False

if __name__ == "__main__":
    print("🚀 Amazon API Test Suite")
    print("=" * 30)
    
    # Run basic functionality test
    basic_success = test_basic_functionality()
    
    # Run specific search test
    search_success = test_specific_search()
    
    # Summary
    print("\n📋 Test Summary")
    print("=" * 20)
    print(f"   Basic Functionality: {'✅ PASS' if basic_success else '❌ FAIL'}")
    print(f"   Specific Search: {'✅ PASS' if search_success else '❌ FAIL'}")
    
    if basic_success and search_success:
        print("\n🎉 All tests passed! The API is working correctly.")
        print("\n📖 Next steps:")
        print("   - Run 'python main.py' for full collection")
        print("   - Check the database and exports")
    else:
        print("\n❌ Some tests failed. Check the error messages above.")
        sys.exit(1)
