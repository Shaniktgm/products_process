#!/usr/bin/env python3
"""
Complete Pipeline Runner
Orchestrates Phase 1 (Data Collection) and Phase 2 (Content Generation)
"""

import argparse
import sys
from typing import Dict, Any

from .phase1_data_collection import DataCollectionPipeline
from .phase2_content_generation import ContentGenerationPipeline

class CompletePipelineRunner:
    """Orchestrates both phases of the product pipeline"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.phase1 = DataCollectionPipeline(db_path)
        self.phase2 = ContentGenerationPipeline(db_path)
        
        # Combined statistics
        self.combined_stats = {
            'phase1': {},
            'phase2': {},
            'total_processing_time': 0,
            'overall_success': True
        }
    
    def run_complete_pipeline(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run both phases sequentially"""
        import time
        start_time = time.time()
        
        print("🚀 Starting Complete Product Pipeline")
        print("=" * 80)
        print("This pipeline consists of two distinct phases:")
        print("📋 Phase 1: Data Collection (CSV → Amazon Scraping)")
        print("✨ Phase 2: Content Generation (Pros/Cons, Titles, Summaries)")
        print("=" * 80)
        
        try:
            # Phase 1: Data Collection
            print("\n" + "="*60)
            print("🎯 PHASE 1: DATA COLLECTION")
            print("="*60)
            
            phase1_results = self.phase1.run_data_collection(affiliate_csv_path)
            self.combined_stats['phase1'] = phase1_results
            
            # Check if Phase 1 was successful
            if phase1_results.get('errors', 0) > phase1_results.get('processed', 0) * 0.5:
                print("⚠️ Phase 1 had many errors. Consider reviewing before proceeding.")
                response = input("Continue to Phase 2? (y/n): ").lower().strip()
                if response != 'y':
                    print("🛑 Pipeline stopped by user.")
                    return self.combined_stats
            
            # Phase 2: Content Generation
            print("\n" + "="*60)
            print("🎯 PHASE 2: CONTENT GENERATION")
            print("="*60)
            
            phase2_results = self.phase2.run_content_generation()
            self.combined_stats['phase2'] = phase2_results
            
            # Calculate total time
            end_time = time.time()
            self.combined_stats['total_processing_time'] = end_time - start_time
            
            # Final summary
            self._print_final_summary()
            
        except KeyboardInterrupt:
            print("\n🛑 Pipeline interrupted by user.")
            self.combined_stats['overall_success'] = False
        except Exception as e:
            print(f"\n❌ Pipeline failed with error: {e}")
            import traceback
            traceback.print_exc()
            self.combined_stats['overall_success'] = False
        
        return self.combined_stats
    
    def run_phase1_only(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run only Phase 1: Data Collection"""
        print("🚀 Running Phase 1 Only: Data Collection")
        print("=" * 60)
        
        phase1_results = self.phase1.run_data_collection(affiliate_csv_path)
        self.combined_stats['phase1'] = phase1_results
        self.combined_stats['phase2'] = {'skipped': True, 'message': 'Phase 2 not run'}
        
        return self.combined_stats
    
    def run_phase2_only(self) -> Dict[str, Any]:
        """Run only Phase 2: Content Generation"""
        print("🚀 Running Phase 2 Only: Content Generation")
        print("=" * 60)
        
        phase2_results = self.phase2.run_content_generation()
        self.combined_stats['phase1'] = {'skipped': True, 'message': 'Phase 1 not run'}
        self.combined_stats['phase2'] = phase2_results
        
        return self.combined_stats
    
    def _print_final_summary(self):
        """Print final pipeline summary"""
        print("\n" + "="*80)
        print("🎉 COMPLETE PIPELINE SUMMARY")
        print("="*80)
        
        # Phase 1 Summary
        phase1 = self.combined_stats['phase1']
        if not phase1.get('skipped'):
            print(f"📋 PHASE 1 - DATA COLLECTION:")
            print(f"   ✅ Affiliate links processed: {phase1.get('processed', 0)}")
            print(f"   🆕 New products created: {phase1.get('products_created', 0)}")
            print(f"   🔄 Products updated: {phase1.get('products_updated', 0)}")
            print(f"   🖼️ Images downloaded: {phase1.get('images_downloaded', 0)}")
            print(f"   ❌ Errors: {phase1.get('errors', 0)}")
        else:
            print(f"📋 PHASE 1 - SKIPPED: {phase1.get('message', 'Not run')}")
        
        # Phase 2 Summary
        phase2 = self.combined_stats['phase2']
        if not phase2.get('skipped'):
            print(f"\n✨ PHASE 2 - CONTENT GENERATION:")
            print(f"   ✨ Pros/Cons generated: {phase2.get('pros_cons_generated', 0)}")
            print(f"   🎨 Pretty titles generated: {phase2.get('pretty_titles_generated', 0)}")
            print(f"   📝 Summaries generated: {phase2.get('summaries_generated', 0)}")
            print(f"   🔍 Fields extracted: {sum(phase2.get('fields_extracted', {}).values())}")
            print(f"   📂 Categories assigned: {phase2.get('categories_assigned', 0)}")
            print(f"   ❌ Errors: {phase2.get('errors', 0)}")
        else:
            print(f"\n✨ PHASE 2 - SKIPPED: {phase2.get('message', 'Not run')}")
        
        # Overall Summary
        print(f"\n⏱️ TOTAL PROCESSING TIME: {self.combined_stats['total_processing_time']:.2f} seconds")
        print(f"🎯 OVERALL SUCCESS: {'✅ SUCCESS' if self.combined_stats['overall_success'] else '❌ FAILED'}")
        print("="*80)

def main():
    """Main entry point with command line arguments"""
    parser = argparse.ArgumentParser(description='Complete Product Pipeline Runner')
    parser.add_argument('--csv', default='products/product_affilate_links.csv',
                       help='Path to CSV file with affiliate links')
    parser.add_argument('--db', default='multi_platform_products.db',
                       help='Path to SQLite database')
    parser.add_argument('--phase', choices=['1', '2', 'both'], default='both',
                       help='Which phase to run: 1 (data collection), 2 (content generation), or both')
    
    args = parser.parse_args()
    
    # Initialize pipeline runner
    runner = CompletePipelineRunner(args.db)
    
    try:
        if args.phase == '1':
            results = runner.run_phase1_only(args.csv)
        elif args.phase == '2':
            results = runner.run_phase2_only()
        else:  # both
            results = runner.run_complete_pipeline(args.csv)
        
        # Exit with appropriate code
        sys.exit(0 if results['overall_success'] else 1)
        
    except Exception as e:
        print(f"❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    main()
