#!/usr/bin/env python3
"""
Enhanced Amazon Pros & Cons Generator
Generates product-specific pros and cons using rich Amazon API data including:
- Amazon product features
- Brand information and reputation
- Product variations (colors, sizes, pricing)
- Amazon categories and browse nodes
- Material and construction details
"""

import sqlite3
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import logging

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
    BRAND_REPUTATION = "brand_reputation"
    VARIETY = "variety"
    OTHER = "other"

class ImportanceLevel(Enum):
    """Importance levels for pros and cons"""
    CRITICAL = "critical"
    HIGH = "high"
    MEDIUM = "medium"
    LOW = "low"
    MINOR = "minor"

@dataclass
class EnhancedFeature:
    """Enhanced pro/con feature with rich Amazon data"""
    text: str
    category: FeatureCategory
    importance: ImportanceLevel
    explanation: str
    impact_score: float  # -1 to 1 (negative for cons, positive for pros)
    product_specific: bool = True
    amazon_data_source: str = ""  # Which Amazon data source this came from
    confidence: float = 1.0  # Confidence in this analysis

class EnhancedAmazonProsConsGenerator:
    """Generates intelligent pros and cons using comprehensive Amazon API data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.logger = logging.getLogger(__name__)
        
        # Brand reputation scoring
        self.brand_tiers = {
            'premium': 5.0,
            'high-end': 4.5,
            'mid-tier': 3.5,
            'value': 3.0,
            'budget': 2.5
        }
        
        # Material quality scoring
        self.material_quality = {
            'egyptian cotton': 5.0,
            'supima cotton': 4.8,
            'organic cotton': 4.7,
            'bamboo': 4.5,
            'cotton': 4.0,
            'linen': 4.2,
            'microfiber': 3.0,
            'polyester': 2.5
        }
        
        # Thread count quality ranges
        self.thread_count_ranges = {
            'ultra-luxury': (800, 2000),
            'luxury': (400, 799),
            'premium': (300, 399),
            'standard': (200, 299),
            'basic': (100, 199)
        }

    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)

    def _get_comprehensive_product_data(self, product_id: int) -> Dict[str, Any]:
        """Get comprehensive product data including all Amazon API data"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Get main product data
            cursor.execute("""
                SELECT 
                    p.*,
                    b.name as brand_name,
                    b.amazon_brand_name,
                    b.amazon_manufacturer_name,
                    b.company_type,
                    b.business_size,
                    b.sustainability_practices,
                    b.customer_satisfaction_score,
                    b.quality_tier,
                    b.innovation_score,
                    b.sustainability_score,
                    b.customer_promise,
                    b.return_policy,
                    b.warranty_info
                FROM products p
                LEFT JOIN brands b ON p.brand_id = b.id
                WHERE p.id = ?
            """, (product_id,))
            
            product_data = cursor.fetchone()
            if not product_data:
                return {}
            
            # Get column names
            columns = [description[0] for description in cursor.description]
            product_dict = dict(zip(columns, product_data))
            
            # Get Amazon features from unified smart_features table
            cursor.execute("""
                SELECT feature_text, feature_type, display_order
                FROM smart_features
                WHERE product_id = ? AND source_type = 'amazon_raw'
                ORDER BY display_order
            """, (product_id,))
            
            product_dict['amazon_features'] = [
                {'text': row[0], 'type': row[1], 'order': row[2]}
                for row in cursor.fetchall()
            ]
            
            # Get product variations
            cursor.execute("""
                SELECT 
                    variation_type,
                    variation_value,
                    display_name,
                    price,
                    availability_status,
                    amazon_asin
                FROM product_variations
                WHERE product_id = ?
                ORDER BY display_order
            """, (product_id,))
            
            product_dict['variations'] = [
                {
                    'type': row[0],
                    'value': row[1],
                    'name': row[2],
                    'price': row[3],
                    'availability': row[4],
                    'asin': row[5]
                }
                for row in cursor.fetchall()
            ]
            
            # Get Amazon categories
            cursor.execute("""
                SELECT 
                    pc.amazon_browse_node_name,
                    pc.amazon_browse_node_id,
                    ac.category_path,
                    ac.category_level
                FROM product_categories pc
                LEFT JOIN amazon_categories ac ON pc.amazon_browse_node_id = ac.browse_node_id
                WHERE pc.product_id = ? AND pc.amazon_browse_node_name IS NOT NULL
                ORDER BY ac.category_level
            """, (product_id,))
            
            product_dict['amazon_categories'] = [
                {
                    'name': row[0],
                    'node_id': row[1],
                    'path': row[2],
                    'level': row[3]
                }
                for row in cursor.fetchall()
            ]
            
            return product_dict
            
        except Exception as e:
            self.logger.error(f"Error getting product data: {e}")
            return {}
        finally:
            conn.close()

    def _analyze_amazon_features(self, features: List[Dict]) -> List[EnhancedFeature]:
        """Analyze Amazon product features for pros and cons with enhanced specificity"""
        pros_cons = []
        
        for feature in features:
            text = feature['text'].lower()
            
            # 1. ENHANCED CERTIFICATION EXTRACTION
            if 'oeko-tex' in text:
                pros_cons.append(EnhancedFeature(
                    text="OEKO-TEX certified safe materials",
                    category=FeatureCategory.SAFETY,
                    importance=ImportanceLevel.HIGH,
                    explanation="OEKO-TEX certification ensures textiles are free from harmful substances",
                    impact_score=0.9,
                    amazon_data_source="amazon_features",
                    confidence=0.95
                ))
            
            if 'gots' in text:
                pros_cons.append(EnhancedFeature(
                    text="GOTS certified organic materials",
                    category=FeatureCategory.SUSTAINABILITY,
                    importance=ImportanceLevel.HIGH,
                    explanation="Global Organic Textile Standard certification for organic textiles",
                    impact_score=0.9,
                    amazon_data_source="amazon_features",
                    confidence=0.95
                ))
            
            if 'organic' in text and 'certified' in text:
                pros_cons.append(EnhancedFeature(
                    text="Certified organic materials",
                    category=FeatureCategory.SUSTAINABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Organic certification ensures environmentally friendly materials",
                    impact_score=0.7,
                    amazon_data_source="amazon_features",
                    confidence=0.8
                ))
            
            # 2. ENHANCED SUSTAINABILITY FEATURES
            if 'plastic-free' in text or 'packaged without plastic' in text:
                pros_cons.append(EnhancedFeature(
                    text="Plastic-free packaging",
                    category=FeatureCategory.SUSTAINABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Environmentally friendly packaging without plastic materials",
                    impact_score=0.6,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            if any(keyword in text for keyword in ['sustainable', 'eco-friendly', 'planet-friendly', 'environmentally']):
                pros_cons.append(EnhancedFeature(
                    text="Environmentally conscious and sustainable materials",
                    category=FeatureCategory.SUSTAINABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Product features highlight environmental responsibility",
                    impact_score=0.7,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            # 3. ENHANCED MEASUREMENT & SPECIFICATION EXTRACTION
            import re
            
            # Thread count extraction
            thread_count_match = re.search(r'(\d{3,4})\s*thread\s*count', text)
            if thread_count_match:
                tc = thread_count_match.group(1)
                pros_cons.append(EnhancedFeature(
                    text=f"{tc} thread count construction",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.HIGH,
                    explanation=f"High thread count ({tc}) indicates superior fabric density and softness",
                    impact_score=0.8,
                    amazon_data_source="amazon_features",
                    confidence=0.95
                ))
            
            # Deep pocket measurements
            pocket_match = re.search(r'(\d{1,2})\s*["""]\s*deep\s*pocket', text)
            if pocket_match:
                depth = pocket_match.group(1)
                pros_cons.append(EnhancedFeature(
                    text=f"{depth}-inch deep pocket fitted sheet",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"Deep pocket design accommodates mattresses up to {depth} inches thick",
                    impact_score=0.6,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            # 4. ENHANCED COMFORT FEATURES
            if any(keyword in text for keyword in ['cooling', 'breathable', 'moisture-wicking', 'temperature regulating']):
                pros_cons.append(EnhancedFeature(
                    text="Advanced temperature regulation and breathability",
                    category=FeatureCategory.COMFORT,
                    importance=ImportanceLevel.HIGH,
                    explanation="Features specifically designed for comfort and temperature control",
                    impact_score=0.8,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            # 5. ENHANCED DESIGN DETAIL EXTRACTION
            if 'envelope' in text and 'closure' in text:
                pros_cons.append(EnhancedFeature(
                    text="Envelope closure pillowcases",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Envelope closure design keeps pillows secure and prevents pillowcase slippage",
                    impact_score=0.5,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            if 'lustrous' in text or 'sheen' in text or 'elegant finish' in text:
                pros_cons.append(EnhancedFeature(
                    text="Lustrous finish with elegant sheen",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Premium finish that adds visual appeal and luxurious feel",
                    impact_score=0.6,
                    amazon_data_source="amazon_features",
                    confidence=0.8
                ))
            
            if any(keyword in text for keyword in ['deep pocket', 'fitted', 'elastic', 'corner tabs']):
                pros_cons.append(EnhancedFeature(
                    text="Thoughtful design features for better fit and functionality",
                    category=FeatureCategory.DESIGN,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Design elements that improve practical use and fit",
                    impact_score=0.6,
                    amazon_data_source="amazon_features",
                    confidence=0.8
                ))
            
            # 6. ENHANCED CARE INSTRUCTION EXTRACTION
            if 'cold water' in text and 'low' in text:
                pros_cons.append(EnhancedFeature(
                    text="Cold water wash, low heat dry recommended",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Specific care instructions for optimal fabric preservation",
                    impact_score=0.4,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            if 'machine wash' in text and 'tumble dry' in text:
                pros_cons.append(EnhancedFeature(
                    text="Machine washable and tumble dry safe",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Easy care instructions for convenient maintenance",
                    impact_score=0.5,
                    amazon_data_source="amazon_features",
                    confidence=0.8
                ))
            
            # 7. USE CASE IDENTIFICATION
            if 'gift' in text and any(keyword in text for keyword in ['housewarming', 'wedding', 'anniversary', 'mother\'s day', 'father\'s day']):
                pros_cons.append(EnhancedFeature(
                    text="Suitable for gifts and special occasions",
                    category=FeatureCategory.OTHER,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Product positioning emphasizes gift suitability for various occasions",
                    impact_score=0.6,
                    amazon_data_source="amazon_features",
                    confidence=0.8
                ))
            
            # 8. BRAND POSITIONING ANALYSIS
            if any(keyword in text for keyword in ['luxury', 'luxurious', 'premium', 'indulgent']):
                pros_cons.append(EnhancedFeature(
                    text="Luxury positioning and premium quality",
                    category=FeatureCategory.BRAND_REPUTATION,
                    importance=ImportanceLevel.HIGH,
                    explanation="Brand positioning emphasizes luxury and premium quality",
                    impact_score=0.8,
                    amazon_data_source="amazon_features",
                    confidence=0.9
                ))
            
            # Analyze for cons
            if any(keyword in text for keyword in ['hand wash', 'dry clean', 'delicate cycle']):
                pros_cons.append(EnhancedFeature(
                    text="Requires special care and maintenance",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Product requires more careful handling than standard items",
                    impact_score=-0.5,
                    amazon_data_source="amazon_features",
                    confidence=0.8
                ))
            
            if any(keyword in text for keyword in ['wrinkle', 'iron', 'steam']):
                pros_cons.append(EnhancedFeature(
                    text=f"May require additional care to maintain appearance",
                    category=FeatureCategory.MAINTENANCE,
                    importance=ImportanceLevel.LOW,
                    explanation="Product may need extra attention to look its best",
                    impact_score=-0.3,
                    amazon_data_source="amazon_features",
                    confidence=0.7
                ))
        
        return pros_cons

    def _analyze_brand_reputation(self, product_data: Dict) -> List[EnhancedFeature]:
        """Analyze brand information for pros and cons"""
        pros_cons = []
        
        brand_name = product_data.get('amazon_brand_name') or product_data.get('brand_name')
        company_type = product_data.get('company_type')
        business_size = product_data.get('business_size')
        quality_tier = product_data.get('quality_tier')
        customer_satisfaction = product_data.get('customer_satisfaction_score')
        sustainability_practices = product_data.get('sustainability_practices')
        
        if not brand_name:
            return pros_cons
        
        # Analyze business type
        if company_type:
            if 'veteran' in company_type.lower():
                pros_cons.append(EnhancedFeature(
                    text=f"Supports veteran-owned business",
                    category=FeatureCategory.BRAND_REPUTATION,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Brand is veteran-owned, supporting community values",
                    impact_score=0.6,
                    amazon_data_source="brand_data",
                    confidence=0.9
                ))
            
            if 'small business' in company_type.lower():
                pros_cons.append(EnhancedFeature(
                    text=f"Supports small business",
                    category=FeatureCategory.BRAND_REPUTATION,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Small business support with potential for personalized service",
                    impact_score=0.5,
                    amazon_data_source="brand_data",
                    confidence=0.9
                ))
        
        # Analyze quality tier
        if quality_tier:
            if quality_tier in ['premium', 'high-end']:
                pros_cons.append(EnhancedFeature(
                    text=f"Premium brand with established quality standards",
                    category=FeatureCategory.BRAND_REPUTATION,
                    importance=ImportanceLevel.HIGH,
                    explanation=f"Brand is positioned as {quality_tier} with higher quality expectations",
                    impact_score=0.8,
                    amazon_data_source="brand_data",
                    confidence=0.9
                ))
            elif quality_tier in ['budget', 'value']:
                pros_cons.append(EnhancedFeature(
                    text=f"Value-focused brand with competitive pricing",
                    category=FeatureCategory.PRICE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"Brand positioned as {quality_tier} offering good value",
                    impact_score=0.6,
                    amazon_data_source="brand_data",
                    confidence=0.9
                ))
        
        # Analyze customer satisfaction
        if customer_satisfaction and customer_satisfaction >= 4.5:
            pros_cons.append(EnhancedFeature(
                text=f"High customer satisfaction rating",
                category=FeatureCategory.BRAND_REPUTATION,
                importance=ImportanceLevel.HIGH,
                explanation=f"Brand maintains {customer_satisfaction} customer satisfaction score",
                impact_score=0.8,
                amazon_data_source="brand_data",
                confidence=0.9
            ))
        elif customer_satisfaction and customer_satisfaction < 3.5:
            pros_cons.append(EnhancedFeature(
                text=f"Below-average customer satisfaction",
                category=FeatureCategory.BRAND_REPUTATION,
                importance=ImportanceLevel.HIGH,
                explanation=f"Brand has {customer_satisfaction} customer satisfaction score",
                impact_score=-0.6,
                amazon_data_source="brand_data",
                confidence=0.9
            ))
        
        # Analyze sustainability
        if sustainability_practices:
            try:
                practices = json.loads(sustainability_practices) if isinstance(sustainability_practices, str) else sustainability_practices
                if practices and len(practices) > 0:
                    pros_cons.append(EnhancedFeature(
                        text=f"Strong sustainability practices",
                        category=FeatureCategory.SUSTAINABILITY,
                        importance=ImportanceLevel.MEDIUM,
                        explanation=f"Brand implements {', '.join(practices[:2])} and other sustainable practices",
                        impact_score=0.7,
                        amazon_data_source="brand_data",
                        confidence=0.9
                    ))
            except:
                pass
        
        return pros_cons

    def _analyze_material_quality(self, product_data: Dict) -> List[EnhancedFeature]:
        """Analyze material and construction quality"""
        pros_cons = []
        
        material_type = (product_data.get('amazon_material_type') or '').lower()
        thread_count = product_data.get('amazon_thread_count')
        weave_type = (product_data.get('amazon_weave_type') or '').lower()
        
        # Analyze material quality
        if material_type:
            material_score = self.material_quality.get(material_type, 3.0)
            
            if material_score >= 4.5:
                pros_cons.append(EnhancedFeature(
                    text=f"Premium {material_type.title()} material construction",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.HIGH,
                    explanation=f"{material_type.title()} is considered a premium material for bedding",
                    impact_score=0.8,
                    amazon_data_source="product_data",
                    confidence=0.9
                ))
            elif material_score <= 3.0:
                pros_cons.append(EnhancedFeature(
                    text=f"Basic {material_type.title()} material",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"{material_type.title()} is a more basic material option",
                    impact_score=-0.4,
                    amazon_data_source="product_data",
                    confidence=0.9
                ))
        
        # Analyze thread count
        if thread_count:
            thread_count_int = int(thread_count) if str(thread_count).isdigit() else 0
            
            if thread_count_int >= 800:
                pros_cons.append(EnhancedFeature(
                    text=f"Ultra-luxury {thread_count} thread count",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.HIGH,
                    explanation=f"{thread_count} thread count represents ultra-luxury quality",
                    impact_score=0.9,
                    amazon_data_source="product_data",
                    confidence=0.9
                ))
            elif thread_count_int >= 400:
                pros_cons.append(EnhancedFeature(
                    text=f"Luxury {thread_count} thread count",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.HIGH,
                    explanation=f"{thread_count} thread count represents luxury quality",
                    impact_score=0.8,
                    amazon_data_source="product_data",
                    confidence=0.9
                ))
            elif thread_count_int < 200:
                pros_cons.append(EnhancedFeature(
                    text=f"Lower thread count may affect durability",
                    category=FeatureCategory.DURABILITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"{thread_count} thread count is below premium standards",
                    impact_score=-0.5,
                    amazon_data_source="product_data",
                    confidence=0.8
                ))
        
        # Analyze weave type
        if weave_type:
            if weave_type in ['sateen', 'percale', 'jersey']:
                pros_cons.append(EnhancedFeature(
                    text=f"Quality {weave_type} weave construction",
                    category=FeatureCategory.QUALITY,
                    importance=ImportanceLevel.MEDIUM,
                    explanation=f"{weave_type.title()} weave provides good balance of comfort and durability",
                    impact_score=0.6,
                    amazon_data_source="product_data",
                    confidence=0.8
                ))
        
        return pros_cons

    def _analyze_variations(self, variations: List[Dict]) -> List[EnhancedFeature]:
        """Analyze product variations for pros and cons"""
        pros_cons = []
        
        if not variations:
            return pros_cons
        
        # Count variations
        color_variations = [v for v in variations if v['type'] in ['color', 'color_size']]
        size_variations = [v for v in variations if v['type'] in ['size', 'color_size']]
        
        # Analyze variety
        if len(color_variations) >= 5:
            pros_cons.append(EnhancedFeature(
                text=f"Extensive color selection with {len(color_variations)} options",
                category=FeatureCategory.VARIETY,
                importance=ImportanceLevel.MEDIUM,
                explanation="Wide range of color options to match different preferences and decor",
                impact_score=0.6,
                amazon_data_source="variations",
                confidence=0.9
            ))
        elif len(color_variations) <= 2:
            pros_cons.append(EnhancedFeature(
                text=f"Limited color selection with only {len(color_variations)} options",
                category=FeatureCategory.VARIETY,
                importance=ImportanceLevel.LOW,
                explanation="Fewer color options may limit matching with existing decor",
                impact_score=-0.3,
                amazon_data_source="variations",
                confidence=0.8
            ))
        
        if len(size_variations) >= 6:
            pros_cons.append(EnhancedFeature(
                text=f"Comprehensive size range with {len(size_variations)} options",
                category=FeatureCategory.VARIETY,
                importance=ImportanceLevel.MEDIUM,
                explanation="Wide range of sizes to fit different bed types and preferences",
                impact_score=0.6,
                amazon_data_source="variations",
                confidence=0.9
            ))
        
        # Analyze pricing consistency
        prices = [v['price'] for v in variations if v['price']]
        if prices:
            price_range = max(prices) - min(prices)
            if price_range > 50:
                pros_cons.append(EnhancedFeature(
                    text=f"Significant price variation across sizes/colors",
                    category=FeatureCategory.PRICE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Price differences between variations may affect value perception",
                    impact_score=-0.4,
                    amazon_data_source="variations",
                    confidence=0.8
                ))
        
        return pros_cons

    def _analyze_pricing(self, product_data: Dict) -> List[EnhancedFeature]:
        """Analyze pricing and value"""
        pros_cons = []
        
        price = product_data.get('price')
        discount_percentage = product_data.get('discount_percentage')
        
        if price:
            # Analyze price point
            if price >= 150:
                pros_cons.append(EnhancedFeature(
                    text=f"Premium pricing at ${price}",
                    category=FeatureCategory.PRICE,
                    importance=ImportanceLevel.HIGH,
                    explanation="Higher price point may limit accessibility but suggests premium quality",
                    impact_score=-0.5,
                    amazon_data_source="product_data",
                    confidence=0.9
                ))
            elif price <= 50:
                pros_cons.append(EnhancedFeature(
                    text=f"Budget-friendly pricing at ${price}",
                    category=FeatureCategory.PRICE,
                    importance=ImportanceLevel.MEDIUM,
                    explanation="Affordable price point makes it accessible to more customers",
                    impact_score=0.6,
                    amazon_data_source="product_data",
                    confidence=0.9
                ))
        
        if discount_percentage and discount_percentage > 20:
            pros_cons.append(EnhancedFeature(
                text=f"Excellent value with {discount_percentage}% discount",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.HIGH,
                explanation=f"Significant discount of {discount_percentage}% provides excellent value",
                impact_score=0.8,
                amazon_data_source="product_data",
                confidence=0.9
            ))
        elif discount_percentage and discount_percentage < 5:
            pros_cons.append(EnhancedFeature(
                text=f"Minimal discount at {discount_percentage}%",
                category=FeatureCategory.PRICE,
                importance=ImportanceLevel.LOW,
                explanation="Very small discount may not provide significant savings",
                impact_score=-0.2,
                amazon_data_source="product_data",
                confidence=0.8
            ))
        
        return pros_cons

    def _analyze_feature_relationships(self, product_data: Dict) -> List[EnhancedFeature]:
        """Analyze how different features work together for synergistic benefits"""
        pros_cons = []
        
        material_type = (product_data.get('material') or '').lower()
        weave_type = (product_data.get('weave_type') or '').lower()
        thread_count = product_data.get('thread_count')
        
        # 9. FEATURE RELATIONSHIP UNDERSTANDING
        
        # Egyptian cotton + sateen weave combination
        if 'egyptian cotton' in material_type and 'sateen' in weave_type:
            pros_cons.append(EnhancedFeature(
                text="Egyptian cotton with sateen weave luxury combination",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.HIGH,
                explanation="Premium Egyptian cotton enhanced by lustrous sateen weave creates exceptional softness and durability",
                impact_score=0.9,
                amazon_data_source="feature_combination",
                confidence=0.95
            ))
        
        # High thread count + premium material
        if thread_count and thread_count >= 600 and any(premium in material_type for premium in ['egyptian cotton', 'organic cotton']):
            pros_cons.append(EnhancedFeature(
                text=f"{thread_count} thread count premium material construction",
                category=FeatureCategory.QUALITY,
                importance=ImportanceLevel.HIGH,
                explanation=f"High thread count ({thread_count}) combined with premium material creates superior fabric quality",
                impact_score=0.8,
                amazon_data_source="feature_combination",
                confidence=0.9
            ))
        
        # Bamboo + cooling properties
        if 'bamboo' in material_type and any(keyword in str(product_data.get('amazon_features', [])).lower() for keyword in ['cooling', 'breathable']):
            pros_cons.append(EnhancedFeature(
                text="Bamboo material with natural cooling properties",
                category=FeatureCategory.COMFORT,
                importance=ImportanceLevel.HIGH,
                explanation="Bamboo's natural moisture-wicking properties combined with cooling features provide exceptional temperature regulation",
                impact_score=0.8,
                amazon_data_source="feature_combination",
                confidence=0.9
            ))
        
        # Organic certification + sustainability practices
        if any(keyword in str(product_data.get('amazon_features', [])).lower() for keyword in ['organic', 'certified organic']) and any(keyword in str(product_data.get('amazon_features', [])).lower() for keyword in ['sustainable', 'eco-friendly']):
            pros_cons.append(EnhancedFeature(
                text="Certified organic with comprehensive sustainability practices",
                category=FeatureCategory.SUSTAINABILITY,
                importance=ImportanceLevel.HIGH,
                explanation="Organic certification combined with sustainability practices demonstrates comprehensive environmental responsibility",
                impact_score=0.8,
                amazon_data_source="feature_combination",
                confidence=0.9
            ))
        
        return pros_cons

    def generate_enhanced_features(self, product_id: int) -> List[EnhancedFeature]:
        """Generate comprehensive pros and cons using all Amazon data"""
        product_data = self._get_comprehensive_product_data(product_id)
        
        if not product_data:
            return []
        
        all_features = []
        
        # Analyze different data sources
        all_features.extend(self._analyze_amazon_features(product_data.get('amazon_features', [])))
        all_features.extend(self._analyze_brand_reputation(product_data))
        all_features.extend(self._analyze_material_quality(product_data))
        all_features.extend(self._analyze_variations(product_data.get('variations', [])))
        all_features.extend(self._analyze_pricing(product_data))
        all_features.extend(self._analyze_feature_relationships(product_data))
        
        # Remove duplicates and sort by impact score
        unique_features = []
        seen_texts = set()
        
        for feature in all_features:
            if feature.text not in seen_texts:
                unique_features.append(feature)
                seen_texts.add(feature.text)
        
        # Sort by impact score (absolute value) and importance
        importance_order = {
            ImportanceLevel.CRITICAL: 5,
            ImportanceLevel.HIGH: 4,
            ImportanceLevel.MEDIUM: 3,
            ImportanceLevel.LOW: 2,
            ImportanceLevel.MINOR: 1
        }
        
        unique_features.sort(key=lambda x: (abs(x.impact_score), importance_order[x.importance]), reverse=True)
        
        return unique_features[:10]  # Return top 10 features

    def save_enhanced_features(self, product_id: int) -> bool:
        """Save enhanced features to database"""
        features = self.generate_enhanced_features(product_id)
        
        if not features:
            return False
        
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            # Clear existing processed features for this product (keep amazon_raw)
            cursor.execute("DELETE FROM smart_features WHERE product_id = ? AND source_type = 'processed_pros_cons'", (product_id,))
            
            # Insert new enhanced features
            for feature in features:
                cursor.execute("""
                    INSERT INTO smart_features (
                        product_id, feature_text, feature_type, enhanced_feature_type, category, 
                        importance, explanation, impact_score, product_specific, source_type
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id,
                    feature.text,
                    'pro' if feature.impact_score > 0 else 'con',
                    'pros' if feature.impact_score > 0 else 'cons',
                    feature.category.value,
                    feature.importance.value,
                    feature.explanation,
                    feature.impact_score,
                    feature.product_specific,
                    'processed_pros_cons'
                ))
            
            conn.commit()
            return True
            
        except Exception as e:
            self.logger.error(f"Error saving enhanced features: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()

def main():
    """Test the enhanced generator"""
    generator = EnhancedAmazonProsConsGenerator()
    
    # Test on a sample product
    test_product_id = 77  # Bamboo Bay product
    
    print(f"Testing enhanced pros/cons generator on product {test_product_id}")
    features = generator.generate_enhanced_features(test_product_id)
    
    print(f"\nGenerated {len(features)} enhanced features:")
    for i, feature in enumerate(features, 1):
        print(f"{i}. [{feature.category.value.upper()}] {feature.text}")
        print(f"   Impact: {feature.impact_score:.2f} | Importance: {feature.importance.value}")
        print(f"   Source: {feature.amazon_data_source} | Confidence: {feature.confidence}")
        print(f"   Explanation: {feature.explanation}")
        print()

if __name__ == "__main__":
    main()
