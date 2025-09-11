#!/usr/bin/env python3
"""
Script to add new score columns to the products table
Adds: price_value_score, commission_score
"""

import sqlite3

def add_new_score_columns():
    """Add new score columns to the products table"""
    print("🔄 Adding new score columns to products table...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Add new score columns
            new_columns = [
                "price_value_score REAL DEFAULT NULL",
                "commission_score REAL DEFAULT NULL"
            ]
            
            for column in new_columns:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {column}")
                    print(f"   ✅ Added column: {column.split()[0]}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"   ⚠️  Column already exists: {column.split()[0]}")
                    else:
                        print(f"   ❌ Error adding column {column.split()[0]}: {e}")
            
            conn.commit()
            print("\n✅ New score columns added successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_new_score_columns()
