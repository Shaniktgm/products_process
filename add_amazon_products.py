#!/usr/bin/env python3
"""
Add 100 Amazon products to the database using the Product Advertising API
Searches for bedding products and adds them with full data collection
"""

import sqlite3
import time
import random
from datetime import datetime
from typing import List, Dict, Any
import sys
import os

# Add the pipeline directory to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from pipeline.phase2_amazon_api.phase2_amazon_api import AmazonAPIDataCollectionPipeline

class AmazonProductAdder:
    """Add Amazon products by searching the API"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.api_pipeline = AmazonAPIDataCollectionPipeline(db_path)
        
        # Search terms for bedding products
        self.search_terms = [
            "bed sheets",
            "cotton sheets",
            "bamboo sheets",
            "linen sheets",
            "silk sheets",
            "microfiber sheets",
            "thread count sheets",
            "luxury bed sheets",
            "cooling sheets",
            "organic sheets",
            "Egyptian cotton sheets",
            "Supima cotton sheets",
            "sateen sheets",
            "percale sheets",
            "jersey sheets",
            "flannel sheets",
            "bedding sets",
            "sheet sets",
            "duvet covers",
            "pillowcases",
            "bedding accessories",
            "mattress protectors",
            "bed skirts",
            "comforters",
            "quilts",
            "blankets",
            "throws",
            "bed pillows",
            "memory foam pillows",
            "down pillows"
        ]
        
        # Track added products
        self.added_products = []
        self.stats = {
            'searched_terms': 0,
            'products_found': 0,
            'products_added': 0,
            'errors': 0
        }
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _extract_asin_from_url(self, url: str) -> str:
        """Extract ASIN from Amazon URL"""
        import re
        # Try different URL patterns
        patterns = [
            r'/dp/([A-Z0-9]{10})',
            r'/product/([A-Z0-9]{10})',
            r'asin=([A-Z0-9]{10})',
            r'/([A-Z0-9]{10})/'
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url)
            if match:
                return match.group(1)
        return None
    
    def _search_amazon_products(self, search_term: str, max_results: int = 10) -> List[Dict[str, Any]]:
        """Search Amazon for products using the API"""
        try:
            print(f"🔍 Searching for: '{search_term}'")
            
            # Create a custom search with more results
            payload = {
                'Keywords': search_term,
                'SearchIndex': 'All',
                'ItemCount': min(max_results, 10),  # Amazon API max is 10
                'Resources': [
                    'Images.Primary.Large',
                    'ItemInfo.Title',
                    'ItemInfo.ByLineInfo',
                    'Offers.Listings.Price'
                ]
            }
            
            search_results = self.api_pipeline.api._make_request('SearchItems', payload)
            
            if not search_results or 'SearchResult' not in search_results:
                print(f"   ⚠️ No results for '{search_term}'")
                return []
            
            products = []
            for item in search_results['SearchResult'].get('Items', []):
                try:
                    asin = item.get('ASIN')
                    if not asin:
                        continue
                    
                    # Extract basic product info
                    item_info = item.get('ItemInfo', {})
                    title = item_info.get('Title', {}).get('DisplayValue', '')
                    
                    # Get price info
                    offers = item.get('Offers', {})
                    listings = offers.get('Listings', [])
                    price = None
                    if listings:
                        price_info = listings[0].get('Price', {})
                        if price_info:
                            amount = price_info.get('Amount', 0)
                            if amount:
                                price = float(amount)
                    
                    # Get brand info
                    byline = item_info.get('ByLineInfo', {})
                    brand = byline.get('Brand', {}).get('DisplayValue', '')
                    
                    # Get image
                    images = item.get('Images', {})
                    primary_image = images.get('Primary', {})
                    large_image = primary_image.get('Large', {})
                    image_url = large_image.get('URL', '') if large_image else ''
                    
                    product_data = {
                        'asin': asin,
                        'title': title,
                        'brand': brand,
                        'price': price,
                        'image_url': image_url,
                        'search_term': search_term
                    }
                    
                    products.append(product_data)
                    
                except Exception as e:
                    print(f"   ⚠️ Error processing search result: {e}")
                    continue
            
            print(f"   ✅ Found {len(products)} products")
            return products
            
        except Exception as e:
            print(f"   ❌ Error searching for '{search_term}': {e}")
            return []
    
    def _add_product_to_database(self, product_data: Dict[str, Any]) -> bool:
        """Add a product to the database"""
        conn = self._get_db_connection()
        cursor = conn.cursor()
        
        try:
            asin = product_data['asin']
            title = product_data['title']
            brand = product_data['brand']
            price = product_data['price']
            image_url = product_data['image_url']
            search_term = product_data['search_term']
            
            # Check if product already exists
            cursor.execute("SELECT id FROM products WHERE amazon_asin = ?", (asin,))
            existing = cursor.fetchone()
            
            if existing:
                print(f"   ⏭️ Product {asin} already exists, skipping")
                return False
            
            # Generate SKU and title
            sku = f"AMZ-{asin}"
            product_title = title if title else f"Amazon Product {asin}"
            
            # Create product
            cursor.execute("""
                INSERT INTO products (sku, title, amazon_asin, amazon_product_id, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?)
            """, (sku, product_title, asin, asin, datetime.now(), datetime.now()))
            
            product_id = cursor.lastrowid
            
            # Add to tracking
            self.added_products.append({
                'id': product_id,
                'asin': asin,
                'title': product_title,
                'brand': brand,
                'search_term': search_term
            })
            
            # If we have an image URL, add it to product_images
            if image_url:
                cursor.execute("""
                    INSERT INTO product_images (product_id, original_url, is_primary, is_amazon_image, created_at, updated_at)
                    VALUES (?, ?, ?, ?, ?, ?)
                """, (product_id, image_url, True, True, datetime.now(), datetime.now()))
            
            conn.commit()
            print(f"   ✅ Added product {product_id}: {product_title[:50]}...")
            return True
            
        except Exception as e:
            print(f"   ❌ Error adding product {product_data.get('asin', 'unknown')}: {e}")
            conn.rollback()
            return False
        finally:
            conn.close()
    
    def add_products_from_search(self, target_count: int = 100) -> Dict[str, Any]:
        """Add products by searching Amazon"""
        print(f"🚀 Starting to add {target_count} Amazon products")
        print("=" * 60)
        
        # Shuffle search terms for variety
        search_terms = self.search_terms.copy()
        random.shuffle(search_terms)
        
        products_per_search = max(1, target_count // len(search_terms))
        
        for search_term in search_terms:
            if self.stats['products_added'] >= target_count:
                break
            
            remaining = target_count - self.stats['products_added']
            search_count = min(products_per_search, remaining, 10)  # Max 10 per search
            
            print(f"\n📋 Search term: '{search_term}' (need {remaining} more products)")
            
            # Search for products
            products = self._search_amazon_products(search_term, search_count)
            self.stats['searched_terms'] += 1
            self.stats['products_found'] += len(products)
            
            # Add products to database
            for product in products:
                if self.stats['products_added'] >= target_count:
                    break
                
                if self._add_product_to_database(product):
                    self.stats['products_added'] += 1
                
                # Rate limiting
                time.sleep(0.5)
            
            # Rate limiting between searches
            time.sleep(1)
        
        return self.stats
    
    def populate_amazon_data_for_new_products(self) -> Dict[str, Any]:
        """Populate Amazon API data for all newly added products"""
        print(f"\n🔄 Populating Amazon API data for {len(self.added_products)} new products...")
        
        # Get product IDs
        product_ids = [p['id'] for p in self.added_products]
        
        # Use the existing API pipeline to populate data
        api_stats = {
            'products_processed': 0,
            'products_updated': 0,
            'variations_added': 0,
            'categories_added': 0,
            'brands_updated': 0,
            'features_added': 0,
            'images_added': 0,
            'errors': 0
        }
        
        for product in self.added_products:
            try:
                product_id = product['id']
                asin = product['asin']
                
                print(f"  📦 Processing product {product_id} (ASIN: {asin})")
                
                # Use the API pipeline to populate comprehensive data
                success = self.api_pipeline._populate_product_data(product_id, asin)
                
                if success:
                    api_stats['products_updated'] += 1
                    print(f"    ✅ Successfully populated data for product {product_id}")
                else:
                    api_stats['errors'] += 1
                    print(f"    ❌ Failed to populate data for product {product_id}")
                
                api_stats['products_processed'] += 1
                
                # Rate limiting
                time.sleep(2)
                
            except Exception as e:
                print(f"    ❌ Error processing product {product.get('id', 'unknown')}: {e}")
                api_stats['errors'] += 1
        
        return api_stats
    
    def run_full_addition(self, target_count: int = 100) -> Dict[str, Any]:
        """Run the complete process to add products"""
        print("🚀 Adding Amazon Products to Database")
        print("=" * 60)
        
        # Step 1: Add products from search
        search_stats = self.add_products_from_search(target_count)
        
        # Step 2: Populate Amazon API data
        if self.added_products:
            api_stats = self.populate_amazon_data_for_new_products()
        else:
            api_stats = {}
        
        # Final statistics
        final_stats = {
            'search_stats': search_stats,
            'api_stats': api_stats,
            'total_products_added': len(self.added_products),
            'added_products': self.added_products
        }
        
        print(f"\n🎉 Product Addition Complete!")
        print(f"   📊 Products added: {len(self.added_products)}")
        print(f"   🔍 Search terms used: {search_stats['searched_terms']}")
        print(f"   📦 Products found: {search_stats['products_found']}")
        print(f"   ❌ Errors: {search_stats['errors']}")
        
        if api_stats:
            print(f"   🎯 API data populated: {api_stats['products_updated']}")
            print(f"   🎨 Variations added: {api_stats.get('variations_added', 0)}")
            print(f"   🏷️ Categories added: {api_stats.get('categories_added', 0)}")
        
        return final_stats

def main():
    """Main function to add Amazon products"""
    adder = AmazonProductAdder()
    
    # Add 100 products
    results = adder.run_full_addition(100)
    
    print(f"\n🎊 Successfully added {results['total_products_added']} Amazon products!")
    
    # Show some examples
    if results['added_products']:
        print(f"\n📋 Sample added products:")
        for i, product in enumerate(results['added_products'][:5]):
            print(f"   {i+1}. {product['title'][:60]}... (ASIN: {product['asin']})")

if __name__ == "__main__":
    main()
