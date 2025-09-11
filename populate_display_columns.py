#!/usr/bin/env python3
"""
Script to populate pretty_title and short_description columns for existing products
"""

import sqlite3
import re

def generate_pretty_title(title: str) -> str:
    """Generate a short, easy-to-read title from the full title"""
    # Remove common redundant phrases
    title = re.sub(r'\s*-\s*Luxury.*?(?=\s*-\s*|$)', '', title)
    title = re.sub(r'\s*-\s*Thick and Natural.*?(?=\s*-\s*|$)', '', title)
    title = re.sub(r'\s*-\s*Deep Pockets.*?(?=\s*-\s*|$)', '', title)
    title = re.sub(r'\s*-\s*Soft.*?(?=\s*-\s*|$)', '', title)
    title = re.sub(r'\s*-\s*Breathable.*?(?=\s*-\s*|$)', '', title)
    title = re.sub(r'\s*-\s*Durable.*?(?=\s*-\s*|$)', '', title)
    title = re.sub(r'\s*-\s*Bedding Set.*?(?=\s*-\s*|$)', '', title)
    
    # Extract key information: Brand + Product Type + Key Feature + Size
    parts = title.split(' - ')
    if len(parts) >= 2:
        # Take first part (brand + product type) and key feature
        main_part = parts[0]
        key_feature = None
        
        # Look for thread count or material in the title
        if 'thread count' in title.lower():
            thread_match = re.search(r'(\d+)\s*thread count', title, re.IGNORECASE)
            if thread_match:
                key_feature = f"{thread_match.group(1)} Thread Count"
        elif 'cotton' in title.lower():
            if 'egyptian cotton' in title.lower():
                key_feature = "Egyptian Cotton"
            elif 'bamboo' in title.lower():
                key_feature = "Bamboo"
            else:
                key_feature = "Cotton"
        
        # Look for size
        size_match = re.search(r'\b(king|queen|twin|full|california king)\b', title, re.IGNORECASE)
        size = size_match.group(1).title() if size_match else ""
        
        # Construct pretty title
        if key_feature and size:
            return f"{main_part} - {key_feature} {size}"
        elif key_feature:
            return f"{main_part} - {key_feature}"
        elif size:
            return f"{main_part} - {size}"
        else:
            return main_part
    
    # Fallback: truncate to reasonable length
    return title[:60] + "..." if len(title) > 60 else title

def generate_short_description(title: str, description: str = "") -> str:
    """Generate a short description for website display"""
    
    # Extract key features from title and description
    features = []
    
    # Material
    if 'egyptian cotton' in title.lower():
        features.append("Egyptian cotton")
    elif 'bamboo' in title.lower():
        features.append("bamboo")
    elif 'cotton' in title.lower():
        features.append("cotton")
    
    # Thread count
    thread_match = re.search(r'(\d+)\s*thread count', title, re.IGNORECASE)
    if thread_match:
        features.append(f"{thread_match.group(1)}-thread count")
    
    # Size
    size_match = re.search(r'\b(king|queen|twin|full|california king)\b', title, re.IGNORECASE)
    if size_match:
        features.append(f"{size_match.group(1)} size")
    
    # Key benefits
    if 'cooling' in title.lower() or 'cool' in title.lower():
        features.append("cooling technology")
    if 'breathable' in title.lower():
        features.append("breathable")
    if 'soft' in title.lower():
        features.append("soft feel")
    
    # Construct short description
    if features:
        feature_text = ", ".join(features[:3])  # Limit to 3 features
        return f"Premium {feature_text} sheets offering comfort and durability for a restful night's sleep."
    else:
        return "High-quality bedding set designed for comfort and durability."

def populate_display_columns():
    """Populate pretty_title and short_description for all products"""
    print("🔄 Populating display columns for existing products...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Get all products
            cursor.execute("SELECT id, title, description FROM products")
            products = cursor.fetchall()
            
            print(f"📊 Found {len(products)} products to update")
            
            updated_count = 0
            for product_id, title, description in products:
                try:
                    # Generate pretty title and short description
                    pretty_title = generate_pretty_title(title)
                    short_description = generate_short_description(title, description or "")
                    
                    # Update database
                    cursor.execute("""
                        UPDATE products 
                        SET pretty_title = ?, short_description = ?
                        WHERE id = ?
                    """, (pretty_title, short_description, product_id))
                    
                    updated_count += 1
                    
                    if updated_count % 10 == 0:
                        print(f"   Progress: {updated_count}/{len(products)} products updated")
                
                except Exception as e:
                    print(f"   ❌ Error updating product {product_id}: {e}")
                    continue
            
            conn.commit()
            print(f"\n✅ Successfully updated {updated_count}/{len(products)} products")
            
            # Show some examples
            print("\n📋 Examples of generated content:")
            cursor.execute("SELECT title, pretty_title, short_description FROM products LIMIT 3")
            examples = cursor.fetchall()
            
            for i, (title, pretty_title, short_description) in enumerate(examples, 1):
                print(f"\nExample {i}:")
                print(f"  Original Title: {title[:80]}...")
                print(f"  Pretty Title: {pretty_title}")
                print(f"  Short Description: {short_description}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    populate_display_columns()
