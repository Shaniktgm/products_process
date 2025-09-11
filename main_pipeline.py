#!/usr/bin/env python3
"""
Complete Product Pipeline - A-Z
Unified pipeline that handles everything from affiliate links to final product data
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
from tqdm import tqdm

# Import our existing systems
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core.generate_product_summaries import ProductSummaryGenerator
from core.enhanced_pros_cons_system import EnhancedProsConsSystem
from core.dynamic_pros_cons_generator import DynamicProsConsGenerator

class CompleteProductPipeline:
    """Complete A-Z pipeline for product data processing"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.images_dir = Path("images/products")
        self.images_dir.mkdir(exist_ok=True)
        
        # Initialize subsystems
        self.summary_generator = ProductSummaryGenerator(db_path)
        self.enhanced_pros_cons = EnhancedProsConsSystem(db_path)
        self.dynamic_pros_cons = DynamicProsConsGenerator(db_path)
        
        # Rate limiting
        self.request_delay = 2  # seconds between requests
        self.last_request_time = 0
        
        # Session for persistent connections
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
        
        # Statistics tracking
        self.stats = {
            'affiliate_links_processed': 0,
            'products_created': 0,
            'products_updated': 0,
            'images_downloaded': 0,
            'summaries_generated': 0,
            'pros_cons_generated': 0,
            'pretty_titles_generated': 0,
            'errors': 0
        }
    
    def _rate_limit(self):
        """Ensure we don't make requests too quickly"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        if time_since_last < self.request_delay:
            time.sleep(self.request_delay - time_since_last)
        self.last_request_time = time.time()
    
    def _get_db_connection(self):
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _extract_amazon_product_id(self, url: str) -> Optional[str]:
        """Extract Amazon product ID from URL"""
        try:
            # Handle different Amazon URL formats
            if '/dp/' in url:
                return url.split('/dp/')[1].split('/')[0].split('?')[0]
            elif '/product/' in url:
                return url.split('/product/')[1].split('/')[0].split('?')[0]
            elif 'asin=' in url:
                return url.split('asin=')[1].split('&')[0]
            return None
        except:
            return None
    
    def _get_or_create_platform(self, conn: sqlite3.Connection, platform_name: str) -> int:
        """Get or create platform and return platform_id"""
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM platforms WHERE name = ?", (platform_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            cursor.execute(
                "INSERT INTO platforms (name, display_name, base_url) VALUES (?, ?, ?)",
                (platform_name, platform_name.title(), f"https://{platform_name}.com")
            )
            conn.commit()
            return cursor.lastrowid
    
    def _get_or_create_product_from_affiliate(self, conn: sqlite3.Connection, 
                                            amazon_product_id: str, title: str, 
                                            platform_id: int) -> int:
        """Get or create product from affiliate data"""
        cursor = conn.cursor()
        
        # Check if product already exists
        cursor.execute(
            "SELECT id FROM products WHERE amazon_product_id = ?", 
            (amazon_product_id,)
        )
        result = cursor.fetchone()
        
        if result:
            return result[0]
        else:
            # Create new product with a unique SKU
            sku = f"AMZ-{amazon_product_id}"
            cursor.execute("""
                INSERT INTO products (
                    sku, amazon_product_id, title, created_at, updated_at
                ) VALUES (?, ?, ?, ?, ?)
            """, (sku, amazon_product_id, title, datetime.now(), datetime.now()))
            conn.commit()
            return cursor.lastrowid
    
    def _create_or_update_affiliate_link(self, conn: sqlite3.Connection, 
                                       product_id: int, referral_link: str,
                                       commission_rate: float, end_date: str = None,
                                       internal_link: str = None) -> int:
        """Create or update affiliate link"""
        cursor = conn.cursor()
        
        # Generate pretty referral link
        pretty_link = self._generate_pretty_referral_link(referral_link)
        
        # Get platform_id for Amazon
        cursor.execute("SELECT id FROM platforms WHERE name = 'amazon'")
        platform_result = cursor.fetchone()
        platform_id = platform_result[0] if platform_result else 1
        
        cursor.execute("""
            INSERT OR REPLACE INTO affiliation_details (
                product_id, platform_id, link_type, affiliate_url, 
                pretty_referral_link, commission_rate, end_date, 
                affiliate_page_internal_link, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """, (product_id, platform_id, 'web', referral_link, pretty_link, 
              commission_rate, end_date, internal_link, datetime.now(), datetime.now()))
        
        conn.commit()
        return cursor.lastrowid
    
    def _generate_pretty_referral_link(self, referral_link: str) -> str:
        """Generate a short, valid referral link with homeprinciple tag"""
        try:
            # Extract the base URL and add our tag
            parsed = urlparse(referral_link)
            base_url = f"{parsed.scheme}://{parsed.netloc}{parsed.path}"
            
            # Add our tag
            if '?' in referral_link:
                return f"{base_url}?tag=homeprinciple&{parsed.query}"
            else:
                return f"{base_url}?tag=homeprinciple"
        except:
            return referral_link
    
    def process_affiliate_links_file(self, csv_file_path: str) -> Dict[str, int]:
        """Process affiliate links CSV file"""
        print("🔗 Processing affiliate links...")
        
        results = {
            'processed': 0,
            'created': 0,
            'updated': 0,
            'errors': 0
        }
        
        conn = self._get_db_connection()
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in tqdm(reader, desc="Processing affiliate links"):
                    try:
                        referral_link = row.get('referral link', '').strip()
                        if not referral_link:
                            continue
                        
                        # Extract Amazon product ID
                        amazon_product_id = self._extract_amazon_product_id(referral_link)
                        if not amazon_product_id:
                            print(f"⚠️  No Amazon product ID found in URL: {referral_link}")
                            results['errors'] += 1
                            continue
                        
                        # Get or create platform
                        platform_name = row.get('platform', 'amazon').strip()
                        platform_id = self._get_or_create_platform(conn, platform_name)
                        
                        # Get title from row or generate from URL
                        title = row.get('title', '').strip()
                        if not title:
                            title = f"Amazon Product {amazon_product_id}"
                        
                        # Get or create product
                        product_id = self._get_or_create_product_from_affiliate(
                            conn, amazon_product_id, title, platform_id
                        )
                        
                        # Parse commission rate
                        commission_str = row.get('commission', '0')
                        if commission_str:
                            commission_str = commission_str.replace('%', '')
                            commission_rate = float(commission_str) / 100.0 if commission_str else 0.0
                        else:
                            commission_rate = 0.0
                        
                        # Get other fields
                        end_date = row.get('End date', '').strip() or None
                        internal_link = row.get('affilate_page_internal_link', '').strip() or None
                        
                        # Create or update affiliate link
                        self._create_or_update_affiliate_link(
                            conn, product_id, referral_link, commission_rate, 
                            end_date, internal_link
                        )
                        
                        results['processed'] += 1
                        if product_id:
                            results['created'] += 1
                        
                    except Exception as e:
                        print(f"❌ Error processing row: {e}")
                        results['errors'] += 1
                        continue
        
        finally:
            conn.close()
        
        self.stats['affiliate_links_processed'] = results['processed']
        return results
    
    def extract_product_details(self, url: str) -> Dict[str, Any]:
        """Extract detailed product information from Amazon URL"""
        self._rate_limit()
        
        try:
            response = self.session.get(url, timeout=10)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Extract product details
            details = {}
            
            # Title
            title_elem = soup.find('span', {'id': 'productTitle'})
            if title_elem:
                details['title'] = title_elem.get_text().strip()
            
            # Price
            price_elem = soup.find('span', {'class': 'a-price-whole'})
            if price_elem:
                price_text = price_elem.get_text().replace(',', '')
                try:
                    details['price'] = float(price_text)
                except:
                    pass
            
            # Rating
            rating_elem = soup.find('span', {'class': 'a-icon-alt'})
            if rating_elem:
                rating_text = rating_elem.get_text()
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    details['rating'] = float(rating_match.group(1))
            
            # Review count
            review_elem = soup.find('span', {'id': 'acrCustomerReviewText'})
            if review_elem:
                review_text = review_elem.get_text()
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    details['review_count'] = int(review_match.group(1).replace(',', ''))
            
            # Description
            desc_elem = soup.find('div', {'id': 'feature-bullets'})
            if desc_elem:
                bullets = desc_elem.find_all('span', {'class': 'a-list-item'})
                descriptions = []
                for bullet in bullets:
                    text = bullet.get_text().strip()
                    if text and not text.startswith('Make sure this fits'):
                        descriptions.append(text)
                details['description'] = ' '.join(descriptions)
            
            # Brand
            brand_elem = soup.find('a', {'id': 'bylineInfo'})
            if brand_elem:
                details['brand'] = brand_elem.get_text().strip()
            
            # Material and other specs
            spec_elem = soup.find('div', {'id': 'detailBullets_feature_div'})
            if spec_elem:
                spec_items = spec_elem.find_all('span', {'class': 'a-list-item'})
                for item in spec_items:
                    text = item.get_text().strip()
                    if 'Material' in text:
                        details['material'] = text.split('Material')[1].strip()
                    elif 'Color' in text:
                        details['color'] = text.split('Color')[1].strip()
                    elif 'Size' in text:
                        details['size'] = text.split('Size')[1].strip()
            
            # Images
            image_elements = soup.find_all('img', {'data-old-hires': True})
            image_urls = []
            for img in image_elements:
                img_url = img.get('data-old-hires') or img.get('src')
                if img_url and 'amazon' in img_url:
                    image_urls.append(img_url)
            
            if image_urls:
                details['image_urls'] = image_urls
            
            return details
            
        except Exception as e:
            print(f"❌ Error extracting details from {url}: {e}")
            return {}
    
    def download_image(self, image_url: str, product_id: str) -> Optional[str]:
        """Download image and return local path"""
        try:
            self._rate_limit()
            
            response = self.session.get(image_url, timeout=10)
            response.raise_for_status()
            
            # Create filename
            filename = f"{product_id}_{int(time.time())}.jpg"
            local_path = self.images_dir / filename
            
            # Save image
            with open(local_path, 'wb') as f:
                f.write(response.content)
            
            return str(local_path)
            
        except Exception as e:
            print(f"❌ Error downloading image {image_url}: {e}")
            return None
    
    def update_product_with_details(self, conn: sqlite3.Connection, 
                                  product_id: int, details: Dict[str, Any]):
        """Update product with extracted details"""
        cursor = conn.cursor()
        
        # Prepare update fields
        update_fields = []
        update_values = []
        
        for field, value in details.items():
            if field == 'image_urls':
                continue  # Handle images separately
            if value is not None:
                update_fields.append(f"{field} = ?")
                update_values.append(value)
        
        if update_fields:
            update_values.append(datetime.now())  # updated_at
            update_values.append(product_id)  # WHERE clause
            
            query = f"""
                UPDATE products 
                SET {', '.join(update_fields)}, updated_at = ?
                WHERE product_id = ?
            """
            cursor.execute(query, update_values)
            conn.commit()
        
        # Handle images
        if 'image_urls' in details and details['image_urls']:
            for i, image_url in enumerate(details['image_urls'][:5]):  # Limit to 5 images
                # Download image
                local_path = self.download_image(image_url, str(product_id))
                
                if local_path:
                    # Insert into product_images table
                    cursor.execute("""
                        INSERT OR REPLACE INTO product_images (
                            product_id, original_url, local_path, is_primary, display_order
                        ) VALUES (?, ?, ?, ?, ?)
                    """, (product_id, image_url, local_path, i == 0, i))
                    conn.commit()
                    self.stats['images_downloaded'] += 1
    
    def generate_pretty_title(self, title: str, brand: str = None) -> str:
        """Generate a pretty, short title for product cards"""
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
        elif 'Comforter' in title:
            components.append('Comforter')
        elif 'Pillow' in title:
            components.append('Pillow')
        elif 'Duvet' in title:
            components.append('Duvet')
        
        # Join components
        if components:
            pretty_title = ' '.join(components)
        else:
            # Fallback: truncate original title
            pretty_title = title[:50] + '...' if len(title) > 50 else title
        
        return pretty_title
    
    def run_complete_pipeline(self, affiliate_csv_path: str = "products/product_affilate_links.csv") -> Dict[str, Any]:
        """Run the complete A-Z pipeline"""
        print("🚀 Starting Complete Product Pipeline A-Z")
        print("=" * 60)
        
        # Step 1: Process affiliate links
        print("\n📋 Step 1: Processing Affiliate Links")
        affiliate_results = self.process_affiliate_links_file(affiliate_csv_path)
        print(f"✅ Processed {affiliate_results['processed']} affiliate links")
        
        # Step 2: Extract product details from URLs
        print("\n🔍 Step 2: Extracting Product Details from URLs")
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
            
            for product_id, amazon_id, referral_link in tqdm(products_to_process, desc="Extracting details"):
                try:
                    # Extract details from URL
                    details = self.extract_product_details(referral_link)
                    
                    if details:
                        # Update product with details
                        self.update_product_with_details(conn, product_id, details)
                        
                        # Generate pretty title
                        pretty_title = self.generate_pretty_title(
                            details.get('title', ''), 
                            details.get('brand', '')
                        )
                        
                        cursor.execute(
                            "UPDATE products SET pretty_title = ? WHERE id = ?",
                            (pretty_title, product_id)
                        )
                        conn.commit()
                        self.stats['pretty_titles_generated'] += 1
                        self.stats['products_updated'] += 1
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    self.stats['errors'] += 1
                    continue
        
        finally:
            conn.close()
        
        # Step 3: Generate enhanced pros and cons
        print("\n✨ Step 3: Generating Enhanced Pros and Cons")
        try:
            pros_cons_results = self.dynamic_pros_cons.regenerate_all_product_features()
            self.stats['pros_cons_generated'] = pros_cons_results.get('successful', 0)
            print(f"✅ Generated enhanced pros/cons for {self.stats['pros_cons_generated']} products")
        except Exception as e:
            print(f"❌ Error generating pros/cons: {e}")
        
        # Step 4: Generate product summaries
        print("\n📝 Step 4: Generating Product Summaries")
        try:
            summary_results = self.summary_generator.generate_all_summaries()
            self.stats['summaries_generated'] = summary_results.get('successful', 0)
            print(f"✅ Generated summaries for {self.stats['summaries_generated']} products")
        except Exception as e:
            print(f"❌ Error generating summaries: {e}")
        
        # Step 5: Calculate scores
        print("\n📊 Step 5: Calculating Product Scores")
        try:
            from core.configurable_scoring_system import ConfigurableScoringSystem
            scoring_system = ConfigurableScoringSystem(self.db_path)
            scoring_results = scoring_system.update_all_product_scores(self.db_path)
            print(f"✅ Calculated scores for products")
        except Exception as e:
            print(f"❌ Error calculating scores: {e}")
        
        # Final statistics
        print("\n🎉 Pipeline Complete!")
        print("=" * 60)
        print("📊 Final Statistics:")
        for key, value in self.stats.items():
            print(f"   {key.replace('_', ' ').title()}: {value}")
        
        return self.stats

def main():
    """Main function to run the complete pipeline"""
    pipeline = CompleteProductPipeline()
    
    # Run the complete pipeline
    results = pipeline.run_complete_pipeline()
    
    print(f"\n✅ Complete pipeline finished!")
    print(f"📈 Total products processed: {results['products_updated']}")
    print(f"🖼️  Images downloaded: {results['images_downloaded']}")
    print(f"📝 Summaries generated: {results['summaries_generated']}")
    print(f"✨ Pros/cons generated: {results['pros_cons_generated']}")

if __name__ == "__main__":
    main()
