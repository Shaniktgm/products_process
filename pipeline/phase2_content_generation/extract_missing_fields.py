#!/usr/bin/env python3
"""
Extract missing fields from existing product data (title, description, summary)
"""

import sqlite3
import re
from typing import Optional, List, Dict, Any

class ProductDataExtractor:
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Material patterns
        self.material_patterns = {
            'cotton': [
                r'100%\s*cotton', r'cotton', r'egyptian\s*cotton', r'supima\s*cotton',
                r'organic\s*cotton', r'premium\s*cotton', r'fine\s*cotton'
            ],
            'bamboo': [
                r'bamboo', r'viscose\s*from\s*bamboo', r'100%\s*viscose', r'viscose'
            ],
            'linen': [
                r'linen', r'belgian\s*linen', r'flax', r'natural\s*flax'
            ],
            'silk': [
                r'silk', r'silky', r'silk\s*blend'
            ],
            'polyester': [
                r'polyester', r'poly\s*blend', r'synthetic'
            ],
            'microfiber': [
                r'microfiber', r'micro\s*fiber'
            ]
        }
        
        # Weave type patterns
        self.weave_patterns = {
            'sateen': [r'sateen', r'satin'],
            'percale': [r'percale'],
            'basketweave': [r'basketweave', r'basket\s*weave'],
            'twill': [r'twill'],
            'jersey': [r'jersey', r'knit'],
            'flannel': [r'flannel']
        }
        
        # Color patterns
        self.color_patterns = [
            r'white', r'ivory', r'cream', r'beige', r'gray', r'grey', r'black',
            r'blue', r'navy', r'royal\s*blue', r'sky\s*blue', r'powder\s*blue',
            r'green', r'sage', r'emerald', r'forest\s*green',
            r'red', r'burgundy', r'wine', r'crimson',
            r'yellow', r'gold', r'champagne',
            r'purple', r'lavender', r'plum',
            r'pink', r'rose', r'blush',
            r'brown', r'tan', r'chocolate', r'mocha',
            r'stone', r'pewter', r'silver', r'charcoal'
        ]
        
        # Size patterns
        self.size_patterns = [
            r'twin', r'twin\s*xl', r'full', r'queen', r'king', r'california\s*king',
            r'cal\s*king', r'split\s*king', r'standard', r'euro', r'body\s*pillow'
        ]
        
        # Thread count patterns
        self.thread_count_patterns = [
            r'(\d+)\s*thread\s*count', r'(\d+)\s*tc', r'(\d+)\s*threads',
            r'thread\s*count[:\s]*(\d+)', r'tc[:\s]*(\d+)'
        ]
        
        # Category patterns
        self.category_patterns = {
            'Bath Towels': [
                r'bath\s*towel', r'bath\s*sheet', r'towel\s*set', r'bath\s*set',
                r'hand\s*towel', r'washcloth', r'bath\s*sheet\s*set'
            ],
            'Sheet Sets': [
                r'sheet\s*set', r'bed\s*sheet\s*set', r'bedding\s*set', r'bed\s*set',
                r'\d+\s*piece\s*sheet', r'\d+\s*pc\s*sheet', r'complete\s*set'
            ],
            'Individual Sheets': [
                r'fitted\s*sheet', r'flat\s*sheet', r'bed\s*sheet', r'single\s*sheet',
                r'deep\s*pocket\s*sheet', r'elastic\s*sheet'
            ],
            'Pillowcases': [
                r'pillowcase', r'pillow\s*case', r'pillow\s*cover', r'pillow\s*sham'
            ],
            'Bed Pillows': [
                r'pillow', r'down\s*alternative\s*pillow', r'memory\s*foam\s*pillow',
                r'chamber\s*pillow', r'body\s*pillow', r'decorative\s*pillow'
            ],
            'Comforters': [
                r'comforter', r'duvet\s*insert', r'duvet\s*filler', r'bed\s*comforter',
                r'all\s*season\s*comforter', r'lightweight\s*comforter'
            ],
            'Duvet Inserts': [
                r'duvet\s*insert', r'duvet\s*filler', r'insert\s*comforter'
            ],
            'Duvet Covers': [
                r'duvet\s*cover', r'duvet\s*set', r'cover\s*set'
            ],
            'Bed Blankets': [
                r'blanket', r'throw\s*blanket', r'bed\s*blanket', r'quilt',
                r'bedspread', r'coverlet'
            ],
            'Mattress Protectors': [
                r'mattress\s*protector', r'mattress\s*pad', r'mattress\s*topper',
                r'bed\s*protector', r'waterproof\s*protector'
            ],
            'Quilts': [
                r'quilt', r'quilted', r'patchwork\s*quilt'
            ]
        }

    def extract_material(self, text: str) -> Optional[str]:
        """Extract material from text"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        # Check for specific materials
        for material, patterns in self.material_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return material.title()
        
        return None

    def extract_weave_type(self, text: str) -> Optional[str]:
        """Extract weave type from text"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        for weave, patterns in self.weave_patterns.items():
            for pattern in patterns:
                if re.search(pattern, text_lower):
                    return weave.title()
        
        return None

    def extract_color(self, text: str) -> Optional[str]:
        """Extract color from text"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        for pattern in self.color_patterns:
            match = re.search(pattern, text_lower)
            if match:
                return match.group(0).title()
        
        return None

    def extract_size(self, text: str) -> Optional[str]:
        """Extract size from text"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        for pattern in self.size_patterns:
            match = re.search(pattern, text_lower)
            if match:
                size = match.group(0).title()
                # Clean up common variations
                if 'california' in size.lower():
                    return 'California King'
                elif 'split' in size.lower():
                    return 'Split King'
                elif 'xl' in size.lower():
                    return 'Twin XL'
                return size
        
        return None

    def extract_thread_count(self, text: str) -> Optional[int]:
        """Extract thread count from text"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        for pattern in self.thread_count_patterns:
            match = re.search(pattern, text_lower)
            if match:
                try:
                    return int(match.group(1))
                except (ValueError, IndexError):
                    continue
        
        return None

    def extract_brand(self, text: str) -> Optional[str]:
        """Extract brand from text"""
        if not text:
            return None
            
        # Common brand patterns
        brand_patterns = [
            r'from\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$|,|\.)',
            r'by\s+([A-Z][a-zA-Z\s&]+?)(?:\s|$|,|\.)',
            r'([A-Z][a-zA-Z\s&]+?)\s+[Ss]heet',
            r'([A-Z][a-zA-Z\s&]+?)\s+[Cc]omforter',
            r'([A-Z][a-zA-Z\s&]+?)\s+[Pp]illow'
        ]
        
        for pattern in brand_patterns:
            match = re.search(pattern, text)
            if match:
                brand = match.group(1).strip()
                # Filter out common words that aren't brands
                if brand.lower() not in ['the', 'and', 'or', 'of', 'in', 'on', 'at', 'to', 'for']:
                    return brand
        
        return None

    def extract_category(self, text: str) -> Optional[str]:
        """Extract category from text with enhanced detection (from extract_amazon_product.py)"""
        if not text:
            return None
            
        text_lower = text.lower()
        
        # Enhanced category detection from extract_amazon_product.py
        if 'sheet' in text_lower:
            return 'Bed Sheets'
        elif 'pillow' in text_lower:
            return 'Pillows'
        elif 'comforter' in text_lower:
            return 'Comforters'
        elif 'blanket' in text_lower:
            return 'Blankets'
        elif 'duvet' in text_lower:
            return 'Duvets'
        elif 'mattress' in text_lower:
            return 'Mattress Accessories'
        
        # Fallback to original pattern-based scoring
        category_scores = {}
        
        for category, patterns in self.category_patterns.items():
            score = 0
            for pattern in patterns:
                matches = len(re.findall(pattern, text_lower))
                score += matches
            
            if score > 0:
                category_scores[category] = score
        
        # Prioritize more specific categories over general ones
        # Check for specific exclusions first
        if 'bath' in text_lower and 'sheet' in text_lower:
            # If it contains both "bath" and "sheet", it's likely a bath towel set
            if 'Bath Towels' in category_scores:
                return 'Bath Towels'
        
        # Return the category with the highest score
        if category_scores:
            return max(category_scores, key=category_scores.get)
        
        return None

    def extract_all_fields(self, title: str, description: str, summary: str) -> Dict[str, Any]:
        """Extract all missing fields from available text"""
        # Combine all text for analysis
        combined_text = f"{title or ''} {description or ''} {summary or ''}"
        
        return {
            'material': self.extract_material(combined_text),
            'weave_type': self.extract_weave_type(combined_text),
            'color': self.extract_color(combined_text),
            'size': self.extract_size(combined_text),
            'thread_count': self.extract_thread_count(combined_text),
            'brand': self.extract_brand(combined_text),
            'suggested_category': self.extract_category(combined_text)
        }

    def update_product_fields(self, product_id: int, fields: Dict[str, Any]) -> int:
        """Update product with extracted fields"""
        updates = []
        values = []
        
        for field, value in fields.items():
            if value is not None and field != 'suggested_category':
                updates.append(f"{field} = ?")
                values.append(value)
        
        if not updates:
            return 0
        
        values.append(product_id)
        
        query = f"""
            UPDATE products 
            SET {', '.join(updates)}
            WHERE id = ?
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute(query, values)
            conn.commit()
            return cursor.rowcount

    def assign_category(self, product_id: int, category_name: str) -> bool:
        """Assign a category to a product if it doesn't already have one"""
        if not category_name:
            return False
            
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Check if product already has a category
            cursor.execute("""
                SELECT COUNT(*) FROM product_categories 
                WHERE product_id = ?
            """, (product_id,))
            
            if cursor.fetchone()[0] > 0:
                return False  # Product already has categories
            
            # Insert the category
            cursor.execute("""
                INSERT INTO product_categories (product_id, category_name, is_primary)
                VALUES (?, ?, 1)
            """, (product_id, category_name))
            
            conn.commit()
            return True

    def process_all_products(self) -> Dict[str, int]:
        """Process all products and extract missing fields"""
        stats = {
            'products_processed': 0,
            'products_updated': 0,
            'categories_assigned': 0,
            'fields_extracted': {
                'material': 0,
                'weave_type': 0,
                'color': 0,
                'size': 0,
                'thread_count': 0,
                'brand': 0,
                'suggested_category': 0
            }
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all products
            cursor.execute("""
                SELECT id, title, description, product_summary, brand
                FROM products
                ORDER BY id
            """)
            
            products = cursor.fetchall()
            
            for product_id, title, description, summary, existing_brand in products:
                stats['products_processed'] += 1
                
                # Extract fields
                extracted = self.extract_all_fields(title, description, summary)
                
                # Don't override existing brand
                if existing_brand and existing_brand.strip():
                    extracted['brand'] = existing_brand
                
                # Count extracted fields
                for field, value in extracted.items():
                    if value is not None:
                        stats['fields_extracted'][field] += 1
                
                # Update database with extracted fields
                updated = self.update_product_fields(product_id, extracted)
                if updated > 0:
                    stats['products_updated'] += 1
                
                # Handle category assignment
                suggested_category = extracted.get('suggested_category')
                if suggested_category:
                    category_assigned = self.assign_category(product_id, suggested_category)
                    if category_assigned:
                        stats['categories_assigned'] += 1
                
                # Print progress
                extracted_fields = [f"{k}: {v}" for k, v in extracted.items() if v is not None and k != 'suggested_category']
                category_info = f" → Category: {suggested_category}" if suggested_category else ""
                if extracted_fields:
                    print(f"✅ Product {product_id}: {', '.join(extracted_fields)}{category_info}")
                else:
                    print(f"⚠️  Product {product_id}: No fields extracted{category_info}")
        
        return stats

def main():
    """Main function"""
    print("🔍 Extracting missing fields from existing product data...")
    print("=" * 60)
    
    extractor = ProductDataExtractor()
    stats = extractor.process_all_products()
    
    print("\n" + "=" * 60)
    print("📊 EXTRACTION RESULTS:")
    print(f"Products processed: {stats['products_processed']}")
    print(f"Products updated: {stats['products_updated']}")
    print(f"Categories assigned: {stats['categories_assigned']}")
    print("\nFields extracted:")
    for field, count in stats['fields_extracted'].items():
        print(f"  {field}: {count}")
    
    print(f"\n🎉 Extraction complete!")

if __name__ == "__main__":
    main()
