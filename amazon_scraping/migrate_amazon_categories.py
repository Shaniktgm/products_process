#!/usr/bin/env python3
"""
Migration script to add Amazon category support to the database
"""

import sqlite3
import json

def migrate_database():
    """Add Amazon category columns to the database"""
    
    db_path = "multi_platform_products.db"
    
    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        print("🔄 Migrating database to support Amazon categories...")
        
        # Check if columns already exist
        cursor.execute("PRAGMA table_info(product_categories)")
        columns = [row[1] for row in cursor.fetchall()]
        
        # Add new columns if they don't exist
        if 'amazon_category_path' not in columns:
            cursor.execute("ALTER TABLE product_categories ADD COLUMN amazon_category_path TEXT")
            print("✅ Added amazon_category_path column")
        
        if 'amazon_breadcrumbs' not in columns:
            cursor.execute("ALTER TABLE product_categories ADD COLUMN amazon_breadcrumbs TEXT")
            print("✅ Added amazon_breadcrumbs column")
        
        if 'source' not in columns:
            cursor.execute("ALTER TABLE product_categories ADD COLUMN source VARCHAR(20) DEFAULT 'custom'")
            print("✅ Added source column")
        
        # Update existing records to have 'custom' source
        cursor.execute("UPDATE product_categories SET source = 'custom' WHERE source IS NULL")
        
        conn.commit()
        print("✅ Migration completed successfully!")
        
        # Show current stats
        cursor.execute("""
            SELECT 
                source,
                COUNT(DISTINCT product_id) as product_count,
                COUNT(*) as total_categories
            FROM product_categories 
            GROUP BY source
        """)
        
        print("\n📊 Current category statistics:")
        for row in cursor.fetchall():
            source, product_count, total_categories = row
            print(f"   {source}: {product_count} products, {total_categories} categories")

if __name__ == "__main__":
    migrate_database()
