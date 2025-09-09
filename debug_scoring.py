#!/usr/bin/env python3
"""
Debug script to test scoring calculation
"""

import sqlite3
from configurable_scoring_system import ConfigurableScoringSystem

def debug_scoring():
    scoring_system = ConfigurableScoringSystem()
    
    # Get one product from database
    with sqlite3.connect("multi_platform_products.db") as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM products WHERE sku = 'AMZ-B08M9SMVSG'")
        product_row = cursor.fetchone()
        
        # Get column names
        cursor.execute("PRAGMA table_info(products)")
        columns = [col[1] for col in cursor.fetchall()]
        
        # Convert to dictionary
        product_data = dict(zip(columns, product_row))
        
        print("Product data:")
        print(f"  SKU: {product_data.get('sku')}")
        print(f"  Title: {product_data.get('title', '')[:50]}...")
        print(f"  Price: {product_data.get('price')}")
        print(f"  Rating: {product_data.get('rating')}")
        print(f"  Review Count: {product_data.get('review_count')}")
        print(f"  Current overall_score: {product_data.get('overall_score')}")
        print(f"  Current overall_value_score: {product_data.get('overall_value_score')}")
        
        # Calculate new score
        new_score = scoring_system.calculate_overall_score(product_data)
        print(f"\nCalculated new score: {new_score}")
        
        # Test fallback calculation
        fallback_score = scoring_system._calculate_fallback_score("overall_value_score", "price_rating_ratio", product_data)
        print(f"Fallback calculation: {fallback_score}")

if __name__ == "__main__":
    debug_scoring()
