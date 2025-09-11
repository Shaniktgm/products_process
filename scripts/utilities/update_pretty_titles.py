#!/usr/bin/env python3
"""
Script to update all existing products with improved pretty titles
"""

import sqlite3
import re

def _extract_size_from_title(title: str) -> str:
    """Extract size from title"""
    size_match = re.search(r'\b(king|queen|twin|full|california king)\b', title, re.IGNORECASE)
    if size_match:
        size = size_match.group(1).lower()
        if size == 'california king':
            return 'California King'
        else:
            return size.title()
    return ""

def _extract_piece_count(title: str) -> str:
    """Extract piece count from title"""
    piece_match = re.search(r'(\d+)\s*[pP]iece', title)
    if piece_match:
        return piece_match.group(1)
    return ""

def _extract_thread_count_from_title(title: str) -> str:
    """Extract thread count from title"""
    thread_match = re.search(r'(\d+)\s*thread count', title, re.IGNORECASE)
    if thread_match:
        return thread_match.group(1)
    return ""

def _extract_material_from_title(title: str) -> str:
    """Extract material from title"""
    if 'egyptian cotton' in title.lower():
        return 'Egyptian Cotton'
    elif 'bamboo' in title.lower():
        return 'Bamboo'
    elif 'linen' in title.lower():
        return 'Linen'
    elif 'sateen' in title.lower():
        return 'Sateen'
    elif 'percale' in title.lower():
        return 'Percale'
    return ""

def _extract_brand_from_title(title: str) -> str:
    """Extract brand from title"""
    brands = ['Breescape', 'Threadmill', 'Buffy', 'Boll & Branch', 'Bamboo Bay', 'Coop Home Goods']
    for brand in brands:
        if brand.lower() in title.lower():
            return brand
    return ""

def _extract_product_type(title: str) -> str:
    """Extract product type from title"""
    if 'sheet set' in title.lower():
        return 'Sheets'
    elif 'comforter' in title.lower():
        return 'Comforter'
    elif 'duvet' in title.lower():
        return 'Duvet'
    elif 'protector' in title.lower():
        return 'Protector'
    elif 'bundle' in title.lower():
        return 'Bundle'
    else:
        return 'Sheets'

def _generate_pretty_title(title: str) -> str:
    """Generate a short, complete title for product cards (no mid-word cuts)"""
    
    # Extract key components
    size = _extract_size_from_title(title)
    piece_count = _extract_piece_count(title)
    thread_count = _extract_thread_count_from_title(title)
    material = _extract_material_from_title(title)
    brand = _extract_brand_from_title(title)
    product_type = _extract_product_type(title)
    
    # Build title components
    components = []
    
    # Start with size if available
    if size:
        components.append(size)
    
    # Add piece count if available
    if piece_count:
        components.append(f"{piece_count}-Pc")
    
    # Add product type
    if product_type:
        components.append(product_type)
    
    # Add material if it's a key differentiator
    if material and material.lower() not in ['cotton']:  # Skip generic cotton
        components.append(material)
    
    # Add thread count if available
    if thread_count:
        components.append(f"{thread_count} Thread")
    
    # Add brand if it's not too long and adds value
    if brand and len(brand) <= 15 and brand not in ['California Design Den']:
        components.append(brand)
    
    # Join components with spaces and commas
    if components:
        pretty_title = " ".join(components)
        
        # Ensure it's not too long (max 50 characters for product cards)
        if len(pretty_title) > 50:
            # Try to shorten by removing less important components
            if thread_count and len(pretty_title) > 50:
                components = [c for c in components if not c.endswith('Thread')]
                pretty_title = " ".join(components)
            
            if len(pretty_title) > 50:
                # Final fallback: truncate at word boundary
                words = pretty_title.split()
                result = ""
                for word in words:
                    if len(result + " " + word) <= 47:  # Leave room for "..."
                        result += (" " + word) if result else word
                    else:
                        break
                if result != pretty_title:
                    result += "..."
                pretty_title = result
        
        return pretty_title
    
    # Fallback: create a simple title
    if size:
        return f"{size} Sheet Set"
    else:
        return "Bedding Set"

def update_pretty_titles():
    """Update all existing products with improved pretty titles"""
    print("🔄 Updating pretty titles for existing products...")
    
    try:
        with sqlite3.connect("multi_platform_products.db") as conn:
            cursor = conn.cursor()
            
            # Get all products
            cursor.execute("SELECT id, title, pretty_title FROM products")
            products = cursor.fetchall()
            
            print(f"📊 Found {len(products)} products to update")
            
            updated_count = 0
            for product_id, title, old_pretty_title in products:
                try:
                    # Generate new pretty title
                    new_pretty_title = _generate_pretty_title(title)
                    
                    # Update database
                    cursor.execute("""
                        UPDATE products 
                        SET pretty_title = ?
                        WHERE id = ?
                    """, (new_pretty_title, product_id))
                    
                    updated_count += 1
                    
                    if updated_count % 10 == 0:
                        print(f"   Progress: {updated_count}/{len(products)} products updated")
                
                except Exception as e:
                    print(f"   ❌ Error updating product {product_id}: {e}")
                    continue
            
            conn.commit()
            print(f"\n✅ Successfully updated {updated_count}/{len(products)} products")
            
            # Show some examples
            print("\n📋 Examples of improved pretty titles:")
            cursor.execute("SELECT title, pretty_title FROM products LIMIT 5")
            examples = cursor.fetchall()
            
            for i, (title, pretty_title) in enumerate(examples, 1):
                print(f"\nExample {i}:")
                print(f"  Original Title: {title[:80]}...")
                print(f"  Pretty Title:   {pretty_title} ({len(pretty_title)} chars)")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    update_pretty_titles()
