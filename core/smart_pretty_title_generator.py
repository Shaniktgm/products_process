#!/usr/bin/env python3
"""
Smart Pretty Title Generator
Creates concise, descriptive product names based on title and description
"""

import sqlite3
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass

@dataclass
class TitleComponent:
    """Component of a pretty title"""
    text: str
    priority: int  # Higher number = higher priority
    category: str  # brand, size, material, type, feature, etc.

class SmartPrettyTitleGenerator:
    """Generates intelligent, concise pretty titles (max 8 words)"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
    
    def generate_all_pretty_titles(self) -> Dict[str, int]:
        """Generate smart pretty titles for all products"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'titles_generated': 0,
            'errors': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all products with their data (prefer Amazon API title/brand when available)
            cursor.execute('''
                SELECT 
                    p.id,
                    COALESCE(NULLIF(p.amazon_title, ''), p.title) as source_title,
                    p.product_summary,
                    p.material, p.weave_type, p.thread_count,
                    p.amazon_brand as source_brand,
                    p.amazon_asin
                FROM products p
                WHERE COALESCE(NULLIF(p.amazon_title, ''), p.title) IS NOT NULL
                  AND COALESCE(NULLIF(p.amazon_title, ''), p.title) != ''
                ORDER BY p.id
            ''')
            
            products = cursor.fetchall()
            stats['total_products'] = len(products)
            
            for product in products:
                try:
                    product_id = product[0]
                    raw_title = product[1] or ''
                    summary = product[2] or ''
                    material = product[3] or ''
                    weave_type = product[4] or ''
                    thread_count = product[5]
                    brand = product[6] or ''
                    asin = product[7] or ''

                    # Clean generic placeholders from titles like "Amazon Product" and ASIN tokens
                    title = self._clean_generic_title(raw_title, asin)
                    
                    # Generate smart pretty title
                    pretty_title = self._generate_smart_pretty_title(
                        title, '', summary, material, weave_type, 
                        thread_count, 'white', 'queen', brand, 50.0, 4.5
                    )
                    
                    # Update database
                    cursor.execute('''
                        UPDATE products 
                        SET pretty_title = ? 
                        WHERE id = ?
                    ''', (pretty_title, product_id))
                    
                    stats['processed_products'] += 1
                    stats['titles_generated'] += 1
                    
                    print(f"✅ Product {product_id}: '{pretty_title}'")
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    stats['errors'] += 1
                    continue
            
            conn.commit()
        
        return stats
    
    def _generate_smart_pretty_title(self, title: str, description: str, summary: str,
                                   material: str, weave_type: str, thread_count: int,
                                   color: str, size: str, brand: str, price: float, 
                                   rating: float) -> str:
        """Generate a smart, concise pretty title (max 10 words) using the most relevant product information"""
        
        # Combine all text for analysis - prioritize description for fabric details
        combined_text = f"{description} {title} {summary}".lower()
        
        # Extract components with priorities - focus on fabric details
        components = []
        
        # 1. Brand (highest priority if available)
        if brand and brand.lower() not in ['unknown', 'visit the', '']:
            clean_brand = self._clean_brand_name(brand)
            if clean_brand:
                components.append(TitleComponent(clean_brand, 100, 'brand'))
        
        # 2. Material/Fabric type (high priority - extract from description if not in material field)
        fabric_type = self._extract_fabric_type(combined_text, material)
        if fabric_type:
            components.append(TitleComponent(fabric_type, 95, 'fabric'))
        
        # 3. Thread count (high priority - extract from description if not in thread_count field)
        extracted_thread_count = self._extract_thread_count_from_text(combined_text, thread_count)
        if extracted_thread_count:
            components.append(TitleComponent(f"{extracted_thread_count} Thread", 90, 'thread_count'))
        
        # 4. Weave type (high priority - extract from description if not in weave_type field)
        extracted_weave = self._extract_weave_from_text(combined_text, weave_type)
        if extracted_weave:
            components.append(TitleComponent(extracted_weave, 85, 'weave'))
        
        # 5. Product type (medium-high priority)
        product_type = self._extract_product_type(combined_text, title)
        if product_type:
            components.append(TitleComponent(product_type, 80, 'type'))
        
        # 6. Size (medium priority)
        if size:
            clean_size = self._clean_size(size)
            if clean_size:
                components.append(TitleComponent(clean_size, 70, 'size'))
        
        # 7. Key features (medium priority)
        features = self._extract_key_features(combined_text)
        for feature in features[:1]:  # Max 1 feature to save space
            components.append(TitleComponent(feature, 60, 'feature'))
        
        # 8. Color (low priority)
        if color:
            clean_color = self._clean_color(color)
            if clean_color:
                components.append(TitleComponent(clean_color, 50, 'color'))
        
        # Sort by priority and build title
        components.sort(key=lambda x: x.priority, reverse=True)
        
        # Build title with max 8 words
        title_words = []
        for component in components:
            component_words = component.text.split()
            if len(title_words) + len(component_words) <= 8:
                title_words.extend(component_words)
            else:
                break
        
        # Join and clean up
        pretty_title = ' '.join(title_words)
        
        # Ensure we have something meaningful
        if not pretty_title or len(pretty_title.split()) < 2:
            # Fallback: extract key words from title and description
            fallback_words = self._extract_fallback_words(title + ' ' + description)
            pretty_title = ' '.join(fallback_words[:8])
        
        return pretty_title

    def _clean_generic_title(self, title: str, asin: str) -> str:
        """Remove generic placeholders like 'Amazon Product' and ASIN tokens from titles."""
        if not title:
            return ''
        cleaned = title.strip()
        # Remove leading generic label
        if cleaned.lower().startswith('amazon product'):
            cleaned = cleaned[len('amazon product'):].strip('-: _')
        # Remove ASIN occurrences
        import re
        asin_pat = asin if asin else ''
        cleaned = re.sub(r"\b[A-Z0-9]{10}\b", "", cleaned).strip()
        if asin_pat:
            cleaned = cleaned.replace(asin_pat, '').strip()
        # Collapse spaces
        cleaned = re.sub(r"\s{2,}", " ", cleaned)
        return cleaned or 'Product'
    
    def _clean_brand_name(self, brand: str) -> str:
        """Clean and standardize brand name"""
        if not brand:
            return ""
        
        brand = brand.strip()
        
        # Remove common prefixes/suffixes
        brand = re.sub(r'\b(visit the|the)\b', '', brand, flags=re.IGNORECASE).strip()
        brand = re.sub(r'\s+', ' ', brand)
        
        # Standardize common brands
        brand_mappings = {
            'boll & branch': 'Boll & Branch',
            'boll and branch': 'Boll & Branch',
            'california design den': 'California Design Den',
            'chateau home': 'Chateau Home',
            'coop home goods': 'Coop Home Goods'
        }
        
        brand_lower = brand.lower()
        for key, value in brand_mappings.items():
            if key in brand_lower:
                return value
        
        return brand.title()
    
    def _extract_product_type(self, text: str, title: str) -> str:
        """Extract the main product type"""
        text_lower = text.lower()
        title_lower = title.lower()
        
        # Priority order for product types
        if any(word in text_lower for word in ['bath towel', 'bath sheet', 'hand towel', 'washcloth']):
            return 'Bath Towel Set'
        elif any(word in text_lower for word in ['sheet set', 'bed sheet set', 'bedding set']):
            return 'Sheet Set'
        elif any(word in text_lower for word in ['fitted sheet', 'flat sheet', 'bed sheet']):
            return 'Bed Sheet'
        elif any(word in text_lower for word in ['pillowcase', 'pillow case']):
            return 'Pillowcase'
        elif any(word in text_lower for word in ['pillow', 'bed pillow']):
            return 'Bed Pillow'
        elif any(word in text_lower for word in ['comforter', 'duvet insert']):
            return 'Comforter'
        elif any(word in text_lower for word in ['duvet cover']):
            return 'Duvet Cover'
        elif any(word in text_lower for word in ['blanket', 'throw blanket']):
            return 'Blanket'
        elif any(word in text_lower for word in ['mattress protector', 'mattress pad']):
            return 'Mattress Protector'
        elif any(word in text_lower for word in ['quilt']):
            return 'Quilt'
        
        return ""
    
    def _clean_size(self, size: str) -> str:
        """Clean and standardize size"""
        if not size:
            return ""
        
        size = size.strip().upper()
        
        # Standardize size names
        size_mappings = {
            'KING': 'King',
            'QUEEN': 'Queen',
            'FULL': 'Full',
            'TWIN': 'Twin',
            'CAL KING': 'Cal King',
            'CALIFORNIA KING': 'Cal King',
            'SPLIT KING': 'Split King',
            'TWIN XL': 'Twin XL'
        }
        
        for key, value in size_mappings.items():
            if key in size:
                return value
        
        return size
    
    def _clean_material(self, material: str) -> str:
        """Clean and standardize material"""
        if not material:
            return ""
        
        material = material.strip()
        
        # Standardize material names
        material_mappings = {
            'egyptian cotton': 'Egyptian Cotton',
            'cotton': 'Cotton',
            'bamboo': 'Bamboo',
            'linen': 'Linen',
            'silk': 'Silk',
            'microfiber': 'Microfiber',
            'polyester': 'Polyester'
        }
        
        material_lower = material.lower()
        for key, value in material_mappings.items():
            if key in material_lower:
                return value
        
        return material.title()
    
    def _clean_weave_type(self, weave_type: str) -> str:
        """Clean and standardize weave type"""
        if not weave_type:
            return ""
        
        weave_type = weave_type.strip()
        
        # Standardize weave names
        weave_mappings = {
            'sateen': 'Sateen',
            'percale': 'Percale',
            'basketweave': 'Basketweave',
            'twill': 'Twill'
        }
        
        weave_lower = weave_type.lower()
        for key, value in weave_mappings.items():
            if key in weave_lower:
                return value
        
        return weave_type.title()
    
    def _extract_key_features(self, text: str) -> List[str]:
        """Extract key features from text"""
        features = []
        text_lower = text.lower()
        
        # Key features to look for
        feature_patterns = {
            'Cooling': ['cooling', 'temperature regulating', 'breathable'],
            'Organic': ['organic', 'certified organic'],
            'Hypoallergenic': ['hypoallergenic', 'allergy free'],
            'Deep Pocket': ['deep pocket', 'deep pockets'],
            'Wrinkle Resistant': ['wrinkle resistant', 'wrinkle-free'],
            'Moisture Wicking': ['moisture wicking', 'wicking'],
            'Antimicrobial': ['antimicrobial', 'antibacterial']
        }
        
        for feature, patterns in feature_patterns.items():
            if any(pattern in text_lower for pattern in patterns):
                features.append(feature)
        
        return features
    
    def _clean_color(self, color: str) -> str:
        """Clean and standardize color"""
        if not color:
            return ""
        
        color = color.strip().title()
        
        # Standardize common colors
        color_mappings = {
            'White': 'White',
            'Ivory': 'Ivory',
            'Cream': 'Cream',
            'Beige': 'Beige',
            'Grey': 'Grey',
            'Gray': 'Grey',
            'Navy': 'Navy',
            'Blue': 'Blue',
            'Green': 'Green',
            'Pink': 'Pink',
            'Yellow': 'Yellow'
        }
        
        for key, value in color_mappings.items():
            if key.lower() in color.lower():
                return value
        
        return color
    
    def _extract_fabric_type(self, text: str, existing_material: str) -> str:
        """Extract fabric type from text, prioritizing description over existing material field"""
        if existing_material and existing_material.lower() not in ['unknown', '']:
            return self._clean_material(existing_material)
        
        # Enhanced fabric type extraction from description
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
            'sateen': 'Sateen',
            'percale': 'Percale'
        }
        
        text_lower = text.lower()
        for pattern, fabric in fabric_patterns.items():
            if pattern in text_lower:
                return fabric
        
        return ""
    
    def _extract_thread_count_from_text(self, text: str, existing_thread_count: int) -> int:
        """Extract thread count from text, prioritizing description over existing field"""
        if existing_thread_count and existing_thread_count > 0:
            return existing_thread_count
        
        # Extract thread count from description
        thread_patterns = [
            r'(\d+)\s*thread\s*count',
            r'(\d+)\s*tc',
            r'(\d+)\s*thread',
            r'thread\s*count[:\s]*(\d+)',
            r'tc[:\s]*(\d+)'
        ]
        
        for pattern in thread_patterns:
            match = re.search(pattern, text, re.IGNORECASE)
            if match:
                try:
                    count = int(match.group(1))
                    if 50 <= count <= 2000:  # Reasonable thread count range
                        return count
                except ValueError:
                    continue
        
        return None
    
    def _extract_weave_from_text(self, text: str, existing_weave: str) -> str:
        """Extract weave type from text, prioritizing description over existing field"""
        if existing_weave and existing_weave.lower() not in ['unknown', '']:
            return self._clean_weave_type(existing_weave)
        
        # Enhanced weave type extraction from description
        weave_patterns = {
            'sateen': 'Sateen',
            'percale': 'Percale',
            'basketweave': 'Basketweave',
            'twill': 'Twill',
            'jersey': 'Jersey',
            'flannel': 'Flannel',
            'oxford': 'Oxford',
            'herringbone': 'Herringbone'
        }
        
        text_lower = text.lower()
        for pattern, weave in weave_patterns.items():
            if pattern in text_lower:
                return weave
        
        return ""
    
    def _extract_fallback_words(self, text: str) -> List[str]:
        """Extract key words as fallback from title and description"""
        if not text:
            return ["Product"]
        
        # Remove common words and extract meaningful terms
        words = re.findall(r'\b[A-Za-z]+\b', text)
        
        # Filter out common words
        stop_words = {
            'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with',
            'by', 'from', 'up', 'about', 'into', 'through', 'during', 'before',
            'after', 'above', 'below', 'between', 'among', 'is', 'are', 'was',
            'were', 'be', 'been', 'being', 'have', 'has', 'had', 'do', 'does',
            'did', 'will', 'would', 'could', 'should', 'may', 'might', 'must',
            'can', 'this', 'that', 'these', 'those', 'a', 'an', 'as', 'if',
            'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few',
            'more', 'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only',
            'own', 'same', 'so', 'than', 'too', 'very', 'just', 'now'
        }
        
        meaningful_words = [word for word in words if word.lower() not in stop_words]
        
        return meaningful_words[:8]  # Max 8 words

def main():
    """Main function"""
    print("🎨 Smart Pretty Title Generator")
    print("=" * 50)
    
    generator = SmartPrettyTitleGenerator()
    results = generator.generate_all_pretty_titles()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Total products: {results['total_products']}")
    print(f"Processed products: {results['processed_products']}")
    print(f"Titles generated: {results['titles_generated']}")
    print(f"Errors: {results['errors']}")
    
    print(f"\n🎉 Smart pretty title generation complete!")

if __name__ == "__main__":
    main()

