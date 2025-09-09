#!/usr/bin/env python3
"""
Check what scoring data currently exists in the database
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

def check_current_scores():
    """Check what scoring data exists in the database"""
    print("📊 Current Scoring Data in Database")
    print("=" * 50)
    
    try:
        db = MultiPlatformDatabaseService("multi_platform_products.db")
        
        # Get all products
        products = db.get_products(limit=20)
        
        if not products:
            print("❌ No products found in database.")
            return
        
        print(f"Found {len(products)} products. Checking for scoring data...\n")
        
        # Check what scoring fields exist
        scoring_fields = []
        for product in products:
            for key in product.keys():
                if 'score' in key.lower() or 'rating' in key.lower():
                    if key not in scoring_fields:
                        scoring_fields.append(key)
        
        print(f"Scoring-related fields found: {scoring_fields}\n")
        
        # Show scoring data for each product
        for i, product in enumerate(products, 1):
            print(f"{i}. {product['title'][:60]}...")
            print(f"   Brand: {product['brand']}")
            print(f"   Price: ${product['price']}")
            
            # Show existing scoring data
            if 'rating' in product and product['rating']:
                print(f"   Rating: {product['rating']} ⭐")
            if 'review_count' in product and product['review_count']:
                print(f"   Review Count: {product['review_count']}")
            
            # Check for any other scoring fields
            for field in scoring_fields:
                if field in product and product[field]:
                    print(f"   {field}: {product[field]}")
            
            print()
        
        # Check database schema for scoring columns
        print("🔍 Checking database schema for scoring columns...")
        import sqlite3
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            cursor.execute("PRAGMA table_info(products)")
            columns = cursor.fetchall()
            
            scoring_columns = []
            for column in columns:
                column_name = column[1]
                if 'score' in column_name.lower() or 'rating' in column_name.lower():
                    scoring_columns.append(column_name)
            
            if scoring_columns:
                print(f"Scoring columns in database: {scoring_columns}")
            else:
                print("No dedicated scoring columns found in database schema")
    
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    check_current_scores()
