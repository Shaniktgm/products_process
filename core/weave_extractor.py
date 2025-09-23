#!/usr/bin/env python3
"""
Weave Extractor
Extracts and saves weave/fabric construction type from product data to the weave_type column
"""

import sqlite3
import re
from typing import Dict, Any, Optional

class WeaveExtractor:
    """Extracts weave/fabric construction type from product data and saves to database"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
    
    def extract_all_weaves(self) -> Dict[str, int]:
        """Extract weave types for all products"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'weaves_extracted': 0,
            'errors': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all products with their data
            cursor.execute('''
                SELECT 
                    p.id,
                    COALESCE(NULLIF(p.amazon_title, ''), p.title) as source_title,
                    GROUP_CONCAT(sf.feature_text, ' ') as amazon_features,
                    p.weave_type
                FROM products p
                LEFT JOIN smart_features sf ON p.id = sf.product_id AND sf.source_type = 'amazon_raw'
                WHERE COALESCE(NULLIF(p.amazon_title, ''), p.title) IS NOT NULL
                  AND COALESCE(NULLIF(p.amazon_title, ''), p.title) != ''
                GROUP BY p.id
                ORDER BY p.id
            ''')
            
            products = cursor.fetchall()
            stats['total_products'] = len(products)
            
            for product in products:
                try:
                    product_id = product[0]
                    title = product[1] or ''
                    amazon_features = product[2] or ''
                    existing_weave = product[3] or ''
                    
                    # Only extract if weave_type is empty or "None"
                    if existing_weave and existing_weave.lower() not in ['none', '']:
                        stats['processed_products'] += 1
                        continue
                    
                    # Extract weave type
                    weave = self._extract_weave_type(title, '', amazon_features)
                    
                    # Update database
                    cursor.execute('''
                        UPDATE products 
                        SET weave_type = ? 
                        WHERE id = ?
                    ''', (weave, product_id))
                    
                    stats['processed_products'] += 1
                    if weave and weave.lower() != 'none':
                        stats['weaves_extracted'] += 1
                    
                    print(f"✅ Product {product_id}: weave_type = '{weave}'")
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    stats['errors'] += 1
                    continue
            
            conn.commit()
        
        return stats
    
    def _extract_weave_type(self, title: str, description: str, amazon_features: str) -> Optional[str]:
        """Extract weave/fabric construction type from product text"""
        # Combine all text for analysis
        combined_text = f"{title} {description} {amazon_features}".lower()
        
        # Enhanced weave type extraction
        weave_patterns = {
            'sateen': 'Sateen',
            'satin': 'Sateen',  # Satin is often used interchangeably with sateen
            'percale': 'Percale',
            'flannel': 'Flannel',
            'jersey': 'Jersey',
            'knit': 'Jersey',  # Knit often refers to jersey
            'basketweave': 'Basketweave',
            'basket weave': 'Basketweave',
            'twill': 'Twill',
            'oxford': 'Oxford',
            'herringbone': 'Herringbone',
            'microfiber': 'Microfiber',
            'fleece': 'Fleece',
            'terry': 'Terry',
            'towel': 'Terry'  # Towels are typically terry weave
        }
        
        # Search for weave patterns (prioritize more specific matches)
        for pattern, weave in weave_patterns.items():
            if pattern in combined_text:
                return weave
        
        # Special cases for common bedding materials
        if 'bamboo' in combined_text and 'viscose' in combined_text:
            return 'Bamboo Viscose'
        elif 'silk' in combined_text:
            return 'Silk'  # Silk is both material and weave type
        elif 'linen' in combined_text:
            return 'Linen'  # Linen is both material and weave type
        
        # If no specific weave found, return None
        return None
    
    def extract_weave_for_product(self, product_id: int) -> Optional[str]:
        """Extract weave type for a specific product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COALESCE(NULLIF(amazon_title, ''), title) as source_title,
                    GROUP_CONCAT(sf.feature_text, ' ') as amazon_features
                FROM products p
                LEFT JOIN smart_features sf ON p.id = sf.product_id AND sf.source_type = 'amazon_raw'
                WHERE p.id = ?
                GROUP BY p.id
            ''', (product_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            title, amazon_features = result
            return self._extract_weave_type(title or '', '', amazon_features or '')

def main():
    """Main function"""
    print("🧵 Weave Extractor")
    print("=" * 50)
    
    extractor = WeaveExtractor()
    results = extractor.extract_all_weaves()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Total products: {results['total_products']}")
    print(f"Processed products: {results['processed_products']}")
    print(f"Weaves extracted: {results['weaves_extracted']}")
    print(f"Errors: {results['errors']}")
    
    print(f"\n🎉 Weave extraction complete!")

if __name__ == "__main__":
    main()
