#!/usr/bin/env python3
"""
Dynamic Pros & Cons Generator
Generates product-specific pros and cons based on actual product characteristics
"""

import sqlite3
import re
from typing import List, Dict, Any, Optional, Tuple
from pathlib import Path


class DynamicProsConsGenerator:
    """Generate product-specific pros and cons based on actual product data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Initialize tables if needed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Ensure product_features table exists with all needed columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS product_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    feature_text TEXT NOT NULL,
                    feature_type TEXT NOT NULL,
                    category TEXT,
                    importance TEXT,
                    impact_score REAL,
                    ai_generated BOOLEAN DEFAULT FALSE,
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def regenerate_all_product_features(self) -> Dict[str, int]:
        """Regenerate pros/cons for all products based on their unique characteristics"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'total_features_generated': 0,
            'errors': 0
        }
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products with their details
                cursor.execute("""
                    SELECT id, pretty_title, brand, material, price, rating, description
                    FROM products
                    ORDER BY id
                """)
                
                products = cursor.fetchall()
                stats['total_products'] = len(products)
                
                for product_id, title, brand, material, price, rating, description in products:
                    try:
                        generated_count = self._generate_product_specific_features(
                            product_id, title, brand, material, price, rating, description, cursor
                        )
                        if generated_count > 0:
                            stats['processed_products'] += 1
                            stats['total_features_generated'] += generated_count
                        
                    except Exception as e:
                        print(f"⚠️  Error processing product {product_id}: {e}")
                        stats['errors'] += 1
                
                conn.commit()
                
        except Exception as e:
            print(f"❌ Database error: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _generate_product_specific_features(self, product_id: int, title: str, brand: str, 
                                          material: str, price: float, rating: float, 
                                          description: str, cursor) -> int:
        """Generate product-specific features based on actual characteristics"""
        
        # Clear existing features for this product
        cursor.execute("DELETE FROM product_features WHERE product_id = ?", (product_id,))
        
        # Analyze product characteristics
        characteristics = self._analyze_product_characteristics(title, brand, material, price, rating, description)
        
        # Generate pros and cons based on characteristics
        features = self._generate_features_from_characteristics(characteristics)
        
        # Insert new features
        feature_count = 0
        for feature_type, feature_list in features.items():
            for i, feature in enumerate(feature_list):
                category = self._categorize_feature(feature)
                importance = self._determine_importance(feature, feature_type, characteristics)
                impact_score = self._calculate_impact_score(feature, feature_type, characteristics)
                
                cursor.execute("""
                    INSERT INTO product_features 
                    (product_id, feature_text, feature_type, category, importance, 
                     impact_score, ai_generated, display_order)
                    VALUES (?, ?, ?, ?, ?, ?, TRUE, ?)
                """, (product_id, feature, feature_type, category, importance, 
                      impact_score, i + 1))
                
                feature_count += 1
        
        return feature_count
    
    def _analyze_product_characteristics(self, title: str, brand: str, material: str, 
                                       price: float, rating: float, description: str) -> Dict[str, Any]:
        """Analyze product to extract key characteristics"""
        title_lower = title.lower() if title else ""
        description_lower = description.lower() if description else ""
        brand_lower = brand.lower() if brand else ""
        material_lower = material.lower() if material else ""
        
        characteristics = {
            'title': title,
            'brand': brand,
            'material': material,
            'price': price,
            'rating': rating,
            'description': description,
            'size': self._extract_size(title_lower),
            'thread_count': self._extract_thread_count(title_lower, description_lower),
            'weave_type': self._extract_weave_type(title_lower, description_lower),
            'cotton_type': self._extract_cotton_type(description_lower),
            'special_features': self._extract_special_features(description_lower),
            'price_tier': self._categorize_price_tier(price),
            'rating_tier': self._categorize_rating_tier(rating),
            'brand_tier': self._categorize_brand_tier(brand_lower),
            'certifications': self._extract_certifications(description_lower),
            'care_instructions': self._extract_care_instructions(description_lower)
        }
        
        return characteristics
    
    def _extract_size(self, title_lower: str) -> str:
        """Extract bed size from title"""
        if 'king' in title_lower:
            return 'king'
        elif 'queen' in title_lower:
            return 'queen'
        elif 'twin' in title_lower:
            return 'twin'
        elif 'full' in title_lower or 'double' in title_lower:
            return 'full'
        else:
            return 'unknown'
    
    def _extract_thread_count(self, title_lower: str, description_lower: str) -> Optional[int]:
        """Extract thread count from title or description"""
        # Look in title first
        thread_match = re.search(r'(\d+)\s*thread', title_lower)
        if thread_match:
            return int(thread_match.group(1))
        
        # Look in description
        thread_match = re.search(r'(\d+)\s*thread', description_lower)
        if thread_match:
            return int(thread_match.group(1))
        
        return None
    
    def _extract_weave_type(self, title_lower: str, description_lower: str) -> str:
        """Extract weave type (sateen, percale, etc.)"""
        if 'sateen' in title_lower or 'sateen' in description_lower:
            return 'sateen'
        elif 'percale' in title_lower or 'percale' in description_lower:
            return 'percale'
        elif 'jersey' in title_lower or 'jersey' in description_lower:
            return 'jersey'
        else:
            return 'unknown'
    
    def _extract_cotton_type(self, description_lower: str) -> str:
        """Extract cotton type (Supima, Egyptian, etc.)"""
        if 'supima' in description_lower:
            return 'supima'
        elif 'egyptian' in description_lower:
            return 'egyptian'
        elif 'pima' in description_lower:
            return 'pima'
        else:
            return 'regular'
    
    def _extract_special_features(self, description_lower: str) -> List[str]:
        """Extract special features from description"""
        features = []
        
        if 'cooling' in description_lower or 'cool' in description_lower:
            features.append('cooling')
        if 'moisture' in description_lower or 'wicking' in description_lower:
            features.append('moisture-wicking')
        if 'breathable' in description_lower or 'breathability' in description_lower:
            features.append('breathable')
        if 'hypoallergenic' in description_lower:
            features.append('hypoallergenic')
        if 'deep pocket' in description_lower:
            features.append('deep-pocket')
        if 'wrinkle' in description_lower and 'free' in description_lower:
            features.append('wrinkle-resistant')
        if 'pilling' in description_lower and 'resistant' in description_lower:
            features.append('pill-resistant')
        if 'fade' in description_lower and 'resistant' in description_lower:
            features.append('fade-resistant')
        if 'shrink' in description_lower and 'resistant' in description_lower:
            features.append('shrink-resistant')
        
        return features
    
    def _categorize_price_tier(self, price: float) -> str:
        """Categorize price into tiers"""
        if not price:
            return 'unknown'
        elif price < 50:
            return 'budget'
        elif price < 100:
            return 'mid-range'
        elif price < 200:
            return 'premium'
        else:
            return 'luxury'
    
    def _categorize_rating_tier(self, rating: float) -> str:
        """Categorize rating into tiers"""
        if not rating:
            return 'unknown'
        elif rating >= 4.5:
            return 'excellent'
        elif rating >= 4.0:
            return 'very-good'
        elif rating >= 3.5:
            return 'good'
        else:
            return 'poor'
    
    def _categorize_brand_tier(self, brand_lower: str) -> str:
        """Categorize brand into tiers"""
        premium_brands = ['buffy', 'brooklinen', 'parachute', 'snowe', 'coyuchi']
        mid_tier_brands = ['california design den', 'threadmill', 'breescape']
        
        if any(premium in brand_lower for premium in premium_brands):
            return 'premium'
        elif any(mid in brand_lower for mid in mid_tier_brands):
            return 'mid-tier'
        else:
            return 'value'
    
    def _extract_certifications(self, description_lower: str) -> List[str]:
        """Extract certifications from description"""
        certifications = []
        
        if 'oeko-tex' in description_lower:
            certifications.append('oeko-tex')
        if 'gots' in description_lower:
            certifications.append('gots')
        if 'organic' in description_lower:
            certifications.append('organic')
        if 'fair trade' in description_lower:
            certifications.append('fair-trade')
        
        return certifications
    
    def _extract_care_instructions(self, description_lower: str) -> Dict[str, bool]:
        """Extract care instructions from description"""
        care = {
            'machine_washable': 'machine wash' in description_lower,
            'tumble_dry': 'tumble dry' in description_lower,
            'easy_care': 'easy care' in description_lower or 'easy to care' in description_lower,
            'wrinkle_free': 'wrinkle free' in description_lower or 'wrinkle-free' in description_lower
        }
        return care
    
    def _generate_features_from_characteristics(self, characteristics: Dict[str, Any]) -> Dict[str, List[str]]:
        """Generate pros and cons based on product characteristics"""
        features = {'pro': [], 'con': []}
        
        # Thread count features
        thread_count = characteristics.get('thread_count')
        if thread_count:
            if thread_count >= 1000:
                features['pro'].append('Ultra-High Thread Count')
                features['pro'].append('Luxurious Feel')
                features['con'].append('Higher Price Point')
            elif thread_count >= 600:
                features['pro'].append('High Thread Count')
                features['pro'].append('Durable Construction')
            elif thread_count >= 300:
                features['pro'].append('Good Thread Count')
                features['pro'].append('Balanced Quality')
            else:
                features['con'].append('Lower Thread Count')
        
        # Weave type features
        weave_type = characteristics.get('weave_type')
        if weave_type == 'sateen':
            features['pro'].append('Silky Smooth Feel')
            features['pro'].append('Luxurious Sheen')
            features['con'].append('Can Sleep Warm')
        elif weave_type == 'percale':
            features['pro'].append('Crisp, Cool Feel')
            features['pro'].append('Breathable')
            features['con'].append('Can Feel Rough Initially')
        
        # Cotton type features
        cotton_type = characteristics.get('cotton_type')
        if cotton_type == 'supima':
            features['pro'].append('Premium Supima Cotton')
            features['pro'].append('Extra-Long Staple Fibers')
            features['pro'].append('Superior Softness')
        elif cotton_type == 'egyptian':
            features['pro'].append('Egyptian Cotton Quality')
            features['pro'].append('Luxury Feel')
        elif cotton_type == 'pima':
            features['pro'].append('Pima Cotton Quality')
            features['pro'].append('Enhanced Durability')
        
        # Special features
        special_features = characteristics.get('special_features', [])
        if 'cooling' in special_features:
            features['pro'].append('Advanced Cooling Technology')
            features['pro'].append('Temperature Regulation')
        if 'moisture-wicking' in special_features:
            features['pro'].append('Moisture-Wicking Properties')
            features['pro'].append('Stays Dry All Night')
        if 'breathable' in special_features:
            features['pro'].append('Enhanced Breathability')
        if 'hypoallergenic' in special_features:
            features['pro'].append('Hypoallergenic')
            features['pro'].append('Gentle on Sensitive Skin')
        if 'deep-pocket' in special_features:
            features['pro'].append('Deep Pocket Design')
            features['pro'].append('Secure Fit')
        if 'wrinkle-resistant' in special_features:
            features['pro'].append('Wrinkle-Resistant')
        if 'pill-resistant' in special_features:
            features['pro'].append('Pill-Resistant')
        if 'fade-resistant' in special_features:
            features['pro'].append('Fade-Resistant')
        if 'shrink-resistant' in special_features:
            features['pro'].append('Shrink-Resistant')
        
        # Price tier features
        price_tier = characteristics.get('price_tier')
        if price_tier == 'luxury':
            features['pro'].append('Luxury Quality')
            features['con'].append('Premium Price Point')
        elif price_tier == 'premium':
            features['pro'].append('High-End Quality')
            features['con'].append('Higher Price Point')
        elif price_tier == 'budget':
            features['pro'].append('Affordable Price')
            features['con'].append('Basic Quality')
        
        # Rating features
        rating_tier = characteristics.get('rating_tier')
        if rating_tier == 'excellent':
            features['pro'].append('Highly Rated')
            features['pro'].append('Customer Favorite')
        elif rating_tier == 'very-good':
            features['pro'].append('Well-Rated')
        elif rating_tier == 'poor':
            features['con'].append('Lower Customer Rating')
        
        # Brand tier features
        brand_tier = characteristics.get('brand_tier')
        if brand_tier == 'premium':
            features['pro'].append('Premium Brand')
            features['pro'].append('Trusted Quality')
        elif brand_tier == 'value':
            features['pro'].append('Value Brand')
        
        # Certifications
        certifications = characteristics.get('certifications', [])
        if 'oeko-tex' in certifications:
            features['pro'].append('OEKO-TEX Certified')
            features['pro'].append('Safe Materials')
        if 'organic' in certifications:
            features['pro'].append('Organic Certified')
            features['pro'].append('Eco-Friendly')
        if 'fair-trade' in certifications:
            features['pro'].append('Fair Trade Certified')
            features['pro'].append('Ethical Manufacturing')
        
        # Care instructions
        care = characteristics.get('care_instructions', {})
        if care.get('machine_washable'):
            features['pro'].append('Machine Washable')
        if care.get('easy_care'):
            features['pro'].append('Easy Care')
        if not care.get('wrinkle_free'):
            features['con'].append('May Wrinkle Easily')
        
        # Size-specific features
        size = characteristics.get('size')
        if size == 'king':
            features['pro'].append('King Size Coverage')
        elif size == 'queen':
            features['pro'].append('Queen Size Coverage')
        elif size == 'twin':
            features['pro'].append('Perfect for Kids')
        
        # Material-based features
        material = (characteristics.get('material') or '').lower()
        if 'cotton' in material:
            features['pro'].append('Natural Cotton Fiber')
            features['pro'].append('Breathable')
            features['con'].append('May Wrinkle')
        elif 'bamboo' in material:
            features['pro'].append('Bamboo Fiber')
            features['pro'].append('Eco-Friendly')
            features['con'].append('Requires Gentle Care')
        elif 'linen' in material:
            features['pro'].append('Natural Linen')
            features['pro'].append('Highly Breathable')
            features['con'].append('Wrinkles Easily')
        
        # Remove duplicates and limit
        features['pro'] = list(dict.fromkeys(features['pro']))[:10]  # Max 10 pros
        features['con'] = list(dict.fromkeys(features['con']))[:6]   # Max 6 cons
        
        return features
    
    def _categorize_feature(self, feature: str) -> str:
        """Categorize feature into category"""
        feature_lower = feature.lower()
        
        if any(keyword in feature_lower for keyword in ['thread', 'count', 'luxury', 'premium', 'quality', 'durable']):
            return 'quality'
        elif any(keyword in feature_lower for keyword in ['soft', 'smooth', 'comfort', 'cool', 'breathable', 'temperature']):
            return 'comfort'
        elif any(keyword in feature_lower for keyword in ['care', 'wash', 'maintenance', 'wrinkle', 'pill']):
            return 'care'
        elif any(keyword in feature_lower for keyword in ['price', 'affordable', 'value', 'budget']):
            return 'value'
        elif any(keyword in feature_lower for keyword in ['brand', 'rated', 'certified', 'organic', 'eco']):
            return 'brand'
        else:
            return 'other'
    
    def _determine_importance(self, feature: str, feature_type: str, characteristics: Dict[str, Any]) -> str:
        """Determine importance level for feature"""
        feature_lower = feature.lower()
        
        # High importance features
        high_importance = [
            'thread count', 'luxury', 'premium', 'supima', 'egyptian',
            'cooling', 'breathable', 'soft', 'durable', 'price point'
        ]
        
        if any(keyword in feature_lower for keyword in high_importance):
            return 'high'
        
        # Medium importance
        medium_importance = [
            'certified', 'organic', 'eco-friendly', 'machine washable',
            'wrinkle', 'pill', 'fade', 'shrink'
        ]
        
        if any(keyword in feature_lower for keyword in medium_importance):
            return 'medium'
        
        return 'medium'  # Default
    
    def _calculate_impact_score(self, feature: str, feature_type: str, characteristics: Dict[str, Any]) -> float:
        """Calculate impact score for feature"""
        base_score = 0.7 if feature_type == 'pro' else -0.7
        
        feature_lower = feature.lower()
        
        # High impact features
        high_impact = [
            'thread count', 'luxury', 'premium', 'supima', 'cooling',
            'breathable', 'soft', 'durable', 'price point'
        ]
        
        if any(keyword in feature_lower for keyword in high_impact):
            return base_score * 1.2
        
        # Medium impact
        medium_impact = [
            'certified', 'organic', 'eco-friendly', 'machine washable',
            'wrinkle', 'pill', 'fade', 'shrink'
        ]
        
        if any(keyword in feature_lower for keyword in medium_impact):
            return base_score * 1.0
        
        return base_score * 0.8  # Lower impact


def main():
    """Main function to regenerate all product features"""
    db_path = "multi_platform_products.db"
    
    if not Path(db_path).exists():
        print(f"❌ Database not found: {db_path}")
        return
    
    print("🚀 Starting Dynamic Pros/Cons Generation")
    print("=" * 50)
    
    # Initialize generator
    generator = DynamicProsConsGenerator(db_path)
    
    # Regenerate all features
    print("\n📊 Regenerating product-specific features...")
    stats = generator.regenerate_all_product_features()
    
    print(f"\n✅ Generation Complete!")
    print(f"   Total Products: {stats['total_products']}")
    print(f"   Processed Products: {stats['processed_products']}")
    print(f"   Total Features Generated: {stats['total_features_generated']}")
    print(f"   Errors: {stats['errors']}")
    
    # Show sample results
    print("\n📋 Sample Product-Specific Features:")
    try:
        with sqlite3.connect(db_path) as conn:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.pretty_title, pf.feature_text, pf.feature_type, pf.category, pf.importance, pf.impact_score
                FROM products p
                JOIN product_features pf ON p.id = pf.product_id
                WHERE pf.ai_generated = 1
                ORDER BY p.id, pf.feature_type, pf.impact_score DESC
                LIMIT 20
            """)
            
            results = cursor.fetchall()
            current_product = None
            for title, feature, ftype, category, importance, impact in results:
                if title != current_product:
                    print(f"\n🏷️  {title}:")
                    current_product = title
                
                emoji = "✅" if ftype == 'pro' else "❌"
                print(f"   {emoji} {feature} ({category}, {importance}, {impact:.2f})")
                
    except Exception as e:
        print(f"⚠️  Error showing results: {e}")


if __name__ == "__main__":
    main()
