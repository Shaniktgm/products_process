#!/usr/bin/env python3
"""
Automated Product Pipeline
Complete solution for adding new products from URL files
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

class AutomatedProductPipeline:
    """Complete pipeline for adding new products from URL files"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.images_dir = Path("images/products")
        self.images_dir.mkdir(exist_ok=True)
        
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
    
    def process_url_file(self, file_path: str, file_format: str = "csv") -> Dict[str, Any]:
        """
        Main entry point: Process a file containing product URLs
        
        Args:
            file_path: Path to file containing URLs
            file_format: "csv" or "txt" or "json"
        
        Returns:
            Dictionary with processing results
        """
        print(f"🚀 Starting automated product pipeline...")
        print(f"📁 Processing file: {file_path}")
        
        # Read URLs from file
        urls = self._read_urls_from_file(file_path, file_format)
        print(f"📋 Found {len(urls)} URLs to process")
        
        # Process each URL
        results = {
            'total_urls': len(urls),
            'successful': 0,
            'failed': 0,
            'duplicates': 0,
            'errors': [],
            'products_added': []
        }
        
        for i, url_data in enumerate(urls, 1):
            print(f"\n📦 Processing {i}/{len(urls)}: {url_data.get('url', 'Unknown URL')}")
            
            try:
                # Check for duplicates
                if self._is_duplicate(url_data['url']):
                    print(f"   ⚠️  Duplicate product found, skipping")
                    results['duplicates'] += 1
                    continue
                
                # Extract product data
                product_data = self._extract_product_data(url_data)
                
                if not product_data:
                    print(f"   ❌ Failed to extract product data")
                    results['failed'] += 1
                    results['errors'].append(f"Failed to extract data from {url_data['url']}")
                    continue
                
                # Validate data completeness
                validation_result = self._validate_product_data(product_data)
                if not validation_result['is_valid']:
                    print(f"   ⚠️  Data validation failed: {validation_result['errors']}")
                    # Continue anyway, but log the issues
                
                # Save to database
                product_id = self._save_product_to_database(product_data)
                
                if product_id:
                    print(f"   ✅ Product saved with ID: {product_id}")
                    results['successful'] += 1
                    results['products_added'].append({
                        'id': product_id,
                        'sku': product_data.get('sku'),
                        'title': product_data.get('title'),
                        'url': url_data['url']
                    })
                else:
                    print(f"   ❌ Failed to save product to database")
                    results['failed'] += 1
                    results['errors'].append(f"Database save failed for {url_data['url']}")
                
            except Exception as e:
                print(f"   ❌ Error processing URL: {e}")
                results['failed'] += 1
                results['errors'].append(f"Exception for {url_data['url']}: {str(e)}")
            
            # Rate limiting
            self._rate_limit()
        
        # Calculate scores for all new products
        if results['successful'] > 0:
            print(f"\n📊 Calculating scores for {results['successful']} new products...")
            self._calculate_scores_for_new_products(results['products_added'])
        
        # Print summary
        self._print_summary(results)
        
        return results
    
    def _read_urls_from_file(self, file_path: str, file_format: str) -> List[Dict[str, Any]]:
        """Read URLs from various file formats"""
        urls = []
        
        if file_format.lower() == "csv":
            with open(file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for row in reader:
                    if 'url' in row and row['url'].strip():
                        urls.append({
                            'url': row['url'].strip(),
                            'commission_rate': row.get('commission_rate', ''),
                            'notes': row.get('notes', '')
                        })
        
        elif file_format.lower() == "txt":
            with open(file_path, 'r', encoding='utf-8') as f:
                for line in f:
                    line = line.strip()
                    if line and line.startswith('http'):
                        urls.append({'url': line})
        
        elif file_format.lower() == "json":
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    urls = data
                elif isinstance(data, dict) and 'urls' in data:
                    urls = data['urls']
        
        return urls
    
    def _is_duplicate(self, url: str) -> bool:
        """Check if product already exists in database"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Extract ASIN from URL
            asin = self._extract_asin_from_url(url)
            if not asin:
                return False
            
            # Check if ASIN exists
            cursor.execute("SELECT COUNT(*) FROM products WHERE sku LIKE ?", (f"%{asin}%",))
            count = cursor.fetchone()[0]
            
            return count > 0
    
    def _extract_asin_from_url(self, url: str) -> Optional[str]:
        """Extract ASIN from Amazon URL"""
        try:
            # Handle different Amazon URL formats
            if '/dp/' in url:
                asin = url.split('/dp/')[1].split('/')[0].split('?')[0]
            elif '/product/' in url:
                asin = url.split('/product/')[1].split('/')[0].split('?')[0]
            elif 'asin=' in url:
                asin = parse_qs(urlparse(url).query).get('asin', [None])[0]
            else:
                return None
            
            # Validate ASIN format (10 characters, alphanumeric)
            if asin and len(asin) == 10 and asin.isalnum():
                return asin
            return None
            
        except Exception:
            return None
    
    def _extract_product_data(self, url_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Extract product data from URL"""
        url = url_data['url']
        
        try:
            # Make request with rate limiting
            self._rate_limit()
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            
            # Check for bot detection
            if "Robot Check" in response.text or "captcha" in response.text.lower():
                print(f"   ⚠️  Bot detection detected, skipping")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract basic product info
            product_data = {
                'url': url,
                'commission_rate': url_data.get('commission_rate', ''),
                'notes': url_data.get('notes', ''),
                'extraction_timestamp': time.strftime('%Y-%m-%d %H:%M:%S')
            }
            
            # Extract ASIN
            asin = self._extract_asin_from_url(url)
            if asin:
                product_data['sku'] = f"AMZ-{asin}"
                product_data['asin'] = asin
            
            # Extract title
            title_selectors = [
                '#productTitle',
                'h1.a-size-large',
                'h1[data-automation-id="product-title"]',
                '.product-title',
                'h1'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    product_data['title'] = self._clean_text(title_elem.get_text())
                    break
            
            # Extract price
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '.a-price-range .a-offscreen',
                '[data-automation-id="product-price"]',
                '.price'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text()
                    price = self._extract_price(price_text)
                    if price:
                        product_data['price'] = price
                        break
            
            # Extract rating
            rating_selectors = [
                '.a-icon-alt',
                '[data-automation-id="product-rating"]',
                '.rating'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text()
                    rating = self._extract_rating(rating_text)
                    if rating:
                        product_data['rating'] = rating
                        break
            
            # Extract review count
            review_selectors = [
                '#acrCustomerReviewText',
                '[data-automation-id="review-count"]',
                '.review-count'
            ]
            
            for selector in review_selectors:
                review_elem = soup.select_one(selector)
                if review_elem:
                    review_text = review_elem.get_text()
                    review_count = self._extract_review_count(review_text)
                    if review_count:
                        product_data['review_count'] = review_count
                        break
            
            # Extract images
            images = self._extract_images(soup, asin)
            if images:
                product_data['primary_image_url'] = images[0]
                product_data['image_urls'] = json.dumps(images)
            
            # Extract description
            desc_selectors = [
                '#feature-bullets ul',
                '.product-description',
                '[data-automation-id="product-description"]'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    product_data['description'] = self._clean_text(desc_elem.get_text())
                    break
            
            return product_data
            
        except Exception as e:
            print(f"   ❌ Error extracting data: {e}")
            return None
    
    def _extract_images(self, soup: BeautifulSoup, asin: str) -> List[str]:
        """Extract and download product images"""
        images = []
        
        try:
            # Find image elements
            img_selectors = [
                '#landingImage',
                '.a-dynamic-image',
                '[data-automation-id="product-image"]',
                'img[data-old-hires]'
            ]
            
            img_elements = []
            for selector in img_selectors:
                elements = soup.select(selector)
                img_elements.extend(elements)
            
            # Remove duplicates
            seen_urls = set()
            for img in img_elements:
                img_url = img.get('src') or img.get('data-src') or img.get('data-old-hires')
                if img_url and img_url not in seen_urls:
                    seen_urls.add(img_url)
                    
                    # Download and save image
                    local_path = self._download_image(img_url, asin, len(images))
                    if local_path:
                        images.append(local_path)
            
            return images
            
        except Exception as e:
            print(f"   ⚠️  Error extracting images: {e}")
            return []
    
    def _download_image(self, img_url: str, asin: str, index: int) -> Optional[str]:
        """Download image and save locally"""
        try:
            # Determine file extension
            ext = '.jpg'
            if '.webp' in img_url:
                ext = '.webp'
            elif '.png' in img_url:
                ext = '.png'
            
            # Create filename
            if index == 0:
                filename = f"{asin}{ext}"
            else:
                filename = f"{asin}_{index}{ext}"
            
            filepath = self.images_dir / filename
            
            # Download image
            response = self.session.get(img_url, timeout=30)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            return f"/images/products/{filename}"
            
        except Exception as e:
            print(f"   ⚠️  Error downloading image: {e}")
            return None
    
    def _validate_product_data(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """Validate product data completeness"""
        required_fields = ['title', 'price', 'rating', 'review_count', 'primary_image_url']
        missing_fields = []
        
        for field in required_fields:
            if not product_data.get(field):
                missing_fields.append(field)
        
        return {
            'is_valid': len(missing_fields) == 0,
            'missing_fields': missing_fields,
            'errors': [f"Missing {field}" for field in missing_fields]
        }
    
    def _save_product_to_database(self, product_data: Dict[str, Any]) -> Optional[int]:
        """Save product to database"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Insert product
                cursor.execute("""
                    INSERT INTO products (
                        sku, title, description, price, rating, review_count,
                        primary_image_url, image_urls, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, datetime('now'), datetime('now'))
                """, (
                    product_data.get('sku'),
                    product_data.get('title'),
                    product_data.get('description'),
                    product_data.get('price'),
                    product_data.get('rating'),
                    product_data.get('review_count'),
                    product_data.get('primary_image_url'),
                    product_data.get('image_urls')
                ))
                
                product_id = cursor.lastrowid
                
                # Add to Amazon platform
                cursor.execute("SELECT id FROM platforms WHERE name = 'Amazon'")
                platform_result = cursor.fetchone()
                if platform_result:
                    platform_id = platform_result[0]
                    cursor.execute("""
                        INSERT INTO product_platforms (product_id, platform_id, platform_url)
                        VALUES (?, ?, ?)
                    """, (product_id, platform_id, product_data['url']))
                
                # Add affiliate link if commission rate provided
                if product_data.get('commission_rate'):
                    cursor.execute("""
                        INSERT INTO affiliate_links (product_id, platform_id, url, commission_rate)
                        VALUES (?, ?, ?, ?)
                    """, (product_id, platform_id, product_data['url'], product_data['commission_rate']))
                
                conn.commit()
                return product_id
                
        except Exception as e:
            print(f"   ❌ Database error: {e}")
            return None
    
    def _calculate_scores_for_new_products(self, products: List[Dict[str, Any]]):
        """Calculate scores for newly added products"""
        try:
            # Import and run scoring system
            from configurable_scoring_system import ConfigurableScoringSystem
            
            scoring_system = ConfigurableScoringSystem(self.db_path)
            scoring_system.update_all_product_scores()
            
            print(f"   ✅ Scores calculated for {len(products)} products")
            
        except Exception as e:
            print(f"   ⚠️  Error calculating scores: {e}")
    
    def _rate_limit(self):
        """Implement rate limiting"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _clean_text(self, text: str) -> str:
        """Clean extracted text"""
        if not text:
            return ""
        return re.sub(r'\s+', ' ', text.strip())
    
    def _extract_price(self, price_text: str) -> Optional[float]:
        """Extract price from text"""
        try:
            # Remove currency symbols and extract number
            price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
            if price_match:
                return float(price_match.group())
        except:
            pass
        return None
    
    def _extract_rating(self, rating_text: str) -> Optional[float]:
        """Extract rating from text"""
        try:
            # Look for patterns like "4.5 out of 5"
            rating_match = re.search(r'(\d+\.?\d*)\s*out of', rating_text)
            if rating_match:
                return float(rating_match.group(1))
            
            # Look for just the number
            rating_match = re.search(r'(\d+\.?\d*)', rating_text)
            if rating_match:
                rating = float(rating_match.group(1))
                if rating <= 5:  # Valid rating range
                    return rating
        except:
            pass
        return None
    
    def _extract_review_count(self, review_text: str) -> Optional[int]:
        """Extract review count from text"""
        try:
            # Remove commas and extract number
            count_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
            if count_match:
                return int(count_match.group(1))
        except:
            pass
        return None
    
    def _print_summary(self, results: Dict[str, Any]):
        """Print processing summary"""
        print(f"\n🎉 Processing Complete!")
        print(f"📊 Summary:")
        print(f"   Total URLs: {results['total_urls']}")
        print(f"   ✅ Successful: {results['successful']}")
        print(f"   ❌ Failed: {results['failed']}")
        print(f"   ⚠️  Duplicates: {results['duplicates']}")
        
        if results['errors']:
            print(f"\n❌ Errors:")
            for error in results['errors'][:5]:  # Show first 5 errors
                print(f"   - {error}")
            if len(results['errors']) > 5:
                print(f"   ... and {len(results['errors']) - 5} more errors")
        
        if results['products_added']:
            print(f"\n✅ Products Added:")
            for product in results['products_added'][:5]:  # Show first 5
                print(f"   - {product['sku']}: {product['title'][:50]}...")
            if len(results['products_added']) > 5:
                print(f"   ... and {len(results['products_added']) - 5} more products")

def main():
    """Example usage"""
    pipeline = AutomatedProductPipeline()
    
    # Example: Process a CSV file
    # results = pipeline.process_url_file("new_products.csv", "csv")
    
    # Example: Process a text file
    # results = pipeline.process_url_file("urls.txt", "txt")
    
    print("🚀 Automated Product Pipeline Ready!")
    print("Usage: pipeline.process_url_file('your_file.csv', 'csv')")

if __name__ == "__main__":
    main()
