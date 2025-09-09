#!/usr/bin/env python3
"""
Product extraction script for Amazon affiliate URLs
Extracts product information and saves images locally
"""

import csv
import json
import os
import re
import time
import requests
from urllib.parse import urlparse, parse_qs
from bs4 import BeautifulSoup
import sqlite3
from datetime import datetime
import uuid

class ProductExtractor:
    def __init__(self, csv_file="hp_products_new_products_to_add_all.csv", images_dir="product_images"):
        self.csv_file = csv_file
        self.images_dir = images_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Cache-Control': 'max-age=0',
        })
        
        # Create images directory
        os.makedirs(self.images_dir, exist_ok=True)
        
        # Platform mapping
        self.platform_mapping = {
            'levanta': 'amazon',
            'amazon_associates': 'amazon',
            '': 'amazon'  # Default to amazon if platform is empty
        }
    
    def extract_asin_from_url(self, url):
        """Extract ASIN from Amazon URL"""
        try:
            # Try to extract from /dp/ pattern
            match = re.search(r'/dp/([A-Z0-9]{10})', url)
            if match:
                return match.group(1)
            
            # Try to extract from query parameters
            parsed = urlparse(url)
            query_params = parse_qs(parsed.query)
            if 'asin' in query_params:
                return query_params['asin'][0]
            
            return None
        except Exception as e:
            print(f"Error extracting ASIN from {url}: {e}")
            return None
    
    def clean_text(self, element):
        """Clean and normalize text from BeautifulSoup element"""
        if not element:
            return ""
        if hasattr(element, 'get_text'):
            text = element.get_text()
        else:
            text = str(element)
        return re.sub(r'\s+', ' ', text.strip())
    
    def extract_price(self, soup):
        """Extract price from Amazon page"""
        try:
            # Try different price selectors
            price_selectors = [
                '.a-price-whole',
                '.a-price .a-offscreen',
                '#priceblock_dealprice',
                '#priceblock_ourprice',
                '.a-price-range',
                '[data-a-price-amount]'
            ]
            
            for selector in price_selectors:
                price_elem = soup.select_one(selector)
                if price_elem:
                    price_text = price_elem.get_text(strip=True)
                    # Extract numeric price
                    price_match = re.search(r'[\d,]+\.?\d*', price_text.replace(',', ''))
                    if price_match:
                        return float(price_match.group())
            
            return None
        except Exception as e:
            print(f"Error extracting price: {e}")
            return None
    
    def extract_rating(self, soup):
        """Extract rating from Amazon page"""
        try:
            rating_selectors = [
                '.a-icon-alt',
                '[data-hook="rating-out-of-text"]',
                '.a-star-mini .a-icon-alt'
            ]
            
            for selector in rating_selectors:
                rating_elem = soup.select_one(selector)
                if rating_elem:
                    rating_text = rating_elem.get_text(strip=True)
                    rating_match = re.search(r'(\d+\.?\d*)\s*out of 5', rating_text)
                    if rating_match:
                        return float(rating_match.group(1))
            
            return None
        except Exception as e:
            print(f"Error extracting rating: {e}")
            return None
    
    def extract_review_count(self, soup):
        """Extract review count from Amazon page"""
        try:
            review_selectors = [
                '[data-hook="total-review-count"]',
                '#acrCustomerReviewText',
                '.a-size-base'
            ]
            
            for selector in review_selectors:
                review_elem = soup.select_one(selector)
                if review_elem:
                    review_text = review_elem.get_text(strip=True)
                    review_match = re.search(r'([\d,]+)', review_text.replace(',', ''))
                    if review_match:
                        return int(review_match.group(1))
            
            return None
        except Exception as e:
            print(f"Error extracting review count: {e}")
            return None
    
    def extract_images(self, soup, asin):
        """Extract and download product images"""
        try:
            images = []
            
            # Try different image selectors
            img_selectors = [
                '#landingImage',
                '.a-dynamic-image',
                '[data-old-hires]',
                '.a-button-selected img'
            ]
            
            for selector in img_selectors:
                img_elements = soup.select(selector)
                for img in img_elements:
                    img_url = img.get('src') or img.get('data-src') or img.get('data-old-hires')
                    if img_url and 'http' in img_url:
                        # Download and save image
                        local_path = self.download_image(img_url, asin, len(images))
                        if local_path:
                            images.append(local_path)
            
            return images[:5]  # Limit to 5 images
        except Exception as e:
            print(f"Error extracting images: {e}")
            return []
    
    def download_image(self, img_url, asin, index):
        """Download and save image locally"""
        try:
            # Clean URL
            if img_url.startswith('//'):
                img_url = 'https:' + img_url
            
            # Get file extension
            parsed_url = urlparse(img_url)
            ext = os.path.splitext(parsed_url.path)[1] or '.jpg'
            
            # Create filename
            filename = f"{asin}_{index}{ext}"
            filepath = os.path.join(self.images_dir, filename)
            
            # Skip if already exists
            if os.path.exists(filepath):
                return filepath
            
            # Download image
            response = self.session.get(img_url, timeout=10)
            response.raise_for_status()
            
            # Save image
            with open(filepath, 'wb') as f:
                f.write(response.content)
            
            print(f"Downloaded image: {filename}")
            return filepath
            
        except Exception as e:
            print(f"Error downloading image {img_url}: {e}")
            return None
    
    def extract_product_data(self, url, platform, commission_rate):
        """Extract all product data from Amazon URL"""
        try:
            print(f"Extracting data from: {url}")
            
            # Extract ASIN
            asin = self.extract_asin_from_url(url)
            if not asin:
                print(f"Could not extract ASIN from URL: {url}")
                return None
            
            # Get clean Amazon URL
            clean_url = f"https://www.amazon.com/dp/{asin}"
            
            # Fetch page
            response = self.session.get(clean_url, timeout=15)
            response.raise_for_status()
            
            # Check if we got a valid response
            if "Robot Check" in response.text or "captcha" in response.text.lower():
                print(f"Bot detection triggered for {asin}")
                return None
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Debug: Check if we got the product page
            if not soup.select_one('#productTitle') and not soup.select_one('h1'):
                print(f"No product title found for {asin} - might be blocked or invalid")
                return None
            
            # Extract basic info
            title_elem = soup.select_one('#productTitle')
            title = title_elem.get_text().strip() if title_elem else ""
            if not title:
                h1_elem = soup.select_one('h1')
                title = h1_elem.get_text().strip() if h1_elem else ""
            
            brand_elem = soup.select_one('#bylineInfo')
            brand = brand_elem.get_text().strip() if brand_elem else ""
            if not brand:
                brand_elem = soup.select_one('.a-link-normal')
                brand = brand_elem.get_text().strip() if brand_elem else ""
            
            price = self.extract_price(soup)
            rating = self.extract_rating(soup)
            review_count = self.extract_review_count(soup)
            
            # Extract images
            images = self.extract_images(soup, asin)
            
            # Extract description
            description = ""
            desc_selectors = [
                '#feature-bullets ul',
                '#productDescription',
                '.a-unordered-list'
            ]
            
            for selector in desc_selectors:
                desc_elem = soup.select_one(selector)
                if desc_elem:
                    description = desc_elem.get_text().strip()
                    break
            
            # Create product data
            product_data = {
                "main_product_data": {
                    "sku": f"AMZ-{asin}",
                    "title": title or f"Product {asin}",
                    "brand": brand or "Unknown Brand",
                    "description": description or f"Product description for {title or asin}",
                    "short_description": title or f"Product {asin}",
                    "slug": f"product-{asin.lower()}",
                    "price": price or 0.0,
                    "original_price": price or 0.0,
                    "discount_percentage": 0,
                    "currency": "USD",
                    "rating": rating or 0.0,
                    "review_count": review_count or 0,
                    "primary_image_url": images[0] if images else "",
                    "image_urls": json.dumps(images),
                    "video_urls": "[]",
                    "availability": "In Stock",
                    "stock_status": "Available",
                    "stock_quantity": 100,
                    "condition": "New",
                    "warranty": "Manufacturer warranty",
                    "return_policy": "30-day return policy",
                    "shipping_info": "Free shipping on orders over $25",
                    "age_recommendation": "All ages",
                    "ingredients": "",
                    "weight": 0.0,
                    "dimensions": "{}",
                    "color": "",
                    "material": "",
                    "size": "",
                    "meta_title": f"{title or asin} - Amazon",
                    "meta_description": f"Shop {title or asin} on Amazon",
                    "tags": json.dumps(["amazon", "product"]),
                    "deal_badges": "[]",
                    "is_active": True,
                    "is_featured": False,
                    "is_bestseller": False,
                    "overall_value_score": 0.0
                },
                "platform_data": {
                    "platforms": [{
                        "platform_name": self.platform_mapping.get(platform, "amazon"),
                        "platform_sku": asin,
                        "platform_url": clean_url,
                        "platform_price": price or 0.0,
                        "platform_availability": "In Stock",
                        "platform_rating": rating or 0.0,
                        "platform_review_count": review_count or 0,
                        "platform_specific_data": json.dumps({"ASIN": asin}),
                        "is_primary": True
                    }]
                },
                "affiliate_links": {
                    "links": [{
                        "platform_name": self.platform_mapping.get(platform, "amazon"),
                        "link_type": "web",
                        "affiliate_url": url,
                        "commission_rate": float(commission_rate.replace('%', '')) / 100 if commission_rate else 0.04,
                        "estimated_commission": (price or 0.0) * (float(commission_rate.replace('%', '')) / 100 if commission_rate else 0.04),
                        "is_active": True
                    }]
                },
                "product_features": {
                    "features": []
                },
                "product_specifications": {
                    "specifications": []
                },
                "product_categories": {
                    "categories": [{
                        "category_name": "Amazon Products",
                        "category_path": "Amazon > Products",
                        "is_primary": True,
                        "display_order": 1
                    }]
                }
            }
            
            print(f"Successfully extracted: {title or asin}")
            return product_data
            
        except Exception as e:
            print(f"Error extracting product data from {url}: {e}")
            return None
    
    def process_csv(self):
        """Process all URLs in the CSV file"""
        products = []
        
        try:
            with open(self.csv_file, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                
                for i, row in enumerate(reader):
                    url = row.get('referral link', '').strip()
                    platform = row.get('platform', '').strip()
                    commission_rate = row.get('commision rate', '').strip()
                    
                    if not url:
                        continue
                    
                    print(f"\nProcessing {i+1}/21: {url}")
                    
                    # Extract product data
                    product_data = self.extract_product_data(url, platform, commission_rate)
                    if product_data:
                        products.append(product_data)
                    
                    # Rate limiting - be respectful
                    time.sleep(2)
                    
        except Exception as e:
            print(f"Error processing CSV: {e}")
        
        return products
    
    def save_products_json(self, products, filename="extracted_products.json"):
        """Save extracted products to JSON file"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(products, f, indent=2, ensure_ascii=False)
            print(f"\nSaved {len(products)} products to {filename}")
        except Exception as e:
            print(f"Error saving products: {e}")
    
    def save_products_database(self, products, db_path="multi_platform_products.db"):
        """Save extracted products to database"""
        try:
            with sqlite3.connect(db_path) as conn:
                cursor = conn.cursor()
                
                for product in products:
                    main_data = product["main_product_data"]
                    
                    # Insert main product
                    cursor.execute("""
                        INSERT INTO products (
                            sku, title, brand, description, short_description, slug,
                            price, original_price, discount_percentage, currency,
                            rating, review_count, primary_image_url, image_urls,
                            video_urls, availability, stock_status, stock_quantity,
                            condition, warranty, return_policy, shipping_info,
                            age_recommendation, ingredients, weight, dimensions,
                            color, material, size, meta_title, meta_description,
                            tags, deal_badges, is_active, is_featured, is_bestseller,
                            overall_value_score, created_at, updated_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        main_data["sku"], main_data["title"], main_data["brand"],
                        main_data["description"], main_data["short_description"], main_data["slug"],
                        main_data["price"], main_data["original_price"], main_data["discount_percentage"],
                        main_data["currency"], main_data["rating"], main_data["review_count"],
                        main_data["primary_image_url"], main_data["image_urls"], main_data["video_urls"],
                        main_data["availability"], main_data["stock_status"], main_data["stock_quantity"],
                        main_data["condition"], main_data["warranty"], main_data["return_policy"],
                        main_data["shipping_info"], main_data["age_recommendation"], main_data["ingredients"],
                        main_data["weight"], main_data["dimensions"], main_data["color"], main_data["material"],
                        main_data["size"], main_data["meta_title"], main_data["meta_description"],
                        main_data["tags"], main_data["deal_badges"], main_data["is_active"],
                        main_data["is_featured"], main_data["is_bestseller"], main_data["overall_value_score"],
                        datetime.now(), datetime.now()
                    ))
                    
                    product_id = cursor.lastrowid
                    
                    # Insert platform data
                    for platform in product["platform_data"]["platforms"]:
                        cursor.execute("""
                            INSERT INTO product_platforms (
                                product_id, platform_id, platform_sku, platform_url,
                                platform_price, platform_availability, platform_rating,
                                platform_review_count, platform_specific_data, is_primary
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            product_id, 1, platform["platform_sku"], platform["platform_url"],
                            platform["platform_price"], platform["platform_availability"],
                            platform["platform_rating"], platform["platform_review_count"],
                            platform["platform_specific_data"], platform["is_primary"]
                        ))
                    
                    # Insert affiliate links
                    for link in product["affiliate_links"]["links"]:
                        cursor.execute("""
                            INSERT INTO affiliate_links (
                                product_id, platform_id, link_type, affiliate_url,
                                commission_rate, estimated_commission, is_active
                            ) VALUES (?, ?, ?, ?, ?, ?, ?)
                        """, (
                            product_id, 1, link["link_type"], link["affiliate_url"],
                            link["commission_rate"], link["estimated_commission"], link["is_active"]
                        ))
                    
                    # Insert categories
                    for category in product["product_categories"]["categories"]:
                        cursor.execute("""
                            INSERT INTO product_categories (
                                product_id, category_name, category_path, is_primary, display_order
                            ) VALUES (?, ?, ?, ?, ?)
                        """, (
                            product_id, category["category_name"], category["category_path"],
                            category["is_primary"], category["display_order"]
                        ))
                
                conn.commit()
                print(f"\nSaved {len(products)} products to database")
                
        except Exception as e:
            print(f"Error saving to database: {e}")

def main():
    """Main function"""
    print("🚀 Starting product extraction from Amazon URLs...")
    
    extractor = ProductExtractor()
    
    # Process CSV file
    products = extractor.process_csv()
    
    if products:
        # Save to JSON
        extractor.save_products_json(products)
        
        # Save to database
        extractor.save_products_database(products)
        
        print(f"\n✅ Successfully extracted {len(products)} products!")
        print(f"📁 Images saved to: {extractor.images_dir}/")
        print("📄 Product data saved to: extracted_products.json")
        print("🗄️  Products added to database")
    else:
        print("❌ No products were extracted")

if __name__ == "__main__":
    main()
