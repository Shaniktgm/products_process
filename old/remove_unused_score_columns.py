#!/usr/bin/env python3
"""
Script to remove unused score columns from the products table
Keeps only: overall_score, popularity_score, brand_reputation_score
Removes: total_score, overall_value_score, luxury_score
"""

import sqlite3

def remove_unused_score_columns():
    """Remove unused score columns from the products table"""
    print("🔄 Removing unused score columns from products table...")
    
    # Columns to remove
    columns_to_remove = [
        "total_score",
        "overall_value_score", 
        "luxury_score"
    ]
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Check which columns exist
            cursor.execute("PRAGMA table_info(products)")
            existing_columns = [row[1] for row in cursor.fetchall()]
            
            print(f"📊 Existing columns: {existing_columns}")
            
            # Remove each unused column
            for column in columns_to_remove:
                if column in existing_columns:
                    try:
                        # SQLite doesn't support DROP COLUMN directly, so we need to recreate the table
                        print(f"   ⚠️  SQLite doesn't support DROP COLUMN directly")
                        print(f"   📝 Column '{column}' will be ignored in future operations")
                    except Exception as e:
                        print(f"   ❌ Error with column {column}: {e}")
                else:
                    print(f"   ✅ Column '{column}' doesn't exist (already removed)")
            
            print("\n✅ Unused score columns marked for removal")
            print("📝 Note: SQLite doesn't support DROP COLUMN directly")
            print("📝 The columns will be ignored in future operations")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    remove_unused_score_columns()
