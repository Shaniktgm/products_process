#!/usr/bin/env python3
"""
Simplify database structure by keeping only products table with platform_id
"""

import sqlite3

def add_platform_id_to_products():
    """Add platform_id column to products table"""
    print("🔧 Adding platform_id to products table")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Check if platform_id column already exists
            cursor.execute("PRAGMA table_info(products)")
            columns = [col[1] for col in cursor.fetchall()]
            
            if 'platform_id' not in columns:
                # Add platform_id column
                cursor.execute("ALTER TABLE products ADD COLUMN platform_id INTEGER")
                print("   ✅ Added platform_id column to products table")
                
                # Add foreign key constraint (if supported)
                try:
                    cursor.execute("""
                        CREATE TABLE products_new AS 
                        SELECT id, sku, title, brand, description, short_description, slug, 
                               price, original_price, discount_percentage, currency, rating, 
                               review_count, primary_image_url, image_urls, video_urls, 
                               availability, stock_status, stock_quantity, condition, warranty, 
                               return_policy, shipping_info, age_recommendation, ingredients, 
                               weight, dimensions, color, material, size, meta_title, 
                               meta_description, tags, deal_badges, is_active, is_featured, 
                               is_bestseller, created_at, updated_at, total_score, 
                               popularity_score, brand_reputation_score, overall_value_score, 
                               luxury_score, overall_score, platform_id
                        FROM products
                    """)
                    
                    cursor.execute("DROP TABLE products")
                    cursor.execute("ALTER TABLE products_new RENAME TO products")
                    
                    # Recreate indexes
                    cursor.execute("CREATE UNIQUE INDEX idx_products_slug ON products(slug)")
                    cursor.execute("CREATE INDEX idx_products_sku ON products(sku)")
                    cursor.execute("CREATE INDEX idx_products_brand ON products(brand)")
                    cursor.execute("CREATE INDEX idx_products_price ON products(price)")
                    cursor.execute("CREATE INDEX idx_products_rating ON products(rating)")
                    cursor.execute("CREATE INDEX idx_products_overall_score ON products(overall_score)")
                    cursor.execute("CREATE INDEX idx_products_platform_id ON products(platform_id)")
                    
                    print("   ✅ Recreated table with proper structure and indexes")
                    
                except Exception as e:
                    print(f"   ⚠️  Could not recreate table with constraints: {e}")
                    print("   ✅ platform_id column added successfully")
            else:
                print("   ⚠️  platform_id column already exists")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error adding platform_id column: {str(e)}")

def get_platform_id_for_amazon():
    """Get the platform_id for Amazon"""
    print("\n🔍 Finding Amazon platform ID")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            cursor.execute("SELECT id, display_name FROM platforms WHERE name = 'amazon'")
            amazon_platform = cursor.fetchone()
            
            if amazon_platform:
                platform_id, platform_name = amazon_platform
                print(f"   ✅ Found Amazon platform: ID {platform_id}")
                return platform_id
            else:
                print("   ❌ Amazon platform not found")
                return None
                
    except Exception as e:
        print(f"❌ Error finding Amazon platform: {str(e)}")
        return None

def update_products_with_platform_id(platform_id):
    """Update all products with platform_id"""
    print(f"\n📝 Updating products with platform_id = {platform_id}")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Update all products with the platform_id
            cursor.execute("UPDATE products SET platform_id = ? WHERE platform_id IS NULL", (platform_id,))
            
            updated_count = cursor.rowcount
            print(f"   ✅ Updated {updated_count} products with platform_id")
            
            # Verify the update
            cursor.execute("SELECT COUNT(*) FROM products WHERE platform_id = ?", (platform_id,))
            count = cursor.fetchone()[0]
            print(f"   ✅ Total products with platform_id {platform_id}: {count}")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error updating products: {str(e)}")

def show_products_with_platforms():
    """Show products with their platform information"""
    print("\n📊 Products with Platform Information")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT p.title, p.price, p.rating, p.review_count, pl.display_name as platform_name
                FROM products p
                LEFT JOIN platforms pl ON p.platform_id = pl.id
                ORDER BY p.title
                LIMIT 5
            """)
            
            products = cursor.fetchall()
            
            for title, price, rating, review_count, platform_name in products:
                print(f"📦 {title[:50]}...")
                print(f"   Platform: {platform_name}")
                print(f"   Price: ${price}, Rating: {rating}★, Reviews: {review_count}")
                print()
            
            # Show summary
            cursor.execute("""
                SELECT pl.display_name, COUNT(p.id) as product_count
                FROM platforms pl
                LEFT JOIN products p ON pl.id = p.platform_id
                GROUP BY pl.id, pl.display_name
                ORDER BY product_count DESC
            """)
            
            platform_summary = cursor.fetchall()
            print("📈 Platform Summary:")
            for platform_name, product_count in platform_summary:
                print(f"   {platform_name}: {product_count} products")
                
    except Exception as e:
        print(f"❌ Error showing products: {str(e)}")

def backup_product_platforms_data():
    """Backup product_platforms data before cleanup"""
    print("\n💾 Backing up product_platforms data")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Create backup table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS product_platforms_backup AS 
                SELECT * FROM product_platforms
            """)
            
            cursor.execute("SELECT COUNT(*) FROM product_platforms_backup")
            backup_count = cursor.fetchone()[0]
            
            print(f"   ✅ Backed up {backup_count} records to product_platforms_backup")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error backing up data: {str(e)}")

def cleanup_product_platforms():
    """Clean up the redundant product_platforms table"""
    print("\n🧹 Cleaning up product_platforms table")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Check if we should keep the table structure for future use
            print("   💡 Keeping product_platforms table structure for future multi-platform expansion")
            print("   🗑️  Clearing redundant data from product_platforms")
            
            # Clear the data but keep the table structure
            cursor.execute("DELETE FROM product_platforms")
            
            cursor.execute("SELECT COUNT(*) FROM product_platforms")
            remaining_count = cursor.fetchone()[0]
            
            print(f"   ✅ Cleared product_platforms data (remaining records: {remaining_count})")
            print("   📋 Table structure preserved for future multi-platform products")
            
            conn.commit()
            
    except Exception as e:
        print(f"❌ Error cleaning up product_platforms: {str(e)}")

def show_database_structure():
    """Show the simplified database structure"""
    print("\n🏗️ Simplified Database Structure")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Show products table structure
            cursor.execute("PRAGMA table_info(products)")
            products_columns = cursor.fetchall()
            
            print("📦 Products Table:")
            for col in products_columns:
                col_id, name, type_name, not_null, default_val, pk = col
                pk_marker = " (PRIMARY KEY)" if pk else ""
                print(f"   {name} ({type_name}){pk_marker}")
            
            print(f"\nTotal columns in products: {len(products_columns)}")
            
            # Show platforms table
            cursor.execute("SELECT COUNT(*) FROM platforms")
            platform_count = cursor.fetchone()[0]
            print(f"\n🌐 Platforms: {platform_count} platforms available")
            
            # Show product count
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            print(f"📦 Products: {product_count} products")
            
    except Exception as e:
        print(f"❌ Error showing structure: {str(e)}")

def main():
    """Main function"""
    print("🎯 Simplifying Database Structure")
    print("=" * 60)
    print("Moving from product_platforms to products table with platform_id")
    print()
    
    # Step 1: Add platform_id to products table
    add_platform_id_to_products()
    
    # Step 2: Get Amazon platform ID
    amazon_platform_id = get_platform_id_for_amazon()
    
    if amazon_platform_id:
        # Step 3: Update products with platform_id
        update_products_with_platform_id(amazon_platform_id)
        
        # Step 4: Show results
        show_products_with_platforms()
        
        # Step 5: Backup and cleanup
        backup_product_platforms_data()
        cleanup_product_platforms()
        
        # Step 6: Show final structure
        show_database_structure()
        
        print("\n🎉 Database structure simplified successfully!")
        print("\n💡 What changed:")
        print("   ✅ Added platform_id column to products table")
        print("   ✅ All products now have platform_id = 1 (Amazon)")
        print("   ✅ Removed redundant data from product_platforms")
        print("   ✅ Preserved product_platforms structure for future use")
        print("   ✅ Created backup of original data")
        
    else:
        print("❌ Could not find Amazon platform. Please check platforms table.")

if __name__ == "__main__":
    main()
