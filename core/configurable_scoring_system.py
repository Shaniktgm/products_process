#!/usr/bin/env python3
"""
Configurable scoring system that reads from scoring_config.json
"""

import json
import sqlite3
import os
from typing import Dict, Any, Optional, Union
import math

class ConfigurableScoringSystem:
    """Configurable scoring system for products"""
    
    def __init__(self, config_file: str = "core/scoring_config.json"):
        self.config_file = config_file
        self.config = self._load_config()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load configuration from JSON file"""
        try:
            with open(self.config_file, 'r', encoding='utf-8') as f:
                config = json.load(f)
            print(f"✅ Loaded scoring configuration from {self.config_file}")
            return config
        except FileNotFoundError:
            print(f"❌ Configuration file {self.config_file} not found")
            return self._get_default_config()
        except json.JSONDecodeError as e:
            print(f"❌ Error parsing configuration file: {e}")
            return self._get_default_config()
    
    def _get_default_config(self) -> Dict[str, Any]:
        """Get default configuration if file is not available"""
        return {
            "overall_score": {
                "method": "price_based",
                "formula": "price"
            },
            "sub_scores": {
                "popularity_score": {"fallback_method": "review_count_simplified"},
                "brand_reputation_score": {"fallback_method": "rating_as_is"},
                "price_value_score": {"fallback_method": "price_commission_value"},
                "overall_value_score": {"fallback_method": "price_rating_ratio"},
                "luxury_score": {"fallback_method": "price_based"}
            }
        }
    
    def calculate_overall_score(self, product_data: Dict[str, Any], price_range: tuple = None) -> float:
        """Calculate overall score based on configuration"""
        method = self.config.get("overall_score", {}).get("method", "comprehensive_composite")
        
        if method == "comprehensive_composite":
            return self._calculate_comprehensive_composite_score(product_data)
        elif method == "weighted_composite":
            return self._calculate_weighted_composite_score(product_data)
        elif method == "overall_value_score":
            return self._calculate_overall_value_score(product_data)
        elif method == "price_based":
            return self._calculate_price_based_score(product_data)
        elif method == "value_focused":
            return self._calculate_value_focused_score(product_data, price_range)
        elif method == "luxury_premium":
            return self._calculate_luxury_premium_score(product_data)
        else:
            # Default to comprehensive_composite
            return self._calculate_comprehensive_composite_score(product_data)
    
    
    def _calculate_comprehensive_composite_score(self, product_data: Dict[str, Any]) -> float:
        """Calculate comprehensive composite score using popularity, brand reputation, and price value"""
        weights = self.config.get("scoring_weights", {})
        
        # Calculate sub-scores if not available
        sub_scores = self.calculate_sub_scores(product_data)
        popularity_score = sub_scores.get('popularity_score', 0)
        brand_reputation_score = sub_scores.get('brand_reputation_score', 0)
        price_value_score = sub_scores.get('price_value_score', 0)
        
        weighted_score = (
            popularity_score * weights.get('popularity_score', 0.2) +
            brand_reputation_score * weights.get('brand_reputation_score', 0.2) +
            price_value_score * weights.get('price_value_score', 0.6)
        )
        
        return round(weighted_score, 2)
    
    
    def calculate_sub_scores(self, product_data: Dict[str, Any]) -> Dict[str, float]:
        """Calculate sub-scores based on configuration (popularity, brand reputation, price value)"""
        sub_scores = {}
        
        # Calculate all 3 required sub-scores
        required_scores = ["popularity_score", "brand_reputation_score", "price_value_score"]
        
        for score_name in required_scores:
            if score_name in self.config.get("sub_scores", {}):
                score_config = self.config["sub_scores"][score_name]
                if score_name in product_data and product_data[score_name]:
                    # Use existing score if available
                    sub_scores[score_name] = float(product_data[score_name])
                else:
                    # Calculate fallback score
                    fallback_method = score_config.get("fallback_method", "default")
                    sub_scores[score_name] = self._calculate_fallback_score(
                        score_name, fallback_method, product_data
                    )
        
        return sub_scores
    
    def _calculate_fallback_score(self, score_name: str, method: str, product_data: Dict[str, Any]) -> float:
        """Calculate fallback score when CSV data is not available (2-5 range)"""
        if method == "rating_based":
            rating = product_data.get('rating', 0) or 0
            # Convert rating (0-5) to score (2-5)
            if rating >= 4.5:
                return 5.0
            elif rating >= 4.0:
                return 4.5
            elif rating >= 3.5:
                return 3.5
            elif rating >= 3.0:
                return 3.0
            else:
                return 2.5
        
        elif method == "rating_as_is":
            rating = product_data.get('rating')
            # Use rating as-is, fallback to 2 if no rating
            if rating is not None and rating != '' and rating != 0:
                return float(rating)
            else:
                return 2.0
        
        elif method == "review_count_based":
            review_count = product_data.get('review_count', 0) or 0
            thresholds = self.config.get("review_count_thresholds", {})
            
            if review_count >= thresholds.get("very_high", 5000):
                return 5.0
            elif review_count >= thresholds.get("high", 2000):
                return 4.5
            elif review_count >= thresholds.get("moderate", 1000):
                return 4.0
            elif review_count >= thresholds.get("low", 500):
                return 3.5
            else:
                return 2.5
        
        elif method == "review_count_simplified":
            review_count = product_data.get('review_count', 0) or 0
            
            # Simplified thresholds: >1000=5, >500=4, <500=3
            if review_count > 1000:
                return 5.0
            elif review_count > 500:
                return 4.0
            else:
                return 3.0
        
        elif method == "price_rating_ratio":
            rating = product_data.get('rating', 0) or 0
            price = product_data.get('price', 0) or 0
            
            if rating >= 4.0 and price < 100:
                return 5.0
            elif rating >= 4.0 and price < 150:
                return 4.5
            elif rating >= 3.5 and price < 200:
                return 4.0
            else:
                return 3.0
        
        elif method == "price_commission_value":
            # Get price and commission rate
            price = product_data.get('price', 0) or 0
            commission_rate = product_data.get('commission_rate', 0.10) or 0.10  # Default 10%
            
            # Calculate price × commission rate (earnings per sale)
            earnings_per_sale = price * commission_rate
            
            if earnings_per_sale > 20:
                return 5.0
            elif earnings_per_sale > 15:
                return 4.0
            elif earnings_per_sale > 10:
                return 3.0
            elif earnings_per_sale > 5:
                return 2.0
            else:
                return 1.0
        
        elif method == "price_based":
            price = product_data.get('price', 0) or 0
            thresholds = self.config.get("price_categories", {})
            
            if price >= thresholds.get("luxury", {}).get("min_price", 250):
                return 5.0
            elif price >= thresholds.get("premium", {}).get("min_price", 150):
                return 4.5
            elif price >= thresholds.get("mid_range", {}).get("min_price", 50):
                return 3.5
            else:
                return 2.5
        
        
        else:
            return 3.5  # Default score (middle of 2-5 range)
    
    def apply_material_bonus(self, product_data: Dict[str, Any], base_score: float) -> float:
        """Apply material-based bonus to score (ensuring 2-5 range)"""
        material = str(product_data.get('material', '')).lower()
        bonuses = self.config.get("material_bonuses", {})
        
        for material_type, bonus in bonuses.items():
            if material_type.replace('_', ' ') in material:
                new_score = base_score + bonus
                return max(2.0, min(5.0, new_score))  # Clamp to 2-5 range
        
        return base_score
    
    def apply_thread_count_bonus(self, product_data: Dict[str, Any], base_score: float) -> float:
        """Apply thread count bonus to score"""
        # This would need to be extracted from product description or specifications
        # For now, return base score
        return base_score
    
    def update_all_product_scores(self, db_path: str = "multi_platform_products.db"):
        """Update all product scores in database using current configuration"""
        print(f"🔄 Updating product scores using configuration: {self.config.get('overall_score', {}).get('method', 'price_based')}")
        print("=" * 60)
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # No price range needed for overall_value_score method
                price_range = None
                
                # Get all products with commission rates
                cursor.execute("""
                    SELECT p.*, ad.commission_rate
                    FROM products p
                    LEFT JOIN affiliation_details ad ON p.id = ad.product_id
                """)
                products = cursor.fetchall()
                
                # Get column names
                cursor.execute("PRAGMA table_info(products)")
                product_columns = [col[1] for col in cursor.fetchall()]
                columns = product_columns + ['commission_rate']
                
                updated_count = 0
                
                for product_row in products:
                    try:
                        # Convert row to dictionary
                        product_data = dict(zip(columns, product_row))
                        
                        # Calculate new overall score and sub-scores
                        new_overall_score = self.calculate_overall_score(product_data, price_range)
                        sub_scores = self.calculate_sub_scores(product_data)
                        
                        # Update database with overall score and all sub-scores
                        cursor.execute("""
                            UPDATE products 
                            SET overall_score = ?, popularity_score = ?, brand_reputation_score = ?, 
                                price_value_score = ?
                            WHERE id = ?
                        """, (new_overall_score, 
                              sub_scores.get('popularity_score', 0), 
                              sub_scores.get('brand_reputation_score', 0),
                              sub_scores.get('price_value_score', 0),
                              product_data['id']))
                        
                        updated_count += 1
                        
                        if updated_count % 5 == 0:
                            print(f"   Progress: {updated_count}/{len(products)} products updated")
                    
                    except Exception as e:
                        print(f"   ❌ Error updating product {product_data.get('id', 'Unknown')}: {str(e)}")
                        continue
                
                conn.commit()
                print(f"✅ Successfully updated {updated_count}/{len(products)} products")
                
        except Exception as e:
            print(f"❌ Error updating database: {str(e)}")
    
    def show_scoring_summary(self, db_path: str = "multi_platform_products.db"):
        """Show summary of current scoring data"""
        print(f"\n📊 Scoring Summary (Method: {self.config.get('overall_score', {}).get('method', 'price_based')})")
        print("=" * 60)
        
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                # Get scoring statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_products,
                        AVG(overall_score) as avg_overall_score,
                        AVG(overall_value_score) as avg_overall_value_score
                    FROM products
                """)
                
                stats = cursor.fetchone()
                
                print(f"Total Products: {stats[0]}")
                print(f"Average Overall Score: {stats[1]:.2f}")
                print(f"Average Overall Value Score: {stats[2]:.2f}")
                
                # Show top scoring products
                print("\n🏆 Top 5 Products by Overall Score:")
                cursor.execute("""
                    SELECT title, overall_score, overall_value_score
                    FROM products 
                    WHERE overall_score IS NOT NULL
                    ORDER BY overall_score DESC 
                    LIMIT 5
                """)
                
                top_products = cursor.fetchall()
                for i, (title, overall_score, overall_value_score) in enumerate(top_products, 1):
                    print(f"   {i}. {title[:50]}...")
                    print(f"      Overall Score: {overall_score:.2f}, Value Score: {overall_value_score:.2f}")
                
        except Exception as e:
            print(f"❌ Error showing summary: {str(e)}")
    
    def list_available_methods(self):
        """List all available scoring methods"""
        print("📋 Available Scoring Methods:")
        print("=" * 40)
        
        methods = self.config.get("overall_score", {}).get("options", {})
        for method_name, method_info in methods.items():
            print(f"   {method_name}:")
            print(f"      Description: {method_info.get('description', 'No description')}")
            print(f"      Formula: {method_info.get('formula', 'No formula')}")
            print()

def main():
    """Main function to demonstrate the configurable scoring system"""
    scoring_system = ConfigurableScoringSystem()
    
    # Show available methods
    scoring_system.list_available_methods()
    
    # Update all product scores
    scoring_system.update_all_product_scores()
    
    # Show summary
    scoring_system.show_scoring_summary()
    
    print("\n🎉 Configurable scoring system demonstration completed!")
    print("\n💡 To change scoring method, edit 'scoring_config.json' and run this script again.")

if __name__ == "__main__":
    main()
