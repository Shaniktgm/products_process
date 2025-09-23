#!/usr/bin/env python3
"""
Phase 1: Data Collection Pipeline
Handles CSV processing and Amazon product data scraping
"""

import csv
import json
import sqlite3
import requests
import time
import os
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup
from urllib.parse import urlparse, parse_qs
import re
from datetime import datetime
from tqdm import tqdm

class DataCollectionPipeline:
    """Phase 1: Collect product data from Amazon via affiliate links"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.images_dir = Path("images/products")
        self.images_dir.mkdir(exist_ok=True)
        
        # Rate limiting - wait a few seconds between calls
        self.request_delay = 3  # seconds between requests
        self.last_request_time = 0
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Statistics tracking
        self.stats = {
            'processed': 0,
            'products_created': 0,
            'products_updated': 0,
            'images_downloaded': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _rate_limit(self):
        """Ensure we wait between requests to be respectful to Amazon"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _extract_amazon_product_id(self, url: str) -> Optional[str]:
        """Extract Amazon product ID from affiliate link"""
        try:
            # Handle different Amazon URL formats
            patterns = [
                r'/dp/([A-Z0-9]{10})',  # Standard /dp/ format
                r'/product/([A-Z0-9]{10})',  # Alternative /product/ format
                r'asin=([A-Z0-9]{10})',  # ASIN parameter
                r'/([A-Z0-9]{10})/',  # Direct ASIN in path
            ]
            
            for pattern in patterns:
                match = re.search(pattern, url, re.IGNORECASE)
                if match:
                    return match.group(1)
            
            return None
        except Exception as e:
            print(f"❌ Error extracting product ID from {url}: {e}")
            return None
    
    def _clean_amazon_url(self, url: str) -> Optional[str]:
        """Clean Amazon URL by removing referral parameters and keeping only the product URL"""
        try:
            # Parse the URL
            parsed = urlparse(url)
            
            # Extract ASIN from the path
            asin = None
            if '/dp/' in parsed.path:
                asin = parsed.path.split('/dp/')[1].split('/')[0]
            elif '/product/' in parsed.path:
                asin = parsed.path.split('/product/')[1].split('/')[0]
            elif 'asin=' in parsed.query:
                asin = parse_qs(parsed.query).get('asin', [None])[0]
            
            if asin:
                # Reconstruct clean URL: https://www.amazon.com/dp/ASIN
                clean_url = f"https://www.amazon.com/dp/{asin}"
                return clean_url
            
            return url  # Return original if can't clean
        except Exception as e:
            print(f"❌ Error cleaning URL {url}: {e}")
            return url
    
    def _convert_affiliate_to_product_url(self, affiliate_url: str) -> Optional[str]:
        """Convert affiliate link to direct product link"""
        try:
            # Extract product ID from affiliate link
            product_id = self._extract_amazon_product_id(affiliate_url)
            if not product_id:
                return None
            
            # Create direct Amazon product URL
            return f"https://www.amazon.com/dp/{product_id}"
        except Exception as e:
            print(f"❌ Error converting affiliate URL {affiliate_url}: {e}")
            return None
    
    def _update_product_price_discount(self, cursor, product_id: int, discount: Optional[float], start_date: Optional[datetime]) -> None:
        """Update only price and discount for existing product"""
        try:
            # Update affiliation_details with new discount and start_date
            cursor.execute("""
                UPDATE affiliation_details 
                SET discount = ?, start_date = ?, updated_at = ?
                WHERE product_id = ? AND platform_id = 8
            """, (discount, start_date, datetime.now(), product_id))
            
            # Update products table updated_at timestamp
            cursor.execute("""
                UPDATE products 
                SET updated_at = ?
                WHERE id = ?
            """, (datetime.now(), product_id))
            
            print(f"   ✅ Updated price/discount for product {product_id}")
            
        except Exception as e:
            print(f"   ❌ Error updating product {product_id}: {e}")
            raise
    
    def process_affiliate_links_file(self, csv_file_path: str) -> Dict[str, int]:
        """Process CSV file with affiliate links with smart 48-hour logic"""
        print(f"📋 Processing affiliate links from: {csv_file_path}")
        
        if not os.path.exists(csv_file_path):
            print(f"❌ CSV file not found: {csv_file_path}")
            return {'processed': 0, 'errors': 1}
        
        conn = self._get_db_connection()
        
        try:
            cursor = conn.cursor()
            
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in tqdm(reader, desc="Processing affiliate links"):
                    try:
                        # Extract affiliate URL - try different column names
                        affiliate_url = (row.get('referral link', '') or 
                                       row.get('affiliate_url', '') or 
                                       row.get('affiliate link', '')).strip()
                        if not affiliate_url:
                            continue
                        
                        # Extract discount and start_date
                        discount = None
                        start_date = None
                        
                        # Handle discount
                        discount_str = row.get('discount', '').strip()
                        if discount_str:
                            try:
                                discount = float(discount_str)
                            except ValueError:
                                print(f"⚠️ Invalid discount value: {discount_str}")
                        
                        # Handle start_date
                        start_date_str = row.get('Start date', '').strip()
                        if start_date_str:
                            try:
                                # Parse date format like "Sep 10, 2025 09:59 GMT+3"
                                from datetime import datetime
                                # Try to parse the date format
                                start_date = datetime.strptime(start_date_str.split(' GMT')[0], '%b %d, %Y %H:%M').date()
                            except ValueError:
                                try:
                                    # Try alternative format
                                    start_date = datetime.strptime(start_date_str.split(' GMT')[0], '%m/%d/%Y %H:%M').date()
                                except ValueError:
                                    print(f"⚠️ Invalid start_date format: {start_date_str}")
                        
                        # Convert affiliate link to product link
                        product_url = self._convert_affiliate_to_product_url(affiliate_url)
                        if not product_url:
                            print(f"⚠️ Could not convert affiliate URL: {affiliate_url}")
                            self.stats['errors'] += 1
                            continue
                        
                        # Extract product ID
                        product_id = self._extract_amazon_product_id(affiliate_url)
                        if not product_id:
                            print(f"⚠️ Could not extract product ID from: {affiliate_url}")
                            self.stats['errors'] += 1
                            continue
                        
                        # Check if product already exists and get last update time
                        cursor.execute("""
                            SELECT id, updated_at FROM products 
                            WHERE amazon_product_id = ?
                        """, (product_id,))
                        existing_product = cursor.fetchone()
                        
                        if existing_product:
                            product_db_id, last_updated = existing_product
                            
                            # Check if updated within last 48 hours
                            if last_updated:
                                last_updated_dt = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                                time_diff = datetime.now() - last_updated_dt.replace(tzinfo=None)
                                
                                if time_diff.total_seconds() < 48 * 3600:  # 48 hours in seconds
                                    print(f"⏭️ Product {product_id} updated {time_diff.total_seconds()/3600:.1f}h ago - skipping")
                                    self.stats['skipped'] += 1
                                    continue
                            
                            # Product exists but not updated recently - update only price/discount
                            print(f"🔄 Updating price/discount for existing product {product_id}")
                            self._update_product_price_discount(cursor, product_db_id, discount, start_date)
                            self.stats['products_updated'] += 1
                        else:
                            # New product - create and process fully
                            print(f"🆕 Creating new product {product_id}")
                            sku = f"AMZ-{product_id}"
                            title = f"Amazon Product {product_id}"
                            
                            # Create new product
                            cursor.execute("""
                                INSERT INTO products (sku, title, amazon_product_id, created_at, updated_at)
                                VALUES (?, ?, ?, ?, ?)
                            """, (sku, title, product_id, datetime.now(), datetime.now()))
                            
                            new_product_id = cursor.lastrowid
                            
                            # Add affiliate link
                            cursor.execute("""
                                INSERT INTO affiliation_details 
                                (product_id, platform_id, affiliate_url, link_type, discount, start_date)
                                VALUES (?, 8, ?, 'web', ?, ?)
                            """, (new_product_id, affiliate_url, discount, start_date))
                            
                            self.stats['products_created'] += 1
                        
                        conn.commit()
                        self.stats['processed'] += 1
                        
                    except Exception as e:
                        print(f"❌ Error processing row: {e}")
                        self.stats['errors'] += 1
                        continue
        
        finally:
            conn.close()
        
        return self.stats
    
    def extract_product_details(self, url: str) -> Dict[str, Any]:
        """Extract product details from Amazon URL"""
        self._rate_limit()  # Wait between requests
        
        try:
            print(f"🔍 Scraping: {url}")
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product details
            details = {}
            
            # Title
            title_selectors = [
                '#productTitle',
                'h1.a-size-large',
                '.product-title',
                'h1[data-automation-id="product-title"]'
            ]
            
            for selector in title_selectors:
                title_elem = soup.select_one(selector)
                if title_elem:
                    details['title'] = title_elem.get_text().strip()
                    break
            
            # Price
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price-range'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text().strip()
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        details['price'] = float(price_match.group().replace(',', ''))
                        break
            
            # Rating
            rating_elem = soup.select_one('.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    details['rating'] = float(rating_match.group(1))
            
            # Review count
            review_elem = soup.select_one('#acrCustomerReviewText, .a-size-base')
            if review_elem:
                review_text = review_elem.get_text()
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    details['review_count'] = int(review_match.group(1).replace(',', ''))
            
            # Brand
            brand_elem = soup.select_one('#bylineInfo, .a-link-normal')
            if brand_elem:
                details['brand'] = brand_elem.get_text().strip()
            
            # Description
            desc_selectors = [
                '#feature-bullets ul',
                '.a-unordered-list',
                '#productDescription'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    details['description'] = desc_elem.get_text().strip()
                    break
            
            # Images
            image_elem = soup.select_one('#landingImage, #imgBlkFront')
            if image_elem:
                details['primary_image_url'] = image_elem.get('src') or image_elem.get('data-src')
            
            # Additional images
            additional_images = []
            img_elements = soup.select('#altImages img, .a-dynamic-image')
            for img in img_elements[:5]:  # Limit to 5 additional images
                img_url = img.get('src') or img.get('data-src')
                if img_url and 'http' in img_url:
                    additional_images.append(img_url)
            
            if additional_images:
                details['image_urls'] = additional_images
            
            return details
            
        except Exception as e:
            print(f"❌ Error extracting details from {url}: {e}")
            return {}
    
    def download_image(self, image_url: str, product_id: str) -> Optional[str]:
        """Download and save product image"""
        try:
            if not image_url or 'http' not in image_url:
                return None
            
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Determine file extension
            content_type = response.headers.get('content-type', '')
            if 'jpeg' in content_type or 'jpg' in content_type:
                ext = '.jpg'
            elif 'png' in content_type:
                ext = '.png'
            elif 'webp' in content_type:
                ext = '.webp'
            else:
                ext = '.jpg'  # Default
            
            # Save image
            image_path = self.images_dir / f"{product_id}{ext}"
            with open(image_path, 'wb') as f:
                f.write(response.content)
            
            self.stats['images_downloaded'] += 1
            return str(image_path)
            
        except Exception as e:
            print(f"❌ Error downloading image {image_url}: {e}")
            return None
    
    def update_product_with_details(self, conn: sqlite3.Connection, 
                                  product_id: int, details: Dict[str, Any]):
        """Update product with extracted details"""
        cursor = conn.cursor()
        
        # Update basic product info
        cursor.execute("""
            UPDATE products SET
                title = ?, description = ?, price = ?, rating = ?,
                review_count = ?, brand = ?, primary_image_url = ?,
                image_urls = ?, updated_at = ?
            WHERE id = ?
        """, (
            details.get('title'),
            details.get('description'),
            details.get('price'),
            details.get('rating'),
            details.get('review_count'),
            details.get('brand'),
            details.get('primary_image_url'),
            json.dumps(details.get('image_urls', [])),
            datetime.now(),
            product_id
        ))
        
        # Download primary image
        if details.get('primary_image_url'):
            image_path = self.download_image(details['primary_image_url'], str(product_id))
            if image_path:
                cursor.execute(
                    "UPDATE products SET local_image_path = ? WHERE id = ?",
                    (image_path, product_id)
                )
        
        # Download additional images
        if details.get('image_urls'):
            for i, img_url in enumerate(details['image_urls'][:3]):  # Limit to 3 additional
                image_path = self.download_image(img_url, f"{product_id}_{i+1}")
                # Could store additional image paths in a separate table if needed
    
    def run_data_collection(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run Phase 1: Data Collection Pipeline"""
        print("🚀 Starting Phase 1: Data Collection Pipeline")
        print("=" * 60)
        
        # Step 1: Process affiliate links
        print("\n📋 Step 1: Processing Affiliate Links")
        affiliate_results = self.process_affiliate_links_file(affiliate_csv_path)
        print(f"✅ Processed {affiliate_results['processed']} affiliate links")
        print(f"   📊 Created {affiliate_results['products_created']} new products")
        print(f"   🔄 Updated {affiliate_results['products_updated']} existing products")
        print(f"   📊 Skipped {affiliate_results['skipped']} existing products")
        print(f"   ❌ Errors: {affiliate_results['errors']}")
        
        # Step 2: Extract product details from URLs
        print("\n🔍 Step 2: Extracting Product Details from Amazon")
        conn = self._get_db_connection()
        
        try:
            cursor = conn.cursor()
            cursor.execute("""
                SELECT p.id, p.amazon_product_id, ad.affiliate_url
                FROM products p
                JOIN affiliation_details ad ON p.id = ad.product_id
                WHERE p.title IS NULL OR p.title = '' OR p.description IS NULL
            """)
            
            products_to_process = cursor.fetchall()
            print(f"📊 Found {len(products_to_process)} products needing data extraction")
            
            for product_id, amazon_id, referral_link in tqdm(products_to_process, desc="Extracting details"):
                try:
                    # Convert affiliate link to product link
                    product_url = self._convert_affiliate_to_product_url(referral_link)
                    if not product_url:
                        print(f"⚠️ Could not convert affiliate URL for product {product_id}")
                        continue
                    
                    # Extract details from product URL (not affiliate URL)
                    details = self.extract_product_details(product_url)
                    
                    if details:
                        # Update product with details
                        self.update_product_with_details(conn, product_id, details)
                        
                        # Generate simple pretty title (like main pipeline)
                        pretty_title = self.generate_pretty_title(
                            details.get('title', ''), 
                            details.get('brand', '')
                        )
                        
                        cursor.execute(
                            "UPDATE products SET pretty_title = ? WHERE id = ?",
                            (pretty_title, product_id)
                        )
                        conn.commit()
                        
                        self.stats['products_updated'] += 1
                        print(f"✅ Updated product {product_id}: {details.get('title', 'No title')[:50]}...")
                    else:
                        print(f"⚠️ No details extracted for product {product_id}")
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    self.stats['errors'] += 1
                    continue
        
        finally:
            conn.close()
        
        # Final statistics
        print(f"\n📊 Phase 1 Complete!")
        print(f"   ✅ Products updated: {self.stats['products_updated']}")
        print(f"   🖼️ Images downloaded: {self.stats['images_downloaded']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
        
        return self.stats
    
    def generate_pretty_title(self, title: str, brand: str = None) -> str:
        """Generate a pretty, short title for product cards (from main_pipeline.py)"""
        if not title:
            return "Product"
        
        # Extract key components
        components = []
        
        # Brand
        if brand and brand not in ['Unknown', 'Visit the', '']:
            components.append(brand)
        
        # Extract size
        size_match = re.search(r'\b(King|Queen|Full|Twin|Cal King|Split King)\b', title, re.IGNORECASE)
        if size_match:
            components.append(f"{size_match.group(1)}")
        
        # Extract thread count
        thread_match = re.search(r'(\d+)\s*thread', title, re.IGNORECASE)
        if thread_match:
            components.append(f"{thread_match.group(1)} Thread")
        
        # Extract material
        material_match = re.search(r'(Egyptian Cotton|Cotton|Bamboo|Linen|Silk)', title, re.IGNORECASE)
        if material_match:
            components.append(material_match.group(1))
        
        # Extract product type
        if 'Sheet' in title:
            components.append('Sheet Set')
        elif 'Pillow' in title:
            components.append('Pillow')
        elif 'Comforter' in title:
            components.append('Comforter')
        elif 'Blanket' in title:
            components.append('Blanket')
        elif 'Duvet' in title:
            components.append('Duvet')
        
        # Join components
        if components:
            return ' '.join(components[:4])  # Limit to 4 components
        
        # Fallback: use first few words of title
        words = title.split()[:6]
        return ' '.join(words)

def main():
    """Run Phase 1: Data Collection Pipeline"""
    pipeline = DataCollectionPipeline()
    results = pipeline.run_data_collection()
    
    print(f"\n🎉 Phase 1 Complete!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
