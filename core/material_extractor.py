#!/usr/bin/env python3
"""
Material Extractor
Extracts and saves fabric/material type from product data to the material column
"""

import sqlite3
import re
from typing import Dict, Any, Optional

class MaterialExtractor:
    """Extracts fabric/material type from product data and saves to database"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
    
    def extract_all_materials(self) -> Dict[str, int]:
        """Extract material types for all products"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'materials_extracted': 0,
            'errors': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all products with their data
            cursor.execute('''
                SELECT 
                    p.id,
                    COALESCE(NULLIF(p.amazon_title, ''), p.title) as source_title,
                    p.description,
                    GROUP_CONCAT(af.feature_text, ' ') as amazon_features
                FROM products p
                LEFT JOIN amazon_features af ON p.id = af.product_id
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
                    description = product[2] or ''
                    amazon_features = product[3] or ''
                    
                    # Extract material type
                    material = self._extract_material_type(title, description, amazon_features)
                    
                    # Update database
                    cursor.execute('''
                        UPDATE products 
                        SET material = ? 
                        WHERE id = ?
                    ''', (material, product_id))
                    
                    stats['processed_products'] += 1
                    if material:
                        stats['materials_extracted'] += 1
                    
                    print(f"✅ Product {product_id}: material = '{material}'")
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    stats['errors'] += 1
                    continue
            
            conn.commit()
        
        return stats
    
    def _extract_material_type(self, title: str, description: str, amazon_features: str) -> Optional[str]:
        """Extract fabric/material type from product text"""
        # Combine all text for analysis
        combined_text = f"{title} {description} {amazon_features}".lower()
        
        # Enhanced fabric type extraction
        fabric_patterns = {
            'egyptian cotton': 'Egyptian Cotton',
            'organic cotton': 'Organic Cotton', 
            '100% cotton': 'Cotton',
            'cotton': 'Cotton',
            'bamboo': 'Bamboo',
            'bamboo viscose': 'Bamboo Viscose',
            'linen': 'Linen',
            'silk': 'Silk',
            'microfiber': 'Microfiber',
            'polyester': 'Polyester',
            'tencel': 'Tencel',
            'eucalyptus': 'Eucalyptus',
            'modal': 'Modal',
            'rayon': 'Rayon',
            'flannel': 'Flannel',
            'jersey': 'Jersey'
        }
        
        # Search for fabric patterns (prioritize more specific matches)
        for pattern, fabric in fabric_patterns.items():
            if pattern in combined_text:
                return fabric
        
        # If no specific fabric found, try generic material detection
        if any(word in combined_text for word in ['cotton', 'fabric', 'textile']):
            return 'Cotton'
        
        return None
    
    def extract_material_for_product(self, product_id: int) -> Optional[str]:
        """Extract material type for a specific product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT 
                    COALESCE(NULLIF(amazon_title, ''), title) as source_title,
                    description,
                    amazon_features
                FROM products 
                WHERE id = ?
            ''', (product_id,))
            
            result = cursor.fetchone()
            if not result:
                return None
            
            title, description, amazon_features = result
            return self._extract_material_type(title or '', description or '', amazon_features or '')

def main():
    """Main function"""
    print("🧵 Material Extractor")
    print("=" * 50)
    
    extractor = MaterialExtractor()
    results = extractor.extract_all_materials()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Total products: {results['total_products']}")
    print(f"Processed products: {results['processed_products']}")
    print(f"Materials extracted: {results['materials_extracted']}")
    print(f"Errors: {results['errors']}")
    
    print(f"\n🎉 Material extraction complete!")

if __name__ == "__main__":
    main()
