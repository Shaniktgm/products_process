#!/usr/bin/env python3
"""
Easy script to add new categories to the hierarchical system
"""

import sqlite3
import sys
from typing import Optional

def add_category(name: str, slug: str, description: str = "", parent_slug: str = None, sort_order: int = 0):
    """Add a new category to the system"""
    print(f"➕ Adding category: {name}")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Get parent_id if parent_slug is provided
            parent_id = None
            level = 0
            
            if parent_slug:
                cursor.execute("SELECT id, level FROM categories WHERE slug = ?", (parent_slug,))
                parent_result = cursor.fetchone()
                if parent_result:
                    parent_id, parent_level = parent_result
                    level = parent_level + 1
                    print(f"   📁 Parent: {parent_slug} (level {parent_level})")
                else:
                    print(f"   ❌ Parent category '{parent_slug}' not found")
                    return False
            
            # Insert new category
            cursor.execute("""
                INSERT INTO categories 
                (name, slug, description, parent_id, level, sort_order, is_active)
                VALUES (?, ?, ?, ?, ?, ?, 1)
            """, (name, slug, description, parent_id, level, sort_order))
            
            conn.commit()
            print(f"   ✅ Added: {name} (slug: {slug}, level: {level})")
            
            # Show the category path
            if parent_slug:
                cursor.execute("""
                    WITH RECURSIVE category_path AS (
                        SELECT id, name, parent_id, name as path, 0 as level
                        FROM categories WHERE slug = ?
                        UNION ALL
                        SELECT c.id, c.name, c.parent_id, 
                               cp.path || ' > ' || c.name as path, cp.level + 1
                        FROM categories c
                        JOIN category_path cp ON c.id = cp.parent_id
                    )
                    SELECT path FROM category_path WHERE parent_id IS NULL
                """, (slug,))
                
                path_result = cursor.fetchone()
                if path_result:
                    print(f"   📂 Full path: {path_result[0]}")
            
            return True
            
    except sqlite3.IntegrityError as e:
        if "UNIQUE constraint failed" in str(e):
            print(f"   ⚠️  Category with slug '{slug}' already exists")
        else:
            print(f"   ❌ Database error: {e}")
        return False
    except Exception as e:
        print(f"   ❌ Error adding category: {e}")
        return False

def list_categories():
    """List all categories in hierarchy"""
    print("\n📂 Current Category Hierarchy")
    print("=" * 50)
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT name, slug, level, parent_id, sort_order
                FROM categories 
                WHERE is_active = 1
                ORDER BY level, sort_order, name
            """)
            
            categories = cursor.fetchall()
            
            for name, slug, level, parent_id, sort_order in categories:
                indent = "  " * level
                print(f"{indent}📁 {name} ({slug})")
            
            print(f"\nTotal categories: {len(categories)}")
            
    except Exception as e:
        print(f"❌ Error listing categories: {e}")

def show_usage():
    """Show usage examples"""
    print("🎯 Category Management Tool")
    print("=" * 50)
    print()
    print("Usage examples:")
    print()
    print("1. Add a root category:")
    print("   python3 add_category.py 'Furniture' 'furniture' 'Furniture and home decor'")
    print()
    print("2. Add a subcategory:")
    print("   python3 add_category.py 'Sofas' 'sofas' 'Sofas and couches' 'furniture'")
    print()
    print("3. Add a specific material category:")
    print("   python3 add_category.py 'Microfiber' 'microfiber' 'Microfiber sheets' 'sheets'")
    print()
    print("4. List all categories:")
    print("   python3 add_category.py --list")
    print()
    print("5. Interactive mode:")
    print("   python3 add_category.py --interactive")

def interactive_mode():
    """Interactive mode for adding categories"""
    print("🎯 Interactive Category Addition")
    print("=" * 50)
    
    while True:
        print("\nOptions:")
        print("1. Add new category")
        print("2. List all categories")
        print("3. Exit")
        
        choice = input("\nEnter choice (1-3): ").strip()
        
        if choice == "1":
            name = input("Category name: ").strip()
            if not name:
                print("❌ Name is required")
                continue
            
            slug = input("Category slug (auto-generated if empty): ").strip()
            if not slug:
                slug = name.lower().replace(" ", "-").replace("&", "and")
            
            description = input("Description (optional): ").strip()
            
            parent_slug = input("Parent category slug (optional): ").strip()
            if not parent_slug:
                parent_slug = None
            
            sort_order = input("Sort order (default 0): ").strip()
            try:
                sort_order = int(sort_order) if sort_order else 0
            except ValueError:
                sort_order = 0
            
            add_category(name, slug, description, parent_slug, sort_order)
        
        elif choice == "2":
            list_categories()
        
        elif choice == "3":
            print("👋 Goodbye!")
            break
        
        else:
            print("❌ Invalid choice")

def main():
    """Main function"""
    if len(sys.argv) == 1:
        show_usage()
        return
    
    if sys.argv[1] == "--list":
        list_categories()
        return
    
    if sys.argv[1] == "--interactive":
        interactive_mode()
        return
    
    if len(sys.argv) < 3:
        print("❌ Usage: python3 add_category.py 'Name' 'slug' [description] [parent_slug] [sort_order]")
        print("   Or: python3 add_category.py --list")
        print("   Or: python3 add_category.py --interactive")
        return
    
    name = sys.argv[1]
    slug = sys.argv[2]
    description = sys.argv[3] if len(sys.argv) > 3 else ""
    parent_slug = sys.argv[4] if len(sys.argv) > 4 else None
    sort_order = int(sys.argv[5]) if len(sys.argv) > 5 else 0
    
    add_category(name, slug, description, parent_slug, sort_order)

if __name__ == "__main__":
    main()
