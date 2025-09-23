#!/usr/bin/env python3
"""
Enhanced Pipeline Runner - Root Level
Simple entry point for the enhanced 3-phase pipeline with Amazon API integration
"""

import sys
import os

# Add pipeline directory to path
sys.path.append(os.path.join(os.path.dirname(__file__), 'pipeline'))

from pipeline.run_enhanced_pipeline import EnhancedPipelineRunner

def main():
    """Run the enhanced pipeline"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Enhanced Pipeline with Amazon API Integration')
    parser.add_argument('--phase', choices=['1', '2', '3', '1+2', '2+3', 'all'], 
                       default='all', help='Which phase(s) to run')
    parser.add_argument('--csv', default='products/product_affilate_links.csv',
                       help='Path to affiliate links CSV file')
    parser.add_argument('--db', default='multi_platform_products.db',
                       help='Path to database file')
    
    args = parser.parse_args()
    
    print("🚀 Enhanced Pipeline with Amazon API Integration")
    print("=" * 60)
    print("Phase 1: CSV Ingestion + Basic Scraping")
    print("Phase 2: Amazon API Data Collection (2s delay)")
    print("Phase 3: Content Generation + Scoring")
    print("=" * 60)
    
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
