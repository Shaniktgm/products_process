#!/usr/bin/env python3
"""
Add comprehensive scoring system to existing database
"""

import sys
import os
import sqlite3
import csv
from typing import Dict, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

class ScoringSystemUpdater:
    """Add scoring system to existing database"""
    
    def __init__(self):
        self.db = MultiPlatformDatabaseService("multi_platform_products.db")
    
    def add_scoring_columns(self):
        """Add scoring columns to existing products table"""
        print("🔧 Adding Scoring Columns to Database")
        print("=" * 50)
        
        try:
            with sqlite3.connect("multi_platform_products.db") as conn:
                cursor = conn.cursor()
                
                # Add new scoring columns (removed score_value)
                scoring_columns = [
                    "total_score REAL",
                    "popularity_score REAL", 
                    "brand_reputation_score REAL",
                    "overall_value_score REAL",
                    "luxury_score REAL",
                    "overall_score REAL"
                ]
                
                for column in scoring_columns:
                    column_name = column.split()[0]
                    try:
                        cursor.execute(f"ALTER TABLE products ADD COLUMN {column}")
                        print(f"   ✅ Added column: {column_name}")
                    except sqlite3.OperationalError as e:
                        if "duplicate column name" in str(e):
                            print(f"   ⚠️  Column {column_name} already exists")
                        else:
                            print(f"   ❌ Error adding {column_name}: {e}")
                
                conn.commit()
                print("✅ Scoring columns added successfully")
                
        except Exception as e:
            print(f"❌ Error adding scoring columns: {str(e)}")
    
    def calculate_overall_score(self, product_data: Dict[str, Any]) -> float:
        """
        Calculate overall_score - easily configurable method
        Currently: overall_score = price
        """
        # TODO: Make this method easily configurable
        # For now: overall_score = price
        price = product_data.get('price')
        if price and price > 0:
            return float(price)
        return 0.0
    
    def update_products_with_scoring(self):
        """Update all products with scoring data"""
        print("\n📊 Updating Products with Scoring Data")
        print("=" * 50)
        
        try:
            with sqlite3.connect("multi_platform_products.db") as conn:
                cursor = conn.cursor()
                
                # Get all products
                cursor.execute("SELECT id, price FROM products")
                products = cursor.fetchall()
                
                print(f"Found {len(products)} products to update")
                
                updated_count = 0
                
                for product_id, price in products:
                    try:
                        # Calculate overall_score (currently = price)
                        overall_score = self.calculate_overall_score({'price': price})
                        
                        # Update product with scoring data
                        cursor.execute("""
                            UPDATE products SET
                                overall_score = ?
                            WHERE id = ?
                        """, (overall_score, product_id))
                        
                        updated_count += 1
                        
                        if updated_count % 5 == 0:
                            print(f"   Progress: {updated_count}/{len(products)} products updated")
                    
                    except Exception as e:
                        print(f"   ❌ Error updating product {product_id}: {str(e)}")
                        continue
                
                conn.commit()
                print(f"✅ Successfully updated {updated_count}/{len(products)} products with scoring data")
                
        except Exception as e:
            print(f"❌ Error updating products: {str(e)}")
    
    def import_csv_scoring_data(self):
        """Import scoring data from CSV files"""
        print("\n📥 Importing Scoring Data from CSV Files")
        print("=" * 50)
        
        # Import from filtered products CSV
        self._import_from_filtered_products()
        
        # Import from three rows CSV
        self._import_from_three_rows()
    
    def _import_from_filtered_products(self):
        """Import scoring data from filtered products CSV"""
        print("\n📋 Importing from filtered_products.csv...")
        
        try:
            with open("old/sheets_filtered_products.csv", 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                products = list(reader)
            
            print(f"Found {len(products)} products in filtered CSV")
            
            with sqlite3.connect("multi_platform_products.db") as conn:
                cursor = conn.cursor()
                
                updated_count = 0
                
                for row in products:
                    try:
                        # Extract scoring data
                        total_score = self._extract_score(row.get('Total score', ''))
                        popularity_score = self._extract_score(row.get('Popularity (sub score)', ''))
                        brand_reputation_score = self._extract_score(row.get('Brand Reputation (sub score)', ''))
                        overall_value_score = self._extract_score(row.get('Overall Value (sub score)', ''))
                        luxury_score = self._extract_score(row.get('Luxury (sub score)', ''))
                        
                        # Find matching product by title
                        title = row.get('Name', '').strip()
                        if title:
                            cursor.execute("SELECT id, price FROM products WHERE title = ?", (title,))
                            product = cursor.fetchone()
                            
                            if product:
                                product_id, price = product
                                
                                # Calculate overall_score (currently = price)
                                overall_score = self.calculate_overall_score({'price': price})
                                
                                # Update with CSV scoring data
                                cursor.execute("""
                                    UPDATE products SET
                                        total_score = ?,
                                        popularity_score = ?,
                                        brand_reputation_score = ?,
                                        overall_value_score = ?,
                                        luxury_score = ?,
                                        overall_score = ?
                                    WHERE id = ?
                                """, (
                                    total_score, popularity_score, brand_reputation_score,
                                    overall_value_score, luxury_score, overall_score, product_id
                                ))
                                
                                updated_count += 1
                                print(f"   ✅ Updated: {title[:50]}...")
                    
                    except Exception as e:
                        print(f"   ❌ Error processing {row.get('Name', 'Unknown')}: {str(e)}")
                        continue
                
                conn.commit()
                print(f"✅ Updated {updated_count} products from filtered CSV")
                
        except Exception as e:
            print(f"❌ Error importing from filtered CSV: {str(e)}")
    
    def _import_from_three_rows(self):
        """Import scoring data from three rows CSV"""
        print("\n📋 Importing from products_three_rows.csv...")
        
        try:
            with open("sheets_raw_data/products_three_rows.csv", 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                products = list(reader)
            
            print(f"Found {len(products)} products in three rows CSV")
            
            with sqlite3.connect("multi_platform_products.db") as conn:
                cursor = conn.cursor()
                
                updated_count = 0
                
                for row in products:
                    try:
                        # Extract basic data
                        title = row.get('title', '').strip()
                        rating = self._extract_rating(row.get('rating', ''))
                        review_count = self._extract_review_count(row.get('review_count', ''))
                        
                        if title:
                            # Find matching product by title
                            cursor.execute("SELECT id, price FROM products WHERE title = ?", (title,))
                            product = cursor.fetchone()
                            
                            if product:
                                product_id, price = product
                                
                                # Calculate overall_score (currently = price)
                                overall_score = self.calculate_overall_score({'price': price})
                                
                                # Calculate estimated scores based on rating and review count
                                estimated_total_score = self._estimate_total_score(rating, review_count)
                                estimated_popularity = self._estimate_popularity_score(review_count)
                                estimated_brand_reputation = self._estimate_brand_reputation_score(rating)
                                estimated_value = self._estimate_value_score(price, rating)
                                estimated_luxury = self._estimate_luxury_score(price)
                                
                                # Update with calculated scoring data
                                cursor.execute("""
                                    UPDATE products SET
                                        total_score = ?,
                                        popularity_score = ?,
                                        brand_reputation_score = ?,
                                        overall_value_score = ?,
                                        luxury_score = ?,
                                        overall_score = ?
                                    WHERE id = ?
                                """, (
                                    estimated_total_score, estimated_popularity, estimated_brand_reputation,
                                    estimated_value, estimated_luxury, overall_score, product_id
                                ))
                                
                                updated_count += 1
                                print(f"   ✅ Updated: {title[:50]}...")
                    
                    except Exception as e:
                        print(f"   ❌ Error processing {row.get('title', 'Unknown')}: {str(e)}")
                        continue
                
                conn.commit()
                print(f"✅ Updated {updated_count} products from three rows CSV")
                
        except Exception as e:
            print(f"❌ Error importing from three rows CSV: {str(e)}")
    
    def _extract_score(self, score_str: str) -> Optional[float]:
        """Extract numeric score from string"""
        if not score_str:
            return None
        
        try:
            return float(score_str)
        except ValueError:
            return None
    
    def _extract_rating(self, rating_str: str) -> Optional[float]:
        """Extract rating from string"""
        if not rating_str:
            return None
        
        try:
            return float(rating_str)
        except ValueError:
            return None
    
    def _extract_review_count(self, review_count_str: str) -> int:
        """Extract review count from string"""
        if not review_count_str:
            return 0
        
        try:
            return int(review_count_str)
        except ValueError:
            return 0
    
    def _estimate_total_score(self, rating: Optional[float], review_count: int) -> float:
        """Estimate total score based on rating and review count"""
        if not rating:
            return 5.0  # Default score
        
        # Base score from rating (scale 1-5 to 1-10)
        base_score = rating * 2
        
        # Bonus for high review count (indicates popularity/trust)
        if review_count > 1000:
            bonus = 1.0
        elif review_count > 500:
            bonus = 0.5
        else:
            bonus = 0.0
        
        return min(base_score + bonus, 10.0)
    
    def _estimate_popularity_score(self, review_count: int) -> float:
        """Estimate popularity score based on review count"""
        if review_count > 5000:
            return 9.0
        elif review_count > 2000:
            return 8.0
        elif review_count > 1000:
            return 7.0
        elif review_count > 500:
            return 6.0
        else:
            return 5.0
    
    def _estimate_brand_reputation_score(self, rating: Optional[float]) -> float:
        """Estimate brand reputation score based on rating"""
        if not rating:
            return 5.0
        
        if rating >= 4.5:
            return 9.0
        elif rating >= 4.0:
            return 7.0
        elif rating >= 3.5:
            return 5.0
        else:
            return 3.0
    
    def _estimate_value_score(self, price: Optional[float], rating: Optional[float]) -> float:
        """Estimate value score based on price and rating"""
        if not price or not rating:
            return 5.0
        
        # Higher rating with lower price = better value
        if price < 100 and rating >= 4.0:
            return 9.0
        elif price < 150 and rating >= 4.0:
            return 8.0
        elif price < 200 and rating >= 3.5:
            return 7.0
        else:
            return 6.0
    
    def _estimate_luxury_score(self, price: Optional[float]) -> float:
        """Estimate luxury score based on price"""
        if not price:
            return 5.0
        
        if price > 250:
            return 9.0
        elif price > 150:
            return 7.0
        elif price > 100:
            return 5.0
        else:
            return 3.0
    
    def show_scoring_summary(self):
        """Show summary of scoring data"""
        print("\n📊 Scoring System Summary")
        print("=" * 50)
        
        try:
            with sqlite3.connect("multi_platform_products.db") as conn:
                cursor = conn.cursor()
                
                # Get scoring statistics
                cursor.execute("""
                    SELECT 
                        COUNT(*) as total_products,
                        AVG(overall_score) as avg_overall_score,
                        AVG(total_score) as avg_total_score,
                        AVG(popularity_score) as avg_popularity_score,
                        AVG(brand_reputation_score) as avg_brand_reputation_score,
                        AVG(overall_value_score) as avg_overall_value_score,
                        AVG(luxury_score) as avg_luxury_score
                    FROM products
                """)
                
                stats = cursor.fetchone()
                
                print(f"Total Products: {stats[0]}")
                print(f"Average Overall Score: {stats[1]:.2f}")
                print(f"Average Total Score: {stats[2]:.2f}")
                print(f"Average Popularity Score: {stats[3]:.2f}")
                print(f"Average Brand Reputation Score: {stats[4]:.2f}")
                print(f"Average Overall Value Score: {stats[5]:.2f}")
                print(f"Average Luxury Score: {stats[6]:.2f}")
                
                # Show top scoring products
                print("\n🏆 Top 5 Products by Overall Score:")
                cursor.execute("""
                    SELECT title, overall_score, total_score
                    FROM products 
                    WHERE overall_score IS NOT NULL
                    ORDER BY overall_score DESC 
                    LIMIT 5
                """)
                
                top_products = cursor.fetchall()
                for i, (title, overall_score, total_score) in enumerate(top_products, 1):
                    print(f"   {i}. {title[:50]}...")
                    print(f"      Overall Score: {overall_score:.2f}, Total Score: {total_score:.2f}")
                
        except Exception as e:
            print(f"❌ Error showing summary: {str(e)}")

def main():
    """Main function"""
    updater = ScoringSystemUpdater()
    
    # Step 1: Add scoring columns
    updater.add_scoring_columns()
    
    # Step 2: Update products with basic scoring
    updater.update_products_with_scoring()
    
    # Step 3: Import CSV scoring data
    updater.import_csv_scoring_data()
    
    # Step 4: Show summary
    updater.show_scoring_summary()
    
    print("\n🎉 Scoring system implementation completed!")

if __name__ == "__main__":
    main()
