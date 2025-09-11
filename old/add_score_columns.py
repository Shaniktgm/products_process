#!/usr/bin/env python3
"""
Script to add score columns to the products table
"""

import sqlite3

def add_score_columns():
    """Add score columns to the products table"""
    print("🔄 Adding score columns to products table...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Add score columns
            score_columns = [
                "overall_score REAL DEFAULT NULL",
                "total_score REAL DEFAULT NULL", 
                "popularity_score REAL DEFAULT NULL",
                "brand_reputation_score REAL DEFAULT NULL",
                "overall_value_score REAL DEFAULT NULL",
                "luxury_score REAL DEFAULT NULL"
            ]
            
            for column in score_columns:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {column}")
                    print(f"   ✅ Added column: {column.split()[0]}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"   ⚠️  Column already exists: {column.split()[0]}")
                    else:
                        print(f"   ❌ Error adding column {column.split()[0]}: {e}")
            
            conn.commit()
            print("\n✅ Score columns added successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_score_columns()
