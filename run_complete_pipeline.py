#!/usr/bin/env python3
"""
Complete Pipeline Runner with Progress Tracking
Runs the full product pipeline with detailed progress and statistics
"""

import sqlite3
import time
import sys
from pathlib import Path
from typing import Dict, Any
import csv

# Import our systems
from core.dynamic_pros_cons_generator import DynamicProsConsGenerator
from core.configurable_scoring_system import ConfigurableScoringSystem
from process_affiliate_links import AffiliateLinksProcessor


class CompletePipelineRunner:
    """Complete pipeline runner with progress tracking"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.stats = {
            'start_time': None,
            'end_time': None,
            'total_products': 0,
            'products_processed': 0,
            'features_generated': 0,
            'scores_calculated': 0,
            'affiliate_links_processed': 0,
            'errors': 0,
            'warnings': 0
        }
    
    def print_progress_bar(self, current: int, total: int, prefix: str = 'Progress', 
                          suffix: str = 'Complete', length: int = 50):
        """Print a progress bar"""
        percent = ("{0:.1f}").format(100 * (current / float(total)))
        filled_length = int(length * current // total)
        bar = '█' * filled_length + '-' * (length - filled_length)
        
        print(f'\r{prefix} |{bar}| {current}/{total} ({percent}%) {suffix}', end='\r')
        
        # Print new line when complete
        if current == total:
            print()
    
    def run_complete_pipeline(self) -> Dict[str, Any]:
        """Run the complete pipeline with progress tracking"""
        print("🚀 COMPLETE PRODUCT PIPELINE")
        print("=" * 60)
        
        self.stats['start_time'] = time.time()
        
        # Step 1: Process Affiliate Links
        print("\n📊 Step 1: Processing Affiliate Links...")
        self._process_affiliate_links()
        
        # Step 2: Generate Dynamic Pros/Cons
        print("\n🔍 Step 2: Generating Product-Specific Features...")
        self._generate_dynamic_features()
        
        # Step 3: Calculate Product Scores
        print("\n📈 Step 3: Calculating Product Scores...")
        self._calculate_product_scores()
        
        # Step 4: Final Statistics
        print("\n📋 Step 4: Generating Final Statistics...")
        self._generate_final_statistics()
        
        self.stats['end_time'] = time.time()
        
        return self.stats
    
    def _process_affiliate_links(self):
        """Process affiliate links with progress tracking"""
        try:
            csv_file = "products/product_affilate_links.csv"
            if not Path(csv_file).exists():
                print(f"⚠️  Affiliate links CSV not found: {csv_file}")
                return
            
            # Count total rows for progress tracking
            with open(csv_file, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                total_rows = sum(1 for row in reader)
            
            print(f"   📁 Processing {total_rows} affiliate links...")
            
            # Process affiliate links
            processor = AffiliateLinksProcessor(self.db_path)
            results = processor.process_csv_file(csv_file)
            
            self.stats['affiliate_links_processed'] = results['total_rows']
            self.stats['total_products'] = results['processed_products']
            
            print(f"   ✅ Processed {results['total_rows']} affiliate links")
            print(f"   ✅ Created/Updated {results['processed_products']} products")
            
            if results['errors'] > 0:
                self.stats['errors'] += results['errors']
                print(f"   ⚠️  {results['errors']} errors encountered")
                
        except Exception as e:
            print(f"   ❌ Error processing affiliate links: {e}")
            self.stats['errors'] += 1
    
    def _generate_dynamic_features(self):
        """Generate dynamic pros/cons with progress tracking"""
        try:
            # Get total products for progress tracking
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products")
                total_products = cursor.fetchone()[0]
            
            print(f"   🔄 Generating features for {total_products} products...")
            
            # Generate dynamic features
            generator = DynamicProsConsGenerator(self.db_path)
            results = generator.regenerate_all_product_features()
            
            self.stats['products_processed'] = results['processed_products']
            self.stats['features_generated'] = results['total_features_generated']
            
            print(f"   ✅ Generated {results['total_features_generated']} features")
            print(f"   ✅ Processed {results['processed_products']} products")
            
            if results['errors'] > 0:
                self.stats['errors'] += results['errors']
                print(f"   ⚠️  {results['errors']} errors encountered")
                
        except Exception as e:
            print(f"   ❌ Error generating features: {e}")
            self.stats['errors'] += 1
    
    def _calculate_product_scores(self):
        """Calculate product scores with progress tracking"""
        try:
            # Get total products for progress tracking
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products")
                total_products = cursor.fetchone()[0]
            
            print(f"   📊 Calculating scores for {total_products} products...")
            
            # Initialize scoring system
            scoring_system = ConfigurableScoringSystem()
            
            # Calculate scores
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all products with their data
                cursor.execute('''
                    SELECT p.id, p.amazon_product_id, p.brand, p.price, p.rating, p.review_count,
                           ad.commission_rate
                    FROM products p
                    LEFT JOIN affiliation_details ad ON p.id = ad.product_id
                ''')
                
                products = cursor.fetchall()
                
                for i, (product_id, amazon_id, brand, price, rating, review_count, commission_rate) in enumerate(products, 1):
                    # Show progress
                    self.print_progress_bar(i, len(products), prefix='Calculating Scores', suffix='Products')
                    
                    # Prepare product data
                    product_data = {
                        'id': product_id,
                        'amazon_product_id': amazon_id,
                        'brand': brand,
                        'price': price,
                        'rating': rating,
                        'review_count': review_count,
                        'commission_rate': commission_rate or 0.10
                    }
                    
                    # Calculate scores
                    overall_score = scoring_system.calculate_overall_score(product_data)
                    sub_scores = scoring_system.calculate_sub_scores(product_data)
                    
                    # Update database
                    cursor.execute('''
                        UPDATE products SET
                            overall_score = ?,
                            total_score = ?,
                            popularity_score = ?,
                            brand_reputation_score = ?,
                            overall_value_score = ?,
                            luxury_score = ?,
                            price_value_score = ?,
                            commission_score = ?
                        WHERE id = ?
                    ''', (
                        overall_score,
                        sub_scores.get('total_score', overall_score),
                        sub_scores.get('popularity_score', 3.0),
                        sub_scores.get('brand_reputation_score', 3.0),
                        sub_scores.get('overall_value_score', 3.0),
                        sub_scores.get('luxury_score', 3.0),
                        sub_scores.get('price_value_score', 3.0),
                        sub_scores.get('commission_score', 3.0),
                        product_id
                    ))
                
                conn.commit()
                self.stats['scores_calculated'] = len(products)
                
            print(f"\n   ✅ Calculated scores for {len(products)} products")
                
        except Exception as e:
            print(f"   ❌ Error calculating scores: {e}")
            self.stats['errors'] += 1
    
    def _generate_final_statistics(self):
        """Generate final database statistics"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Count records in each table
                tables = [
                    'products', 'product_features', 'brands', 'affiliation_details',
                    'platforms', 'product_categories', 'product_specifications',
                    'product_reviews', 'product_images'
                ]
                
                print("   📊 Final Database Statistics:")
                for table in tables:
                    try:
                        cursor.execute(f"SELECT COUNT(*) FROM {table}")
                        count = cursor.fetchone()[0]
                        print(f"      {table}: {count} records")
                    except:
                        print(f"      {table}: table not found")
                
                # Show sample data
                print("\n   📋 Sample Products with Scores:")
                cursor.execute("""
                    SELECT p.amazon_product_id, p.brand, p.price, p.overall_score, 
                           b.display_name, b.brand_tier
                    FROM products p
                    LEFT JOIN brands b ON p.brand_id = b.id
                    ORDER BY p.overall_score DESC
                    LIMIT 5
                """)
                
                results = cursor.fetchall()
                for amazon_id, brand, price, score, display_name, tier in results:
                    print(f"      {amazon_id} | {display_name} | ${price} | Score: {score:.1f}")
                
        except Exception as e:
            print(f"   ❌ Error generating statistics: {e}")
            self.stats['errors'] += 1
    
    def print_final_summary(self):
        """Print final pipeline summary"""
        elapsed_time = self.stats['end_time'] - self.stats['start_time']
        
        print("\n" + "=" * 60)
        print("🎉 PIPELINE COMPLETE!")
        print("=" * 60)
        print(f"⏱️  Total Time: {elapsed_time:.1f} seconds")
        print(f"📊 Products: {self.stats['total_products']}")
        print(f"🔍 Features Generated: {self.stats['features_generated']}")
        print(f"📈 Scores Calculated: {self.stats['scores_calculated']}")
        print(f"🔗 Affiliate Links: {self.stats['affiliate_links_processed']}")
        print(f"❌ Errors: {self.stats['errors']}")
        print(f"⚠️  Warnings: {self.stats['warnings']}")
        
        if self.stats['errors'] == 0:
            print("✅ SUCCESS: No errors encountered!")
        else:
            print(f"⚠️  {self.stats['errors']} errors encountered - check logs")
        
        success_rate = ((self.stats['products_processed'] / max(self.stats['total_products'], 1)) * 100)
        print(f"📈 Success Rate: {success_rate:.1f}%")


def main():
    """Main function to run the complete pipeline"""
    print("🚀 Starting Complete Product Pipeline...")
    
    # Initialize and run pipeline
    runner = CompletePipelineRunner()
    stats = runner.run_complete_pipeline()
    
    # Print final summary
    runner.print_final_summary()
    
    return stats


if __name__ == "__main__":
    main()
