#!/usr/bin/env python3
"""
Script to update existing products with improved data extraction
Extracts material, color, size, ingredients, dimensions, and improves summaries
"""

import sqlite3
import requests
from bs4 import BeautifulSoup
import re
import time
from typing import Dict, Any, Optional, List

class ProductDataUpdater:
    """Update existing products with improved data extraction"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
    
    def _rate_limit(self):
        """Rate limiting to avoid being blocked"""
        time.sleep(1)
    
    def _extract_material(self, soup: BeautifulSoup, title: str, description: str) -> str:
        """Extract material/fabric type from product page"""
        material_keywords = {
            'cotton': ['cotton', '100% cotton', 'pure cotton'],
            'egyptian cotton': ['egyptian cotton', 'egyptian', 'supima cotton'],
            'bamboo': ['bamboo', 'bamboo viscose', 'bamboo rayon'],
            'linen': ['linen', 'flax'],
            'sateen': ['sateen', 'sateen weave'],
            'percale': ['percale', 'percale weave'],
            'microfiber': ['microfiber', 'micro fiber', 'micro-fiber'],
            'silk': ['silk', 'mulberry silk'],
            'polyester': ['polyester', 'poly'],
            'blend': ['blend', 'mixed', 'combination']
        }
        
        # Combine title and description for analysis
        text_to_analyze = f"{title} {description}".lower()
        
        # Look for material keywords
        for material, keywords in material_keywords.items():
            for keyword in keywords:
                if keyword in text_to_analyze:
                    return material.title()
        
        # Check product specifications table
        spec_tables = soup.find_all('table', {'id': 'productDetails_detailBullets_sections1'})
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True).lower()
                    
                    if 'material' in label or 'fabric' in label or 'composition' in label:
                        for material, keywords in material_keywords.items():
                            for keyword in keywords:
                                if keyword in value:
                                    return material.title()
        
        # Check bullet points
        bullet_points = soup.find_all('span', {'class': 'a-list-item'})
        for bullet in bullet_points:
            text = bullet.get_text(strip=True).lower()
            for material, keywords in material_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        return material.title()
        
        return 'Unknown'
    
    def _extract_color(self, soup: BeautifulSoup, title: str) -> str:
        """Extract color from product page"""
        colors = [
            'white', 'black', 'gray', 'grey', 'beige', 'cream', 'ivory',
            'blue', 'navy', 'royal blue', 'sky blue', 'light blue',
            'red', 'burgundy', 'maroon', 'pink', 'rose',
            'green', 'forest green', 'sage', 'mint', 'olive',
            'yellow', 'gold', 'champagne', 'tan', 'brown',
            'purple', 'lavender', 'plum', 'charcoal', 'silver'
        ]
        
        # Check title first
        title_lower = title.lower()
        for color in colors:
            if color in title_lower:
                return color.title()
        
        # Check color selection buttons
        color_buttons = soup.find_all(['button', 'span'], {'class': lambda x: x and 'color' in x.lower()})
        for button in color_buttons:
            text = button.get_text(strip=True)
            for color in colors:
                if color in text.lower():
                    return color.title()
        
        return 'Unknown'
    
    def _extract_size(self, soup: BeautifulSoup, title: str) -> str:
        """Extract size from product page"""
        size_patterns = [
            r'(twin|twin xl)',
            r'(full|double)',
            r'(queen)',
            r'(king|california king)',
            r'(king xl)',
            r'(\d+["\']?\s*x\s*\d+["\']?)',  # Dimensions like 60" x 80"
            r'(\d+\s*inch)',  # Single dimension
        ]
        
        # Check title first
        title_lower = title.lower()
        for pattern in size_patterns:
            match = re.search(pattern, title_lower)
            if match:
                return match.group(1).title()
        
        # Check size selection
        size_elements = soup.find_all(['button', 'span'], {'class': lambda x: x and 'size' in x.lower()})
        for element in size_elements:
            text = element.get_text(strip=True)
            for pattern in size_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    return match.group(1).title()
        
        return 'Unknown'
    
    def _extract_ingredients(self, soup: BeautifulSoup, description: str) -> str:
        """Extract ingredients from product page"""
        if description:
            desc_lower = description.lower()
            if 'ingredients' in desc_lower or 'composition' in desc_lower:
                lines = description.split('\n')
                for line in lines:
                    if 'ingredients' in line.lower() or 'composition' in line.lower():
                        return line.strip()
        
        details = soup.find_all('div', {'id': 'detailBullets_feature_div'})
        for detail in details:
            text = detail.get_text(strip=True)
            if 'ingredients' in text.lower() or 'composition' in text.lower():
                return text
        
        return 'Not specified'
    
    def _extract_dimensions(self, soup: BeautifulSoup) -> str:
        """Extract dimensions from product page"""
        dimension_patterns = [
            r'(\d+["\']?\s*x\s*\d+["\']?\s*x\s*\d+["\']?)',  # 3D dimensions
            r'(\d+["\']?\s*x\s*\d+["\']?)',  # 2D dimensions
            r'(\d+\s*inch)',  # Single dimension
        ]
        
        page_text = soup.get_text()
        for pattern in dimension_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return 'Not specified'
    
    def update_product_data(self, product_id: int, url: str) -> bool:
        """Update a single product with improved data extraction"""
        try:
            print(f"   🔍 Updating product {product_id}...")
            
            # Rate limiting
            self._rate_limit()
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for bot detection
            if "Robot Check" in response.text or "captcha" in response.text.lower():
                print(f"   ⚠️  Bot detection detected, skipping...")
                return False
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Get current product data
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT title, description FROM products WHERE id = ?", (product_id,))
                result = cursor.fetchone()
                
                if not result:
                    print(f"   ❌ Product {product_id} not found")
                    return False
                
                title, description = result
                
                # Extract new data
                material = self._extract_material(soup, title, description or '')
                color = self._extract_color(soup, title)
                size = self._extract_size(soup, title)
                ingredients = self._extract_ingredients(soup, description or '')
                dimensions = self._extract_dimensions(soup)
                
                # Update database
                cursor.execute("""
                    UPDATE products 
                    SET material = ?, color = ?, size = ?, ingredients = ?, dimensions = ?
                    WHERE id = ?
                """, (material, color, size, ingredients, dimensions, product_id))
                
                conn.commit()
                
                print(f"   ✅ Updated: Material={material}, Color={color}, Size={size}")
                return True
                
        except Exception as e:
            print(f"   ❌ Error updating product {product_id}: {e}")
            return False
    
    def update_all_products(self):
        """Update all products with improved data extraction"""
        print("🔄 Updating existing products with improved data extraction...")
        print("=" * 60)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products with affiliate links
                cursor.execute("""
                    SELECT p.id, p.title, al.affiliate_url
                    FROM products p
                    JOIN affiliate_links al ON p.id = al.product_id
                    WHERE al.affiliate_url IS NOT NULL
                    ORDER BY p.id
                """)
                
                products = cursor.fetchall()
                print(f"📊 Found {len(products)} products to update")
                
                updated_count = 0
                for i, (product_id, title, url) in enumerate(products, 1):
                    print(f"\n[{i}/{len(products)}] Processing: {title[:50]}...")
                    
                    if self.update_product_data(product_id, url):
                        updated_count += 1
                
                print(f"\n✅ Successfully updated {updated_count}/{len(products)} products")
                
        except Exception as e:
            print(f"❌ Error: {e}")

if __name__ == "__main__":
    updater = ProductDataUpdater()
    updater.update_all_products()
