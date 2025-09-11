#!/usr/bin/env python3
"""
Enhanced Automated Product Pipeline
Complete solution for adding new products with summaries, enhanced pros/cons, and Vercel upload
"""

import csv
import json
import sqlite3
import requests
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re
from datetime import datetime, timedelta
import statistics
import sys

# Import our existing systems
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.generate_product_summaries import ProductSummaryGenerator
from core.enhanced_pros_cons_system import EnhancedProsConsSystem
from image_management.upload_to_vercel import VercelBlobUploader
from image_management.update_local_to_vercel import LocalToVercelUpdater

class EnhancedAutomatedPipeline:
    """Complete enhanced pipeline for adding new products"""
    
    def __init__(self, db_path: str = "multi_platform_products.db", vercel_token: str = None):
        self.db_path = db_path
        self.images_dir = Path("images/products")
        self.images_dir.mkdir(exist_ok=True)
        
        # Initialize subsystems
        self.summary_generator = ProductSummaryGenerator(db_path)
        self.enhanced_pros_cons = EnhancedProsConsSystem(db_path)
        self.vercel_uploader = VercelBlobUploader(vercel_token) if vercel_token else None
        self.vercel_updater = LocalToVercelUpdater(db_path)
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
        # Statistics tracking
        self.stats = {
            'session_start': datetime.now(),
            'total_requests': 0,
            'successful_requests': 0,
            'failed_requests': 0,
            'request_times': [],
            'extraction_times': [],
            'validation_times': [],
            'database_times': [],
            'image_processing_times': [],
            'error_categories': {},
            'platform_stats': {},
            'affiliate_type_stats': {},
            'data_quality_scores': [],
            'retry_counts': {},
            'cache_hits': 0,
            'cache_misses': 0
        }
    
    def _track_request_time(self, start_time: float, end_time: float, success: bool, error_type: str = None):
        """Track request timing and success/failure"""
        request_time = end_time - start_time
        self.stats['request_times'].append(request_time)
        self.stats['total_requests'] += 1
        
        if success:
            self.stats['successful_requests'] += 1
        else:
            self.stats['failed_requests'] += 1
            if error_type:
                self.stats['error_categories'][error_type] = self.stats['error_categories'].get(error_type, 0) + 1
    
    def _track_extraction_time(self, start_time: float, end_time: float):
        """Track data extraction timing"""
        extraction_time = end_time - start_time
        self.stats['extraction_times'].append(extraction_time)
    
    def _track_validation_time(self, start_time: float, end_time: float):
        """Track validation timing"""
        validation_time = end_time - start_time
        self.stats['validation_times'].append(validation_time)
    
    def _track_database_time(self, start_time: float, end_time: float):
        """Track database operation timing"""
        db_time = end_time - start_time
        self.stats['database_times'].append(db_time)
    
    def _track_image_processing_time(self, start_time: float, end_time: float):
        """Track image processing timing"""
        image_time = end_time - start_time
        self.stats['image_processing_times'].append(image_time)
    
    def _track_platform_stats(self, platform: str, success: bool):
        """Track platform-specific statistics"""
        if platform not in self.stats['platform_stats']:
            self.stats['platform_stats'][platform] = {'total': 0, 'successful': 0, 'failed': 0}
        
        self.stats['platform_stats'][platform]['total'] += 1
        if success:
            self.stats['platform_stats'][platform]['successful'] += 1
        else:
            self.stats['platform_stats'][platform]['failed'] += 1
    
    def _track_affiliate_type_stats(self, affiliate_type: str, success: bool):
        """Track affiliate type statistics"""
        if affiliate_type not in self.stats['affiliate_type_stats']:
            self.stats['affiliate_type_stats'][affiliate_type] = {'total': 0, 'successful': 0, 'failed': 0}
        
        self.stats['affiliate_type_stats'][affiliate_type]['total'] += 1
        if success:
            self.stats['affiliate_type_stats'][affiliate_type]['successful'] += 1
        else:
            self.stats['affiliate_type_stats'][affiliate_type]['failed'] += 1
    
    def _track_data_quality_score(self, score: float):
        """Track data quality scores"""
        self.stats['data_quality_scores'].append(score)
    
    def _track_retry(self, url: str, retry_count: int):
        """Track retry attempts"""
        self.stats['retry_counts'][url] = retry_count
    
    def _track_cache_hit(self):
        """Track cache hit"""
        self.stats['cache_hits'] += 1
    
    def _track_cache_miss(self):
        """Track cache miss"""
        self.stats['cache_misses'] += 1
    
    def _print_progress_bar(self, current: int, total: int, prefix: str = 'Progress', suffix: str = 'Complete', length: int = 50):
        """Print a progress bar"""
        percent = ("{0:.1f}").format(100 * (current / float(total)))
        filled_length = int(length * current // total)
        bar = '█' * filled_length + '-' * (length - filled_length)
        
        # Calculate ETA
        if current > 0:
            elapsed_time = time.time() - self.stats['session_start'].timestamp()
            avg_time_per_item = elapsed_time / current
            remaining_items = total - current
            eta_seconds = remaining_items * avg_time_per_item
            eta_str = f"ETA: {int(eta_seconds//60)}m {int(eta_seconds%60)}s"
        else:
            eta_str = "ETA: calculating..."
        
        print(f'\r{prefix} |{bar}| {current}/{total} ({percent}%) {suffix} - {eta_str}', end='\r')
        
        # Print new line when complete
        if current == total:
            print()
    
    def get_processing_statistics(self) -> Dict[str, Any]:
        """Get comprehensive processing statistics"""
        session_duration = datetime.now() - self.stats['session_start']
        
        # Calculate success rates
        total_requests = self.stats['total_requests']
        success_rate = (self.stats['successful_requests'] / total_requests * 100) if total_requests > 0 else 0
        
        # Calculate timing statistics
        def get_timing_stats(times_list):
            if not times_list:
                return {'avg': 0, 'min': 0, 'max': 0, 'median': 0, 'total': 0}
            return {
                'avg': statistics.mean(times_list),
                'min': min(times_list),
                'max': max(times_list),
                'median': statistics.median(times_list),
                'total': sum(times_list)
            }
        
        # Calculate platform success rates
        platform_rates = {}
        for platform, stats in self.stats['platform_stats'].items():
            if stats['total'] > 0:
                platform_rates[platform] = {
                    'success_rate': (stats['successful'] / stats['total'] * 100),
                    'total': stats['total'],
                    'successful': stats['successful'],
                    'failed': stats['failed']
                }
        
        # Calculate affiliate type success rates
        affiliate_rates = {}
        for affiliate_type, stats in self.stats['affiliate_type_stats'].items():
            if stats['total'] > 0:
                affiliate_rates[affiliate_type] = {
                    'success_rate': (stats['successful'] / stats['total'] * 100),
                    'total': stats['total'],
                    'successful': stats['successful'],
                    'failed': stats['failed']
                }
        
        # Calculate data quality statistics
        data_quality_stats = {}
        if self.stats['data_quality_scores']:
            data_quality_stats = {
                'avg_score': statistics.mean(self.stats['data_quality_scores']),
                'min_score': min(self.stats['data_quality_scores']),
                'max_score': max(self.stats['data_quality_scores']),
                'median_score': statistics.median(self.stats['data_quality_scores'])
            }
        
        # Calculate throughput
        throughput = total_requests / session_duration.total_seconds() if session_duration.total_seconds() > 0 else 0
        
        return {
            'session_info': {
                'start_time': self.stats['session_start'].isoformat(),
                'duration_seconds': session_duration.total_seconds(),
                'duration_formatted': str(session_duration).split('.')[0]
            },
            'overall_stats': {
                'total_requests': total_requests,
                'successful_requests': self.stats['successful_requests'],
                'failed_requests': self.stats['failed_requests'],
                'success_rate_percent': round(success_rate, 2),
                'throughput_per_second': round(throughput, 2)
            },
            'timing_stats': {
                'request_times': get_timing_stats(self.stats['request_times']),
                'extraction_times': get_timing_stats(self.stats['extraction_times']),
                'validation_times': get_timing_stats(self.stats['validation_times']),
                'database_times': get_timing_stats(self.stats['database_times']),
                'image_processing_times': get_timing_stats(self.stats['image_processing_times'])
            },
            'platform_performance': platform_rates,
            'affiliate_type_performance': affiliate_rates,
            'data_quality': data_quality_stats,
            'error_analysis': {
                'error_categories': self.stats['error_categories'],
                'retry_counts': self.stats['retry_counts'],
                'cache_performance': {
                    'hits': self.stats['cache_hits'],
                    'misses': self.stats['cache_misses'],
                    'hit_rate': (self.stats['cache_hits'] / (self.stats['cache_hits'] + self.stats['cache_misses']) * 100) if (self.stats['cache_hits'] + self.stats['cache_misses']) > 0 else 0
                }
            }
        }
    
    def print_processing_statistics(self):
        """Print comprehensive processing statistics in a formatted way"""
        stats = self.get_processing_statistics()
        
        print("\n" + "="*80)
        print("📊 COMPREHENSIVE PROCESSING STATISTICS")
        print("="*80)
        
        # Session Info
        print(f"\n🕐 SESSION INFO:")
        print(f"   Start Time: {stats['session_info']['start_time']}")
        print(f"   Duration: {stats['session_info']['duration_formatted']}")
        
        # Overall Stats
        print(f"\n📈 OVERALL PERFORMANCE:")
        print(f"   Total Requests: {stats['overall_stats']['total_requests']}")
        print(f"   Successful: {stats['overall_stats']['successful_requests']}")
        print(f"   Failed: {stats['overall_stats']['failed_requests']}")
        print(f"   Success Rate: {stats['overall_stats']['success_rate_percent']}%")
        print(f"   Throughput: {stats['overall_stats']['throughput_per_second']} requests/second")
        
        # Timing Stats
        print(f"\n⏱️  TIMING STATISTICS:")
        timing = stats['timing_stats']
        print(f"   Request Times:")
        print(f"     Average: {timing['request_times']['avg']:.2f}s")
        print(f"     Median: {timing['request_times']['median']:.2f}s")
        print(f"     Range: {timing['request_times']['min']:.2f}s - {timing['request_times']['max']:.2f}s")
        
        print(f"   Extraction Times:")
        print(f"     Average: {timing['extraction_times']['avg']:.2f}s")
        print(f"     Total: {timing['extraction_times']['total']:.2f}s")
        
        print(f"   Database Times:")
        print(f"     Average: {timing['database_times']['avg']:.2f}s")
        print(f"     Total: {timing['database_times']['total']:.2f}s")
        
        # Platform Performance
        if stats['platform_performance']:
            print(f"\n🏪 PLATFORM PERFORMANCE:")
            for platform, perf in stats['platform_performance'].items():
                print(f"   {platform}: {perf['success_rate']:.1f}% ({perf['successful']}/{perf['total']})")
        
        # Affiliate Type Performance
        if stats['affiliate_type_performance']:
            print(f"\n🔗 AFFILIATE TYPE PERFORMANCE:")
            for affiliate_type, perf in stats['affiliate_type_performance'].items():
                print(f"   {affiliate_type}: {perf['success_rate']:.1f}% ({perf['successful']}/{perf['total']})")
        
        # Data Quality
        if stats['data_quality']:
            print(f"\n📊 DATA QUALITY:")
            quality = stats['data_quality']
            print(f"   Average Score: {quality['avg_score']:.1f}%")
            print(f"   Score Range: {quality['min_score']:.1f}% - {quality['max_score']:.1f}%")
            print(f"   Median Score: {quality['median_score']:.1f}%")
        
        # Error Analysis
        if stats['error_analysis']['error_categories']:
            print(f"\n❌ ERROR ANALYSIS:")
            for error_type, count in stats['error_analysis']['error_categories'].items():
                print(f"   {error_type}: {count} occurrences")
        
        # Cache Performance
        cache_perf = stats['error_analysis']['cache_performance']
        if cache_perf['hits'] > 0 or cache_perf['misses'] > 0:
            print(f"\n💾 CACHE PERFORMANCE:")
            print(f"   Hits: {cache_perf['hits']}")
            print(f"   Misses: {cache_perf['misses']}")
            print(f"   Hit Rate: {cache_perf['hit_rate']:.1f}%")
        
        print("\n" + "="*80)
    
    def process_url_file_enhanced(self, file_path: str, file_format: str = "csv", 
                                 upload_to_vercel: bool = True) -> Dict[str, Any]:
        """
        Enhanced main entry point: Process a file containing product URLs with full pipeline
        
        Args:
            file_path: Path to file containing URLs
            file_format: "csv" or "txt" or "json"
            upload_to_vercel: Whether to upload images to Vercel
        
        Returns:
            Dict with processing results
        """
        
        print("🚀 Enhanced Automated Product Pipeline")
        print("=" * 60)
        print(f"📁 Processing file: {file_path}")
        print(f"📋 Format: {file_format}")
        print(f"☁️  Vercel upload: {'Yes' if upload_to_vercel else 'No'}")
        print("=" * 60)
        
        results = {
            'total_urls': 0,
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'products_added': [],
            'summaries_generated': 0,
            'enhanced_pros_cons': 0,
            'images_uploaded': 0,
            'vercel_urls_updated': 0,
            'errors': []
        }
        
        try:
            # Step 1: Extract URLs from file
            urls = self._extract_urls_from_file(file_path, file_format)
            results['total_urls'] = len(urls)
            
            if not urls:
                print("❌ No URLs found in file")
                return results
            
            print(f"📊 Found {len(urls)} URLs to process")
            print("=" * 60)
            
            # Step 2: Process each URL
            for i, url in enumerate(urls, 1):
                # Print progress bar
                self._print_progress_bar(i-1, len(urls), prefix='Processing URLs', suffix='URLs')
                
                print(f"\n📦 [{i}/{len(urls)}] Processing: {url[:60]}...")
                
                # Track request start time
                request_start_time = time.time()
                
                try:
                    # Step 0: Validate affiliate URL
                    validation = self._validate_affiliate_url(url)
                    if not validation['is_valid']:
                        print(f"   ❌ Invalid affiliate URL: {validation['reason']}")
                        results['invalid_urls'] = results.get('invalid_urls', 0) + 1
                        results['errors'].append(f"Invalid affiliate URL: {validation['reason']}")
                        
                        # Track failed request
                        self._track_request_time(request_start_time, time.time(), False, "invalid_url")
                        continue
                    
                    print(f"   ✅ Valid {validation['affiliate_type']} affiliate URL")
                    
                    # Two-pass product data extraction
                    print(f"   🔄 Pass 1: Initial data extraction...")
                    extraction_start = time.time()
                    product_data = self._extract_product_data(url, pass_number=1)
                    self._track_extraction_time(extraction_start, time.time())
                    
                    # Validate first pass results
                    validation_start = time.time()
                    validation_result = self._validate_extracted_data(product_data, url)
                    self._track_validation_time(validation_start, time.time())
                    
                    if validation_result['needs_second_pass']:
                        print(f"   🔄 Pass 2: Enhanced data extraction...")
                        print(f"      Reason: {validation_result['reason']}")
                        
                        # Second pass with enhanced extraction
                        extraction_start = time.time()
                        enhanced_data = self._extract_product_data(url, pass_number=2)
                        self._track_extraction_time(extraction_start, time.time())
                        
                        # Merge results from both passes
                        product_data = self._merge_extraction_results(product_data, enhanced_data)
                        print(f"   ✅ Data merged from both passes")
                    else:
                        print(f"   ✅ First pass data is sufficient")
                    
                    if not product_data:
                        print(f"   ❌ Failed to extract product data")
                        results['failed'] += 1
                        results['errors'].append(f"Failed to extract data from {url}")
                        
                        # Track failed request
                        self._track_request_time(request_start_time, time.time(), False, "extraction_failed")
                        continue
                    
                    # Check for duplicates
                    if self._is_duplicate(product_data['sku']):
                        print(f"   ⚠️  Duplicate SKU: {product_data['sku']}")
                        print(f"   🔗 Adding affiliate link to existing product...")
                        
                        # Get existing product ID
                        existing_product_id = self._get_existing_product_id(product_data['sku'])
                        if existing_product_id:
                            # Add affiliate link to existing product
                            success = self._add_affiliate_link_to_existing_product(
                                existing_product_id, url, platform_id=1  # Amazon platform ID
                            )
                            if success:
                                results['duplicates_handled'] = results.get('duplicates_handled', 0) + 1
                                print(f"   ✅ Successfully added affiliate link to existing product")
                            else:
                                results["duplicates"] += 1
                                print(f"   ❌ Failed to add affiliate link")
                        else:
                            results["duplicates"] += 1
                            print(f"   ❌ Could not find existing product ID")
                        continue
                    
                    # Step 3: Prepare image data (will be saved after product insertion)
                    if product_data.get('images'):
                        # Store original image URLs for later processing
                        product_data['original_images'] = product_data['images']
                        product_data['primary_image_url'] = None  # Will be set after image processing
                        product_data['image_urls'] = []  # Will be populated after image processing
                    else:
                        product_data['original_images'] = []
                        product_data['primary_image_url'] = None
                        product_data['image_urls'] = []
                    
                    # Step 4: Insert product into database
                    db_start = time.time()
                    product_id = self._insert_product(product_data)
                    self._track_database_time(db_start, time.time())
                    
                    if not product_id:
                        print(f"   ❌ Failed to insert product into database")
                        results['failed'] += 1
                        results['errors'].append(f"Database insert failed for {url}")
                        
                        # Track failed request
                        self._track_request_time(request_start_time, time.time(), False, "database_error")
                        continue
                    
                    print(f"   ✅ Product inserted with ID: {product_id}")
                    
                    # Step 5: Process images after product insertion
                    if product_data.get('original_images'):
                        print(f"   🖼️  Processing {len(product_data['original_images'])} images...")
                        image_start = time.time()
                        image_data_list = self._save_images_locally(product_data['original_images'], product_id)
                        self._track_image_processing_time(image_start, time.time())
                        
                        # Update product with image data
                        if image_data_list:
                            # Set primary image URL (first image)
                            primary_image = next((img for img in image_data_list if img['is_primary']), image_data_list[0])
                            product_data['primary_image_url'] = primary_image['local_path']
                            
                            # Set image URLs list
                            product_data['image_urls'] = [img['local_path'] for img in image_data_list]
                            
                            # Update database with image data
                            self._update_product_images(product_id, image_data_list)
                            print(f"   ✅ Processed {len(image_data_list)} images")
                        else:
                            print(f"   ⚠️  No images were successfully processed")
                    
                    results['successful'] += 1
                    results['products_added'].append({
                        'id': product_id,
                        'sku': product_data['sku'],
                        'title': product_data['title']
                    })
                    
                    # Track successful request and platform stats
                    self._track_request_time(request_start_time, time.time(), True)
                    self._track_platform_stats(validation['affiliate_type'], True)
                    self._track_affiliate_type_stats(validation['affiliate_type'], True)
                    
                    # Track data quality score if available
                    if 'quality_score' in validation_result:
                        self._track_data_quality_score(validation_result['quality_score'])
                    
                    # Step 5: Generate product summary (skip if no features)
                    print(f"   📝 Generating product summary...")
                    product_data = self.summary_generator.get_product_data(product_id)
                    if product_data and product_data.get("features"):
                        summary = self.summary_generator.generate_summary(product_data)
                        if self.summary_generator.update_product_summary(product_id, summary):
                            print(f"   ✅ Summary generated: {summary[:50]}...")
                            results["summaries_generated"] += 1
                        else:
                            print(f"   ⚠️  Failed to generate summary")
                    else:
                        print(f"   ⚠️  Skipping summary - no features extracted yet")
                    
                    # Step 6: Generate enhanced pros and cons (skip if no features)
                    print(f"   🔍 Generating enhanced pros and cons...")
                    if self._enhance_pros_cons_for_product(product_id):
                        print(f"   ✅ Enhanced pros/cons generated")
                        results['enhanced_pros_cons'] += 1
                    else:
                        print(f"   ⚠️  Skipping enhanced pros/cons - no features to enhance")
                    
                    # Rate limiting
                    self._rate_limit()
                    
                except Exception as e:
                    print(f"   ❌ Error processing {url}: {e}")
                    results['failed'] += 1
                    results['errors'].append(f"Error processing {url}: {e}")
                    
                    # Track failed request
                    self._track_request_time(request_start_time, time.time(), False, "processing_error")
                    continue
            
            # Print final progress bar
            self._print_progress_bar(len(urls), len(urls), prefix='Processing URLs', suffix='URLs')
            
            # Step 7: Upload images to Vercel (if enabled) - only for new products
            if upload_to_vercel and self.vercel_uploader and results['products_added']:
                print(f"\n☁️  Uploading images to Vercel for new products...")
                upload_results = self._upload_new_product_images_to_vercel(results['products_added'])
                results['images_uploaded'] = upload_results.get('successful_uploads', 0)
                print(f"   ✅ Uploaded {results['images_uploaded']} images to Vercel")
                
                # Step 8: Update database with Vercel URLs - only for new products
                print(f"\n🔄 Updating database with Vercel URLs for new products...")
                vercel_results = self._update_vercel_urls_for_new_products(results['products_added'])
                results['vercel_urls_updated'] = vercel_results.get('updated_products', 0)
                print(f"   ✅ Updated {results['vercel_urls_updated']} new products with Vercel URLs")
            
            elif upload_to_vercel and not self.vercel_uploader:
                print(f"\n⚠️  Vercel upload requested but no token provided")
                print(f"   Set VERCEL_TOKEN environment variable to enable upload")
            
            # Step 9: Calculate scores for new products
            print(f"\n📊 Calculating scores for new products...")
            self._calculate_scores_for_new_products(results['products_added'])
            
        except Exception as e:
            print(f"❌ Pipeline error: {e}")
            results['errors'].append(f"Pipeline error: {e}")
        
        # Print comprehensive statistics
        self.print_processing_statistics()
        
        return results
    
    def _extract_urls_from_file(self, file_path: str, file_format: str) -> List[str]:
        """Extract URLs from various file formats"""
        
        urls = []
        
        try:
            if file_format.lower() == "csv":
                with open(file_path, 'r', encoding='utf-8') as f:
                    reader = csv.reader(f)
                    for i, row in enumerate(reader):
                        if i == 0:  # Skip header row
                            continue
                        if row and len(row) > 1 and row[1].strip():
                            urls.append(row[1].strip())
            
            elif file_format.lower() == "txt":
                with open(file_path, 'r', encoding='utf-8') as f:
                    for line in f:
                        line = line.strip()
                        if line and line.startswith('http'):
                            urls.append(line)
            
            elif file_format.lower() == "json":
                with open(file_path, 'r', encoding='utf-8') as f:
                    data = json.load(f)
                    if isinstance(data, list):
                        urls = [item for item in data if isinstance(item, str) and item.startswith('http')]
                    elif isinstance(data, dict) and 'urls' in data:
                        urls = data['urls']
        
        except Exception as e:
            print(f"❌ Error reading file {file_path}: {e}")
        
        return urls
    
    def _extract_product_data(self, url: str, pass_number: int = 1) -> Optional[Dict[str, Any]]:
        """Extract comprehensive product data from URL with two-pass strategy"""
        
        try:
            # Rate limiting
            self._rate_limit()
            
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for bot detection
            if "Robot Check" in response.text or "captcha" in response.text.lower():
                print(f"   ⚠️  Bot detection detected, skipping...")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic product data with pass-specific strategies
            if pass_number == 1:
                # First pass: Use primary selectors for quick extraction
                title = self._extract_title(soup, pass_number=1)
                price = self._extract_price(soup, pass_number=1)
                rating = self._extract_rating(soup, pass_number=1)
                review_count = self._extract_review_count(soup, pass_number=1)
                images = self._extract_images(soup, pass_number=1)
                brand = self._extract_brand(soup, pass_number=1) or 'Unknown'
            else:
                # Second pass: Use enhanced selectors and fallback methods
                title = self._extract_title(soup, pass_number=2)
                price = self._extract_price(soup, pass_number=2)
                rating = self._extract_rating(soup, pass_number=2)
                review_count = self._extract_review_count(soup, pass_number=2)
                images = self._extract_images(soup, pass_number=2)
                brand = self._extract_brand(soup, pass_number=2) or 'Unknown'
            description = self._extract_description(soup)
            
            # Generate SKU from URL
            sku = self._generate_sku_from_url(url)
            
            # Extract features, pros, and cons
            features = self._extract_features(soup)
            specifications = self._extract_specifications(soup)
            categories = self._extract_categories(soup, title)
            
            # Extract additional product details
            material = self._extract_material(soup, title, description)
            color = self._extract_color(soup, title)
            size = self._extract_size(soup, title)
            ingredients = self._extract_ingredients(soup, description)
            dimensions = self._extract_dimensions(soup, specifications)
            
            # Generate display-friendly content
            pretty_title = self._generate_pretty_title(title)
            short_description = self._generate_short_description(title, description)
            
            return {
                'sku': sku,
                'title': title,
                'price': price,
                'rating': rating,
                'review_count': review_count,
                'images': images,
                'url': url,
                'description': description or title,
                'brand': brand,
                'currency': 'USD',
                'availability': 'In Stock',
                'is_active': True,
                'features': features,
                'specifications': specifications,
                'categories': categories,
                'material': material,
                'color': color,
                'size': size,
                'ingredients': ingredients,
                'dimensions': dimensions,
                'pretty_title': pretty_title,
                'short_description': short_description
            }
            
        except Exception as e:
            print(f"   ❌ Error extracting data from {url}: {e}")
            return None
    
    def _extract_title(self, soup: BeautifulSoup, pass_number: int = 1) -> str:
        """Extract product title with pass-specific strategies"""
        if pass_number == 1:
            # First pass: Primary selectors
            selectors = [
                '#productTitle',
                'h1.a-size-large',
                'h1[data-automation-id="product-title"]'
            ]
        else:
            # Second pass: Enhanced selectors with fallbacks
            selectors = [
            '#productTitle',
            'h1.a-size-large',
            'h1[data-automation-id="product-title"]',
            '.product-title',
                'h1',
                '[data-automation-id="product-title"]',
                '.a-size-large.product-title-word-break',
                'h1.a-size-large.product-title-word-break'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                title = element.get_text().strip()
                if title and len(title) > 5:  # Basic quality check
                    return title
        
        return "Unknown Product"
    
    def _extract_price(self, soup: BeautifulSoup, pass_number: int = 1) -> Optional[float]:
        """Extract product price"""
        selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '.price',
            '[data-automation-id="product-price"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                price_text = element.get_text().strip()
                price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                if price_match:
                    return float(price_match.group())
        
        return None
    
    def _extract_rating(self, soup: BeautifulSoup, pass_number: int = 1) -> Optional[float]:
        """Extract product rating"""
        selectors = [
            '.a-icon-alt',
            '[data-automation-id="product-rating"]',
            '.rating'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                rating_text = element.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                    if rating <= 5:
                        return rating
        
        return None
    
    def _extract_review_count(self, soup: BeautifulSoup, pass_number: int = 1) -> Optional[int]:
        """Extract review count"""
        selectors = [
            '#acrCustomerReviewText',
            '[data-automation-id="product-review-count"]',
            '.review-count'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                count_text = element.get_text()
                count_match = re.search(r'([\d,]+)', count_text.replace(',', ''))
                if count_match:
                    return int(count_match.group(1))
        
        return None
    
    def _extract_images(self, soup: BeautifulSoup, pass_number: int = 1) -> List[str]:
        """Extract product images"""
        images = []
        
        # Try different selectors for images
        selectors = [
            '#landingImage',
            '.a-dynamic-image',
            '.product-image img',
            'img[data-old-hires]'
        ]
        
        for selector in selectors:
            elements = soup.select(selector)
            for element in elements:
                src = element.get('src') or element.get('data-src') or element.get('data-old-hires')
                if src and src.startswith('http'):
                    images.append(src)
        
        return images[:5]  # Limit to 5 images
    
    def _extract_brand(self, soup: BeautifulSoup, pass_number: int = 1) -> Optional[str]:
        """Extract product brand"""
        selectors = [
            '#bylineInfo',
            '.brand',
            '[data-automation-id="product-brand"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return None
    
    def _validate_affiliate_url(self, url: str) -> Dict[str, Any]:
        """Validate if URL is a valid affiliate link"""
        validation_result = {
            'is_valid': False,
            'affiliate_type': None,
            'reason': None,
            'product_id': None
        }
        
        try:
            # Check if it's an Amazon URL
            if not re.search(r'amazon\.(com|co\.uk|de|ca|fr|it|es|com\.au)', url, re.IGNORECASE):
                validation_result['reason'] = 'Not an Amazon URL'
                return validation_result
            
            # Extract product ID
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if not asin_match:
                validation_result['reason'] = 'No valid Amazon product ID found'
                return validation_result
            
            validation_result['product_id'] = asin_match.group(1)
            
            # Check for affiliate parameters
            affiliate_params = [
                'ref=', 'tag=', 'maas=', 'linkCode=', 'campaignid=', 'adgroupid=', 'creativeid='
            ]
            
            has_affiliate_param = any(param in url.lower() for param in affiliate_params)
            
            if not has_affiliate_param:
                validation_result['reason'] = 'No affiliate parameters found'
                return validation_result
            
            # Determine affiliate type
            if 'maas=' in url.lower():
                validation_result['affiliate_type'] = 'levana'
            elif 'ref=' in url.lower() or 'tag=' in url.lower():
                validation_result['affiliate_type'] = 'amazon_direct'
            else:
                validation_result['affiliate_type'] = 'other'
            
            validation_result['is_valid'] = True
            return validation_result
            
        except Exception as e:
            validation_result['reason'] = f'Validation error: {str(e)}'
            return validation_result
    
    def _generate_sku_from_url(self, url: str) -> str:
        """Generate SKU from URL - always returns AMAZON-{ASIN} format"""
        # Extract ASIN from various Amazon URL patterns
        asin_patterns = [
            r'/dp/([A-Z0-9]{10})',  # Standard Amazon URL format
            r'/product/([A-Z0-9]{10})',  # Alternative format
            r'asin=([A-Z0-9]{10})',  # ASIN parameter
        ]
        
        for pattern in asin_patterns:
            asin_match = re.search(pattern, url, re.IGNORECASE)
        if asin_match:
                asin = asin_match.group(1).upper()
                return f"AMAZON-{asin}"
        
        # If no ASIN found, this should not happen for valid Amazon URLs
        # But if it does, we'll create a hash-based SKU
        import hashlib
        url_hash = hashlib.md5(url.encode()).hexdigest()[:8].upper()
        return f"AMAZON-{url_hash}"
    
    def _extract_description(self, soup: BeautifulSoup) -> str:
        """Extract product description"""
        selectors = [
            '#feature-bullets ul',
            '#productDescription',
            '.a-unordered-list',
            '.product-description',
            '[data-hook="description"]'
        ]
        
        for selector in selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text().strip()
        
        return ""
    
    def _extract_features(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract product features (pros and cons)"""
        features = []
        
        # Extract bullet points from feature list
        feature_selectors = [
            '#feature-bullets ul li',
            '.a-unordered-list li',
            '.product-features li',
            '[data-hook="feature"]'
        ]
        
        for selector in feature_selectors:
            elements = soup.select(selector)
            for i, element in enumerate(elements):
                text = element.get_text().strip()
                if text and len(text) > 10:  # Filter out short/empty items
                    # Determine if it's a pro or con based on keywords
                    feature_type = self._classify_feature_type(text)
                    features.append({
                        'feature_text': text,
                        'feature_type': feature_type,
                        'display_order': i + 1
                    })
        
        # Extract from product description
        description = self._extract_description(soup)
        if description:
            # Split description into sentences and classify
            sentences = re.split(r'[.!?]+', description)
            for i, sentence in enumerate(sentences):
                sentence = sentence.strip()
                if len(sentence) > 20:  # Filter out short sentences
                    feature_type = self._classify_feature_type(sentence)
                    features.append({
                        'feature_text': sentence,
                        'feature_type': feature_type,
                        'display_order': len(features) + 1
                    })
        
        return features[:10]  # Limit to 10 features
    
    def _classify_feature_type(self, text: str) -> str:
        """Classify feature as pro or con based on keywords"""
        text_lower = text.lower()
        
        # Pro keywords
        pro_keywords = [
            'excellent', 'great', 'amazing', 'perfect', 'outstanding', 'superior',
            'durable', 'long-lasting', 'high-quality', 'premium', 'luxury',
            'soft', 'comfortable', 'breathable', 'easy', 'convenient',
            'affordable', 'value', 'worth', 'recommend', 'love', 'best'
        ]
        
        # Con keywords
        con_keywords = [
            'expensive', 'costly', 'overpriced', 'cheap', 'poor quality',
            'difficult', 'hard', 'uncomfortable', 'rough', 'scratchy',
            'small', 'tight', 'loose', 'fits poorly', 'not recommended',
            'disappointed', 'waste', 'avoid', 'problem', 'issue'
        ]
        
        # Count pro and con keywords
        pro_count = sum(1 for keyword in pro_keywords if keyword in text_lower)
        con_count = sum(1 for keyword in con_keywords if keyword in text_lower)
        
        if con_count > pro_count:
            return 'con'
        elif pro_count > 0:
            return 'pro'
        else:
            return 'pro'  # Default to pro if neutral
    
    def _extract_specifications(self, soup: BeautifulSoup) -> List[Dict[str, Any]]:
        """Extract product specifications"""
        specifications = []
        
        # Extract from technical details table
        tech_table = soup.select_one('#productDetails_techSpec_section_1')
        if tech_table:
            rows = tech_table.select('tr')
            for i, row in enumerate(rows):
                cells = row.select('td')
                if len(cells) >= 2:
                    spec_name = cells[0].get_text().strip()
                    spec_value = cells[1].get_text().strip()
                    if spec_name and spec_value:
                        specifications.append({
                            'spec_name': spec_name,
                            'spec_value': spec_value,
                            'spec_unit': '',
                            'display_order': i + 1
                        })
        
        # Extract from additional details
        additional_details = soup.select_one('#productDetails_detailBullets_sections1')
        if additional_details:
            rows = additional_details.select('tr')
            for i, row in enumerate(rows):
                cells = row.select('td')
                if len(cells) >= 2:
                    spec_name = cells[0].get_text().strip()
                    spec_value = cells[1].get_text().strip()
                    if spec_name and spec_value:
                        specifications.append({
                            'spec_name': spec_name,
                            'spec_value': spec_value,
                            'spec_unit': '',
                            'display_order': len(specifications) + 1
                        })
        
        # Extract common specifications from title/description
        title = self._extract_title(soup)
        if title:
            # Look for thread count
            thread_match = re.search(r'(\d+)\s*thread', title.lower())
            if thread_match:
                specifications.append({
                    'spec_name': 'Thread Count',
                    'spec_value': thread_match.group(1),
                    'spec_unit': 'threads per inch',
                    'display_order': len(specifications) + 1
                })
            
            # Look for material
            materials = ['cotton', 'bamboo', 'linen', 'silk', 'polyester', 'microfiber']
            for material in materials:
                if material in title.lower():
                    specifications.append({
                        'spec_name': 'Material',
                        'spec_value': material.title(),
                        'spec_unit': '',
                        'display_order': len(specifications) + 1
                    })
                    break
        
        return specifications[:15]  # Limit to 15 specifications
    
    def _extract_categories(self, soup: BeautifulSoup, title: str) -> List[Dict[str, Any]]:
        """Extract product categories"""
        categories = []
        
        # Extract from breadcrumbs
        breadcrumbs = soup.select('#wayfinding-breadcrumbs_feature_div a')
        if breadcrumbs:
            for i, breadcrumb in enumerate(breadcrumbs):
                category_name = breadcrumb.get_text().strip()
                if category_name and category_name not in ['Home', 'Amazon']:
                    categories.append({
                        'category_name': category_name,
                        'category_path': ' > '.join([b.get_text().strip() for b in breadcrumbs[:i+1]]),
                        'is_primary': i == 0,
                        'display_order': i + 1
                    })
        
        # If no breadcrumbs, create categories from title analysis
        if not categories and title:
            title_lower = title.lower()
            
            # Bedding categories
            if any(word in title_lower for word in ['sheet', 'bedding', 'bed']):
                categories.append({
                    'category_name': 'Bedding',
                    'category_path': 'Home > Bedding',
                    'is_primary': True,
                    'display_order': 1
                })
            
            # Material categories
            if 'cotton' in title_lower:
                categories.append({
                    'category_name': 'Cotton',
                    'category_path': 'Home > Bedding > Cotton',
                    'is_primary': False,
                    'display_order': 2
                })
            elif 'bamboo' in title_lower:
                categories.append({
                    'category_name': 'Bamboo',
                    'category_path': 'Home > Bedding > Bamboo',
                    'is_primary': False,
                    'display_order': 2
                })
        
        # Default category if none found
        if not categories:
            categories.append({
                'category_name': 'Amazon Products',
                'category_path': 'Amazon > Products',
                'is_primary': True,
                'display_order': 1
            })
        
        return categories
    
    def _extract_material(self, soup: BeautifulSoup, title: str, description: str) -> str:
        """Extract material/fabric type from product page"""
        material_keywords = {
            'cotton': ['cotton', '100% cotton', 'pure cotton'],
            'egyptian cotton': ['egyptian cotton', 'egyptian', 'supima cotton'],
            'bamboo': ['bamboo', 'bamboo viscose', 'bamboo rayon'],
            'linen': ['linen', 'flax'],
            'sateen': ['sateen', 'sateen weave'],
            'percale': ['percale', 'percale weave'],
            'microfiber': ['microfiber', 'micro fiber', 'micro-fiber'],
            'silk': ['silk', 'mulberry silk'],
            'polyester': ['polyester', 'poly'],
            'blend': ['blend', 'mixed', 'combination']
        }
        
        # Combine title and description for analysis
        text_to_analyze = f"{title} {description}".lower()
        
        # Look for material keywords
        for material, keywords in material_keywords.items():
            for keyword in keywords:
                if keyword in text_to_analyze:
                    return material.title()
        
        # Check product specifications table
        spec_tables = soup.find_all('table', {'id': 'productDetails_detailBullets_sections1'})
        for table in spec_tables:
            rows = table.find_all('tr')
            for row in rows:
                cells = row.find_all(['td', 'th'])
                if len(cells) >= 2:
                    label = cells[0].get_text(strip=True).lower()
                    value = cells[1].get_text(strip=True).lower()
                    
                    if 'material' in label or 'fabric' in label or 'composition' in label:
                        for material, keywords in material_keywords.items():
                            for keyword in keywords:
                                if keyword in value:
                                    return material.title()
        
        # Check bullet points
        bullet_points = soup.find_all('span', {'class': 'a-list-item'})
        for bullet in bullet_points:
            text = bullet.get_text(strip=True).lower()
            for material, keywords in material_keywords.items():
                for keyword in keywords:
                    if keyword in text:
                        return material.title()
        
        return 'Unknown'
    
    def _extract_color(self, soup: BeautifulSoup, title: str) -> str:
        """Extract color from product page"""
        # Common color keywords
        colors = [
            'white', 'black', 'gray', 'grey', 'beige', 'cream', 'ivory',
            'blue', 'navy', 'royal blue', 'sky blue', 'light blue',
            'red', 'burgundy', 'maroon', 'pink', 'rose',
            'green', 'forest green', 'sage', 'mint', 'olive',
            'yellow', 'gold', 'champagne', 'tan', 'brown',
            'purple', 'lavender', 'plum', 'charcoal', 'silver'
        ]
        
        # Check title first
        title_lower = title.lower()
        for color in colors:
            if color in title_lower:
                return color.title()
        
        # Check color selection buttons
        color_buttons = soup.find_all(['button', 'span'], {'class': lambda x: x and 'color' in x.lower()})
        for button in color_buttons:
            text = button.get_text(strip=True)
            for color in colors:
                if color in text.lower():
                    return color.title()
        
        # Check product details
        details = soup.find_all('div', {'id': 'detailBullets_feature_div'})
        for detail in details:
            text = detail.get_text(strip=True).lower()
            for color in colors:
                if color in text:
                    return color.title()
        
        return 'Unknown'
    
    def _extract_size(self, soup: BeautifulSoup, title: str) -> str:
        """Extract size from product page"""
        # Common size patterns
        size_patterns = [
            r'(twin|twin xl)',
            r'(full|double)',
            r'(queen)',
            r'(king|california king)',
            r'(king xl)',
            r'(\d+["\']?\s*x\s*\d+["\']?)',  # Dimensions like 60" x 80"
            r'(\d+\s*inch)',  # Single dimension
        ]
        
        # Check title first
        title_lower = title.lower()
        for pattern in size_patterns:
            match = re.search(pattern, title_lower)
            if match:
                return match.group(1).title()
        
        # Check size selection
        size_elements = soup.find_all(['button', 'span'], {'class': lambda x: x and 'size' in x.lower()})
        for element in size_elements:
            text = element.get_text(strip=True)
            for pattern in size_patterns:
                match = re.search(pattern, text.lower())
                if match:
                    return match.group(1).title()
        
        return 'Unknown'
    
    def _extract_ingredients(self, soup: BeautifulSoup, description: str) -> str:
        """Extract ingredients from product page"""
        # Look for ingredients in description
        if description:
            desc_lower = description.lower()
            if 'ingredients' in desc_lower or 'composition' in desc_lower:
                # Try to extract ingredients list
                lines = description.split('\n')
                for line in lines:
                    if 'ingredients' in line.lower() or 'composition' in line.lower():
                        return line.strip()
        
        # Check product details section
        details = soup.find_all('div', {'id': 'detailBullets_feature_div'})
        for detail in details:
            text = detail.get_text(strip=True)
            if 'ingredients' in text.lower() or 'composition' in text.lower():
                return text
        
        return 'Not specified'
    
    def _extract_dimensions(self, soup: BeautifulSoup, specifications: List[Dict[str, Any]]) -> str:
        """Extract dimensions from product page"""
        # Check specifications first
        for spec in specifications:
            if 'dimension' in spec.get('spec_name', '').lower():
                return spec.get('spec_value', '')
        
        # Look for dimension patterns in the page
        dimension_patterns = [
            r'(\d+["\']?\s*x\s*\d+["\']?\s*x\s*\d+["\']?)',  # 3D dimensions
            r'(\d+["\']?\s*x\s*\d+["\']?)',  # 2D dimensions
            r'(\d+\s*inch)',  # Single dimension
        ]
        
        page_text = soup.get_text()
        for pattern in dimension_patterns:
            matches = re.findall(pattern, page_text, re.IGNORECASE)
            if matches:
                return matches[0]
        
        return 'Not specified'
    
    def _generate_pretty_title(self, title: str) -> str:
        """Generate a short, complete title for product cards (no mid-word cuts)"""
        
        # Extract key components
        size = self._extract_size_from_title(title)
        piece_count = self._extract_piece_count(title)
        thread_count = self._extract_thread_count_from_title(title)
        material = self._extract_material_from_title(title)
        brand = self._extract_brand_from_title(title)
        product_type = self._extract_product_type(title)
        
        # Build title components
        components = []
        
        # Start with size if available
        if size:
            components.append(size)
        
        # Add piece count if available
        if piece_count:
            components.append(f"{piece_count}-Pc")
        
        # Add product type
        if product_type:
            components.append(product_type)
        
        # Add material if it's a key differentiator
        if material and material.lower() not in ['cotton']:  # Skip generic cotton
            components.append(material)
        
        # Add thread count if available
        if thread_count:
            components.append(f"{thread_count} Thread")
        
        # Add brand if it's not too long and adds value
        if brand and len(brand) <= 15 and brand not in ['California Design Den']:
            components.append(brand)
        
        # Join components with spaces and commas
        if components:
            pretty_title = " ".join(components)
            
            # Ensure it's not too long (max 50 characters for product cards)
            if len(pretty_title) > 50:
                # Try to shorten by removing less important components
                if thread_count and len(pretty_title) > 50:
                    components = [c for c in components if not c.endswith('Thread')]
                    pretty_title = " ".join(components)
                
                if len(pretty_title) > 50:
                    # Final fallback: truncate at word boundary
                    words = pretty_title.split()
                    result = ""
                    for word in words:
                        if len(result + " " + word) <= 47:  # Leave room for "..."
                            result += (" " + word) if result else word
                        else:
                            break
                    if result != pretty_title:
                        result += "..."
                    pretty_title = result
            
            return pretty_title
        
        # Fallback: create a simple title
        if size:
            return f"{size} Sheet Set"
        else:
            return "Bedding Set"
    
    def _extract_size_from_title(self, title: str) -> str:
        """Extract size from title"""
        size_match = re.search(r'\b(king|queen|twin|full|california king)\b', title, re.IGNORECASE)
        if size_match:
            size = size_match.group(1).lower()
            if size == 'california king':
                return 'California King'
            else:
                return size.title()
        return ""
    
    def _extract_piece_count(self, title: str) -> str:
        """Extract piece count from title"""
        piece_match = re.search(r'(\d+)\s*[pP]iece', title)
        if piece_match:
            return piece_match.group(1)
        return ""
    
    def _extract_thread_count_from_title(self, title: str) -> str:
        """Extract thread count from title"""
        thread_match = re.search(r'(\d+)\s*thread count', title, re.IGNORECASE)
        if thread_match:
            return thread_match.group(1)
        return ""
    
    def _extract_material_from_title(self, title: str) -> str:
        """Extract material from title"""
        if 'egyptian cotton' in title.lower():
            return 'Egyptian Cotton'
        elif 'bamboo' in title.lower():
            return 'Bamboo'
        elif 'linen' in title.lower():
            return 'Linen'
        elif 'sateen' in title.lower():
            return 'Sateen'
        elif 'percale' in title.lower():
            return 'Percale'
        return ""
    
    def _extract_brand_from_title(self, title: str) -> str:
        """Extract brand from title"""
        # Common brands
        brands = ['Breescape', 'Threadmill', 'Buffy', 'Boll & Branch', 'Bamboo Bay', 'Coop Home Goods']
        for brand in brands:
            if brand.lower() in title.lower():
                return brand
        return ""
    
    def _extract_product_type(self, title: str) -> str:
        """Extract product type from title"""
        if 'sheet set' in title.lower():
            return 'Sheets'
        elif 'comforter' in title.lower():
            return 'Comforter'
        elif 'duvet' in title.lower():
            return 'Duvet'
        elif 'protector' in title.lower():
            return 'Protector'
        elif 'bundle' in title.lower():
            return 'Bundle'
        else:
            return 'Sheets'  # Default
    
    def _generate_short_description(self, title: str, description: str = "") -> str:
        """Generate a short description for website display"""
        
        # Extract key features from title and description
        features = []
        
        # Material
        if 'egyptian cotton' in title.lower():
            features.append("Egyptian cotton")
        elif 'bamboo' in title.lower():
            features.append("bamboo")
        elif 'cotton' in title.lower():
            features.append("cotton")
        
        # Thread count
        thread_match = re.search(r'(\d+)\s*thread count', title, re.IGNORECASE)
        if thread_match:
            features.append(f"{thread_match.group(1)}-thread count")
        
        # Size
        size_match = re.search(r'\b(king|queen|twin|full|california king)\b', title, re.IGNORECASE)
        if size_match:
            features.append(f"{size_match.group(1)} size")
        
        # Key benefits
        if 'cooling' in title.lower() or 'cool' in title.lower():
            features.append("cooling technology")
        if 'breathable' in title.lower():
            features.append("breathable")
        if 'soft' in title.lower():
            features.append("soft feel")
        
        # Construct short description
        if features:
            feature_text = ", ".join(features[:3])  # Limit to 3 features
            return f"Premium {feature_text} sheets offering comfort and durability for a restful night's sleep."
        else:
            return "High-quality bedding set designed for comfort and durability."
    
    def _is_duplicate(self, sku: str) -> bool:
        """Check if product already exists"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM products WHERE sku = ?", (sku,))
                return cursor.fetchone()[0] > 0
        except:
            return False
    
    def _get_existing_product_id(self, sku: str) -> Optional[int]:
        """Get existing product ID for a SKU"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT id FROM products WHERE sku = ?", (sku,))
                result = cursor.fetchone()
                return result[0] if result else None
        except:
            return None
    
    def _add_affiliate_link_to_existing_product(self, product_id: int, url: str, platform_id: int = 1) -> bool:
        """Add new affiliate link to existing product"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Check if this exact affiliate URL already exists
                cursor.execute("""
                    SELECT COUNT(*) FROM affiliate_links 
                    WHERE product_id = ? AND affiliate_url = ?
                """, (product_id, url))
                
                if cursor.fetchone()[0] > 0:
                    print(f"   ℹ️  Affiliate link already exists for this product")
                    return False
                
                # Determine link type based on URL
                link_type = "web"
                if "m.amazon.com" in url or "mobile" in url.lower():
                    link_type = "mobile"
                elif "desktop" in url.lower():
                    link_type = "desktop"
                
                # Insert new affiliate link
                cursor.execute("""
                    INSERT INTO affiliate_links (
                        product_id, platform_id, link_type, affiliate_url,
                        commission_rate, estimated_commission, is_active
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, platform_id, link_type, url,
                    None, None, True
                ))
                
                conn.commit()
                print(f"   ✅ Added new affiliate link: {link_type}")
                return True
                
        except Exception as e:
            print(f"   ❌ Error adding affiliate link: {str(e)}")
            return False
    
    def _save_images_locally(self, image_urls: List[str], product_id: int) -> List[Dict[str, Any]]:
        """Save images locally and return image data for database"""
        image_data_list = []
        
        for i, image_url in enumerate(image_urls):
            try:
                # Rate limiting
                self._rate_limit()
                
                response = self.session.get(image_url, timeout=30)
                response.raise_for_status()
                
                # Determine file extension
                content_type = response.headers.get('content-type', '')
                if 'jpeg' in content_type or 'jpg' in content_type:
                    ext = '.jpg'
                    image_type = 'jpg'
                elif 'png' in content_type:
                    ext = '.png'
                    image_type = 'png'
                elif 'webp' in content_type:
                    ext = '.webp'
                    image_type = 'webp'
                else:
                    ext = '.jpg'  # Default
                    image_type = 'jpg'
                
                # Create filename using product_id
                if i == 0:
                    filename = f"{product_id}{ext}"
                else:
                    filename = f"{product_id}_{i}{ext}"
                
                filepath = self.images_dir / filename
                
                # Save image
                with open(filepath, 'wb') as f:
                    f.write(response.content)
                
                # Get file size
                file_size = filepath.stat().st_size
                
                # Create image data for database
                image_data = {
                    'original_url': image_url,
                    'local_path': filename,
                    'vercel_url': None,  # Will be set after manual upload
                    'is_primary': (i == 0),  # First image is primary
                    'display_order': i,
                    'image_type': image_type,
                    'file_size': file_size,
                    'width': None,  # Could be extracted from image if needed
                    'height': None
                }
                
                image_data_list.append(image_data)
                print(f"   💾 Saved image: {filename}")
                
            except Exception as e:
                print(f"   ⚠️  Failed to save image {i}: {e}")
                continue
        
        return image_data_list
    
    def _validate_extracted_data(self, product_data: Optional[Dict[str, Any]], url: str) -> Dict[str, Any]:
        """Validate extracted data and determine if second pass is needed"""
        validation_result = {
            'needs_second_pass': False,
            'reason': None,
            'missing_fields': [],
            'quality_score': 0
        }
        
        if not product_data:
            validation_result['needs_second_pass'] = True
            validation_result['reason'] = 'No data extracted in first pass'
            return validation_result
        
        # Check for essential fields
        essential_fields = ['title', 'price', 'images']
        missing_essential = []
        
        for field in essential_fields:
            if not product_data.get(field):
                missing_essential.append(field)
        
        if missing_essential:
            validation_result['needs_second_pass'] = True
            validation_result['reason'] = f'Missing essential fields: {", ".join(missing_essential)}'
            validation_result['missing_fields'] = missing_essential
            return validation_result
        
        # Check data quality
        quality_issues = []
        
        # Check title quality
        title = product_data.get('title', '')
        if len(title) < 10 or 'Amazon' in title:
            quality_issues.append('poor_title')
        
        # Check price quality
        price = product_data.get('price')
        if not price or price <= 0:
            quality_issues.append('invalid_price')
        
        # Check images quality
        images = product_data.get('images', [])
        if len(images) < 2:
            quality_issues.append('insufficient_images')
        
        # Check description quality
        description = product_data.get('description', '')
        if len(description) < 50:
            quality_issues.append('poor_description')
        
        # Calculate quality score
        total_checks = 4
        passed_checks = total_checks - len(quality_issues)
        quality_score = (passed_checks / total_checks) * 100
        
        validation_result['quality_score'] = quality_score
        
        # Determine if second pass is needed based on quality
        if quality_score < 75 or quality_issues:
            validation_result['needs_second_pass'] = True
            validation_result['reason'] = f'Low quality data (score: {quality_score:.1f}%) - issues: {", ".join(quality_issues)}'
            validation_result['missing_fields'] = quality_issues
        
        return validation_result
    
    def _merge_extraction_results(self, first_pass: Dict[str, Any], second_pass: Dict[str, Any]) -> Dict[str, Any]:
        """Merge results from two extraction passes, preferring better data"""
        merged = first_pass.copy()
        
        # Merge strategy: prefer second pass data, but keep first pass if second pass is empty
        for key, value in second_pass.items():
            if value and (not merged.get(key) or self._is_better_data(key, value, merged.get(key))):
                merged[key] = value
        
        return merged
    
    def _is_better_data(self, field: str, new_value: Any, old_value: Any) -> bool:
        """Determine if new data is better than old data for a specific field"""
        if not old_value:
            return True
        
        if field == 'title':
            # Prefer longer, more descriptive titles
            return len(str(new_value)) > len(str(old_value))
        
        elif field == 'description':
            # Prefer longer, more detailed descriptions
            return len(str(new_value)) > len(str(old_value))
        
        elif field == 'images':
            # Prefer more images
            if isinstance(new_value, list) and isinstance(old_value, list):
                return len(new_value) > len(old_value)
            return bool(new_value)
        
        elif field == 'price':
            # Prefer valid prices over invalid ones
            try:
                new_price = float(new_value) if new_value else 0
                old_price = float(old_value) if old_value else 0
                return new_price > 0 and (old_price <= 0 or new_price > old_price)
            except:
                return bool(new_value)
        
        elif field in ['rating', 'review_count']:
            # Prefer higher values
            try:
                new_val = float(new_value) if new_value else 0
                old_val = float(old_value) if old_value else 0
                return new_val > old_val
            except:
                return bool(new_value)
        
        # For other fields, prefer non-empty values
        return bool(new_value)
    
    def _update_product_images(self, product_id: int, image_data_list: List[Dict[str, Any]]):
        """Update product with image data in the images table"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert each image into the product_images table
                for image_data in image_data_list:
                    cursor.execute("""
                        INSERT INTO product_images (
                            product_id, original_url, local_path, vercel_url,
                            is_primary, display_order, image_type, file_size, width, height
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_id,
                        image_data['original_url'],
                        image_data['local_path'],
                        image_data['vercel_url'],
                        image_data['is_primary'],
                        image_data['display_order'],
                        image_data['image_type'],
                        image_data['file_size'],
                        image_data['width'],
                        image_data['height']
                    ))
                
                # Update the products table with primary image URL
                if image_data_list:
                    primary_image = next((img for img in image_data_list if img['is_primary']), image_data_list[0])
                    cursor.execute("""
                        UPDATE products 
                        SET primary_image_url = ?, image_urls = ?
                        WHERE id = ?
                    """, (
                        primary_image['local_path'],
                        json.dumps([img['local_path'] for img in image_data_list]),
                        product_id
                    ))
                
                conn.commit()
                
        except Exception as e:
            print(f"   ❌ Error updating product images: {str(e)}")
    
    def _insert_product(self, product_data: Dict[str, Any]) -> Optional[int]:
        """Insert product and related data into database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get next available ID
                cursor.execute("SELECT COALESCE(MAX(id), 0) + 1 FROM products")
                next_id = cursor.fetchone()[0]
                
                # Insert main product with explicit ID
                cursor.execute("""
                    INSERT INTO products (
                        id, sku, title, brand, description, price, currency,
                        rating, review_count, primary_image_url, image_urls,
                        availability, is_active, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    next_id,
                    product_data['sku'],
                    product_data['title'],
                    product_data['brand'],
                    product_data['description'],
                    product_data['price'],
                    product_data['currency'],
                    product_data['rating'],
                    product_data['review_count'],
                    product_data['primary_image_url'],
                    json.dumps(product_data['image_urls']),
                    product_data['availability'],
                    product_data['is_active']
                ))
                
                product_id = next_id
                
                # Insert features
                for feature in product_data.get('features', []):
                    cursor.execute("""
                        INSERT INTO product_features (
                            product_id, feature_text, feature_type, display_order
                        ) VALUES (?, ?, ?, ?)
                    """, (
                        product_id,
                        feature['feature_text'],
                        feature['feature_type'],
                        feature['display_order']
                    ))
                
                # Insert specifications
                for spec in product_data.get('specifications', []):
                    cursor.execute("""
                        INSERT INTO product_specifications (
                            product_id, spec_name, spec_value, spec_unit, display_order
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        product_id,
                        spec['spec_name'],
                        spec['spec_value'],
                        spec['spec_unit'],
                        spec['display_order']
                    ))
                
                # Insert categories
                for category in product_data.get('categories', []):
                    cursor.execute("""
                        INSERT INTO product_categories (
                            product_id, category_name, category_path, is_primary, display_order
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (
                        product_id,
                        category['category_name'],
                        category['category_path'],
                        category['is_primary'],
                        category['display_order']
                    ))
                
                conn.commit()
                return product_id
                
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return None
    
    def _calculate_scores_for_new_products(self, products_added: List[Dict[str, Any]]):
        """Calculate scores for newly added products"""
        if not products_added:
            return
        
        print(f"   📊 Calculating scores for {len(products_added)} new products...")
        
        try:
            from core.configurable_scoring_system import ConfigurableScoringSystem
            scoring_system = ConfigurableScoringSystem(self.db_path)
            
            for product in products_added:
                product_id = product['id']
                scoring_system.calculate_product_score(product_id)
            
            print(f"   ✅ Scores calculated for all new products")
            
        except Exception as e:
            print(f"   ⚠️  Error calculating scores: {e}")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        
        self.last_request_time = time.time()
    
    def _enhance_pros_cons_for_product(self, product_id: int) -> bool:
        """Generate enhanced pros/cons for a single product using structured lists"""
        try:
            # Get product info for context
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("""
                    SELECT title, material, brand, price, rating
                    FROM products WHERE id = ?
                """, (product_id,))
                
                product_info = cursor.fetchone()
                if not product_info:
                    return False
                
                title, material, brand, price, rating = product_info
                
                # Clear existing features and replace with structured ones
                cursor.execute("DELETE FROM product_features WHERE product_id = ?", (product_id,))
                
                # Generate relevant structured features
                relevant_features = self._get_relevant_structured_features(
                    title, material, brand, price, rating
                )
                
                # Insert new structured features
                for feature_type, features in relevant_features.items():
                    for i, feature in enumerate(features):
                        category = self._categorize_structured_feature(feature)
                        importance = self._determine_structured_importance(feature, feature_type)
                        impact_score = self._calculate_structured_impact(feature, feature_type)
                        
                        cursor.execute("""
                            INSERT INTO product_features 
                            (product_id, feature_text, feature_type, category, importance, 
                             impact_score, ai_generated, display_order)
                            VALUES (?, ?, ?, ?, ?, ?, TRUE, ?)
                        """, (product_id, feature, feature_type, category, importance, 
                              impact_score, i + 1))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"   ⚠️  Error enhancing pros/cons for product {product_id}: {e}")
            return False
    
    def _categorize_feature(self, feature_text: str, feature_type: str) -> str:
        """Categorize a feature based on its text"""
        text_lower = feature_text.lower()
        
        # Quality indicators
        if any(word in text_lower for word in ['durable', 'quality', 'premium', 'luxury', 'soft', 'smooth']):
            return 'quality'
        
        # Price indicators
        if any(word in text_lower for word in ['price', 'cost', 'expensive', 'cheap', 'affordable', 'value']):
            return 'price'
        
        # Performance indicators
        if any(word in text_lower for word in ['fast', 'efficient', 'effective', 'performance', 'speed']):
            return 'performance'
        
        # Comfort indicators
        if any(word in text_lower for word in ['comfortable', 'comfort', 'fit', 'breathable', 'cooling']):
            return 'comfort'
        
        # Design indicators
        if any(word in text_lower for word in ['design', 'style', 'beautiful', 'attractive', 'color']):
            return 'design'
        
        return 'other'
    
    def _determine_importance(self, feature_text: str, feature_type: str) -> str:
        """Determine importance level of a feature"""
        text_lower = feature_text.lower()
        
        # Critical features
        if any(word in text_lower for word in ['essential', 'critical', 'must', 'required', 'deal breaker']):
            return 'critical'
        
        # High importance
        if any(word in text_lower for word in ['important', 'excellent', 'outstanding', 'amazing', 'perfect']):
            return 'high'
        
        # Medium importance
        if any(word in text_lower for word in ['good', 'nice', 'decent', 'acceptable', 'fine']):
            return 'medium'
        
        # Low importance
        if any(word in text_lower for word in ['minor', 'small', 'slight', 'barely', 'hardly']):
            return 'low'
        
        return 'medium'  # Default
    
    def _calculate_impact_score(self, feature_text: str, feature_type: str) -> float:
        """Calculate impact score for a feature"""
        base_score = 0.5 if feature_type == 'pro' else -0.5
        
        # Adjust based on importance keywords
        text_lower = feature_text.lower()
        
        if any(word in text_lower for word in ['excellent', 'outstanding', 'amazing', 'perfect']):
            return base_score * 1.5
        elif any(word in text_lower for word in ['good', 'nice', 'decent']):
            return base_score * 1.0
        elif any(word in text_lower for word in ['minor', 'small', 'slight']):
            return base_score * 0.3
        
        return base_score
    
    def _get_relevant_structured_features(self, title: str, material: str, 
                                        brand: str, price: float, rating: float) -> Dict[str, List[str]]:
        """Get relevant structured features based on product characteristics"""
        features = {'pro': [], 'con': []}
        title_lower = title.lower()
        
        # Material-based features
        if material:
            material_lower = material.lower()
            
            if 'cotton' in material_lower:
                features['pro'].extend(['Softness', 'Breathability', 'Natural Texture', 'Easy Care'])
                features['con'].extend(['Wrinkles Easily', 'Can Feel Rough at First'])
            
            if 'sateen' in material_lower:
                features['pro'].extend(['Luxurious Feel', 'Silky Drape', 'Silken Sheen'])
                features['con'].extend(['Can Trap Heat'])
            
            if 'linen' in material_lower:
                features['pro'].extend(['Breathability', 'Natural Texture', 'Durability', 'Temperature Regulation'])
                features['con'].extend(['Wrinkles Easily', 'Can Feel Rough at First', 'Needs Gentle Care'])
            
            if 'bamboo' in material_lower:
                features['pro'].extend(['Softness', 'Moisture-Wicking', 'Eco-Friendly', 'Temperature Regulation'])
                features['con'].extend(['Higher Price Point', 'Needs Gentle Care'])
            
            if 'tencel' in material_lower:
                features['pro'].extend(['Softness', 'Moisture-Wicking', 'Temperature Regulation', 'Easy Care'])
                features['con'].extend(['Higher Price Point'])
        
        # Thread count features
        if 'thread' in title_lower:
            features['pro'].extend(['Luxurious Feel', 'Durability'])
            if '1000' in title_lower or '1200' in title_lower:
                features['pro'].append('Premium Quality')
                features['con'].append('Higher Price Point')
        
        # Size-based features
        if 'king' in title_lower or 'queen' in title_lower:
            features['pro'].append('Year-Round Comfort')
        
        if 'twin' in title_lower:
            features['pro'].append('Perfect for Kids')
        
        # Price-based features
        if price:
            if price > 150:
                features['con'].append('Higher Price Point')
                features['pro'].append('Luxury Quality')
            elif price < 50:
                features['pro'].append('Affordable')
            else:
                features['pro'].append('Good Value')
        
        # Rating-based features
        if rating:
            if rating >= 4.5:
                features['pro'].extend(['Trusted Brand', 'Popular Choice'])
            elif rating < 3.5:
                features['con'].append('New Brand')
        
        # Brand-specific features
        if brand:
            brand_lower = brand.lower()
            if 'boll' in brand_lower or 'branch' in brand_lower:
                features['pro'].extend(['Trusted Brand', 'Ethical Manufacturing'])
            elif 'bamboo' in brand_lower:
                features['pro'].extend(['Eco-Friendly', 'Sustainable Fiber'])
        
        # Common sheet features
        features['pro'].extend(['Easy Care', 'Machine Washable'])
        
        # Remove duplicates and limit to reasonable number
        features['pro'] = list(dict.fromkeys(features['pro']))[:8]  # Max 8 pros
        features['con'] = list(dict.fromkeys(features['con']))[:5]  # Max 5 cons
        
        return features
    
    def _categorize_structured_feature(self, feature: str) -> str:
        """Categorize structured feature"""
        feature_lower = feature.lower()
        
        # Quality features
        quality_keywords = ['durability', 'luxurious', 'premium', 'heirloom', 'lasts', 'strong', 'quality']
        if any(keyword in feature_lower for keyword in quality_keywords):
            return 'quality'
        
        # Comfort features
        comfort_keywords = ['softness', 'breathability', 'comfort', 'cooling', 'warmth', 'gentle', 'temperature']
        if any(keyword in feature_lower for keyword in comfort_keywords):
            return 'comfort'
        
        # Care features
        care_keywords = ['easy care', 'wrinkle', 'drying', 'washing', 'maintenance', 'washable']
        if any(keyword in feature_lower for keyword in care_keywords):
            return 'care'
        
        # Design features
        design_keywords = ['style', 'texture', 'finish', 'sheen', 'appeal', 'color', 'drape']
        if any(keyword in feature_lower for keyword in design_keywords):
            return 'design'
        
        # Value features
        value_keywords = ['brand', 'popular', 'returns', 'price', 'affordable', 'value', 'ethical', 'eco-friendly']
        if any(keyword in feature_lower for keyword in value_keywords):
            return 'value'
        
        return 'other'
    
    def _determine_structured_importance(self, feature: str, feature_type: str) -> str:
        """Determine importance for structured feature"""
        feature_lower = feature.lower()
        
        # High importance features
        high_importance = [
            'durability', 'softness', 'breathability', 'easy care', 
            'temperature regulation', 'luxurious feel', 'trusted brand',
            'wrinkles easily', 'sleeps warm', 'higher price point'
        ]
        
        if any(keyword in feature_lower for keyword in high_importance):
            return 'high'
        
        # Medium importance
        medium_importance = [
            'moisture-wicking', 'wrinkle resistance', 'hypoallergenic', 
            'natural texture', 'timeless style', 'popular choice',
            'can feel rough at first', 'needs gentle care'
        ]
        
        if any(keyword in feature_lower for keyword in medium_importance):
            return 'medium'
        
        return 'medium'  # Default
    
    def _calculate_structured_impact(self, feature: str, feature_type: str) -> float:
        """Calculate impact score for structured feature"""
        base_score = 0.7 if feature_type == 'pro' else -0.7
        
        feature_lower = feature.lower()
        
        # High impact features
        high_impact_pros = ['durability', 'softness', 'breathability', 'luxurious feel', 'trusted brand']
        high_impact_cons = ['wrinkles easily', 'sleeps warm', 'higher price point']
        
        if (feature_type == 'pro' and any(keyword in feature_lower for keyword in high_impact_pros)) or \
           (feature_type == 'con' and any(keyword in feature_lower for keyword in high_impact_cons)):
            return base_score * 1.2
        
        # Medium impact features
        medium_impact = ['easy care', 'temperature regulation', 'wrinkle resistance', 'popular choice']
        
        if any(keyword in feature_lower for keyword in medium_impact):
            return base_score * 1.0
        
        return base_score * 0.8  # Lower impact
    
    def _upload_new_product_images_to_vercel(self, products_added: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Upload images to Vercel for only the newly added products"""
        try:
            # Get image files for new products only
            image_files = []
            for product in products_added:
                product_id = product['id']
                
                # Get images for this product
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT primary_image_url, image_urls
                        FROM products
                        WHERE id = ?
                    """, (product_id,))
                    
                    row = cursor.fetchone()
                    if row:
                        primary_url, image_urls = row
                        
                        # Add primary image
                        if primary_url and primary_url.startswith('/images/products/'):
                            filename = primary_url.split('/')[-1]
                            image_path = self.images_dir / filename
                            if image_path.exists():
                                image_files.append(image_path)
                        
                        # Add additional images
                        if image_urls:
                            try:
                                urls_list = json.loads(image_urls)
                                for url in urls_list:
                                    if url.startswith('/images/products/'):
                                        filename = url.split('/')[-1]
                                        image_path = self.images_dir / filename
                                        if image_path.exists() and image_path not in image_files:
                                            image_files.append(image_path)
                            except (json.JSONDecodeError, TypeError):
                                continue
            
            if not image_files:
                return {'successful_uploads': 0, 'failed_uploads': 0, 'errors': []}
            
            print(f"   📊 Found {len(image_files)} images for {len(products_added)} new products")
            
            # Upload images
            results = {
                'successful_uploads': 0,
                'failed_uploads': 0,
                'errors': []
            }
            
            for i, image_path in enumerate(image_files, 1):
                print(f"   📤 [{i}/{len(image_files)}] Uploading {image_path.name}...")
                
                blob_url = self.vercel_uploader.upload_single_image(image_path)
                if blob_url:
                    results['successful_uploads'] += 1
                    self.vercel_uploader.uploaded_urls[image_path.name] = blob_url
                else:
                    results['failed_uploads'] += 1
                    results['errors'].append(f"Failed to upload {image_path.name}")
            
            return results
            
        except Exception as e:
            print(f"   ❌ Error uploading new product images: {e}")
            return {'successful_uploads': 0, 'failed_uploads': 0, 'errors': [str(e)]}
    
    def _update_vercel_urls_for_new_products(self, products_added: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Update Vercel URLs for only the newly added products"""
        try:
            updated_count = 0
            
            for product in products_added:
                product_id = product['id']
                
                with sqlite3.connect(self.db_path) as conn:
                    cursor = conn.cursor()
                    
                    # Get current image URLs
                    cursor.execute("""
                        SELECT primary_image_url, image_urls
                        FROM products
                        WHERE id = ?
                    """, (product_id,))
                    
                    row = cursor.fetchone()
                    if not row:
                        continue
                    
                    primary_url, image_urls = row
                    updated_primary = False
                    updated_image_urls = False
                    
                    # Update primary image URL
                    if primary_url and primary_url.startswith('/images/products/'):
                        filename = primary_url.split('/')[-1]
                        if filename in self.vercel_uploader.uploaded_urls:
                            new_primary_url = self.vercel_uploader.uploaded_urls[filename]
                            cursor.execute("""
                                UPDATE products 
                                SET primary_image_url = ?, updated_at = datetime('now')
                                WHERE id = ?
                            """, (new_primary_url, product_id))
                            updated_primary = True
                    
                    # Update image URLs array
                    if image_urls:
                        try:
                            urls_list = json.loads(image_urls)
                            updated_urls = []
                            
                            for url in urls_list:
                                if url.startswith('/images/products/'):
                                    filename = url.split('/')[-1]
                                    if filename in self.vercel_uploader.uploaded_urls:
                                        updated_urls.append(self.vercel_uploader.uploaded_urls[filename])
                                    else:
                                        updated_urls.append(url)
                                else:
                                    updated_urls.append(url)
                            
                            if updated_urls != urls_list:
                                cursor.execute("""
                                    UPDATE products 
                                    SET image_urls = ?, updated_at = datetime('now')
                                    WHERE id = ?
                                """, (json.dumps(updated_urls), product_id))
                                updated_image_urls = True
                                
                        except (json.JSONDecodeError, TypeError):
                            continue
                    
                    if updated_primary or updated_image_urls:
                        updated_count += 1
                        print(f"   ✅ Updated Vercel URLs for product {product_id}")
                    
                    conn.commit()
            
            return {'updated_products': updated_count}
            
        except Exception as e:
            print(f"   ❌ Error updating Vercel URLs: {e}")
            return {'updated_products': 0, 'error': str(e)}
    
    def _print_enhanced_summary(self, results: Dict[str, Any]):
        """Print enhanced processing summary"""
        print(f"\n🎉 Enhanced Pipeline Complete!")
        print(f"📊 Summary:")
        print(f"   Total URLs: {results['total_urls']}")
        print(f"   ✅ Successful: {results['successful']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   🚫 Invalid URLs: {results.get('invalid_urls', 0)}")
        print(f"   ⚠️  Duplicates: {results['duplicates']}")
        print(f"   🔗 Duplicates Handled: {results.get('duplicates_handled', 0)}")
        print(f"   📝 Summaries Generated: {results['summaries_generated']}")
        print(f"   🔍 Enhanced Pros/Cons: {results['enhanced_pros_cons']}")
        print(f"   ☁️  Images Uploaded: {results['images_uploaded']}")
        print(f"   🔄 Vercel URLs Updated: {results['vercel_urls_updated']}")
        
        if results['errors']:
            print(f"\n❌ Errors:")
            for error in results['errors'][:5]:
                print(f"   - {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more errors")
        
        if results['products_added']:
            print(f"\n✅ Products Added:")
            for product in results['products_added'][:5]:
                print(f"   - {product['sku']}: {product['title'][:50]}...")
            if len(results['products_added']) > 5:
                print(f"   ... and {len(results['products_added']) - 5} more products")

def main():
    """Example usage"""
    
    # Check for Vercel token
    vercel_token = os.getenv('VERCEL_TOKEN')
    
    pipeline = EnhancedAutomatedPipeline(vercel_token=vercel_token)
    
    print("🚀 Enhanced Automated Product Pipeline Ready!")
    print("Features:")
    print("  ✅ Extract product data from URLs")
    print("  ✅ Save images locally")
    print("  ✅ Generate product summaries")
    print("  ✅ Generate enhanced pros and cons")
    print("  ✅ Upload images to Vercel")
    print("  ✅ Update database with Vercel URLs")
    print("  ✅ Calculate product scores")
    print("\nUsage:")
    print("  results = pipeline.process_url_file_enhanced('your_file.csv', 'csv')")
    
    if not vercel_token:
        print("\n⚠️  VERCEL_TOKEN not set - Vercel upload will be skipped")
        print("   Set VERCEL_TOKEN environment variable to enable Vercel upload")

if __name__ == "__main__":
    main()
