#!/usr/bin/env python3
"""
Script to add pretty_title and short_description columns to the products table
"""

import sqlite3

def add_display_columns():
    """Add pretty_title and short_description columns to the products table"""
    print("🔄 Adding display columns to products table...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Add new display columns
            new_columns = [
                "pretty_title TEXT DEFAULT NULL",
                "short_description TEXT DEFAULT NULL"
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
            print("\n✅ Display columns added successfully!")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    add_display_columns()
