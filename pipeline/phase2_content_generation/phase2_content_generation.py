#!/usr/bin/env python3
"""
Phase 2: Content Generation Pipeline
Generates smart pros/cons, pretty titles, and product summaries from scraped data
"""

import os
import sys
from typing import Dict, Any

# Import our existing systems
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.generate_product_summaries import ProductSummaryGenerator
from core.smart_pros_cons_generator import SmartProsConsGenerator
from core.smart_pretty_title_generator import SmartPrettyTitleGenerator
from .extract_missing_fields import ProductDataExtractor

class ContentGenerationPipeline:
    """Phase 2: Generate content from scraped product data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Initialize content generation subsystems
        self.summary_generator = ProductSummaryGenerator(db_path)
        self.smart_pros_cons = SmartProsConsGenerator(db_path)
        self.smart_pretty_titles = SmartPrettyTitleGenerator(db_path)
        self.field_extractor = ProductDataExtractor(db_path)
        
        # Statistics tracking
        self.stats = {
            'pros_cons_generated': 0,
            'pretty_titles_generated': 0,
            'summaries_generated': 0,
            'fields_extracted': {},
            'products_with_extracted_fields': 0,
            'categories_assigned': 0,
            'errors': 0
        }
    
    def run_content_generation(self) -> Dict[str, Any]:
        """Run Phase 2: Content Generation Pipeline"""
        print("🚀 Starting Phase 2: Content Generation Pipeline")
        print("=" * 60)
        
        # Step 1: Generate smart, product-specific pros and cons
        print("\n✨ Step 1: Generating Smart Product-Specific Pros and Cons")
        try:
            # Use the smart pros/cons generator for intelligent, unique features
            smart_results = self.smart_pros_cons.generate_all_smart_features()
            self.stats['pros_cons_generated'] = smart_results.get('total_features_generated', 0)
            print(f"✅ Generated {self.stats['pros_cons_generated']} smart, product-specific features for {smart_results.get('processed_products', 0)} products")
        except Exception as e:
            print(f"❌ Error generating smart pros/cons: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 2: Extract missing fields from existing data
        print("\n🔍 Step 2: Extracting Missing Fields from Existing Data")
        try:
            field_extraction_results = self.field_extractor.process_all_products()
            self.stats['fields_extracted'] = field_extraction_results['fields_extracted']
            self.stats['products_with_extracted_fields'] = field_extraction_results['products_updated']
            self.stats['categories_assigned'] = field_extraction_results['categories_assigned']
            print(f"✅ Extracted fields for {self.stats['products_with_extracted_fields']} products")
            print(f"✅ Assigned categories to {self.stats['categories_assigned']} products")
            print(f"   📊 Fields extracted: {sum(self.stats['fields_extracted'].values())} total")
        except Exception as e:
            print(f"❌ Error extracting fields: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 3: Generate smart pretty titles
        print("\n🎨 Step 3: Generating Smart Pretty Titles")
        try:
            pretty_title_results = self.smart_pretty_titles.generate_all_pretty_titles()
            self.stats['pretty_titles_generated'] = pretty_title_results.get('titles_generated', 0)
            print(f"✅ Generated smart pretty titles for {self.stats['pretty_titles_generated']} products")
        except Exception as e:
            print(f"❌ Error generating pretty titles: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 4: Generate product summaries
        print("\n📝 Step 4: Generating Product Summaries")
        try:
            summary_results = self.summary_generator.generate_all_summaries()
            self.stats['summaries_generated'] = summary_results.get('successful', 0)
            print(f"✅ Generated summaries for {self.stats['summaries_generated']} products")
        except Exception as e:
            print(f"❌ Error generating summaries: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 5: Calculate product scores (from main_pipeline.py)
        print("\n📊 Step 5: Calculating Product Scores")
        try:
            from core.configurable_scoring_system import ConfigurableScoringSystem
            scoring_system = ConfigurableScoringSystem(self.db_path)
            scoring_results = scoring_system.update_all_product_scores(self.db_path)
            print(f"✅ Calculated scores for products")
        except Exception as e:
            print(f"❌ Error calculating scores: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Final statistics
        print(f"\n📊 Phase 2 Complete!")
        print(f"   ✨ Pros/Cons generated: {self.stats['pros_cons_generated']}")
        print(f"   🎨 Pretty titles generated: {self.stats['pretty_titles_generated']}")
        print(f"   📝 Summaries generated: {self.stats['summaries_generated']}")
        print(f"   🔍 Fields extracted: {sum(self.stats['fields_extracted'].values())}")
        print(f"   📂 Categories assigned: {self.stats['categories_assigned']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
        
        return self.stats

def main():
    """Run Phase 2: Content Generation Pipeline"""
    pipeline = ContentGenerationPipeline()
    results = pipeline.run_content_generation()
    
    print(f"\n🎉 Phase 2 Complete!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
