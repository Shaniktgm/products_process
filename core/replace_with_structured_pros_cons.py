#!/usr/bin/env python3
"""
Replace existing pros/cons with structured ones from pros_cons file
"""

import sqlite3
import json
from typing import List, Dict, Any
from pathlib import Path


class StructuredProsConsReplacer:
    """Replace existing features with structured pros/cons"""
    
    def __init__(self, db_path: str, pros_cons_file: str = "pros_cons"):
        self.db_path = db_path
        self.pros_cons_file = pros_cons_file
        self.pros_list = []
        self.cons_list = []
        self._load_pros_cons_lists()
    
    def _load_pros_cons_lists(self):
        """Load pros and cons from the pros_cons file"""
        try:
            with open(self.pros_cons_file, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Split into pros and cons sections
            sections = content.split('cons:')
            if len(sections) != 2:
                raise ValueError("Invalid pros_cons file format")
            
            # Parse pros
            pros_section = sections[0].replace('pros:', '').strip()
            self.pros_list = [line.strip() for line in pros_section.split('\n') 
                             if line.strip() and not line.strip().startswith('#')]
            
            # Parse cons
            cons_section = sections[1].strip()
            self.cons_list = [line.strip() for line in cons_section.split('\n') 
                             if line.strip() and not line.strip().startswith('#')]
            
            print(f"✅ Loaded {len(self.pros_list)} pros and {len(self.cons_list)} cons")
            
        except Exception as e:
            print(f"❌ Error loading pros_cons file: {e}")
            self.pros_list = []
            self.cons_list = []
    
    def replace_all_product_features(self) -> Dict[str, int]:
        """Replace all product features with structured pros/cons"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'total_features_replaced': 0,
            'errors': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products
                cursor.execute("SELECT id, pretty_title, material, brand, price, rating FROM products")
                products = cursor.fetchall()
                stats['total_products'] = len(products)
                
                for product_id, title, material, brand, price, rating in products:
                    try:
                        replaced_count = self._replace_product_features(
                            product_id, title, material, brand, price, rating, cursor
                        )
                        if replaced_count > 0:
                            stats['processed_products'] += 1
                            stats['total_features_replaced'] += replaced_count
                        
                    except Exception as e:
                        print(f"⚠️  Error processing product {product_id}: {e}")
                        stats['errors'] += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _replace_product_features(self, product_id: int, title: str, material: str, 
                                brand: str, price: float, rating: float, cursor) -> int:
        """Replace features for a single product with structured ones"""
        replaced_count = 0
        
        # Clear existing features
        cursor.execute("DELETE FROM product_features WHERE product_id = ?", (product_id,))
        
        # Generate relevant structured features
        relevant_features = self._get_relevant_structured_features(
            title, material, brand, price, rating
        )
        
        # Insert new structured features
        for feature_type, features in relevant_features.items():
            for i, feature in enumerate(features):
                category = self._categorize_feature(feature)
                importance = self._determine_importance(feature, feature_type)
                impact_score = self._calculate_impact_score(feature, feature_type)
                
                cursor.execute("""
                    INSERT INTO product_features 
                    (product_id, feature_text, feature_type, category, importance, 
                     impact_score, ai_generated, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, TRUE, ?)
                """, (product_id, feature, feature_type, category, importance, 
                      impact_score, i + 1))
                
                replaced_count += 1
        
        return replaced_count
    
    def _get_relevant_structured_features(self, title: str, material: str, 
                                        brand: str, price: float, rating: float) -> Dict[str, List[str]]:
        """Get relevant structured features based on product characteristics"""
        features = {'pro': [], 'con': []}
        title_lower = title.lower()
        
        # Material-based features
        if material:
            material_lower = material.lower()
            
            if 'cotton' in material_lower:
                features['pro'].extend(['Softness', 'Breathability', 'Natural Texture', 'Easy Care'])
                features['con'].extend(['Wrinkles Easily', 'Can Feel Rough at First'])
            
            if 'sateen' in material_lower:
                features['pro'].extend(['Luxurious Feel', 'Silky Drape', 'Silken Sheen'])
                features['con'].extend(['Can Trap Heat'])
            
            if 'linen' in material_lower:
                features['pro'].extend(['Breathability', 'Natural Texture', 'Durability', 'Temperature Regulation'])
                features['con'].extend(['Wrinkles Easily', 'Can Feel Rough at First', 'Needs Gentle Care'])
            
            if 'bamboo' in material_lower:
                features['pro'].extend(['Softness', 'Moisture-Wicking', 'Eco-Friendly', 'Temperature Regulation'])
                features['con'].extend(['Higher Price Point', 'Needs Gentle Care'])
            
            if 'tencel' in material_lower:
                features['pro'].extend(['Softness', 'Moisture-Wicking', 'Temperature Regulation', 'Easy Care'])
                features['con'].extend(['Higher Price Point'])
        
        # Thread count features
        if 'thread' in title_lower:
            features['pro'].extend(['Luxurious Feel', 'Durability'])
            if '1000' in title_lower or '1200' in title_lower:
                features['pro'].append('Premium Quality')
                features['con'].append('Higher Price Point')
        
        # Size-based features
        if 'king' in title_lower or 'queen' in title_lower:
            features['pro'].append('Year-Round Comfort')
        
        if 'twin' in title_lower:
            features['pro'].append('Perfect for Kids')
        
        # Price-based features
        if price:
            if price > 150:
                features['con'].append('Higher Price Point')
                features['pro'].append('Luxury Quality')
            elif price < 50:
                features['pro'].append('Affordable')
            else:
                features['pro'].append('Good Value')
        
        # Rating-based features
        if rating:
            if rating >= 4.5:
                features['pro'].extend(['Trusted Brand', 'Popular Choice'])
            elif rating < 3.5:
                features['con'].append('New Brand')
        
        # Brand-specific features
        if brand:
            brand_lower = brand.lower()
            if 'boll' in brand_lower or 'branch' in brand_lower:
                features['pro'].extend(['Trusted Brand', 'Ethical Manufacturing'])
            elif 'bamboo' in brand_lower:
                features['pro'].extend(['Eco-Friendly', 'Sustainable Fiber'])
        
        # Common sheet features
        features['pro'].extend(['Easy Care', 'Machine Washable'])
        
        # Remove duplicates and limit to reasonable number
        features['pro'] = list(dict.fromkeys(features['pro']))[:8]  # Max 8 pros
        features['con'] = list(dict.fromkeys(features['con']))[:5]  # Max 5 cons
        
        return features
    
    def _categorize_feature(self, feature: str) -> str:
        """Categorize structured feature"""
        feature_lower = feature.lower()
        
        # Quality features
        quality_keywords = ['durability', 'luxurious', 'premium', 'heirloom', 'lasts', 'strong', 'quality']
        if any(keyword in feature_lower for keyword in quality_keywords):
            return 'quality'
        
        # Comfort features
        comfort_keywords = ['softness', 'breathability', 'comfort', 'cooling', 'warmth', 'gentle', 'temperature']
        if any(keyword in feature_lower for keyword in comfort_keywords):
            return 'comfort'
        
        # Care features
        care_keywords = ['easy care', 'wrinkle', 'drying', 'washing', 'maintenance', 'washable']
        if any(keyword in feature_lower for keyword in care_keywords):
            return 'care'
        
        # Design features
        design_keywords = ['style', 'texture', 'finish', 'sheen', 'appeal', 'color', 'drape']
        if any(keyword in feature_lower for keyword in design_keywords):
            return 'design'
        
        # Value features
        value_keywords = ['brand', 'popular', 'returns', 'price', 'affordable', 'value', 'ethical', 'eco-friendly']
        if any(keyword in feature_lower for keyword in value_keywords):
            return 'value'
        
        return 'other'
    
    def _determine_importance(self, feature: str, feature_type: str) -> str:
        """Determine importance for structured feature"""
        feature_lower = feature.lower()
        
        # High importance features
        high_importance = [
            'durability', 'softness', 'breathability', 'easy care', 
            'temperature regulation', 'luxurious feel', 'trusted brand',
            'wrinkles easily', 'sleeps warm', 'higher price point'
        ]
        
        if any(keyword in feature_lower for keyword in high_importance):
            return 'high'
        
        # Medium importance
        medium_importance = [
            'moisture-wicking', 'wrinkle resistance', 'hypoallergenic', 
            'natural texture', 'timeless style', 'popular choice',
            'can feel rough at first', 'needs gentle care'
        ]
        
        if any(keyword in feature_lower for keyword in medium_importance):
            return 'medium'
        
        return 'medium'  # Default
    
    def _calculate_impact_score(self, feature: str, feature_type: str) -> float:
        """Calculate impact score for structured feature"""
        base_score = 0.7 if feature_type == 'pro' else -0.7
        
        feature_lower = feature.lower()
        
        # High impact features
        high_impact_pros = ['durability', 'softness', 'breathability', 'luxurious feel', 'trusted brand']
        high_impact_cons = ['wrinkles easily', 'sleeps warm', 'higher price point']
        
        if (feature_type == 'pro' and any(keyword in feature_lower for keyword in high_impact_pros)) or \
           (feature_type == 'con' and any(keyword in feature_lower for keyword in high_impact_cons)):
            return base_score * 1.2
        
        # Medium impact features
        medium_impact = ['easy care', 'temperature regulation', 'wrinkle resistance', 'popular choice']
        
        if any(keyword in feature_lower for keyword in medium_impact):
            return base_score * 1.0
        
        return base_score * 0.8  # Lower impact


def main():
    """Main function to replace features with structured pros/cons"""
    db_path = "multi_platform_products.db"
    pros_cons_file = "pros_cons"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    if not Path(pros_cons_file).exists():
        print(f"❌ Pros/cons file not found: {pros_cons_file}")
        return
    
    print("🚀 Starting Structured Pros/Cons Replacement")
    print("=" * 50)
    
    # Initialize system
    replacer = StructuredProsConsReplacer(db_path, pros_cons_file)
    
    # Replace all features
    print("\n📊 Replacing all product features...")
    stats = replacer.replace_all_product_features()
    
    print(f"\n✅ Replacement Complete!")
    print(f"   Total Products: {stats['total_products']}")
    print(f"   Processed Products: {stats['processed_products']}")
    print(f"   Total Features Replaced: {stats['total_features_replaced']}")
    print(f"   Errors: {stats['errors']}")
    
    # Show sample results
    print("\n📋 Sample Structured Features:")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.pretty_title, pf.feature_text, pf.feature_type, pf.category, pf.importance, pf.impact_score
                FROM products p
                JOIN product_features pf ON p.id = pf.product_id
                WHERE pf.ai_generated = 1
                ORDER BY p.id, pf.feature_type, pf.impact_score DESC
                LIMIT 15
            """)
            
            results = cursor.fetchall()
            for title, feature, ftype, category, importance, impact in results:
                emoji = "✅" if ftype == 'pro' else "❌"
                print(f"   {emoji} {title}: {feature} ({category}, {importance}, {impact:.2f})")
                
    except Exception as e:
        print(f"⚠️  Error showing results: {e}")


if __name__ == "__main__":
    main()
