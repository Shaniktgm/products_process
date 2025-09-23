#!/usr/bin/env python3
"""
Amazon API Data Populator
Populates enhanced database tables with Amazon PA-API 5.0 data
"""

import sqlite3
import json
from datetime import datetime
from typing import Dict, List, Any, Optional
from amazon_api_explorer import AmazonAPIExplorer

class AmazonDataPopulator:
    """Populate database with Amazon PA-API 5.0 data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self.api = AmazonAPIExplorer(
            access_key='AKPATKWXAM1758523929',
            secret_key='YxW3wUc6a96fsRZYxOhHAI5+lIYvszrmqV3Qawfs',
            associate_tag='homeprinciple-20'
        )
    
    def _get_connection(self) -> sqlite3.Connection:
        """Get database connection"""
        return sqlite3.connect(self.db_path)
    
    def populate_product_data(self, product_id: int, asin: str) -> bool:
        """Populate product data from Amazon API"""
        print(f"🔍 Populating data for product {product_id} (ASIN: {asin})")
        
        try:
            # Get comprehensive product data
            payload = {
                'ItemIds': [asin],
                'Resources': [
                    'Images.Primary.Large',
                    'ItemInfo.Title',
                    'ItemInfo.ByLineInfo',
                    'Offers.Listings.Price'
                ]
            }
            
            result = self.api._make_request('GetItems', payload)
            
            if not result or 'ItemsResult' not in result:
                print(f"  ❌ No data retrieved for ASIN {asin}")
                return False
            
            items = result['ItemsResult'].get('Items', [])
            if not items:
                print(f"  ❌ No items found for ASIN {asin}")
                return False
            
            item = items[0]
            
            # Update products table
            self._update_products_table(product_id, item)
            
            # Populate product variations
            self._populate_product_variations(product_id, asin, item)
            
            # Populate categories
            self._populate_categories(product_id, item)
            
            # Populate features
            self._populate_features(product_id, item)
            
            # Populate reviews
            self._populate_reviews(product_id, item)
            
            # Populate images
            self._populate_images(product_id, item)
            
            # Update brands table
            self._update_brands_table(product_id, item)
            
            print(f"  ✅ Successfully populated data for product {product_id}")
            return True
            
        except Exception as e:
            print(f"  ❌ Error populating data for product {product_id}: {e}")
            return False
    
    def _update_products_table(self, product_id: int, item: Dict[str, Any]):
        """Update products table with Amazon data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Extract data from API response
            item_info = item.get('ItemInfo', {})
            offers = item.get('Offers', {})
            reviews = item.get('CustomerReviews', {})
            browse_nodes = item.get('BrowseNodeInfo', {}).get('BrowseNodes', [])
            
            # Prepare update data
            update_data = {}
            
            # Basic info
            if 'Title' in item_info:
                update_data['amazon_title'] = item_info['Title'].get('DisplayValue')
            
            # Brand and manufacturer info
            if 'ByLineInfo' in item_info:
                byline = item_info['ByLineInfo']
                if 'Brand' in byline:
                    update_data['amazon_brand'] = byline['Brand'].get('DisplayValue')
                if 'Manufacturer' in byline:
                    update_data['amazon_manufacturer'] = byline['Manufacturer'].get('DisplayValue')
            
            # Product info
            if 'ProductInfo' in item_info:
                product_info = item_info['ProductInfo']
                if 'Color' in product_info:
                    update_data['amazon_color_code'] = product_info['Color'].get('DisplayValue')
                if 'Size' in product_info:
                    update_data['amazon_size_code'] = product_info['Size'].get('DisplayValue')
                if 'ItemDimensions' in product_info:
                    dimensions = product_info['ItemDimensions']
                    if isinstance(dimensions, dict):
                        update_data['amazon_dimensions'] = json.dumps(dimensions)
            
            # Features
            if 'Features' in item_info:
                features = item_info['Features'].get('DisplayValues', [])
                update_data['amazon_features'] = json.dumps(features)
            
            # Pricing
            if offers and 'Listings' in offers:
                listings = offers['Listings']
                if listings:
                    listing = listings[0]
                    if 'Price' in listing:
                        price = listing['Price']
                        update_data['price'] = float(price.get('Amount', 0))  # Amazon returns as decimal
                        update_data['currency'] = price.get('Currency', 'USD')
                    
                    if 'Availability' in listing:
                        availability = listing['Availability']
                        update_data['amazon_availability_status'] = availability.get('Type')
                    
                    if 'Condition' in listing:
                        update_data['amazon_condition'] = listing['Condition'].get('DisplayValue')
                    
                    if 'MerchantInfo' in listing:
                        update_data['amazon_merchant_name'] = listing['MerchantInfo'].get('Name')
            
            # Reviews
            if reviews:
                if 'StarRating' in reviews:
                    update_data['rating'] = float(reviews['StarRating'].get('Value', 0))
                if 'Count' in reviews:
                    update_data['review_count'] = reviews['Count']
            
            # Browse nodes
            if browse_nodes:
                primary_node = browse_nodes[0]
                update_data['amazon_browse_node_id'] = primary_node.get('Id')
                update_data['amazon_browse_node_name'] = primary_node.get('DisplayName')
            
            # Add timestamp
            update_data['amazon_last_updated'] = datetime.now()
            
            # Build and execute update query
            if update_data:
                set_clause = ', '.join([f"{key} = ?" for key in update_data.keys()])
                values = list(update_data.values()) + [product_id]
                
                cursor.execute(f"""
                    UPDATE products 
                    SET {set_clause}
                    WHERE id = ?
                """, values)
                
                conn.commit()
                print(f"    ✅ Updated products table with {len(update_data)} fields")
            
        except Exception as e:
            print(f"    ❌ Error updating products table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _populate_product_variations(self, product_id: int, asin: str, item: Dict[str, Any]):
        """Populate product variations table"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get variations using GetVariations
            variations_payload = {
                'ASIN': asin,
                'Resources': [
                    'Images.Primary.Large',
                    'ItemInfo.Title',
                    'Offers.Listings.Price'
                ]
            }
            
            variations_result = self.api._make_request('GetVariations', variations_payload)
            
            if variations_result and 'VariationsResult' in variations_result:
                variations = variations_result['VariationsResult'].get('Items', [])
                
                # Clear existing variations
                cursor.execute("DELETE FROM product_variations WHERE product_id = ?", (product_id,))
                
                for i, variation in enumerate(variations):
                    item_info = variation.get('ItemInfo', {})
                    offers = variation.get('Offers', {})
                    images = variation.get('Images', {})
                    
                    # Extract variation data
                    variation_data = {
                        'product_id': product_id,
                        'variation_type': 'color_size',
                        'variation_value': '',
                        'variation_code': '',
                        'display_name': '',
                        'price': None,
                        'currency': 'USD',
                        'availability_status': 'in_stock',
                        'condition': 'new',
                        'is_primary': i == 0,
                        'display_order': i,
                        'amazon_asin': variation.get('ASIN'),
                        'amazon_image_url': None,
                        'amazon_image_alt_text': None
                    }
                    
                    # Title and display name
                    if 'Title' in item_info:
                        title = item_info['Title'].get('DisplayValue', '')
                        variation_data['display_name'] = title
                    
                    # Extract color and size from VariationAttributes (much more reliable!)
                    color = None
                    size = None
                    
                    variation_attributes = variation.get('VariationAttributes', [])
                    for attr in variation_attributes:
                        if attr.get('Name') == 'color_name':
                            color = attr.get('Value', '')
                            # Clean up color names (remove numbers like "05 - Ivory" -> "Ivory")
                            if ' - ' in color:
                                color = color.split(' - ', 1)[1]
                        elif attr.get('Name') == 'size_name':
                            size = attr.get('Value', '')
                    
                    # Set variation values
                    if color and size:
                        variation_data['variation_value'] = f"{color} - {size}"
                        variation_data['variation_code'] = f"{color}_{size}"
                    elif color:
                        variation_data['variation_value'] = color
                        variation_data['variation_code'] = color
                    elif size:
                        variation_data['variation_value'] = size
                        variation_data['variation_code'] = size
                    else:
                        variation_data['variation_value'] = f"Variation {i+1}"
                        variation_data['variation_code'] = f"var_{i+1}"
                    
                    # Pricing - fix the price calculation
                    if offers and 'Listings' in offers:
                        listings = offers['Listings']
                        if listings:
                            listing = listings[0]
                            if 'Price' in listing:
                                price = listing['Price']
                                # Amazon returns price as decimal (e.g., 84.99 = $84.99)
                                amount = price.get('Amount', 0)
                                if amount:
                                    variation_data['price'] = float(amount)
                                variation_data['currency'] = price.get('Currency', 'USD')
                            
                            if 'Availability' in listing:
                                variation_data['availability_status'] = listing['Availability'].get('Type', 'in_stock')
                    
                    # Images
                    if images and 'Primary' in images:
                        primary = images['Primary']
                        if 'Large' in primary:
                            variation_data['amazon_image_url'] = primary['Large'].get('URL')
                            variation_data['amazon_image_alt_text'] = f"Product variation image"
                    
                    # Insert variation
                    cursor.execute("""
                        INSERT INTO product_variations (
                            product_id, variation_type, variation_value, variation_code,
                            display_name, price, currency, availability_status,
                            condition, is_primary, display_order, amazon_asin,
                            amazon_image_url, amazon_image_alt_text
                        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                    """, (
                        variation_data['product_id'],
                        variation_data['variation_type'],
                        variation_data['variation_value'],
                        variation_data['variation_code'],
                        variation_data['display_name'],
                        variation_data['price'],
                        variation_data['currency'],
                        variation_data['availability_status'],
                        variation_data['condition'],
                        variation_data['is_primary'],
                        variation_data['display_order'],
                        variation_data['amazon_asin'],
                        variation_data['amazon_image_url'],
                        variation_data['amazon_image_alt_text']
                    ))
                
                conn.commit()
                print(f"    ✅ Populated {len(variations)} product variations")
            
        except Exception as e:
            print(f"    ❌ Error populating product variations: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _populate_categories(self, product_id: int, item: Dict[str, Any]):
        """Populate categories from browse nodes"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            browse_nodes = item.get('BrowseNodeInfo', {}).get('BrowseNodes', [])
            
            # Clear existing Amazon categories for this product
            cursor.execute("""
                DELETE FROM product_categories 
                WHERE product_id = ? AND source = 'amazon'
            """, (product_id,))
            
            for i, node in enumerate(browse_nodes):
                node_id = node.get('Id')
                node_name = node.get('DisplayName')
                
                if node_id and node_name:
                    # Insert into product_categories
                    cursor.execute("""
                        INSERT INTO product_categories (
                            product_id, category_name, amazon_browse_node_id,
                            amazon_browse_node_name, category_level, is_primary,
                            source, created_at
                        ) VALUES (?, ?, ?, ?, ?, ?, 'amazon', ?)
                    """, (
                        product_id, node_name, node_id, node_name,
                        i + 1, i == 0, datetime.now()
                    ))
                    
                    # Insert into amazon_categories if not exists
                    cursor.execute("""
                        INSERT OR IGNORE INTO amazon_categories (
                            browse_node_id, browse_node_name, category_level
                        ) VALUES (?, ?, ?)
                    """, (node_id, node_name, i + 1))
            
            conn.commit()
            print(f"    ✅ Populated {len(browse_nodes)} categories")
            
        except Exception as e:
            print(f"    ❌ Error populating categories: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _populate_features(self, product_id: int, item: Dict[str, Any]):
        """Populate Amazon features"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            features = item.get('ItemInfo', {}).get('Features', {}).get('DisplayValues', [])
            
            # Clear existing features
            cursor.execute("DELETE FROM amazon_features WHERE product_id = ?", (product_id,))
            
            for i, feature in enumerate(features):
                cursor.execute("""
                    INSERT INTO amazon_features (
                        product_id, feature_text, feature_type,
                        display_order, is_highlighted
                    ) VALUES (?, ?, 'bullet_point', ?, ?)
                """, (product_id, feature, i, i < 3))  # First 3 are highlighted
            
            conn.commit()
            print(f"    ✅ Populated {len(features)} features")
            
        except Exception as e:
            print(f"    ❌ Error populating features: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _populate_reviews(self, product_id: int, item: Dict[str, Any]):
        """Populate Amazon reviews data"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            reviews = item.get('CustomerReviews', {})
            
            if reviews:
                # Clear existing reviews
                cursor.execute("DELETE FROM amazon_reviews WHERE product_id = ?", (product_id,))
                
                star_rating = reviews.get('StarRating', {}).get('Value')
                review_count = reviews.get('Count', 0)
                
                cursor.execute("""
                    INSERT INTO amazon_reviews (
                        product_id, star_rating, review_count, last_updated
                    ) VALUES (?, ?, ?, ?)
                """, (product_id, star_rating, review_count, datetime.now()))
                
                conn.commit()
                print(f"    ✅ Populated reviews data (Rating: {star_rating}, Count: {review_count})")
            
        except Exception as e:
            print(f"    ❌ Error populating reviews: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _populate_images(self, product_id: int, item: Dict[str, Any]):
        """Populate Amazon images"""
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            images = item.get('Images', {})
            
            # Clear existing Amazon images
            cursor.execute("""
                DELETE FROM product_images 
                WHERE product_id = ? AND is_amazon_image = TRUE
            """, (product_id,))
            
            # Primary image
            if 'Primary' in images:
                primary = images['Primary']
                if 'Large' in primary:
                    large = primary['Large']
                    cursor.execute("""
                        INSERT INTO product_images (
                            product_id, original_url, amazon_image_url,
                            amazon_image_type, amazon_image_size, is_primary,
                            is_amazon_image, display_order, created_at
                        ) VALUES (?, ?, ?, 'primary', 'large', TRUE, TRUE, 0, ?)
                    """, (
                        product_id, large.get('URL'), large.get('URL'),
                        datetime.now()
                    ))
            
            # Variant images
            if 'Variants' in images:
                variants = images['Variants']
                for i, variant in enumerate(variants):
                    if 'Large' in variant:
                        large = variant['Large']
                        cursor.execute("""
                            INSERT INTO product_images (
                                product_id, original_url, amazon_image_url,
                                amazon_image_type, amazon_image_size, is_primary,
                                is_amazon_image, display_order, created_at
                            ) VALUES (?, ?, ?, 'variant', 'large', FALSE, TRUE, ?, ?)
                        """, (
                            product_id, large.get('URL'), large.get('URL'),
                            i + 1, datetime.now()
                        ))
            
            conn.commit()
            print(f"    ✅ Populated Amazon images")
            
        except Exception as e:
            print(f"    ❌ Error populating images: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def _update_brands_table(self, product_id: int, item: Dict[str, Any]):
        """Update brands table with Amazon brand data"""
        conn = self._get_connection()
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
                
                # Update product with brand_id
                cursor.execute("UPDATE products SET brand_id = ? WHERE id = ?", (brand_id, product_id))
                
                conn.commit()
                print(f"    ✅ Updated product {product_id} with brand_id {brand_id}")
            
        except Exception as e:
            print(f"    ❌ Error updating brands table: {e}")
            conn.rollback()
        finally:
            conn.close()
    
    def populate_all_products(self, limit: int = None):
        """Populate data for all products with Amazon ASINs"""
        print("🚀 Starting Amazon API Data Population...")
        print("=" * 60)
        
        conn = self._get_connection()
        cursor = conn.cursor()
        
        try:
            # Get products with Amazon ASINs
            query = """
                SELECT id, amazon_product_id 
                FROM products 
                WHERE amazon_product_id IS NOT NULL 
                AND amazon_product_id != ''
            """
            
            if limit:
                query += f" LIMIT {limit}"
            
            cursor.execute(query)
            products = cursor.fetchall()
            
            print(f"📊 Found {len(products)} products to populate")
            
            success_count = 0
            error_count = 0
            
            for product_id, asin in products:
                if self.populate_product_data(product_id, asin):
                    success_count += 1
                else:
                    error_count += 1
                
                # Rate limiting
                import time
                time.sleep(1)  # 1 second between requests
            
            print("\n" + "=" * 60)
            print("🎉 Amazon API Data Population Complete!")
            print(f"✅ Successfully populated: {success_count} products")
            print(f"❌ Failed to populate: {error_count} products")
            
        except Exception as e:
            print(f"❌ Error in populate_all_products: {e}")
        finally:
            conn.close()

def main():
    """Run Amazon data population"""
    populator = AmazonDataPopulator()
    
    # Test with a few products first
    print("🧪 Testing with first 3 products...")
    populator.populate_all_products(limit=3)
    
    # Uncomment to populate all products
    # populator.populate_all_products()

if __name__ == "__main__":
    main()
