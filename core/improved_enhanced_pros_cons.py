#!/usr/bin/env python3
"""
Improved Enhanced Pros and Cons System
Uses structured pros/cons list instead of free text
"""

import sqlite3
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class ImprovedEnhancedProsCons:
    """Enhanced pros/cons system using structured predefined lists"""
    
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
            # Fallback: create basic lists
            self.pros_list = [
                'Softness', 'Breathability', 'Durability', 'Easy Care', 'Luxurious Feel',
                'Temperature Regulation', 'Moisture-Wicking', 'Trusted Brand', 'Popular Choice'
            ]
            self.cons_list = [
                'Wrinkles Easily', 'Higher Price Point', 'Sleeps Warm', 'Can Feel Rough at First',
                'Needs Gentle Care', 'Colors Fade with Washing', 'Can Pill Over Time'
            ]
            print(f"✅ Using fallback lists: {len(self.pros_list)} pros and {len(self.cons_list)} cons")
    
    def enhance_all_products(self) -> Dict[str, int]:
        """Enhance pros/cons for all products using structured lists"""
        stats = {
            'total_products': 0,
            'enhanced_products': 0,
            'total_features_enhanced': 0,
            'errors': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products
                cursor.execute("SELECT id, pretty_title FROM products")
                products = cursor.fetchall()
                stats['total_products'] = len(products)
                
                for product_id, title in products:
                    try:
                        enhanced_count = self._enhance_product_features(product_id, title, cursor)
                        if enhanced_count > 0:
                            stats['enhanced_products'] += 1
                            stats['total_features_enhanced'] += enhanced_count
                        
                    except Exception as e:
                        print(f"⚠️  Error enhancing product {product_id}: {e}")
                        stats['errors'] += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _enhance_product_features(self, product_id: int, title: str, cursor) -> int:
        """Enhance features for a single product"""
        enhanced_count = 0
        
        # Get existing features
        cursor.execute("""
            SELECT feature_text, feature_type, display_order
            FROM product_features
            WHERE product_id = ? AND category IS NULL
        """, (product_id,))
        
        features = cursor.fetchall()
        
        if not features:
            return 0
        
        # Analyze product title for context
        title_lower = title.lower()
        
        for feature_text, feature_type, display_order in features:
            # Map to structured pros/cons
            mapped_features = self._map_to_structured_features(
                feature_text, feature_type, title_lower
            )
            
            if mapped_features:
                # Update with structured features
                for mapped_feature in mapped_features:
                    category = self._categorize_structured_feature(mapped_feature)
                    importance = self._determine_structured_importance(mapped_feature, feature_type)
                    impact_score = self._calculate_structured_impact(mapped_feature, feature_type)
                    
                    # Update the feature
                    cursor.execute("""
                        UPDATE product_features
                        SET feature_text = ?, category = ?, importance = ?, 
                            impact_score = ?, ai_generated = TRUE
                        WHERE product_id = ? AND display_order = ? AND feature_type = ?
                    """, (mapped_feature, category, importance, impact_score, 
                          product_id, display_order, feature_type))
                    
                    enhanced_count += 1
        
        return enhanced_count
    
    def _map_to_structured_features(self, feature_text: str, feature_type: str, title_context: str) -> List[str]:
        """Map free-text feature to structured pros/cons list"""
        feature_lower = feature_text.lower()
        mapped_features = []
        
        # Choose appropriate list based on feature type
        target_list = self.pros_list if feature_type == 'pro' else self.cons_list
        
        # Direct keyword matching
        for structured_feature in target_list:
            if self._is_feature_match(feature_lower, structured_feature.lower(), title_context):
                mapped_features.append(structured_feature)
        
        # If no direct match, try semantic matching
        if not mapped_features:
            semantic_match = self._semantic_match(feature_lower, target_list, title_context)
            if semantic_match:
                mapped_features.append(semantic_match)
        
        # If still no match, keep original but enhance it
        if not mapped_features:
            mapped_features.append(feature_text)
        
        return mapped_features
    
    def _is_feature_match(self, feature_text: str, structured_feature: str, title_context: str) -> bool:
        """Check if feature text matches structured feature"""
        # Direct word match
        if structured_feature in feature_text:
            return True
        
        # Keyword matching
        structured_words = structured_feature.split()
        feature_words = feature_text.split()
        
        # Check if most words from structured feature appear in feature text
        matches = sum(1 for word in structured_words if word in feature_text)
        if matches >= len(structured_words) * 0.6:  # 60% word match
            return True
        
        # Context-specific matching
        if self._context_match(feature_text, structured_feature, title_context):
            return True
        
        return False
    
    def _context_match(self, feature_text: str, structured_feature: str, title_context: str) -> bool:
        """Context-specific matching based on product type"""
        # Sheet-specific matching
        if 'sheet' in title_context:
            sheet_mappings = {
                'softness': ['soft', 'smooth', 'silky', 'buttery'],
                'breathability': ['breathable', 'cooling', 'airflow'],
                'durability': ['durable', 'long-lasting', 'strong'],
                'wrinkle resistance': ['wrinkle', 'wrinkle-free', 'smooth'],
                'easy care': ['easy care', 'machine wash', 'low maintenance'],
                'temperature regulation': ['cooling', 'warmth', 'temperature'],
                'moisture-wicking': ['moisture', 'wicking', 'dry'],
                'hypoallergenic': ['hypoallergenic', 'allergy', 'sensitive'],
                'wrinkles easily': ['wrinkle', 'wrinkles', 'creases'],
                'sleeps warm': ['warm', 'hot', 'heat'],
                'can pill over time': ['pill', 'pilling', 'fuzz'],
                'needs gentle care': ['gentle', 'delicate', 'care'],
                'colors fade with washing': ['fade', 'color', 'washing'],
                'may shrink if not laundered properly': ['shrink', 'laundry', 'wash']
            }
            
            if structured_feature in sheet_mappings:
                keywords = sheet_mappings[structured_feature]
                if any(keyword in feature_text for keyword in keywords):
                    return True
        
        return False
    
    def _semantic_match(self, feature_text: str, target_list: List[str], title_context: str) -> Optional[str]:
        """Semantic matching for features"""
        # Define semantic groups
        semantic_groups = {
            'comfort': ['softness', 'breathability', 'temperature regulation', 'moisture-wicking'],
            'quality': ['durability', 'easy care', 'luxurious feel', 'heirloom quality'],
            'appearance': ['timeless style', 'natural texture', 'crisp finish', 'silken sheen'],
            'care': ['easy care', 'wrinkle resistance', 'quick drying', 'gentle on skin'],
            'value': ['trusted brand', 'popular choice', 'free returns', 'lasts for years'],
            'problems': ['wrinkles easily', 'can feel rough at first', 'higher price point', 'sleeps warm']
        }
        
        # Find which group the feature text belongs to
        for group, features in semantic_groups.items():
            if any(keyword in feature_text for keyword in group.split()):
                # Return the first matching feature from the group
                for feature in features:
                    if feature in target_list:
                        return feature
        
        return None
    
    def _categorize_structured_feature(self, feature: str) -> str:
        """Categorize structured feature"""
        feature_lower = feature.lower()
        
        # Quality features
        quality_keywords = ['durability', 'luxurious', 'premium', 'heirloom', 'lasts', 'strong']
        if any(keyword in feature_lower for keyword in quality_keywords):
            return 'quality'
        
        # Comfort features
        comfort_keywords = ['softness', 'breathability', 'comfort', 'cooling', 'warmth', 'gentle']
        if any(keyword in feature_lower for keyword in comfort_keywords):
            return 'comfort'
        
        # Care features
        care_keywords = ['easy care', 'wrinkle', 'drying', 'washing', 'maintenance']
        if any(keyword in feature_lower for keyword in care_keywords):
            return 'care'
        
        # Design features
        design_keywords = ['style', 'texture', 'finish', 'sheen', 'appeal', 'color']
        if any(keyword in feature_lower for keyword in design_keywords):
            return 'design'
        
        # Value features
        value_keywords = ['brand', 'popular', 'returns', 'price', 'affordable']
        if any(keyword in feature_lower for keyword in value_keywords):
            return 'value'
        
        return 'other'
    
    def _determine_structured_importance(self, feature: str, feature_type: str) -> str:
        """Determine importance for structured feature"""
        feature_lower = feature.lower()
        
        # High importance features
        high_importance = [
            'durability', 'softness', 'breathability', 'easy care', 
            'temperature regulation', 'luxurious feel', 'trusted brand'
        ]
        
        if any(keyword in feature_lower for keyword in high_importance):
            return 'high'
        
        # Critical cons
        if feature_type == 'con' and any(keyword in feature_lower for keyword in 
                                       ['wrinkles easily', 'sleeps warm', 'higher price point']):
            return 'high'
        
        # Medium importance
        medium_importance = [
            'moisture-wicking', 'wrinkle resistance', 'hypoallergenic', 
            'natural texture', 'timeless style', 'popular choice'
        ]
        
        if any(keyword in feature_lower for keyword in medium_importance):
            return 'medium'
        
        return 'medium'  # Default
    
    def _calculate_structured_impact(self, feature: str, feature_type: str) -> float:
        """Calculate impact score for structured feature"""
        base_score = 0.7 if feature_type == 'pro' else -0.7
        
        feature_lower = feature.lower()
        
        # High impact features
        high_impact_pros = ['durability', 'softness', 'breathability', 'luxurious feel']
        high_impact_cons = ['wrinkles easily', 'sleeps warm', 'higher price point']
        
        if (feature_type == 'pro' and any(keyword in feature_lower for keyword in high_impact_pros)) or \
           (feature_type == 'con' and any(keyword in feature_lower for keyword in high_impact_cons)):
            return base_score * 1.2
        
        # Medium impact features
        medium_impact = ['easy care', 'temperature regulation', 'wrinkle resistance', 'trusted brand']
        
        if any(keyword in feature_lower for keyword in medium_impact):
            return base_score * 1.0
        
        return base_score * 0.8  # Lower impact
    
    def add_missing_structured_features(self, product_id: int) -> int:
        """Add missing structured features based on product characteristics"""
        added_count = 0
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get product info
                cursor.execute("""
                    SELECT title, brand, material, price, rating
                    FROM products WHERE id = ?
                """, (product_id,))
                
                product_info = cursor.fetchone()
                if not product_info:
                    return 0
                
                title, brand, material, price, rating = product_info
                title_lower = title.lower()
                
                # Determine relevant features based on product characteristics
                relevant_features = self._get_relevant_features(title_lower, material, price, rating)
                
                # Add missing features
                for feature_type, features in relevant_features.items():
                    for feature in features:
                        # Check if feature already exists
                        cursor.execute("""
                            SELECT COUNT(*) FROM product_features
                            WHERE product_id = ? AND feature_text = ? AND feature_type = ?
                        """, (product_id, feature, feature_type))
                        
                        if cursor.fetchone()[0] == 0:
                            # Add new feature
                            category = self._categorize_structured_feature(feature)
                            importance = self._determine_structured_importance(feature, feature_type)
                            impact_score = self._calculate_structured_impact(feature, feature_type)
                            
                            cursor.execute("""
                                INSERT INTO product_features 
                                (product_id, feature_text, feature_type, category, importance, 
                                 impact_score, ai_generated, display_order)
                                VALUES (?, ?, ?, ?, ?, ?, TRUE, 
                                        (SELECT COALESCE(MAX(display_order), 0) + 1 
                                         FROM product_features WHERE product_id = ?))
                            """, (product_id, feature, feature_type, category, importance, 
                                  impact_score, product_id))
                            
                            added_count += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"⚠️  Error adding features for product {product_id}: {e}")
        
        return added_count
    
    def _get_relevant_features(self, title_lower: str, material: str, price: float, rating: float) -> Dict[str, List[str]]:
        """Get relevant features based on product characteristics"""
        features = {'pro': [], 'con': []}
        
        # Material-based features
        if material:
            material_lower = material.lower()
            
            if 'cotton' in material_lower:
                features['pro'].extend(['Softness', 'Breathability', 'Natural Texture'])
                features['con'].extend(['Wrinkles Easily', 'Can Feel Rough at First'])
            
            if 'sateen' in material_lower:
                features['pro'].extend(['Luxurious Feel', 'Silky Drape', 'Silken Sheen'])
                features['con'].extend(['Less Silky Than Sateen', 'Can Trap Heat'])
            
            if 'linen' in material_lower:
                features['pro'].extend(['Breathability', 'Natural Texture', 'Durability'])
                features['con'].extend(['Wrinkles Easily', 'Can Feel Rough at First'])
            
            if 'bamboo' in material_lower:
                features['pro'].extend(['Softness', 'Moisture-Wicking', 'Eco-Friendly'])
                features['con'].extend(['Higher Price Point', 'Needs Gentle Care'])
        
        # Thread count features
        if 'thread' in title_lower:
            features['pro'].extend(['Luxurious Feel', 'Durability'])
            features['con'].extend(['Higher Price Point'])
        
        # Price-based features
        if price and price > 100:
            features['con'].append('Higher Price Point')
        elif price and price < 50:
            features['pro'].append('Affordable')
        
        # Rating-based features
        if rating and rating >= 4.5:
            features['pro'].extend(['Trusted Brand', 'Popular Choice'])
        elif rating and rating < 3.5:
            features['con'].append('New Brand')
        
        # Size-based features
        if 'king' in title_lower or 'queen' in title_lower:
            features['pro'].append('Year-Round Comfort')
        
        return features


def main():
    """Main function to run the improved enhanced pros/cons system"""
    db_path = "multi_platform_products.db"
    pros_cons_file = "pros_cons"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    if not Path(pros_cons_file).exists():
        print(f"❌ Pros/cons file not found: {pros_cons_file}")
        return
    
    print("🚀 Starting Improved Enhanced Pros/Cons System")
    print("=" * 50)
    
    # Initialize system
    system = ImprovedEnhancedProsCons(db_path, pros_cons_file)
    
    # Enhance all products
    print("\n📊 Enhancing all products...")
    stats = system.enhance_all_products()
    
    print(f"\n✅ Enhancement Complete!")
    print(f"   Total Products: {stats['total_products']}")
    print(f"   Enhanced Products: {stats['enhanced_products']}")
    print(f"   Total Features Enhanced: {stats['total_features_enhanced']}")
    print(f"   Errors: {stats['errors']}")
    
    # Show sample results
    print("\n📋 Sample Enhanced Features:")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.pretty_title, pf.feature_text, pf.category, pf.importance, pf.impact_score
                FROM products p
                JOIN product_features pf ON p.id = pf.product_id
                WHERE pf.ai_generated = 1 AND pf.category IS NOT NULL
                ORDER BY pf.impact_score DESC
                LIMIT 10
            """)
            
            results = cursor.fetchall()
            for title, feature, category, importance, impact in results:
                print(f"   {title}: {feature} ({category}, {importance}, {impact:.2f})")
                
    except Exception as e:
        print(f"⚠️  Error showing results: {e}")


if __name__ == "__main__":
    main()
