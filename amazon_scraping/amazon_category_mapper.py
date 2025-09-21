#!/usr/bin/env python3
"""
Amazon Category Mapper
Maps Amazon's category hierarchy to our database structure
"""

import sqlite3
import json
from typing import Dict, List, Optional, Tuple

class AmazonCategoryMapper:
    """Maps Amazon categories to our database structure"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Amazon category mapping to our parent categories
        self.amazon_to_parent_mapping = {
            # Bed Sheets
            'Sheet & Pillowcase Sets': 'Bed Sheets',
            'Sheets & Pillowcases': 'Bed Sheets',
            'Bed Sheets': 'Bed Sheets',
            'Fitted Sheets': 'Bed Sheets',
            'Flat Sheets': 'Bed Sheets',
            'Pillowcases': 'Bed Sheets',
            
            # Pillows
            'Bed Pillows': 'Pillows',
            'Pillows': 'Pillows',
            'Pillow Protectors': 'Pillows',
            
            # Comforters & Duvets
            'Comforters': 'Comforters & Duvets',
            'Duvet Covers': 'Comforters & Duvets',
            'Duvet Inserts': 'Comforters & Duvets',
            'Quilts': 'Comforters & Duvets',
            'Bedspreads': 'Comforters & Duvets',
            
            # Blankets & Throws
            'Blankets': 'Blankets & Throws',
            'Throws': 'Blankets & Throws',
            'Weighted Blankets': 'Blankets & Throws',
            
            # Mattress Accessories
            'Mattress Protectors': 'Mattress Accessories',
            'Mattress Pads': 'Mattress Accessories',
            'Mattress Toppers': 'Mattress Accessories',
            
            # Non-Bedding
            'Bath Towels': 'Non-Bedding',
            'Bath Sheets': 'Non-Bedding',
            'Hand Towels': 'Non-Bedding',
            'Washcloths': 'Non-Bedding',
            'Clothing': 'Non-Bedding',
            'Sleepwear': 'Non-Bedding',
            'Pajamas': 'Non-Bedding'
        }
    
    def map_amazon_category(self, amazon_breadcrumbs: List[str], amazon_category_path: str) -> Tuple[str, str, str]:
        """
        Map Amazon category to our database structure
        Returns: (category_name, parent_category, source)
        """
        if not amazon_breadcrumbs:
            return 'General Bedding', 'Bedding', 'amazon'
        
        # Get the most specific category (last in breadcrumbs)
        specific_category = amazon_breadcrumbs[-1] if amazon_breadcrumbs else 'General Bedding'
        
        # Map to our parent category
        parent_category = self.amazon_to_parent_mapping.get(specific_category, 'Bedding')
        
        # Handle special cases
        if 'Sheet' in specific_category and 'Set' in specific_category:
            category_name = 'Sheet Sets'
        elif 'Sheet' in specific_category:
            category_name = 'Individual Sheets'
        elif 'Pillow' in specific_category:
            category_name = 'Bed Pillows'
        elif 'Comforter' in specific_category:
            category_name = 'Comforters'
        elif 'Duvet' in specific_category:
            category_name = 'Duvet Inserts'
        elif 'Quilt' in specific_category:
            category_name = 'Quilts'
        elif 'Blanket' in specific_category:
            category_name = 'Bed Blankets'
        elif 'Mattress' in specific_category:
            category_name = 'Mattress Protectors'
        elif 'Bath' in specific_category or 'Towel' in specific_category:
            category_name = 'Bath Towels'
            parent_category = 'Non-Bedding'
        elif 'Clothing' in specific_category or 'Sleepwear' in specific_category or 'Pajama' in specific_category:
            category_name = 'Clothing'
            parent_category = 'Non-Bedding'
        else:
            # Use the specific category name
            category_name = specific_category
        
        return category_name, parent_category, 'amazon'
    
    def update_product_categories_from_amazon(self, product_id: int, amazon_breadcrumbs: List[str], amazon_category_path: str):
        """Update product categories based on Amazon data"""
        category_name, parent_category, source = self.map_amazon_category(amazon_breadcrumbs, amazon_category_path)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing categories for this product
            cursor.execute("DELETE FROM product_categories WHERE product_id = ?", (product_id,))
            
            # Insert new Amazon-based category
            cursor.execute("""
                INSERT INTO product_categories (
                    product_id, category_name, parent_category, category_level, 
                    is_primary, amazon_category_path, amazon_breadcrumbs, source
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id, category_name, parent_category, 3, 1,
                amazon_category_path, json.dumps(amazon_breadcrumbs), source
            ))
            
            conn.commit()
    
    def get_amazon_category_stats(self) -> Dict[str, int]:
        """Get statistics on Amazon categories"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT 
                    source,
                    parent_category,
                    COUNT(DISTINCT product_id) as product_count
                FROM product_categories 
                GROUP BY source, parent_category
                ORDER BY source, product_count DESC
            """)
            
            stats = {}
            for row in cursor.fetchall():
                source, parent, count = row
                key = f"{source}_{parent}"
                stats[key] = count
            
            return stats

def main():
    """Test the Amazon category mapper"""
    mapper = AmazonCategoryMapper()
    
    # Test with sample Amazon data
    test_breadcrumbs = ["Home & Kitchen", "›", "Bedding", "›", "Sheets & Pillowcases", "›", "Sheet & Pillowcase Sets"]
    test_path = "Home & Kitchen > Bedding > Sheets & Pillowcases > Sheet & Pillowcase Sets"
    
    category_name, parent_category, source = mapper.map_amazon_category(test_breadcrumbs, test_path)
    
    print(f"Amazon Breadcrumbs: {test_breadcrumbs}")
    print(f"Category Name: {category_name}")
    print(f"Parent Category: {parent_category}")
    print(f"Source: {source}")

if __name__ == "__main__":
    main()
