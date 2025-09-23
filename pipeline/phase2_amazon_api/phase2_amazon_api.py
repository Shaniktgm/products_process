#!/usr/bin/env python3
"""
Phase 2: Amazon API Data Collection Pipeline
Collects comprehensive product data using Amazon Product Advertising API
"""

import sqlite3
import json
import time
import os
from datetime import datetime
from typing import Dict, Any, List, Optional
from tqdm import tqdm

# Import Amazon API Explorer
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from amazon_api_explorer import AmazonAPIExplorer

class AmazonAPIDataCollectionPipeline:
    """Phase 2: Collect comprehensive product data using Amazon API"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Initialize Amazon API (credentials from secure config)
        sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
        from amazon_api_config import get_amazon_api_config
        
        api_config = get_amazon_api_config()
        self.api = AmazonAPIExplorer(
            access_key=api_config['access_key'],
            secret_key=api_config['secret_key'],
            associate_tag=api_config['associate_tag']
        )
        
        # Rate limiting - 2 seconds between API calls
        self.api_delay = 2.0
        self.last_api_call = 0
        
        # Statistics tracking
        self.stats = {
            'products_processed': 0,
            'products_updated': 0,
            'variations_added': 0,
            'categories_added': 0,
            'brands_updated': 0,
            'features_added': 0,
            'images_added': 0,
            'errors': 0,
            'skipped': 0
        }
    
    def _get_db_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def _rate_limit_api(self):
        """Ensure we wait 2 seconds between API calls"""
        current_time = time.time()
        time_since_last = current_time - self.last_api_call
        
        if time_since_last < self.api_delay:
            sleep_time = self.api_delay - time_since_last
            print(f"⏳ API rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_api_call = time.time()
    
    def _populate_product_data(self, product_id: int, asin: str) -> bool:
        """Populate product with comprehensive Amazon API data"""
        try:
            print(f"  📦 Processing product {product_id} (ASIN: {asin})")
            
            # Get comprehensive product data from Amazon API (tested working set)
            payload = {
                'ItemIds': [asin],
            'Resources': [
                'Images.Primary.Large',
                'ItemInfo.Title',
                'ItemInfo.ByLineInfo',
                'ItemInfo.ProductInfo',
                'ItemInfo.Features',
                'ItemInfo.Classifications',
                'ItemInfo.ExternalIds',
                'Offers.Listings.Price',
                'Offers.Listings.SavingBasis',
                'BrowseNodeInfo.BrowseNodes'
            ]
            }
            
            self._rate_limit_api()
            result = self.api._make_request('GetItems', payload)
            
            if not result or 'ItemsResult' not in result:
                print(f"    ❌ No data from Amazon API for {asin}")
                return False
            
            items = result['ItemsResult'].get('Items', [])
            if not items:
                print(f"    ❌ No items found in API response for {asin}")
                return False
            
            item = items[0]
            conn = self._get_db_connection()
            
            try:
                # Update main product data
                self._update_product_main_data(conn, product_id, item, asin)
                
                # Populate variations
                self._populate_variations(conn, product_id, asin)
                
                # Populate categories
                self._populate_categories(conn, product_id, item)
                
                # Update brands
                self._update_brands_table(conn, product_id, item)
                
                # Populate features
                self._populate_features(conn, product_id, item)
                
                # Populate images
                self._populate_images(conn, product_id, item)
                
                # Populate reviews (limited data available)
                self._populate_reviews(conn, product_id, item)
                
                conn.commit()
                self.stats['products_updated'] += 1
                print(f"    ✅ Successfully updated product {product_id}")
                return True
                
            except Exception as e:
                print(f"    ❌ Error updating product {product_id}: {e}")
                conn.rollback()
                self.stats['errors'] += 1
                return False
            finally:
                conn.close()
                
        except Exception as e:
            print(f"    ❌ Error processing product {product_id}: {e}")
            self.stats['errors'] += 1
            return False
    
    def _update_product_main_data(self, conn: sqlite3.Connection, product_id: int, item: Dict[str, Any], asin: str):
        """Update main product table with Amazon API data"""
        cursor = conn.cursor()
        
        try:
            # Extract data from API response
            item_info = item.get('ItemInfo', {})
            offers = item.get('Offers', {})
            listings = offers.get('Listings', [{}])[0] if offers.get('Listings') else {}
            
            # Title
            title = item_info.get('Title', {}).get('DisplayValue', '')
            
            # Brand and manufacturer
            byline = item_info.get('ByLineInfo', {})
            brand = byline.get('Brand', {}).get('DisplayValue', '')
            manufacturer = byline.get('Manufacturer', {}).get('DisplayValue', '')
            
            # Price and Discount
            price = None
            discount_percentage = None
            if listings.get('Price'):
                amount = listings['Price'].get('Amount', 0)
                if amount:
                    price = float(amount)
                    
                    # Calculate discount if saving basis is available
                    saving_basis = listings.get('SavingBasis', {})
                    if saving_basis and saving_basis.get('Amount'):
                        original_price = float(saving_basis['Amount'])
                        if original_price > price:
                            discount_amount = original_price - price
                            discount_percentage = int((discount_amount / original_price) * 100)
            
            # Availability (not available in API response, set default)
            availability = 'in_stock'  # Default since we can't get this from API
            
            # Condition
            condition = listings.get('Condition', {}).get('DisplayValue', '')
            
            # Merchant
            merchant = listings.get('MerchantInfo', {}).get('Name', '')
            
            # External IDs - use the ASIN from the API request since ExternalIds resource doesn't work
            external_ids = item_info.get('ExternalIds', {})
            # The ASIN is already available from the method parameter
            
            # Product info
            product_info = item_info.get('ProductInfo', {})
            color = product_info.get('Color', {}).get('DisplayValue', '')
            size = product_info.get('Size', {}).get('DisplayValue', '')
            material = product_info.get('Material', {}).get('DisplayValue', '')
            thread_count = product_info.get('ThreadCount', {}).get('DisplayValue', '')
            weave_type = product_info.get('WeaveType', {}).get('DisplayValue', '')
            
            # Item dimensions from ProductInfo
            item_dimensions = product_info.get('ItemDimensions', {})
            dimensions = ''
            weight = ''
            if item_dimensions:
                # Build dimensions string
                dim_parts = []
                if item_dimensions.get('Length'):
                    dim_parts.append(f"L: {item_dimensions['Length'].get('DisplayValue', '')} {item_dimensions['Length'].get('Unit', '')}")
                if item_dimensions.get('Width'):
                    dim_parts.append(f"W: {item_dimensions['Width'].get('DisplayValue', '')} {item_dimensions['Width'].get('Unit', '')}")
                if item_dimensions.get('Height'):
                    dim_parts.append(f"H: {item_dimensions['Height'].get('DisplayValue', '')} {item_dimensions['Height'].get('Unit', '')}")
                dimensions = ', '.join(dim_parts)
                
                # Get weight
                if item_dimensions.get('Weight'):
                    weight = f"{item_dimensions['Weight'].get('DisplayValue', '')} {item_dimensions['Weight'].get('Unit', '')}"
            
            # Certifications
            certifications = []
            if item_info.get('Classifications'):
                classifications = item_info.get('Classifications', {})
                for key, value in classifications.items():
                    if 'certified' in value.get('DisplayValue', '').lower():
                        certifications.append(value.get('DisplayValue', ''))
            
            # Features
            features = item_info.get('Features', {}).get('DisplayValues', [])
            features_text = '; '.join(features) if features else ''
            
            # Extract material, thread_count, weave_type from features
            import re
            thread_count = None
            thread_count_match = re.search(r'(\d{3,4})\s*thread\s*count', features_text.lower())
            if thread_count_match:
                thread_count = int(thread_count_match.group(1))
            
            # Extract weave type from features
            weave_type = None
            if 'sateen' in features_text.lower():
                weave_type = 'sateen'
            elif 'percale' in features_text.lower():
                weave_type = 'percale'
            elif 'flannel' in features_text.lower():
                weave_type = 'flannel'
            
            # Update products table with Amazon data
            cursor.execute("""
                UPDATE products SET
                    amazon_asin = ?, amazon_title = ?, amazon_brand = ?, amazon_manufacturer = ?,
                    amazon_color_code = ?, amazon_size_code = ?,
                    amazon_availability_status = ?, price = ?, discount_percentage = ?, amazon_last_updated = ?,
                    material = ?, thread_count = ?, weave_type = ?
                WHERE id = ?
            """, (
                asin, title, brand, manufacturer, color, size,
                availability, price, discount_percentage, datetime.now(),
                material, thread_count, weave_type, product_id
            ))
            
            print(f"    ✅ Updated main product data")
            
            # Update affiliation_details with Amazon API data if available
            if price is not None or discount_percentage is not None:
                cursor.execute("""
                    UPDATE affiliation_details 
                    SET discount = ?, updated_at = ?
                    WHERE product_id = ? AND platform_id = 8
                """, (discount_percentage, datetime.now(), product_id))
                
                if cursor.rowcount > 0:
                    print(f"    ✅ Updated affiliation_details with Amazon API data")
            
        except Exception as e:
            print(f"    ❌ Error updating main product data: {e}")
            raise
    
    def _populate_variations(self, conn: sqlite3.Connection, product_id: int, asin: str):
        """Populate product variations using GetVariations API"""
        cursor = conn.cursor()
        
        try:
            # Get variations data (minimal working set)
            payload = {
                'ASIN': asin,
                'VariationPage': 1,
                'Resources': [
                    'Images.Primary.Large',
                    'Offers.Listings.Price'
                ]
            }
            
            self._rate_limit_api()
            result = self.api._make_request('GetVariations', payload)
            
            if not result or 'VariationsResult' not in result:
                print(f"    ⚠️ No variations data available")
                return
            
            variations = result['VariationsResult'].get('Items', [])
            if not variations:
                print(f"    ⚠️ No variations found")
                return
            
            for variation in variations:
                variation_asin = variation.get('ASIN', '')
                if not variation_asin:
                    continue
                
                # Extract variation attributes
                variation_attrs = variation.get('VariationAttributes', [])
                color_name = None
                size_name = None
                
                for attr in variation_attrs:
                    attr_name = attr.get('Name', '').lower()
                    attr_value = attr.get('Value', '')
                    
                    if 'color' in attr_name:
                        color_name = attr_value
                    elif 'size' in attr_name:
                        size_name = attr_value
                
                # Determine variation type and value
                if color_name and size_name:
                    variation_type = 'color_size'
                    variation_value = f"{color_name}_{size_name}"
                elif color_name:
                    variation_type = 'color'
                    variation_value = color_name
                elif size_name:
                    variation_type = 'size'
                    variation_value = size_name
                else:
                    continue  # Skip if no clear variation
                
                # Clean color name (remove numbers like "05 - Ivory" -> "Ivory")
                if color_name and ' - ' in color_name:
                    color_name = color_name.split(' - ', 1)[1]
                
                # Price
                price = None
                offers = variation.get('Offers', {})
                listings = offers.get('Listings', [{}])[0] if offers.get('Listings') else {}
                if listings.get('Price'):
                    amount = listings['Price'].get('Amount', 0)
                    if amount:
                        price = float(amount)
                
                # Availability
                availability = listings.get('Availability', {}).get('Message', 'in_stock')
                if 'out of stock' in availability.lower():
                    availability = 'out_of_stock'
                elif 'limited' in availability.lower():
                    availability = 'limited'
                else:
                    availability = 'in_stock'
                
                # Images
                images = variation.get('Images', {})
                primary_image = images.get('Primary', {}).get('Large', {}).get('URL', '')
                
                # Insert variation
                cursor.execute("""
                    INSERT OR REPLACE INTO product_variations (
                        product_id, variation_type, variation_value, variation_code,
                        display_name, price, currency, availability_status,
                        condition, merchant_name, is_primary, display_order,
                        amazon_asin, amazon_image_url, amazon_image_alt_text,
                        created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, variation_type, variation_value, variation_asin,
                    variation_value, price, 'USD', availability,
                    'new', 'Amazon', False, 0,
                    variation_asin, primary_image, f"{variation_value} variation",
                    datetime.now(), datetime.now()
                ))
                
                self.stats['variations_added'] += 1
            
            print(f"    ✅ Added {len(variations)} variations")
            
        except Exception as e:
            print(f"    ❌ Error populating variations: {e}")
            # Don't raise - variations are optional
    
    def _populate_categories(self, conn: sqlite3.Connection, product_id: int, item: Dict[str, Any]):
        """Populate categories from Amazon browse nodes"""
        cursor = conn.cursor()
        
        try:
            browse_nodes = item.get('BrowseNodeInfo', {}).get('BrowseNodes', [])
            
            for node in browse_nodes:
                node_id = node.get('Id')
                node_name = node.get('DisplayName')
                context_name = node.get('ContextFreeName')
                is_root = node.get('IsRoot', False)
                
                if not node_id or not node_name:
                    continue
                
                # Insert/update amazon_categories
                cursor.execute("""
                    INSERT OR REPLACE INTO amazon_categories (
                        browse_node_id, browse_node_name, category_path,
                        category_level, is_leaf_category, product_count,
                        category_description, category_keywords,
                        parent_category_name, category_hierarchy,
                        category_type, is_active, last_updated
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    node_id, node_name, context_name,
                    1, not is_root, 1,
                    f"Amazon category: {node_name}",
                    json.dumps([node_name.lower(), context_name.lower()]),
                    None, json.dumps([node_name]),
                    'primary', True, datetime.now()
                ))
                
                # Insert product category relationship
                cursor.execute("""
                    INSERT OR REPLACE INTO product_categories (
                        product_id, category_name, amazon_browse_node_id,
                        amazon_browse_node_name, category_level, is_primary,
                        source, is_amazon_category, created_at
                    ) VALUES (?, ?, ?, ?, ?, ?, 'amazon', TRUE, ?)
                """, (
                    product_id, node_name, node_id, node_name, 1, True, datetime.now()
                ))
                
                self.stats['categories_added'] += 1
            
            print(f"    ✅ Added {len(browse_nodes)} categories")
            
        except Exception as e:
            print(f"    ❌ Error populating categories: {e}")
            # Don't raise - categories are optional
    
    def _update_brands_table(self, conn: sqlite3.Connection, product_id: int, item: Dict[str, Any]):
        """Update brands table with Amazon brand data"""
        cursor = conn.cursor()
        
        try:
            item_info = item.get('ItemInfo', {})
            byline = item_info.get('ByLineInfo', {})
            
            amazon_brand = byline.get('Brand', {}).get('DisplayValue')
            amazon_manufacturer = byline.get('Manufacturer', {}).get('DisplayValue')
            
            if amazon_brand:
                # Check if brand already exists
                cursor.execute("SELECT id FROM brands WHERE name = ?", (amazon_brand,))
                existing_brand = cursor.fetchone()
                
                if existing_brand:
                    brand_id = existing_brand[0]
                    print(f"    ✅ Found existing brand: {amazon_brand} (ID: {brand_id})")
                else:
                    # Create new brand
                    cursor.execute("""
                        INSERT INTO brands (name, display_name, reputation_score, brand_tier, is_active)
                        VALUES (?, ?, ?, ?, ?)
                    """, (amazon_brand, f"{amazon_brand} (Amazon)", 3.5, 'mid-tier', True))
                    brand_id = cursor.lastrowid
                    print(f"    ✅ Created new brand: {amazon_brand} (ID: {brand_id})")
                
                # Update brand with Amazon-specific data
                cursor.execute("""
                    UPDATE brands SET
                        amazon_brand_name = ?,
                        amazon_manufacturer_name = ?,
                        amazon_last_updated = ?
                    WHERE id = ?
                """, (amazon_brand, amazon_manufacturer, datetime.now(), brand_id))
                
                # Update product with brand_id
                cursor.execute("UPDATE products SET brand_id = ? WHERE id = ?", (brand_id, product_id))
                
                self.stats['brands_updated'] += 1
                print(f"    ✅ Updated brand {brand_id} with Amazon data and linked to product {product_id}")
            
        except Exception as e:
            print(f"    ❌ Error updating brands table: {e}")
            # Don't raise - brand updates are optional
    
    def _populate_features(self, conn: sqlite3.Connection, product_id: int, item: Dict[str, Any]):
        """Populate product features"""
        cursor = conn.cursor()
        
        try:
            features = item.get('ItemInfo', {}).get('Features', {}).get('DisplayValues', [])
            
            for i, feature in enumerate(features):
                cursor.execute("""
                    INSERT OR REPLACE INTO smart_features (
                        product_id, feature_text, feature_type, enhanced_feature_type, display_order, source_type
                    ) VALUES (?, ?, ?, ?, ?, ?)
                """, (product_id, feature, 'bullet_point', 'info', i, 'amazon_raw'))
                
                self.stats['features_added'] += 1
            
            print(f"    ✅ Added {len(features)} features")
            
        except Exception as e:
            print(f"    ❌ Error populating features: {e}")
            # Don't raise - features are optional
    
    def _populate_images(self, conn: sqlite3.Connection, product_id: int, item: Dict[str, Any]):
        """Populate product images"""
        cursor = conn.cursor()
        
        try:
            images = item.get('Images', {})
            images_added = 0
            
            # Primary image
            primary = images.get('Primary', {})
            large = primary.get('Large', {})
            if large.get('URL'):
                # Check if this Amazon image already exists
                cursor.execute("""
                    SELECT id FROM product_images 
                    WHERE product_id = ? AND amazon_image_url = ? AND is_amazon_image = 1
                """, (product_id, large['URL']))
                
                if not cursor.fetchone():
                    cursor.execute("""
                        INSERT INTO product_images (
                            product_id, original_url, amazon_image_url, amazon_image_type,
                            amazon_image_size, is_amazon_image, is_primary, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        product_id, large['URL'], large['URL'], 'primary',
                        'large', True, True, datetime.now()
                    ))
                    images_added += 1
                    self.stats['images_added'] += 1
            
            # Variant images (if available)
            variants = images.get('Variants', [])
            for i, variant in enumerate(variants):
                if variant.get('URL'):
                    # Check if this variant already exists
                    cursor.execute("""
                        SELECT id FROM product_images 
                        WHERE product_id = ? AND amazon_image_url = ? AND is_amazon_image = 1
                    """, (product_id, variant['URL']))
                    
                    if not cursor.fetchone():
                        cursor.execute("""
                            INSERT INTO product_images (
                                product_id, original_url, amazon_image_url, amazon_image_type,
                                amazon_image_size, is_amazon_image, is_primary, display_order, created_at
                            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """, (
                            product_id, variant['URL'], variant['URL'], 'variant',
                            'medium', True, False, i+1, datetime.now()
                        ))
                        images_added += 1
                        self.stats['images_added'] += 1
            
            print(f"    ✅ Added {images_added} new images")
            
        except Exception as e:
            print(f"    ❌ Error populating images: {e}")
            # Don't raise - images are optional
    
    def _populate_reviews(self, conn: sqlite3.Connection, product_id: int, item: Dict[str, Any]):
        """Populate review data (limited by API)"""
        cursor = conn.cursor()
        
        try:
            reviews = item.get('CustomerReviews', {})
            star_rating = reviews.get('StarRating', {}).get('Value')
            review_count = reviews.get('Count')
            
            if star_rating or review_count:
                cursor.execute("""
                    INSERT OR REPLACE INTO amazon_reviews (
                        product_id, asin, star_rating, review_count,
                        last_fetched, created_at, updated_at
                    ) VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (
                    product_id, item.get('ASIN', ''), star_rating, review_count,
                    datetime.now(), datetime.now(), datetime.now()
                ))
                print(f"    ✅ Added review data: {star_rating} stars, {review_count} reviews")
            
        except Exception as e:
            print(f"    ❌ Error populating reviews: {e}")
            # Don't raise - reviews are optional
    
    def run_amazon_api_collection(self) -> Dict[str, Any]:
        """Run Phase 2: Amazon API Data Collection Pipeline"""
        print("🚀 Starting Phase 2: Amazon API Data Collection Pipeline")
        print("=" * 60)
        
        conn = self._get_db_connection()
        
        try:
            cursor = conn.cursor()
            
            # Get products that need Amazon API data
            cursor.execute("""
                SELECT p.id, p.amazon_product_id
                FROM products p
                WHERE p.amazon_product_id IS NOT NULL 
                AND p.amazon_product_id != ''
                AND (p.amazon_last_updated IS NULL OR p.amazon_last_updated < datetime('now', '-7 days'))
                ORDER BY p.id
            """)
            
            products_to_process = cursor.fetchall()
            print(f"📊 Found {len(products_to_process)} products needing Amazon API data")
            
            if not products_to_process:
                print("✅ All products are up to date!")
                return self.stats
            
            # Process each product
            for product_id, asin in tqdm(products_to_process, desc="Processing Amazon API data"):
                try:
                    success = self._populate_product_data(product_id, asin)
                    if success:
                        self.stats['products_processed'] += 1
                    else:
                        self.stats['skipped'] += 1
                    
                except Exception as e:
                    print(f"❌ Error processing product {product_id}: {e}")
                    self.stats['errors'] += 1
                    continue
        
        finally:
            conn.close()
        
        # Final statistics
        print(f"\n📊 Phase 2 Complete!")
        print(f"   📦 Products processed: {self.stats['products_processed']}")
        print(f"   ✅ Products updated: {self.stats['products_updated']}")
        print(f"   🎨 Variations added: {self.stats['variations_added']}")
        print(f"   📂 Categories added: {self.stats['categories_added']}")
        print(f"   🏷️ Brands updated: {self.stats['brands_updated']}")
        print(f"   ✨ Features added: {self.stats['features_added']}")
        print(f"   🖼️ Images added: {self.stats['images_added']}")
        print(f"   ⏭️ Skipped: {self.stats['skipped']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
        
        return self.stats

def main():
    """Run Phase 2: Amazon API Data Collection Pipeline"""
    pipeline = AmazonAPIDataCollectionPipeline()
    results = pipeline.run_amazon_api_collection()
    
    print(f"\n🎉 Phase 2 Complete!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
