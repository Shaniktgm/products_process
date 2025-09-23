#!/usr/bin/env python3
"""
Database Enhancement Script
Enhances existing tables and creates new tables for Amazon PA-API 5.0 integration
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional

class DatabaseEnhancer:
    """Enhance database schema for Amazon PA-API 5.0 integration"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def enhance_existing_tables(self):
        """Add missing columns to existing tables"""
        print("🔧 Enhancing existing tables...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Enhance products table
            print("  📋 Enhancing products table...")
            
            # Add Amazon-specific columns
            amazon_columns = [
                "amazon_asin TEXT",
                "amazon_title TEXT", 
                "amazon_brand TEXT",
                "amazon_manufacturer TEXT",
                "amazon_model TEXT",
                "amazon_color_code TEXT",
                "amazon_size_code TEXT",
                "amazon_material_type TEXT",
                "amazon_thread_count INTEGER",
                "amazon_weave_type TEXT",
                "amazon_certifications TEXT",  # JSON array
                "amazon_features TEXT",  # JSON array
                "amazon_dimensions TEXT",  # JSON object
                "amazon_weight REAL",
                "amazon_availability_status TEXT",
                "amazon_condition TEXT",
                "amazon_merchant_name TEXT",
                "amazon_sales_rank INTEGER",
                "amazon_browse_node_id TEXT",
                "amazon_browse_node_name TEXT",
                "amazon_last_updated TIMESTAMP"
            ]
            
            for column in amazon_columns:
                try:
                    cursor.execute(f"ALTER TABLE products ADD COLUMN {column}")
                    print(f"    ✅ Added column: {column.split()[0]}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"    ⚠️ Column already exists: {column.split()[0]}")
                    else:
                        print(f"    ❌ Error adding column {column.split()[0]}: {e}")
            
            # Enhance product_categories table
            print("  📂 Enhancing product_categories table...")
            
            category_columns = [
                "amazon_browse_node_id TEXT",
                "amazon_browse_node_name TEXT",
                "amazon_category_path TEXT",
                "amazon_breadcrumbs TEXT",
                "category_level INTEGER DEFAULT 1",
                "is_amazon_category BOOLEAN DEFAULT FALSE",
                "last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP"
            ]
            
            for column in category_columns:
                try:
                    cursor.execute(f"ALTER TABLE product_categories ADD COLUMN {column}")
                    print(f"    ✅ Added column: {column.split()[0]}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"    ⚠️ Column already exists: {column.split()[0]}")
                    else:
                        print(f"    ❌ Error adding column {column.split()[0]}: {e}")
            
            # Enhance product_images table
            print("  🖼️ Enhancing product_images table...")
            
            image_columns = [
                "amazon_image_url TEXT",
                "amazon_image_type TEXT",  # 'primary', 'variant', 'lifestyle'
                "amazon_image_size TEXT",  # 'small', 'medium', 'large'
                "amazon_image_variant TEXT",  # color/size variant
                "amazon_image_alt_text TEXT",
                "amazon_image_width INTEGER",
                "amazon_image_height INTEGER",
                "is_amazon_image BOOLEAN DEFAULT FALSE"
            ]
            
            for column in image_columns:
                try:
                    cursor.execute(f"ALTER TABLE product_images ADD COLUMN {column}")
                    print(f"    ✅ Added column: {column.split()[0]}")
                except sqlite3.OperationalError as e:
                    if "duplicate column name" in str(e):
                        print(f"    ⚠️ Column already exists: {column.split()[0]}")
                    else:
                        print(f"    ❌ Error adding column {column.split()[0]}: {e}")
            
            conn.commit()
            print("✅ Existing tables enhanced successfully!")
            
        except Exception as e:
            print(f"❌ Error enhancing tables: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_product_variations_table(self):
        """Create new table for product variations (colors, sizes, prices)"""
        print("🎨 Creating product_variations table...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_variations (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    variation_type TEXT NOT NULL,  -- 'color', 'size', 'color_size'
                    variation_value TEXT NOT NULL,  -- 'White', 'King', 'White_King'
                    variation_code TEXT,  -- Amazon's internal code
                    display_name TEXT,  -- Human-readable name
                    price REAL,
                    currency TEXT DEFAULT 'USD',
                    availability_status TEXT,  -- 'in_stock', 'out_of_stock', 'limited'
                    stock_quantity INTEGER,
                    condition TEXT,  -- 'new', 'used', 'refurbished'
                    merchant_name TEXT,
                    is_primary BOOLEAN DEFAULT FALSE,
                    display_order INTEGER DEFAULT 0,
                    amazon_asin TEXT,  -- ASIN for this specific variation
                    amazon_image_url TEXT,
                    amazon_image_alt_text TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_variations_product ON product_variations (product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_variations_type ON product_variations (variation_type)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_variations_value ON product_variations (variation_value)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_product_variations_asin ON product_variations (amazon_asin)")
            
            conn.commit()
            print("✅ product_variations table created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating product_variations table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_amazon_categories_table(self):
        """Create table for Amazon category hierarchy"""
        print("📂 Creating amazon_categories table...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS amazon_categories (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    browse_node_id TEXT UNIQUE NOT NULL,
                    browse_node_name TEXT NOT NULL,
                    parent_browse_node_id TEXT,
                    category_path TEXT,  -- Full path like "Home & Kitchen > Bedding > Sheets"
                    category_level INTEGER DEFAULT 1,
                    is_leaf_category BOOLEAN DEFAULT FALSE,
                    product_count INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (parent_browse_node_id) REFERENCES amazon_categories (browse_node_id)
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_categories_browse_node ON amazon_categories (browse_node_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_categories_parent ON amazon_categories (parent_browse_node_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_categories_level ON amazon_categories (category_level)")
            
            conn.commit()
            print("✅ amazon_categories table created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating amazon_categories table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_amazon_features_table(self):
        """Create table for Amazon product features"""
        print("🔧 Creating amazon_features table...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS amazon_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    feature_text TEXT NOT NULL,
                    feature_type TEXT,  -- 'bullet_point', 'description', 'specification'
                    display_order INTEGER DEFAULT 0,
                    is_highlighted BOOLEAN DEFAULT FALSE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_features_product ON amazon_features (product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_features_type ON amazon_features (feature_type)")
            
            conn.commit()
            print("✅ amazon_features table created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating amazon_features table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def create_amazon_reviews_table(self):
        """Create table for Amazon customer reviews data"""
        print("⭐ Creating amazon_reviews table...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS amazon_reviews (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    star_rating REAL,
                    review_count INTEGER,
                    review_url TEXT,
                    last_updated TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            """)
            
            # Create indexes
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_reviews_product ON amazon_reviews (product_id)")
            cursor.execute("CREATE INDEX IF NOT EXISTS idx_amazon_reviews_rating ON amazon_reviews (star_rating)")
            
            conn.commit()
            print("✅ amazon_reviews table created successfully!")
            
        except Exception as e:
            print(f"❌ Error creating amazon_reviews table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def delete_unused_tables(self):
        """Delete unused tables"""
        print("🗑️ Cleaning up unused tables...")
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Delete pros_cons_analysis table
            cursor.execute("DROP TABLE IF EXISTS pros_cons_analysis")
            print("  ✅ Deleted pros_cons_analysis table")
            
            # Delete enhanced_product_features table (replaced by smart_product_features)
            cursor.execute("DROP TABLE IF EXISTS enhanced_product_features")
            print("  ✅ Deleted enhanced_product_features table")
            
            conn.commit()
            print("✅ Unused tables cleaned up successfully!")
            
        except Exception as e:
            print(f"❌ Error cleaning up tables: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def run_full_enhancement(self):
        """Run complete database enhancement"""
        print("🚀 Starting Database Enhancement...")
        print("=" * 60)
        
        # Step 1: Delete unused tables
        self.delete_unused_tables()
        
        # Step 2: Enhance existing tables
        self.enhance_existing_tables()
        
        # Step 3: Create new tables
        self.create_product_variations_table()
        self.create_amazon_categories_table()
        self.create_amazon_features_table()
        self.create_amazon_reviews_table()
        
        print("\n" + "=" * 60)
        print("🎉 Database Enhancement Complete!")
        print("\n📊 New Database Structure:")
        print("✅ Enhanced products table with Amazon-specific columns")
        print("✅ Enhanced product_categories table with Amazon browse nodes")
        print("✅ Enhanced product_images table with Amazon image data")
        print("✅ Created product_variations table for colors/sizes/prices")
        print("✅ Created amazon_categories table for category hierarchy")
        print("✅ Created amazon_features table for product features")
        print("✅ Created amazon_reviews table for review data")
        print("✅ Cleaned up unused tables")
        
        # Show final table list
        conn = self._get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        tables = cursor.fetchall()
        conn.close()
        
        print(f"\n📋 Final Tables: {len(tables)} tables")
        for table in tables:
            print(f"  - {table[0]}")

def main():
    """Run database enhancement"""
    enhancer = DatabaseEnhancer()
    enhancer.run_full_enhancement()

if __name__ == "__main__":
    main()
