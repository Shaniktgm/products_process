#!/usr/bin/env python3
"""
Enhanced Pipeline Runner
Orchestrates the complete 3-phase pipeline with Amazon API integration
"""

import os
import sys
from typing import Dict, Any, List

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from phase1_data_collection.phase1_data_collection import DataCollectionPipeline
from phase2_amazon_api.phase2_amazon_api import AmazonAPIDataCollectionPipeline
from phase3_content_generation.phase3_content_generation import ContentGenerationPipeline

class EnhancedPipelineRunner:
    """Complete 3-phase pipeline with Amazon API integration"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Initialize all pipeline phases
        self.phase1 = DataCollectionPipeline(db_path)
        self.phase2 = AmazonAPIDataCollectionPipeline(db_path)
        self.phase3 = ContentGenerationPipeline(db_path)
        
        # Overall statistics
        self.overall_stats = {
            'phase1': {},
            'phase2': {},
            'phase3': {},
            'total_products_processed': 0,
            'total_errors': 0,
            'execution_time': 0
        }
    
    def run_phase1_only(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run only Phase 1: CSV ingestion and basic scraping"""
        print("🚀 Running Phase 1 Only: Data Collection")
        print("=" * 60)
        
        results = self.phase1.run_data_collection(affiliate_csv_path)
        self.overall_stats['phase1'] = results
        
        print(f"\n🎉 Phase 1 Complete!")
        print(f"Results: {results}")
        
        return results
    
    def run_phase2_only(self) -> Dict[str, Any]:
        """Run only Phase 2: Amazon API data collection"""
        print("🚀 Running Phase 2 Only: Amazon API Data Collection")
        print("=" * 60)
        
        results = self.phase2.run_amazon_api_collection()
        self.overall_stats['phase2'] = results
        
        print(f"\n🎉 Phase 2 Complete!")
        print(f"Results: {results}")
        
        return results
    
    def run_phase3_only(self) -> Dict[str, Any]:
        """Run only Phase 3: Content generation"""
        print("🚀 Running Phase 3 Only: Content Generation")
        print("=" * 60)
        
        results = self.phase3.run_content_generation()
        self.overall_stats['phase3'] = results
        
        print(f"\n🎉 Phase 3 Complete!")
        print(f"Results: {results}")
        
        return results
    
    def run_phases_1_and_2(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run Phase 1 and 2: Data collection + Amazon API"""
        print("🚀 Running Phases 1 & 2: Data Collection + Amazon API")
        print("=" * 60)
        
        # Phase 1: CSV ingestion and basic scraping
        print("\n" + "="*60)
        print("PHASE 1: DATA COLLECTION")
        print("="*60)
        phase1_results = self.phase1.run_data_collection(affiliate_csv_path)
        self.overall_stats['phase1'] = phase1_results
        
        # Phase 2: Amazon API data collection
        print("\n" + "="*60)
        print("PHASE 2: AMAZON API DATA COLLECTION")
        print("="*60)
        phase2_results = self.phase2.run_amazon_api_collection()
        self.overall_stats['phase2'] = phase2_results
        
        # Combine results
        combined_results = {
            'phase1': phase1_results,
            'phase2': phase2_results,
            'total_products_processed': phase1_results.get('products_created', 0) + phase1_results.get('products_updated', 0),
            'total_errors': phase1_results.get('errors', 0) + phase2_results.get('errors', 0)
        }
        
        print(f"\n🎉 Phases 1 & 2 Complete!")
        print(f"Combined Results: {combined_results}")
        
        return combined_results
    
    def run_phases_2_and_3(self) -> Dict[str, Any]:
        """Run Phase 2 and 3: Amazon API + Content generation"""
        print("🚀 Running Phases 2 & 3: Amazon API + Content Generation")
        print("=" * 60)
        
        # Phase 2: Amazon API data collection
        print("\n" + "="*60)
        print("PHASE 2: AMAZON API DATA COLLECTION")
        print("="*60)
        phase2_results = self.phase2.run_amazon_api_collection()
        self.overall_stats['phase2'] = phase2_results
        
        # Phase 3: Content generation
        print("\n" + "="*60)
        print("PHASE 3: CONTENT GENERATION")
        print("="*60)
        phase3_results = self.phase3.run_content_generation()
        self.overall_stats['phase3'] = phase3_results
        
        # Combine results
        combined_results = {
            'phase2': phase2_results,
            'phase3': phase3_results,
            'total_products_processed': phase2_results.get('products_processed', 0),
            'total_errors': phase2_results.get('errors', 0) + phase3_results.get('errors', 0)
        }
        
        print(f"\n🎉 Phases 2 & 3 Complete!")
        print(f"Combined Results: {combined_results}")
        
        return combined_results
    
    def run_complete_pipeline(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run complete 3-phase pipeline"""
        import time
        start_time = time.time()
        
        print("🚀 Starting Complete Enhanced Pipeline")
        print("=" * 60)
        print("Phase 1: CSV Ingestion + Basic Scraping")
        print("Phase 2: Amazon API Data Collection")
        print("Phase 3: Content Generation + Scoring")
        print("=" * 60)
        
        # Phase 1: CSV ingestion and basic scraping
        print("\n" + "="*60)
        print("PHASE 1: DATA COLLECTION")
        print("="*60)
        phase1_results = self.phase1.run_data_collection(affiliate_csv_path)
        self.overall_stats['phase1'] = phase1_results
        
        # Phase 2: Amazon API data collection
        print("\n" + "="*60)
        print("PHASE 2: AMAZON API DATA COLLECTION")
        print("="*60)
        phase2_results = self.phase2.run_amazon_api_collection()
        self.overall_stats['phase2'] = phase2_results
        
        # Phase 3: Content generation
        print("\n" + "="*60)
        print("PHASE 3: CONTENT GENERATION")
        print("="*60)
        phase3_results = self.phase3.run_content_generation()
        self.overall_stats['phase3'] = phase3_results
        
        # Calculate execution time
        execution_time = time.time() - start_time
        self.overall_stats['execution_time'] = execution_time
        
        # Final summary
        print("\n" + "="*60)
        print("🎉 COMPLETE PIPELINE FINISHED!")
        print("="*60)
        print(f"⏱️ Total execution time: {execution_time:.2f} seconds")
        print(f"📊 Total products processed: {phase1_results.get('products_created', 0) + phase1_results.get('products_updated', 0)}")
        print(f"✅ Products updated with API data: {phase2_results.get('products_updated', 0)}")
        print(f"✨ Content generated: {phase3_results.get('pros_cons_generated', 0)} features, {phase3_results.get('summaries_generated', 0)} summaries")
        print(f"❌ Total errors: {phase1_results.get('errors', 0) + phase2_results.get('errors', 0) + phase3_results.get('errors', 0)}")
        
        return self.overall_stats
    
    def show_pipeline_status(self):
        """Show current status of all pipeline phases"""
        print("📊 Enhanced Pipeline Status")
        print("=" * 60)
        
        for phase, stats in self.overall_stats.items():
            if isinstance(stats, dict) and stats:
                print(f"\n{phase.upper()}:")
                for key, value in stats.items():
                    print(f"  {key}: {value}")

def main():
    """Main entry point for enhanced pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Pipeline with Amazon API Integration')
    parser.add_argument('--phase', choices=['1', '2', '3', '1+2', '2+3', 'all'], 
                       default='all', help='Which phase(s) to run')
    parser.add_argument('--csv', default='products/product_affilate_links.csv',
                       help='Path to affiliate links CSV file')
    parser.add_argument('--db', default='multi_platform_products.db',
                       help='Path to database file')
    
    args = parser.parse_args()
    
    # Initialize pipeline
    pipeline = EnhancedPipelineRunner(args.db)
    
    # Run selected phase(s)
    if args.phase == '1':
        pipeline.run_phase1_only(args.csv)
    elif args.phase == '2':
        pipeline.run_phase2_only()
    elif args.phase == '3':
        pipeline.run_phase3_only()
    elif args.phase == '1+2':
        pipeline.run_phases_1_and_2(args.csv)
    elif args.phase == '2+3':
        pipeline.run_phases_2_and_3()
    elif args.phase == 'all':
        pipeline.run_complete_pipeline(args.csv)
    
    # Show final status
    pipeline.show_pipeline_status()

if __name__ == "__main__":
    main()
