#!/usr/bin/env python3
"""
Enhanced Pros & Cons System
Comprehensive solution for managing product pros and cons with AI enhancement
"""

import sqlite3
import json
import re
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum
import time

class FeatureCategory(Enum):
    """Categories for pros and cons"""
    QUALITY = "quality"
    PRICE = "price"
    PERFORMANCE = "performance"
    DESIGN = "design"
    DURABILITY = "durability"
    COMFORT = "comfort"
    EASE_OF_USE = "ease_of_use"
    CUSTOMER_SERVICE = "customer_service"
    SHIPPING = "shipping"
    WARRANTY = "warranty"
    SUSTAINABILITY = "sustainability"
    COMPATIBILITY = "compatibility"
    MAINTENANCE = "maintenance"
    SAFETY = "safety"
    OTHER = "other"

class ImportanceLevel(Enum):
    """Importance levels for pros and cons"""
    CRITICAL = "critical"      # Deal breaker/maker
    HIGH = "high"             # Very important
    MEDIUM = "medium"         # Moderately important
    LOW = "low"               # Nice to have
    MINOR = "minor"           # Barely noticeable

@dataclass
class ProConFeature:
    """Enhanced pro/con feature with rich metadata"""
    text: str
    category: FeatureCategory
    importance: ImportanceLevel
    explanation: Optional[str] = None
    evidence: Optional[str] = None  # Supporting evidence
    frequency: Optional[str] = None  # How often mentioned
    impact_score: Optional[float] = None  # -1 to 1 (negative for cons, positive for pros)
    ai_generated: bool = False
    verified: bool = False
    source: Optional[str] = None  # Where this came from

class EnhancedProsConsSystem:
    """Enhanced system for managing product pros and cons"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self._init_enhanced_tables()
    
    def _init_enhanced_tables(self):
        """Initialize enhanced pros/cons tables"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create enhanced product_features table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS enhanced_product_features (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    product_id INTEGER NOT NULL,
                    feature_text TEXT NOT NULL,
                    feature_type TEXT NOT NULL,  -- 'pro', 'con', 'specification', 'general'
                    category TEXT,               -- quality, price, performance, etc.
                    importance TEXT,             -- critical, high, medium, low, minor
                    explanation TEXT,            -- Detailed explanation
                    evidence TEXT,               -- Supporting evidence
                    frequency TEXT,              -- How often mentioned
                    impact_score REAL,           -- -1 to 1 (negative for cons, positive for pros)
                    ai_generated BOOLEAN DEFAULT FALSE,
                    verified BOOLEAN DEFAULT FALSE,
                    source TEXT,                 -- Where this came from
                    display_order INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            ''')
            
            # Create pros_cons_analysis table for AI insights
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS pros_cons_analysis (
                    id INTEGER PRIMARY KEY AUTOINCREMENT NOT NULL,
                    product_id INTEGER NOT NULL,
                    analysis_type TEXT NOT NULL,  -- 'overall', 'category', 'comparison'
                    analysis_data TEXT NOT NULL,  -- JSON with analysis results
                    confidence_score REAL,        -- 0 to 1
                    ai_model TEXT,                -- Which AI model was used
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def migrate_existing_features(self):
        """Migrate existing simple features to enhanced format"""
        print("🔄 Migrating existing features to enhanced format...")
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get existing features
            cursor.execute("""
                SELECT product_id, feature_text, feature_type, display_order
                FROM product_features
                WHERE feature_type IN ('pro', 'con')
            """)
            
            existing_features = cursor.fetchall()
            print(f"📋 Found {len(existing_features)} existing pros/cons to migrate")
            
            migrated_count = 0
            for product_id, feature_text, feature_type, display_order in existing_features:
                # Analyze and enhance the feature
                enhanced_feature = self._analyze_and_enhance_feature(feature_text, feature_type)
                
                # Insert enhanced feature
                cursor.execute("""
                    INSERT INTO enhanced_product_features (
                        product_id, feature_text, feature_type, category, importance,
                        explanation, impact_score, ai_generated, verified, source,
                        display_order
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, feature_text, feature_type,
                    enhanced_feature.category.value,
                    enhanced_feature.importance.value,
                    enhanced_feature.explanation,
                    enhanced_feature.impact_score,
                    enhanced_feature.ai_generated,
                    enhanced_feature.verified,
                    enhanced_feature.source,
                    display_order
                ))
                
                migrated_count += 1
            
            conn.commit()
            print(f"✅ Migrated {migrated_count} features to enhanced format")
    
    def _analyze_and_enhance_feature(self, text: str, feature_type: str) -> ProConFeature:
        """Analyze a simple feature and enhance it with metadata"""
        
        # Basic text analysis
        text_lower = text.lower()
        
        # Determine category based on keywords
        category = self._determine_category(text_lower)
        
        # Determine importance based on keywords and context
        importance = self._determine_importance(text_lower, feature_type)
        
        # Calculate impact score
        impact_score = self._calculate_impact_score(text_lower, feature_type, importance)
        
        # Generate explanation
        explanation = self._generate_explanation(text, category, importance)
        
        return ProConFeature(
            text=text,
            category=category,
            importance=importance,
            explanation=explanation,
            impact_score=impact_score,
            ai_generated=True,
            verified=False,
            source="migration_analysis"
        )
    
    def _determine_category(self, text: str) -> FeatureCategory:
        """Determine feature category based on keywords"""
        category_keywords = {
            FeatureCategory.QUALITY: ['quality', 'durable', 'well-made', 'premium', 'excellent', 'superior'],
            FeatureCategory.PRICE: ['price', 'expensive', 'cheap', 'affordable', 'cost', 'value', 'budget'],
            FeatureCategory.PERFORMANCE: ['performance', 'fast', 'slow', 'efficient', 'effective', 'powerful'],
            FeatureCategory.DESIGN: ['design', 'look', 'appearance', 'style', 'beautiful', 'ugly', 'aesthetic'],
            FeatureCategory.DURABILITY: ['durable', 'lasts', 'long-lasting', 'sturdy', 'fragile', 'breaks'],
            FeatureCategory.COMFORT: ['comfortable', 'comfort', 'soft', 'hard', 'cozy', 'uncomfortable'],
            FeatureCategory.EASE_OF_USE: ['easy', 'simple', 'difficult', 'complicated', 'user-friendly', 'convenient'],
            FeatureCategory.CUSTOMER_SERVICE: ['service', 'support', 'helpful', 'unhelpful', 'customer'],
            FeatureCategory.SHIPPING: ['shipping', 'delivery', 'fast', 'slow', 'free', 'expensive'],
            FeatureCategory.WARRANTY: ['warranty', 'guarantee', 'return', 'refund', 'policy'],
            FeatureCategory.SUSTAINABILITY: ['eco-friendly', 'sustainable', 'green', 'environmental', 'organic'],
            FeatureCategory.COMPATIBILITY: ['compatible', 'works with', 'fits', 'doesn\'t fit', 'compatibility'],
            FeatureCategory.MAINTENANCE: ['maintenance', 'care', 'cleaning', 'wash', 'maintain'],
            FeatureCategory.SAFETY: ['safe', 'safety', 'secure', 'dangerous', 'hazardous']
        }
        
        for category, keywords in category_keywords.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return FeatureCategory.OTHER
    
    def _determine_importance(self, text: str, feature_type: str) -> ImportanceLevel:
        """Determine importance level based on keywords and context"""
        
        # Critical indicators
        critical_keywords = ['essential', 'crucial', 'deal breaker', 'must have', 'terrible', 'awful', 'horrible']
        if any(keyword in text for keyword in critical_keywords):
            return ImportanceLevel.CRITICAL
        
        # High importance indicators
        high_keywords = ['very', 'extremely', 'highly', 'important', 'significant', 'major', 'serious']
        if any(keyword in text for keyword in high_keywords):
            return ImportanceLevel.HIGH
        
        # Low importance indicators
        low_keywords = ['minor', 'slight', 'small', 'little', 'barely', 'hardly']
        if any(keyword in text for keyword in low_keywords):
            return ImportanceLevel.LOW
        
        # Minor indicators
        minor_keywords = ['tiny', 'minimal', 'negligible', 'insignificant']
        if any(keyword in text for keyword in minor_keywords):
            return ImportanceLevel.MINOR
        
        # Default based on feature type
        if feature_type == 'con':
            return ImportanceLevel.MEDIUM  # Cons are generally more important
        else:
            return ImportanceLevel.MEDIUM
    
    def _calculate_impact_score(self, text: str, feature_type: str, importance: ImportanceLevel) -> float:
        """Calculate impact score from -1 (very negative) to 1 (very positive)"""
        
        # Base score based on feature type
        base_score = 0.5 if feature_type == 'pro' else -0.5
        
        # Adjust based on importance
        importance_multipliers = {
            ImportanceLevel.CRITICAL: 1.0,
            ImportanceLevel.HIGH: 0.8,
            ImportanceLevel.MEDIUM: 0.6,
            ImportanceLevel.LOW: 0.4,
            ImportanceLevel.MINOR: 0.2
        }
        
        multiplier = importance_multipliers[importance]
        
        # Adjust based on intensity words
        intensity_keywords = {
            'very': 1.2, 'extremely': 1.3, 'highly': 1.2, 'super': 1.3,
            'slightly': 0.8, 'somewhat': 0.9, 'barely': 0.7
        }
        
        for keyword, intensity in intensity_keywords.items():
            if keyword in text:
                multiplier *= intensity
                break
        
        return base_score * multiplier
    
    def _generate_explanation(self, text: str, category: FeatureCategory, importance: ImportanceLevel) -> str:
        """Generate a detailed explanation for the feature"""
        
        explanations = {
            FeatureCategory.QUALITY: f"This relates to the overall quality and build of the product. {text} indicates the product's manufacturing standards and materials used.",
            FeatureCategory.PRICE: f"This concerns the product's pricing and value proposition. {text} affects the product's accessibility and perceived value.",
            FeatureCategory.PERFORMANCE: f"This relates to how well the product performs its intended function. {text} impacts the user experience and effectiveness.",
            FeatureCategory.DESIGN: f"This concerns the product's visual appeal and aesthetic qualities. {text} affects the product's attractiveness and style.",
            FeatureCategory.DURABILITY: f"This relates to how long the product will last and resist wear. {text} impacts the product's longevity and value over time.",
            FeatureCategory.COMFORT: f"This concerns how comfortable the product is to use. {text} affects the user's physical comfort and satisfaction.",
            FeatureCategory.EASE_OF_USE: f"This relates to how easy the product is to use and understand. {text} impacts the user experience and learning curve.",
            FeatureCategory.CUSTOMER_SERVICE: f"This concerns the support and service provided with the product. {text} affects the overall customer experience.",
            FeatureCategory.SHIPPING: f"This relates to the delivery and shipping experience. {text} impacts the convenience and cost of getting the product.",
            FeatureCategory.WARRANTY: f"This concerns the product's warranty and return policy. {text} affects the buyer's confidence and protection.",
            FeatureCategory.SUSTAINABILITY: f"This relates to the product's environmental impact. {text} affects the product's eco-friendliness and sustainability.",
            FeatureCategory.COMPATIBILITY: f"This concerns how well the product works with other items. {text} impacts the product's versatility and usefulness.",
            FeatureCategory.MAINTENANCE: f"This relates to how easy the product is to care for and maintain. {text} affects the long-term ownership experience.",
            FeatureCategory.SAFETY: f"This concerns the product's safety features and considerations. {text} impacts the user's safety and peace of mind."
        }
        
        base_explanation = explanations.get(category, f"This is a {category.value} consideration. {text} affects the overall product experience.")
        
        # Add importance context
        importance_context = {
            ImportanceLevel.CRITICAL: "This is a critical factor that can make or break the purchase decision.",
            ImportanceLevel.HIGH: "This is an important factor that significantly impacts the product experience.",
            ImportanceLevel.MEDIUM: "This is a moderate factor that affects the product experience.",
            ImportanceLevel.LOW: "This is a minor factor that has a small impact on the product experience.",
            ImportanceLevel.MINOR: "This is a very minor factor that has minimal impact on the product experience."
        }
        
        return f"{base_explanation} {importance_context[importance]}"
    
    def add_enhanced_pro_con(self, product_id: int, feature: ProConFeature) -> int:
        """Add an enhanced pro/con feature to a product"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get next display order
            cursor.execute("""
                SELECT MAX(display_order) FROM enhanced_product_features 
                WHERE product_id = ? AND feature_type = ?
            """, (product_id, 'pro' if feature.impact_score > 0 else 'con'))
            
            max_order = cursor.fetchone()[0] or 0
            
            # Insert enhanced feature
            cursor.execute("""
                INSERT INTO enhanced_product_features (
                    product_id, feature_text, feature_type, category, importance,
                    explanation, evidence, frequency, impact_score, ai_generated,
                    verified, source, display_order
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                product_id, feature.text, 'pro' if feature.impact_score > 0 else 'con',
                feature.category.value, feature.importance.value,
                feature.explanation, feature.evidence, feature.frequency,
                feature.impact_score, feature.ai_generated,
                feature.verified, feature.source, max_order + 1
            ))
            
            feature_id = cursor.lastrowid
            conn.commit()
            
            return feature_id
    
    def get_product_pros_cons(self, product_id: int) -> Dict[str, List[Dict[str, Any]]]:
        """Get enhanced pros and cons for a product"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                SELECT feature_text, category, importance, explanation, evidence,
                       frequency, impact_score, ai_generated, verified, source,
                       display_order
                FROM enhanced_product_features
                WHERE product_id = ? AND feature_type IN ('pro', 'con')
                ORDER BY feature_type, display_order
            """, (product_id,))
            
            features = cursor.fetchall()
            
            pros = []
            cons = []
            
            for feature in features:
                feature_data = {
                    'text': feature[0],
                    'category': feature[1],
                    'importance': feature[2],
                    'explanation': feature[3],
                    'evidence': feature[4],
                    'frequency': feature[5],
                    'impact_score': feature[6],
                    'ai_generated': feature[7],
                    'verified': feature[8],
                    'source': feature[9],
                    'display_order': feature[10]
                }
                
                if feature[6] > 0:  # Positive impact score = pro
                    pros.append(feature_data)
                else:  # Negative impact score = con
                    cons.append(feature_data)
            
            return {'pros': pros, 'cons': cons}
    
    def generate_ai_insights(self, product_id: int) -> Dict[str, Any]:
        """Generate AI-powered insights about pros and cons"""
        
        pros_cons = self.get_product_pros_cons(product_id)
        
        # Analyze pros
        pros_analysis = self._analyze_features(pros_cons['pros'], 'pros')
        
        # Analyze cons
        cons_analysis = self._analyze_features(pros_cons['cons'], 'cons')
        
        # Overall analysis
        overall_analysis = self._generate_overall_analysis(pros_analysis, cons_analysis)
        
        insights = {
            'overall': overall_analysis,
            'pros': pros_analysis,
            'cons': cons_analysis,
            'recommendations': self._generate_recommendations(pros_analysis, cons_analysis),
            'confidence_score': self._calculate_confidence_score(pros_cons)
        }
        
        # Save insights to database
        self._save_ai_insights(product_id, insights)
        
        return insights
    
    def _analyze_features(self, features: List[Dict[str, Any]], feature_type: str) -> Dict[str, Any]:
        """Analyze a list of features and generate insights"""
        
        if not features:
            return {'count': 0, 'categories': {}, 'insights': []}
        
        # Count by category
        categories = {}
        importance_counts = {}
        total_impact = 0
        
        for feature in features:
            category = feature['category']
            importance = feature['importance']
            impact = feature['impact_score']
            
            categories[category] = categories.get(category, 0) + 1
            importance_counts[importance] = importance_counts.get(importance, 0) + 1
            total_impact += abs(impact)
        
        # Generate insights
        insights = []
        
        # Most common category
        if categories:
            most_common_category = max(categories, key=categories.get)
            insights.append(f"Most {feature_type} relate to {most_common_category} ({categories[most_common_category]} items)")
        
        # Importance distribution
        if importance_counts:
            high_importance = importance_counts.get('high', 0) + importance_counts.get('critical', 0)
            if high_importance > 0:
                insights.append(f"{high_importance} {feature_type} are of high importance")
        
        # Impact analysis
        avg_impact = total_impact / len(features) if features else 0
        if avg_impact > 0.7:
            insights.append(f"Overall {feature_type} have high impact on product experience")
        elif avg_impact < 0.3:
            insights.append(f"Overall {feature_type} have low impact on product experience")
        
        return {
            'count': len(features),
            'categories': categories,
            'importance_distribution': importance_counts,
            'average_impact': avg_impact,
            'insights': insights
        }
    
    def _generate_overall_analysis(self, pros_analysis: Dict[str, Any], cons_analysis: Dict[str, Any]) -> Dict[str, Any]:
        """Generate overall analysis combining pros and cons"""
        
        pros_count = pros_analysis['count']
        cons_count = cons_analysis['count']
        
        # Balance analysis
        if pros_count > cons_count * 2:
            balance = "very positive"
        elif pros_count > cons_count:
            balance = "positive"
        elif cons_count > pros_count * 2:
            balance = "very negative"
        elif cons_count > pros_count:
            balance = "negative"
        else:
            balance = "balanced"
        
        # Impact analysis
        pros_impact = pros_analysis['average_impact']
        cons_impact = cons_analysis['average_impact']
        
        if pros_impact > cons_impact:
            impact_balance = "pros outweigh cons"
        elif cons_impact > pros_impact:
            impact_balance = "cons outweigh pros"
        else:
            impact_balance = "balanced impact"
        
        return {
            'balance': balance,
            'impact_balance': impact_balance,
            'pros_count': pros_count,
            'cons_count': cons_count,
            'pros_impact': pros_impact,
            'cons_impact': cons_impact
        }
    
    def _generate_recommendations(self, pros_analysis: Dict[str, Any], cons_analysis: Dict[str, Any]) -> List[str]:
        """Generate recommendations based on pros and cons analysis"""
        
        recommendations = []
        
        # Category-based recommendations
        cons_categories = cons_analysis.get('categories', {})
        if 'quality' in cons_categories:
            recommendations.append("Consider addressing quality concerns highlighted in reviews")
        if 'price' in cons_categories:
            recommendations.append("Price may be a barrier - consider value proposition messaging")
        if 'ease_of_use' in cons_categories:
            recommendations.append("Improve user experience and provide better instructions")
        
        # Importance-based recommendations
        high_importance_cons = cons_analysis.get('importance_distribution', {}).get('high', 0)
        if high_importance_cons > 0:
            recommendations.append("Address high-importance concerns to improve product appeal")
        
        # Balance recommendations
        if cons_analysis['count'] > pros_analysis['count'] * 1.5:
            recommendations.append("Focus on highlighting more positive aspects of the product")
        
        return recommendations
    
    def _calculate_confidence_score(self, pros_cons: Dict[str, List[Dict[str, Any]]]) -> float:
        """Calculate confidence score for the analysis"""
        
        total_features = len(pros_cons['pros']) + len(pros_cons['cons'])
        if total_features == 0:
            return 0.0
        
        # Base confidence on number of features
        base_confidence = min(total_features / 10, 1.0)  # Max confidence at 10+ features
        
        # Adjust based on verification status
        verified_count = sum(1 for feature in pros_cons['pros'] + pros_cons['cons'] if feature.get('verified', False))
        verification_bonus = (verified_count / total_features) * 0.2
        
        return min(base_confidence + verification_bonus, 1.0)
    
    def _save_ai_insights(self, product_id: int, insights: Dict[str, Any]):
        """Save AI insights to database"""
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO pros_cons_analysis (
                    product_id, analysis_type, analysis_data, confidence_score, ai_model
                ) VALUES (?, ?, ?, ?, ?)
            """, (
                product_id, 'overall', json.dumps(insights),
                insights['confidence_score'], 'enhanced_pros_cons_system'
            ))
            
            conn.commit()
    
    def get_enhanced_summary(self, product_id: int) -> str:
        """Get a human-readable summary of enhanced pros and cons"""
        
        pros_cons = self.get_product_pros_cons(product_id)
        insights = self.generate_ai_insights(product_id)
        
        summary = f"## Enhanced Pros & Cons Analysis\n\n"
        
        # Overall summary
        overall = insights['overall']
        summary += f"**Overall Balance**: {overall['balance'].title()} ({overall['pros_count']} pros, {overall['cons_count']} cons)\n"
        summary += f"**Impact Balance**: {overall['impact_balance'].title()}\n\n"
        
        # Pros summary
        if pros_cons['pros']:
            summary += "### ✅ **Strengths**\n"
            for pro in pros_cons['pros'][:5]:  # Top 5 pros
                importance_emoji = {
                    'critical': '🔥', 'high': '⭐', 'medium': '👍', 'low': '👌', 'minor': '💡'
                }
                emoji = importance_emoji.get(pro['importance'], '👍')
                summary += f"- {emoji} **{pro['text']}** ({pro['category']})\n"
                if pro['explanation']:
                    summary += f"  *{pro['explanation'][:100]}...*\n"
            summary += "\n"
        
        # Cons summary
        if pros_cons['cons']:
            summary += "### ❌ **Areas for Improvement**\n"
            for con in pros_cons['cons'][:5]:  # Top 5 cons
                importance_emoji = {
                    'critical': '🚨', 'high': '⚠️', 'medium': '📝', 'low': '💭', 'minor': '💡'
                }
                emoji = importance_emoji.get(con['importance'], '📝')
                summary += f"- {emoji} **{con['text']}** ({con['category']})\n"
                if con['explanation']:
                    summary += f"  *{con['explanation'][:100]}...*\n"
            summary += "\n"
        
        # Recommendations
        if insights['recommendations']:
            summary += "### 💡 **Recommendations**\n"
            for rec in insights['recommendations']:
                summary += f"- {rec}\n"
            summary += "\n"
        
        # Confidence
        confidence = insights['confidence_score']
        confidence_emoji = "🟢" if confidence > 0.8 else "🟡" if confidence > 0.5 else "🔴"
        summary += f"**Analysis Confidence**: {confidence_emoji} {confidence:.1%}\n"
        
        return summary

def main():
    """Example usage"""
    system = EnhancedProsConsSystem()
    
    # Migrate existing features
    system.migrate_existing_features()
    
    # Example: Get enhanced summary for a product
    # summary = system.get_enhanced_summary(1)
    # print(summary)
    
    print("🚀 Enhanced Pros & Cons System Ready!")
    print("Usage: system.get_enhanced_summary(product_id)")

if __name__ == "__main__":
    main()
