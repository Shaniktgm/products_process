#!/usr/bin/env python3
"""
Script to remove pricing-related pros and cons from the database
This script will:
1. Identify all features related to pricing, cost, value, etc.
2. Remove them from the product_features table
3. Update the database
"""

import sqlite3
import re
from typing import List, Dict, Any

class PricingProsConsRemover:
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Keywords that indicate pricing-related content
        self.pricing_keywords = [
            'price', 'cost', 'expensive', 'cheap', 'affordable', 'budget',
            'value', 'worth', 'overpriced', 'premium price', 'higher price',
            'lower price', 'price point', 'pricing', 'costly', 'inexpensive',
            'economical', 'luxury price', 'discount', 'sale', 'deal',
            'money', 'dollar', 'cent', 'investment', 'spend', 'pay',
            'purchase', 'buy', 'cost-effective', 'bang for buck', 'roi'
        ]
        
        # Categories that are pricing-related
        self.pricing_categories = [
            'price', 'value', 'cost', 'pricing', 'affordability', 'budget'
        ]
    
    def connect_database(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close_database(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def is_pricing_related(self, text: str, category: str = None) -> bool:
        """Check if a feature is pricing-related"""
        if not text:
            return False
        
        text_lower = text.lower()
        
        # Check for pricing keywords in the text
        for keyword in self.pricing_keywords:
            if keyword in text_lower:
                return True
        
        # Check if category is pricing-related
        if category and category.lower() in self.pricing_categories:
            return True
        
        return False
    
    def get_pricing_related_features(self) -> List[Dict[str, Any]]:
        """Get all pricing-related features from the database"""
        cursor = self.conn.cursor()
        cursor.execute("""
            SELECT id, product_id, feature_text, feature_type, category
            FROM product_features
            WHERE feature_type IN ('pro', 'con')
        """)
        
        features = []
        for row in cursor.fetchall():
            feature = dict(row)
            if self.is_pricing_related(feature['feature_text'], feature['category']):
                features.append(feature)
        
        return features
    
    def remove_pricing_features(self):
        """Remove all pricing-related features from the database"""
        print("🔄 Removing pricing-related pros and cons...")
        print("=" * 60)
        
        self.connect_database()
        
        try:
            # Get pricing-related features
            pricing_features = self.get_pricing_related_features()
            print(f"📊 Found {len(pricing_features)} pricing-related features to remove")
            
            if not pricing_features:
                print("✅ No pricing-related features found. Nothing to remove.")
                return
            
            # Show some examples before removal
            print(f"\n📋 Examples of features to be removed:")
            for i, feature in enumerate(pricing_features[:10]):
                print(f"   {i+1}. [{feature['feature_type'].upper()}] {feature['feature_text']}")
            
            if len(pricing_features) > 10:
                print(f"   ... and {len(pricing_features) - 10} more")
            
            # Remove pricing-related features
            cursor = self.conn.cursor()
            removed_count = 0
            
            for feature in pricing_features:
                cursor.execute("DELETE FROM product_features WHERE id = ?", (feature['id'],))
                removed_count += 1
            
            self.conn.commit()
            
            print(f"\n✅ Successfully removed {removed_count} pricing-related features")
            
            # Show final statistics
            self.show_final_statistics()
            
        except Exception as e:
            print(f"❌ Removal failed: {e}")
            raise
        finally:
            self.close_database()
    
    def show_final_statistics(self):
        """Show final statistics after removal"""
        cursor = self.conn.cursor()
        
        # Count remaining features
        cursor.execute("SELECT COUNT(*) FROM product_features")
        total_features = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_features WHERE feature_type = 'pro'")
        total_pros = cursor.fetchone()[0]
        
        cursor.execute("SELECT COUNT(*) FROM product_features WHERE feature_type = 'con'")
        total_cons = cursor.fetchone()[0]
        
        print(f"\n📊 Final Statistics:")
        print(f"   Total features remaining: {total_features}")
        print(f"   Pros remaining: {total_pros}")
        print(f"   Cons remaining: {total_cons}")
        
        # Show some examples of remaining features
        cursor.execute("""
            SELECT feature_text, feature_type 
            FROM product_features 
            WHERE feature_type IN ('pro', 'con')
            ORDER BY RANDOM()
            LIMIT 5
        """)
        
        examples = cursor.fetchall()
        if examples:
            print(f"\n📋 Examples of remaining features:")
            for feature_text, feature_type in examples:
                print(f"   [{feature_type.upper()}] {feature_text}")

def main():
    """Main function"""
    print("🚀 Removing Pricing-Related Pros and Cons")
    print("=" * 60)
    
    remover = PricingProsConsRemover()
    remover.remove_pricing_features()

if __name__ == "__main__":
    main()
