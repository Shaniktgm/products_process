#!/usr/bin/env python3
"""
Debug script to test database insertion
"""

import sys
import os

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from database_service import DatabaseService
from mock_data_generator import MockDataGenerator

def test_single_insert():
    """Test inserting a single product"""
    print("🧪 Testing Single Product Insert")
    print("=" * 40)
    
    try:
        # Initialize services
        db_service = DatabaseService()
        generator = MockDataGenerator()
        
        # Generate one product
        product = generator.generate_product(1)
        
        print(f"Generated product:")
        print(f"  ASIN: {product['asin']}")
        print(f"  Title: {product['title']}")
        print(f"  Brand: {product['brand']}")
        print(f"  Price: ${product['price']}")
        print(f"  Features: {product['features']}")
        print(f"  Categories: {product['categories']}")
        print(f"  Tags: {product['tags']}")
        
        # Try to insert
        print(f"\nAttempting to insert...")
        success = db_service.insert_or_update_product(product)
        
        if success:
            print("✅ Product inserted successfully!")
            
            # Check database stats
            stats = db_service.get_database_stats()
            print(f"\nDatabase stats after insert:")
            for key, value in stats.items():
                print(f"  {key}: {value}")
        else:
            print("❌ Product insertion failed!")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")
        import traceback
        traceback.print_exc()

def test_database_schema():
    """Test database schema"""
    print("\n🔍 Testing Database Schema")
    print("=" * 30)
    
    try:
        db_service = DatabaseService()
        
        # Check if tables exist
        import sqlite3
        with sqlite3.connect(db_service.db_path) as conn:
            cursor = conn.cursor()
            
            # List all tables
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
            tables = cursor.fetchall()
            
            print(f"Tables in database:")
            for table in tables:
                print(f"  - {table[0]}")
                
                # Show table schema
                cursor.execute(f"PRAGMA table_info({table[0]})")
                columns = cursor.fetchall()
                print(f"    Columns:")
                for col in columns:
                    print(f"      {col[1]} ({col[2]})")
                print()
                
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_database_schema()
    test_single_insert()
