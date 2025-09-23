#!/usr/bin/env python3
"""
Improved Pretty Title Generator
Creates concise, under-10-word titles using the most relevant product information
"""

import sqlite3
import re
from typing import Dict, Any, Optional

class ImprovedPrettyTitleGenerator:
    """Generates smart, concise pretty titles under 10 words using rich product data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path

    def _extract_thread_count(self, text: str) -> Optional[int]:
        """Extract thread count from text"""
        patterns = [
            r'(\d{3,4})\s*thread',
            r'thread\s*count[:\s]*(\d{3,4})',
            r'(\d{3,4})\s*tc'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, text.lower())
            if match:
                count = int(match.group(1))
                if 200 <= count <= 2000:  # Reasonable range
                    return count
        return None

    def _extract_weave_type(self, text: str) -> Optional[str]:
        """Extract weave type from text"""
        text_lower = text.lower()
        
        if 'sateen' in text_lower:
            return 'Sateen'
        elif 'percale' in text_lower:
            return 'Percale'
        elif 'flannel' in text_lower:
            return 'Flannel'
        elif 'jersey' in text_lower:
            return 'Jersey'
        elif 'linen' in text_lower:
            return 'Linen'
        return None

    def _extract_material(self, text: str) -> Optional[str]:
        """Extract material type from text"""
        text_lower = text.lower()
        
        if 'egyptian cotton' in text_lower:
            return 'Egyptian Cotton'
        elif 'organic cotton' in text_lower:
            return 'Organic Cotton'
        elif 'bamboo' in text_lower:
            return 'Bamboo'
        elif 'linen' in text_lower:
            return 'Linen'
        elif 'microfiber' in text_lower:
            return 'Microfiber'
        elif 'cotton' in text_lower:
            return 'Cotton'
        return None

    def _extract_size(self, text: str) -> Optional[str]:
        """Extract size from text"""
        text_lower = text.lower()
        
        if 'king' in text_lower:
            return 'King'
        elif 'queen' in text_lower:
            return 'Queen'
        elif 'twin' in text_lower:
            return 'Twin'
        elif 'full' in text_lower:
            return 'Full'
        return None

    def _extract_product_type(self, text: str) -> Optional[str]:
        """Extract product type from text"""
        text_lower = text.lower()
        
        if 'sheet set' in text_lower:
            return 'Sheet Set'
        elif 'bed sheet' in text_lower or 'sheet' in text_lower:
            return 'Bed Sheet'
        elif 'pillowcase' in text_lower:
            return 'Pillowcase'
        elif 'comforter' in text_lower:
            return 'Comforter'
        elif 'duvet cover' in text_lower:
            return 'Duvet Cover'
        elif 'blanket' in text_lower:
            return 'Blanket'
        elif 'pillow' in text_lower:
            return 'Pillow'
        return None

    def _clean_brand(self, brand: str) -> Optional[str]:
        """Clean brand name"""
        if not brand or brand.lower() in ['unknown', 'visit the', 'amazon', 'generic']:
            return None
        
        # Remove common suffixes
        brand = re.sub(r'\s+(collection|home|brand)$', '', brand, flags=re.IGNORECASE)
        return brand.strip()

    def _generate_smart_title(self, product_data: Dict[str, Any]) -> str:
        """Generate a smart title under 10 words"""
        
        # Extract data
        amazon_title = product_data.get('amazon_title', '')
        product_summary = product_data.get('product_summary', '')
        brand = product_data.get('amazon_brand', '')
        material = product_data.get('material', '')
        weave_type = product_data.get('weave_type', '')
        thread_count = product_data.get('thread_count')
        amazon_color_code = product_data.get('amazon_color_code', '')
        amazon_size_code = product_data.get('amazon_size_code', '')
        
        # Combine text for extraction
        combined_text = f"{product_summary} {amazon_title}".lower()
        
        # Extract components
        extracted_material = self._extract_material(combined_text) or material
        extracted_thread_count = self._extract_thread_count(combined_text) or thread_count
        extracted_weave = self._extract_weave_type(combined_text) or weave_type
        extracted_size = self._extract_size(combined_text) or amazon_size_code
        extracted_type = self._extract_product_type(combined_text)
        clean_brand = self._clean_brand(brand)
        
        # Build title components (priority order)
        components = []
        
        # 1. Brand (if meaningful)
        if clean_brand:
            components.append(clean_brand)
        
        # 2. Premium material
        if extracted_material:
            components.append(extracted_material)
        
        # 3. Thread count (only if high quality)
        if extracted_thread_count and extracted_thread_count >= 400:
            components.append(f"{extracted_thread_count} Thread")
        
        # 4. Weave type (only if meaningful and different from material)
        if extracted_weave and extracted_weave.lower() not in extracted_material.lower():
            components.append(extracted_weave)
        
        # 5. Product type
        if extracted_type:
            components.append(extracted_type)
        
        # 6. Size (only if not Queen/standard)
        if extracted_size and extracted_size.lower() not in ['queen', 'standard']:
            components.append(extracted_size)
        
        # Create title (max 10 words)
        title = " ".join(components[:10])
        
        # Fallback
        if not title.strip():
            if clean_brand and extracted_material:
                title = f"{clean_brand} {extracted_material} Sheets"
            elif extracted_material:
                title = f"{extracted_material} Bed Sheets"
            else:
                title = "Premium Bed Sheets"
        
        return title.strip()

    def update_all_pretty_titles(self) -> Dict[str, int]:
        """Update all pretty titles with improved generation"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'titles_generated': 0,
            'errors': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all products with Amazon data
            cursor.execute('''
                SELECT 
                    p.id,
                    p.amazon_title,
                    p.product_summary,
                    p.amazon_brand,
                    p.material,
                    p.weave_type,
                    p.thread_count,
                    p.amazon_color_code,
                    p.amazon_size_code
                FROM products p
                WHERE p.amazon_title IS NOT NULL 
                AND p.amazon_title != ''
                ORDER BY p.id
            ''')
            
            products = cursor.fetchall()
            stats['total_products'] = len(products)
            
            for product in products:
                try:
                    product_id = product[0]
                    
                    # Create product data dict
                    product_data = {
                        'amazon_title': product[1] or '',
                        'product_summary': product[2] or '',
                        'amazon_brand': product[3] or '',
                        'material': product[4] or '',
                        'weave_type': product[5] or '',
                        'thread_count': product[6],
                        'amazon_color_code': product[7] or '',
                        'amazon_size_code': product[8] or ''
                    }
                    
                    # Generate new title
                    new_title = self._generate_smart_title(product_data)
                    
                    # Update database
                    cursor.execute('''
                        UPDATE products 
                        SET pretty_title = ? 
                        WHERE id = ?
                    ''', (new_title, product_id))
                    
                    stats['processed_products'] += 1
                    stats['titles_generated'] += 1
                    
                except Exception as e:
                    print(f'❌ Error processing product {product_id}: {e}')
                    stats['errors'] += 1
                    continue
            
            conn.commit()
        
        return stats

def main():
    """Run the improved pretty title generator"""
    print('🎨 IMPROVED PRETTY TITLE GENERATOR')
    print('=' * 50)
    
    generator = ImprovedPrettyTitleGenerator()
    results = generator.update_all_pretty_titles()
    
    print()
    print('🎉 IMPROVED PRETTY TITLE GENERATION COMPLETE!')
    print(f'   📊 Results: {results}')

if __name__ == "__main__":
    main()
