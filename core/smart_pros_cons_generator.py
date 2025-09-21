#!/usr/bin/env python3
"""
Smart Pros & Cons Generator
Generates product-specific pros and cons based on actual product characteristics
"""

import sqlite3
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

class FeatureCategory(Enum):
    """Categories for pros and cons"""
    QUALITY = "quality"
    PRICE = "price"
    PERFORMANCE = "performance"
    DESIGN = "design"
    DURABILITY = "durability"
    COMFORT = "comfort"
    EASE_OF_USE = "ease_of_use"
    MAINTENANCE = "maintenance"
    SUSTAINABILITY = "sustainability"
    SAFETY = "safety"
    OTHER = "other"

class ImportanceLevel(Enum):
    """Importance levels for pros and cons"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINOR = "minor"

@dataclass
class SmartFeature:
    """Smart pro/con feature with rich metadata"""
    text: str
    category: FeatureCategory
    importance: ImportanceLevel
    explanation: str
    impact_score: float  # -1 to 1 (negative for cons, positive for pros)
    product_specific: bool = True

class SmartProsConsGenerator:
    """Generates intelligent, product-specific pros and cons"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Initialize tables if needed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create smart features table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS smart_product_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    feature_text TEXT NOT NULL,
                    feature_type TEXT NOT NULL,
                    category TEXT NOT NULL,
                    importance TEXT NOT NULL,
                    explanation TEXT NOT NULL,
                    impact_score REAL NOT NULL,
                    product_specific BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def generate_all_smart_features(self) -> Dict[str, int]:
        """Generate smart, product-specific features for all products"""
        stats = {
            'total_products': 0,
            'processed_products': 0,
            'total_features_generated': 0,
            'errors': 0
        }
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get all products with their characteristics
            cursor.execute('''
                SELECT 
                    p.id, p.title, p.description, p.product_summary,
                    p.material, p.weave_type, p.thread_count, p.color, p.size, p.brand,
                    p.price, p.rating, p.review_count
                FROM products p
                WHERE p.title IS NOT NULL AND p.title != ''
                ORDER BY p.id
            ''')
            
            products = cursor.fetchall()
            stats['total_products'] = len(products)
            
            for product in products:
                try:
                    product_id = product[0]
                    title = product[1]
                    description = product[2] or ''
                    summary = product[3] or ''
                    material = product[4] or ''
                    weave_type = product[5] or ''
                    thread_count = product[6]
                    color = product[7] or ''
                    size = product[8] or ''
                    brand = product[9] or ''
                    price = product[10]
                    rating = product[11]
                    review_count = product[12]
                    
                    # Generate smart features for this product
                    features = self._generate_smart_features(
                        product_id, title, description, summary,
                        material, weave_type, thread_count, color, size, brand,
                        price, rating, review_count
                    )
                    
                    # Save features to database
                    self._save_features(product_id, features)
                    
                    stats['processed_products'] += 1
                    stats['total_features_generated'] += len(features)
                    
                    print(f"✅ Product {product_id}: Generated {len(features)} smart features")
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    stats['errors'] += 1
                    continue
        
        return stats
    
    def _generate_smart_features(self, product_id: int, title: str, description: str, 
                                summary: str, material: str, weave_type: str, 
                                thread_count: int, color: str, size: str, brand: str,
                                price: float, rating: float, review_count: int) -> List[SmartFeature]:
        """Generate smart, product-specific features"""
        features = []
        
        # Combine all text for analysis
        combined_text = f"{title} {description} {summary}".lower()
        
        # Material-based features
        features.extend(self._generate_material_features(material, combined_text))
        
        # Weave type features
        features.extend(self._generate_weave_features(weave_type, combined_text))
        
        # Thread count features
        features.extend(self._generate_thread_count_features(thread_count, combined_text))
        
        # Brand features
        features.extend(self._generate_brand_features(brand, combined_text))
        
        # Size features
        features.extend(self._generate_size_features(size, combined_text))
        
        # Price features
        features.extend(self._generate_price_features(price, combined_text))
        
        # Rating features
        features.extend(self._generate_rating_features(rating, review_count, combined_text))
        
        # Special features from description
        features.extend(self._generate_special_features(combined_text))
        
        # Generate smart, specific cons
        smart_cons = self._generate_smart_cons(
            product_id, title, description, material, weave_type, 
            thread_count, price, rating, review_count, brand, size
        )
        features.extend(smart_cons)
        
        return features
    
    def _generate_material_features(self, material: str, text: str) -> List[SmartFeature]:
        """Generate features based on material"""
        features = []
        
        if not material:
            return features
        
        material_lower = material.lower()
        
        if 'bamboo' in material_lower:
            features.extend([
                SmartFeature(
                    text="Natural moisture-wicking bamboo fibers",
                    category=FeatureCategory.PERFORMANCE,
                    importance=ImportanceLevel.HIGH,
                    explanation="Bamboo naturally wicks moisture away from the body, keeping you cool and dry throughout the night",
                    impact_score=0.8
                ),
                SmartFeature(
                    text="Eco-friendly and sustainable material",
                    category=FeatureCategory.SUSTAINABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Bamboo is a renewable resource that grows quickly without pesticides or fertilizers",
                    impact_score=0.6
                ),
                SmartFeature(
                    text="Naturally antimicrobial properties",
                    category=FeatureCategory.PERFORMANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Bamboo fibers naturally resist bacteria and odors, keeping sheets fresher longer",
                    impact_score=0.5
                )
            ])
        
        elif 'cotton' in material_lower:
            if 'egyptian' in material_lower:
                features.extend([
                    SmartFeature(
                        text="Premium Egyptian cotton long-staple fibers",
                        category=FeatureCategory.QUALITY,
                        importance=ImportanceLevel.HIGH,
                        explanation="Egyptian cotton has longer, stronger fibers that create a smoother, more durable fabric",
                        impact_score=0.9
                    ),
                    SmartFeature(
                        text="Luxurious softness that improves with washing",
                        category=FeatureCategory.COMFORT,
                        importance=ImportanceLevel.HIGH,
                        explanation="Egyptian cotton becomes softer and more comfortable with each wash",
                        impact_score=0.8
                    )
                ])
            else:
                features.extend([
                    SmartFeature(
                        text="Natural cotton breathability",
                        category=FeatureCategory.COMFORT,
                        importance=ImportanceLevel.MEDIUM,
                        explanation="Cotton naturally allows air to circulate, helping regulate body temperature",
                        impact_score=0.6
                    ),
                    SmartFeature(
                        text="Easy care and machine washable",
                        category=FeatureCategory.MAINTENANCE,
                        importance=ImportanceLevel.MEDIUM,
                        explanation="Cotton is durable and can be easily cleaned in a standard washing machine",
                        impact_score=0.5
                    )
                ])
        
        elif 'linen' in material_lower:
            features.extend([
                SmartFeature(
                    text="Superior breathability and moisture absorption",
                    category=FeatureCategory.PERFORMANCE,
                    importance=ImportanceLevel.HIGH,
                    explanation="Linen is one of the most breathable fabrics, perfect for hot sleepers",
                    impact_score=0.8
                ),
                SmartFeature(
                    text="Natural texture that softens over time",
                    category=FeatureCategory.COMFORT,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Linen develops a beautiful patina and becomes softer with use",
                    impact_score=0.6
                )
            ])
        
        return features
    
    def _generate_weave_features(self, weave_type: str, text: str) -> List[SmartFeature]:
        """Generate features based on weave type"""
        features = []
        
        if not weave_type:
            return features
        
        weave_lower = weave_type.lower()
        
        if 'sateen' in weave_lower:
            features.extend([
                SmartFeature(
                    text="Luxurious silky smooth finish",
                    category=FeatureCategory.COMFORT,
                    importance=ImportanceLevel.HIGH,
                    explanation="Sateen weave creates a smooth, lustrous surface that feels luxurious against the skin",
                    impact_score=0.8
                ),
                SmartFeature(
                    text="Natural wrinkle resistance",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Sateen weave naturally resists wrinkles, keeping sheets looking crisp",
                    impact_score=0.6
                )
            ])
        
        elif 'percale' in weave_lower:
            features.extend([
                SmartFeature(
                    text="Crisp, cool feel perfect for hot sleepers",
                    category=FeatureCategory.COMFORT,
                    importance=ImportanceLevel.HIGH,
                    explanation="Percale weave creates a crisp, matte finish that feels cool and breathable",
                    impact_score=0.8
                ),
                SmartFeature(
                    text="Durable one-over-one weave construction",
                    category=FeatureCategory.DURABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Percale's balanced weave makes it more durable and long-lasting",
                    impact_score=0.6
                )
            ])
        
        elif 'basketweave' in weave_lower:
            features.extend([
                SmartFeature(
                    text="Unique textured appearance",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Basketweave creates an attractive textured pattern that adds visual interest",
                    impact_score=0.5
                ),
                SmartFeature(
                    text="Enhanced breathability",
                    category=FeatureCategory.PERFORMANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="The open weave pattern allows for better air circulation",
                    impact_score=0.6
                )
            ])
        
        return features
    
    def _generate_thread_count_features(self, thread_count: int, text: str) -> List[SmartFeature]:
        """Generate features based on thread count"""
        features = []
        
        if not thread_count:
            return features
        
        if thread_count >= 1000:
            features.extend([
                SmartFeature(
                    text=f"Ultra-luxurious {thread_count} thread count",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.HIGH,
                    explanation=f"With {thread_count} threads per square inch, these sheets offer exceptional softness and durability",
                    impact_score=0.9
                ),
                SmartFeature(
                    text="Silky smooth texture",
                    category=FeatureCategory.COMFORT,
                    importance=ImportanceLevel.HIGH,
                    explanation="High thread count creates an incredibly smooth, silky feel",
                    impact_score=0.8
                )
            ])
        elif thread_count >= 600:
            features.extend([
                SmartFeature(
                    text=f"Premium {thread_count} thread count quality",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"{thread_count} thread count provides excellent balance of softness and durability",
                    impact_score=0.7
                )
            ])
        elif thread_count >= 400:
            features.extend([
                SmartFeature(
                    text=f"Quality {thread_count} thread count construction",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"{thread_count} thread count offers good quality and comfort at an accessible price",
                    impact_score=0.6
                )
            ])
        
        return features
    
    def _generate_brand_features(self, brand: str, text: str) -> List[SmartFeature]:
        """Generate features based on brand reputation"""
        features = []
        
        if not brand:
            return features
        
        brand_lower = brand.lower()
        
        # Premium brands
        if any(premium in brand_lower for premium in ['boll & branch', 'boll and branch', 'frette', 'sferra']):
            features.extend([
                SmartFeature(
                    text="Premium luxury brand reputation",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.HIGH,
                    explanation="This brand is known for exceptional quality and luxury bedding",
                    impact_score=0.8
                ),
                SmartFeature(
                    text="Ethical and sustainable manufacturing",
                    category=FeatureCategory.SUSTAINABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Premium brands often prioritize ethical sourcing and sustainable practices",
                    impact_score=0.6
                )
            ])
        
        # Established brands
        elif any(established in brand_lower for established in ['california design den', 'chateau', 'coop']):
            features.extend([
                SmartFeature(
                    text="Established brand with proven quality",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="This brand has a reputation for consistent quality and customer satisfaction",
                    impact_score=0.6
                )
            ])
        
        return features
    
    def _generate_size_features(self, size: str, text: str) -> List[SmartFeature]:
        """Generate features based on size"""
        features = []
        
        if not size:
            return features
        
        size_lower = size.lower()
        
        if 'king' in size_lower or 'california king' in size_lower:
            features.extend([
                SmartFeature(
                    text="Generous king-size dimensions",
                    category=FeatureCategory.COMFORT,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="King size provides ample space for couples and larger beds",
                    impact_score=0.6
                )
            ])
        elif 'queen' in size_lower:
            features.extend([
                SmartFeature(
                    text="Versatile queen size",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.LOW,
                    explanation="Queen size fits most standard beds and is easy to find accessories for",
                    impact_score=0.4
                )
            ])
        elif 'twin' in size_lower:
            features.extend([
                SmartFeature(
                    text="Perfect for kids' rooms and guest beds",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Twin size is ideal for children's rooms and guest accommodations",
                    impact_score=0.5
                )
            ])
        
        return features
    
    def _generate_price_features(self, price: float, text: str) -> List[SmartFeature]:
        """Generate features based on price"""
        features = []
        
        if not price:
            return features
        
        if price >= 200:
            features.append(SmartFeature(
                text="Premium luxury pricing",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.HIGH,
                explanation="Higher price point reflects premium materials and construction quality",
                impact_score=-0.7
            ))
        elif price >= 100:
            features.append(SmartFeature(
                text="Mid-range pricing for quality",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.MEDIUM,
                explanation="Balanced price point offering good value for quality materials",
                impact_score=-0.4
            ))
        elif price >= 50:
            features.append(SmartFeature(
                text="Affordable quality option",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.MEDIUM,
                explanation="Good value pricing makes quality bedding accessible",
                impact_score=0.5
            ))
        
        return features
    
    def _generate_rating_features(self, rating: float, review_count: int, text: str) -> List[SmartFeature]:
        """Generate features based on rating and review count"""
        features = []
        
        if rating and rating >= 4.5:
            features.append(SmartFeature(
                text="Exceptional customer ratings",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.HIGH,
                explanation=f"Rated {rating}/5 stars by customers, indicating high satisfaction",
                impact_score=0.8
            ))
        elif rating and rating >= 4.0:
            features.append(SmartFeature(
                text="Highly rated by customers",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"Strong {rating}/5 star rating shows customer satisfaction",
                impact_score=0.6
            ))
        
        if review_count and review_count >= 1000:
            features.append(SmartFeature(
                text="Extensively reviewed by customers",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"Over {review_count} reviews provide confidence in the product",
                impact_score=0.5
            ))
        
        return features
    
    def _generate_special_features(self, text: str) -> List[SmartFeature]:
        """Generate features based on special characteristics in the text"""
        features = []
        
        # Deep pocket features
        if 'deep pocket' in text:
            features.append(SmartFeature(
                text="Deep pocket design for secure fit",
                category=FeatureCategory.DESIGN,
                importance=ImportanceLevel.MEDIUM,
                explanation="Deep pockets ensure sheets stay in place on thicker mattresses",
                impact_score=0.6
            ))
        
        # Cooling features
        if any(cooling in text for cooling in ['cooling', 'temperature regulating', 'breathable']):
            features.append(SmartFeature(
                text="Advanced cooling technology",
                category=FeatureCategory.PERFORMANCE,
                importance=ImportanceLevel.HIGH,
                explanation="Special cooling features help regulate body temperature for comfortable sleep",
                impact_score=0.8
            ))
        
        # Organic features
        if 'organic' in text:
            features.append(SmartFeature(
                text="Certified organic materials",
                category=FeatureCategory.SUSTAINABILITY,
                importance=ImportanceLevel.MEDIUM,
                explanation="Organic certification ensures no harmful chemicals or pesticides",
                impact_score=0.6
            ))
        
        # Hypoallergenic features
        if 'hypoallergenic' in text:
            features.append(SmartFeature(
                text="Hypoallergenic properties",
                category=FeatureCategory.SAFETY,
                importance=ImportanceLevel.MEDIUM,
                explanation="Hypoallergenic materials reduce risk of allergic reactions",
                impact_score=0.6
            ))
        
        return features
    
    def _save_features(self, product_id: int, features: List[SmartFeature]):
        """Save features to database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Clear existing smart features for this product
            cursor.execute('DELETE FROM smart_product_features WHERE product_id = ?', (product_id,))
            
            # Insert new features
            for feature in features:
                cursor.execute('''
                    INSERT INTO smart_product_features 
                    (product_id, feature_text, feature_type, category, importance, explanation, impact_score, product_specific)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    product_id,
                    feature.text,
                    'pro' if feature.impact_score > 0 else 'con',
                    feature.category.value,
                    feature.importance.value,
                    feature.explanation,
                    feature.impact_score,
                    feature.product_specific
                ))
            
            conn.commit()
    
    def get_smart_features(self, product_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get smart features for a product"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute('''
                SELECT feature_text, feature_type, category, importance, explanation, impact_score
                FROM smart_product_features
                WHERE product_id = ?
                ORDER BY ABS(impact_score) DESC, feature_text
            ''', (product_id,))
            
            features = cursor.fetchall()
            
            pros = []
            cons = []
            
            for feature in features:
                feature_dict = {
                    'text': feature[0],
                    'category': feature[2],
                    'importance': feature[3],
                    'explanation': feature[4],
                    'impact_score': feature[5]
                }
                
                if feature[1] == 'pro':
                    pros.append(feature_dict)
                else:
                    cons.append(feature_dict)
            
            return {'pros': pros, 'cons': cons}
    
    def _generate_smart_cons(self, product_id: int, title: str, description: str, 
                           material: str, weave_type: str, thread_count: int,
                           price: float, rating: float, review_count: int, 
                           brand: str, size: str) -> List[SmartFeature]:
        """Generate intelligent, specific cons based on product characteristics"""
        cons = []
        
        # Brand popularity and trustworthiness cons
        brand_cons = self._generate_brand_cons(brand, review_count, rating)
        cons.extend(brand_cons)
        
        # Material-specific cons
        material_cons = self._generate_material_cons(material, description)
        cons.extend(material_cons)
        
        # Weave-specific cons
        weave_cons = self._generate_weave_cons(weave_type, description)
        cons.extend(weave_cons)
        
        # Thread count cons
        thread_cons = self._generate_thread_count_cons(thread_count, price)
        cons.extend(thread_cons)
        
        # Size and fit cons
        size_cons = self._generate_size_cons(size, description)
        cons.extend(size_cons)
        
        # Care and maintenance cons
        care_cons = self._generate_care_cons(material, weave_type, description)
        cons.extend(care_cons)
        
        # Value and pricing cons
        value_cons = self._generate_value_cons(price, rating, review_count, material, thread_count)
        cons.extend(value_cons)
        
        # Durability concerns
        durability_cons = self._generate_durability_cons(material, weave_type, thread_count, price)
        cons.extend(durability_cons)
        
        return cons
    
    def _generate_brand_cons(self, brand: str, review_count: int, rating: float) -> List[SmartFeature]:
        """Generate cons based on brand popularity and trustworthiness"""
        cons = []
        
        if not brand or brand.lower() in ['unknown', 'visit the', '']:
            return cons
        
        # New or unknown brand with few reviews
        if review_count < 50:
            cons.append(SmartFeature(
                text="Limited customer feedback available",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"With only {review_count} reviews, there's less data to assess long-term performance and quality consistency",
                impact_score=-0.5
            ))
        
        # Brand with concerning rating patterns
        elif review_count < 200 and rating < 4.0:
            cons.append(SmartFeature(
                text="Mixed customer satisfaction",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.HIGH,
                explanation=f"Rating of {rating}/5 with {review_count} reviews suggests some quality or consistency issues",
                impact_score=-0.7
            ))
        
        # Premium brand with high price but average rating
        elif review_count > 500 and rating < 4.2 and price > 150:
            cons.append(SmartFeature(
                text="Premium pricing doesn't match customer satisfaction",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.HIGH,
                explanation=f"Despite premium pricing, {rating}/5 rating suggests the quality may not justify the cost",
                impact_score=-0.8
            ))
        
        return cons
    
    def _generate_material_cons(self, material: str, description: str) -> List[SmartFeature]:
        """Generate material-specific cons"""
        cons = []
        
        if not material:
            return cons
        
        material_lower = material.lower()
        desc_lower = description.lower()
        
        if 'bamboo' in material_lower:
            cons.append(SmartFeature(
                text="May require special care instructions",
                category=FeatureCategory.MAINTENANCE,
                importance=ImportanceLevel.MEDIUM,
                explanation="Bamboo sheets often need gentle washing and air drying to maintain their softness and prevent shrinkage",
                impact_score=-0.4
            ))
            
            if 'wrinkle' in desc_lower or 'wrinkle-free' not in desc_lower:
                cons.append(SmartFeature(
                    text="Tends to wrinkle more than cotton",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Bamboo fabric is more prone to wrinkling and may require ironing or steaming for a crisp look",
                    impact_score=-0.3
                ))
        
        elif 'cotton' in material_lower:
            if 'egyptian' not in material_lower and 'supima' not in material_lower:
                cons.append(SmartFeature(
                    text="May shrink in first wash",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Regular cotton sheets can shrink 3-5% in the first wash, so consider sizing up if you prefer a looser fit",
                    impact_score=-0.3
                ))
            
            if 'wrinkle-free' not in desc_lower and 'percale' not in material_lower:
                cons.append(SmartFeature(
                    text="Requires ironing for crisp appearance",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.LOW,
                    explanation="Cotton sheets tend to wrinkle and may need ironing or steaming to maintain a crisp, hotel-like appearance",
                    impact_score=-0.2
                ))
        
        elif 'linen' in material_lower:
            cons.append(SmartFeature(
                text="Rough texture initially",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.MEDIUM,
                explanation="Linen starts with a rougher texture that softens over time, but may feel scratchy for sensitive skin initially",
                impact_score=-0.4
            ))
            
            cons.append(SmartFeature(
                text="High maintenance fabric",
                category=FeatureCategory.MAINTENANCE,
                importance=ImportanceLevel.HIGH,
                explanation="Linen requires special care including gentle washing, air drying, and may need ironing while damp",
                impact_score=-0.6
            ))
        
        return cons
    
    def _generate_weave_cons(self, weave_type: str, description: str) -> List[SmartFeature]:
        """Generate weave-specific cons"""
        cons = []
        
        if not weave_type:
            return cons
        
        weave_lower = weave_type.lower()
        
        if 'sateen' in weave_lower:
            cons.append(SmartFeature(
                text="Less breathable than percale",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.MEDIUM,
                explanation="Sateen's tight weave reduces breathability, which may not be ideal for hot sleepers",
                impact_score=-0.4
            ))
            
            cons.append(SmartFeature(
                text="May feel too warm for hot sleepers",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.MEDIUM,
                explanation="The smooth, dense weave of sateen can trap heat, making it less suitable for those who sleep hot",
                impact_score=-0.3
            ))
        
        elif 'percale' in weave_lower:
            cons.append(SmartFeature(
                text="Crisp feel may be too stiff for some",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.LOW,
                explanation="Percale's crisp, cool feel might feel too stiff or formal for those who prefer softer, more relaxed bedding",
                impact_score=-0.2
            ))
        
        return cons
    
    def _generate_thread_count_cons(self, thread_count: int, price: float) -> List[SmartFeature]:
        """Generate thread count-specific cons"""
        cons = []
        
        if not thread_count or thread_count <= 0:
            return cons
        
        if thread_count < 200:
            cons.append(SmartFeature(
                text="Lower thread count may feel less luxurious",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"{thread_count} thread count may feel less smooth and luxurious compared to higher thread count sheets",
                impact_score=-0.4
            ))
        
        elif thread_count > 800 and price < 100:
            cons.append(SmartFeature(
                text="Suspiciously high thread count for price",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.HIGH,
                explanation=f"{thread_count} thread count at this price point may indicate misleading marketing or lower quality construction",
                impact_score=-0.7
            ))
        
        elif thread_count > 1000:
            cons.append(SmartFeature(
                text="Very high thread count may be too dense",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.MEDIUM,
                explanation="Thread counts above 1000 can create sheets that are too dense and less breathable",
                impact_score=-0.3
            ))
        
        return cons
    
    def _generate_size_cons(self, size: str, description: str) -> List[SmartFeature]:
        """Generate size-specific cons"""
        cons = []
        
        if not size:
            return cons
        
        size_lower = size.lower()
        
        if 'king' in size_lower or 'california king' in size_lower:
            cons.append(SmartFeature(
                text="Requires larger washing machine",
                category=FeatureCategory.MAINTENANCE,
                importance=ImportanceLevel.LOW,
                explanation="King size sheets may not fit in standard washing machines and may require commercial or large-capacity machines",
                impact_score=-0.2
            ))
        
        if 'deep pocket' not in description.lower():
            cons.append(SmartFeature(
                text="May not fit thick mattresses",
                category=FeatureCategory.DESIGN,
                importance=ImportanceLevel.MEDIUM,
                explanation="Standard pocket depth may not accommodate thick mattresses, memory foam toppers, or pillow-top mattresses",
                impact_score=-0.3
            ))
        
        return cons
    
    def _generate_care_cons(self, material: str, weave_type: str, description: str) -> List[SmartFeature]:
        """Generate care and maintenance cons"""
        cons = []
        
        if 'dry clean' in description.lower():
            cons.append(SmartFeature(
                text="Requires dry cleaning",
                category=FeatureCategory.MAINTENANCE,
                importance=ImportanceLevel.HIGH,
                explanation="Dry cleaning requirement adds ongoing cost and inconvenience compared to machine-washable options",
                impact_score=-0.7
            ))
        
        if 'hand wash' in description.lower():
            cons.append(SmartFeature(
                text="Hand wash only",
                category=FeatureCategory.MAINTENANCE,
                importance=ImportanceLevel.HIGH,
                explanation="Hand washing requirement is time-consuming and may not be practical for busy households",
                impact_score=-0.6
            ))
        
        if material and 'bamboo' in material.lower() and 'tumble dry' in description.lower():
            cons.append(SmartFeature(
                text="Heat drying may damage bamboo fibers",
                category=FeatureCategory.MAINTENANCE,
                importance=ImportanceLevel.MEDIUM,
                explanation="Bamboo fibers can be damaged by high heat, so air drying is recommended to maintain softness",
                impact_score=-0.4
            ))
        
        return cons
    
    def _generate_value_cons(self, price: float, rating: float, review_count: int, material: str, thread_count: int) -> List[SmartFeature]:
        """Generate value and pricing cons"""
        cons = []
        
        if not price or price <= 0:
            return cons
        
        # High price with low thread count
        if price > 150 and thread_count and thread_count < 400:
            cons.append(SmartFeature(
                text="High price for lower thread count",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"At ${price}, the {thread_count} thread count may not represent the best value compared to higher thread count options",
                impact_score=-0.5
            ))
        
        # Premium pricing with average rating
        if price > 200 and rating and rating < 4.3:
            cons.append(SmartFeature(
                text="Premium price with average satisfaction",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.HIGH,
                explanation=f"At ${price}, the {rating}/5 rating suggests the quality may not justify the premium pricing",
                impact_score=-0.7
            ))
        
        # Synthetic material at high price
        if price > 100 and material and any(synth in material.lower() for synth in ['polyester', 'microfiber', 'blend']):
            cons.append(SmartFeature(
                text="High price for synthetic material",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"At ${price}, synthetic materials typically cost less to produce than natural fibers like cotton or bamboo",
                impact_score=-0.4
            ))
        
        return cons
    
    def _generate_durability_cons(self, material: str, weave_type: str, thread_count: int, price: float) -> List[SmartFeature]:
        """Generate durability concerns"""
        cons = []
        
        if thread_count and thread_count < 200:
            cons.append(SmartFeature(
                text="Lower thread count may wear faster",
                category=FeatureCategory.DURABILITY,
                importance=ImportanceLevel.MEDIUM,
                explanation=f"{thread_count} thread count sheets may not last as long as higher thread count options with regular use",
                impact_score=-0.4
            ))
        
        if material and 'bamboo' in material.lower():
            cons.append(SmartFeature(
                text="Bamboo may lose softness over time",
                category=FeatureCategory.DURABILITY,
                importance=ImportanceLevel.MEDIUM,
                explanation="Bamboo sheets may lose their initial softness and become rougher with repeated washing if not cared for properly",
                impact_score=-0.3
            ))
        
        if price and price < 50 and thread_count and thread_count > 600:
            cons.append(SmartFeature(
                text="Low price may indicate quality shortcuts",
                category=FeatureCategory.DURABILITY,
                importance=ImportanceLevel.HIGH,
                explanation=f"Very low price for {thread_count} thread count may indicate shortcuts in construction or materials that could affect durability",
                impact_score=-0.6
            ))
        
        return cons

def main():
    """Main function"""
    print("🧠 Smart Pros & Cons Generator")
    print("=" * 50)
    
    generator = SmartProsConsGenerator()
    results = generator.generate_all_smart_features()
    
    print("\n" + "=" * 50)
    print("📊 RESULTS:")
    print(f"Total products: {results['total_products']}")
    print(f"Processed products: {results['processed_products']}")
    print(f"Total features generated: {results['total_features_generated']}")
    print(f"Errors: {results['errors']}")
    
    print(f"\n🎉 Smart feature generation complete!")

if __name__ == "__main__":
    main()
