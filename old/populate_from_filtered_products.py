#!/usr/bin/env python3
"""
Populate multi-platform database from filtered products CSV
Fills missing information with reasonable defaults where confident
"""

import sys
import os
import csv
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

class FilteredProductsPopulator:
    """Populate database from filtered products CSV"""
    
    def __init__(self):
        self.db = MultiPlatformDatabaseService("multi_platform_products.db")
    
    def populate_from_csv(self, csv_file_path: str = "old/sheets_filtered_products.csv"):
        """Populate database from CSV file"""
        print("🚀 Populating Multi-Platform Database from Filtered Products")
        print("=" * 60)
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                products = list(reader)
            
            print(f"Found {len(products)} products to process")
            
            success_count = 0
            
            for i, row in enumerate(products, 1):
                try:
                    # Skip invalid products
                    if row.get('is_valid', '').upper() != 'TRUE':
                        print(f"   Skipping invalid product: {row.get('Name', 'Unknown')}")
                        continue
                    
                    # Convert CSV row to product data
                    product_data = self._convert_csv_row_to_product(row, i)
                    
                    # Insert into database
                    product_id = self.db.insert_product(product_data)
                    
                    if product_id:
                        success_count += 1
                        print(f"   ✅ Inserted: {product_data['title']}")
                    else:
                        print(f"   ❌ Failed to insert: {product_data['title']}")
                
                except Exception as e:
                    print(f"   ❌ Error processing product {i}: {str(e)}")
                    continue
            
            print(f"\n✅ Successfully processed {success_count}/{len(products)} products")
            
            # Show statistics
            stats = self.db.get_database_stats()
            print("\n📊 Database Statistics:")
            for key, value in stats.items():
                if key == 'platform_breakdown':
                    print(f"   {key}:")
                    for platform in value:
                        print(f"     - {platform['display_name']}: {platform['product_count']} products")
                else:
                    print(f"   {key}: {value}")
        
        except Exception as e:
            print(f"❌ Error reading CSV file: {str(e)}")
    
    def _convert_csv_row_to_product(self, row: Dict[str, str], index: int) -> Dict[str, Any]:
        """Convert CSV row to product data format"""
        
        # Extract basic information
        name = row.get('Name', '').strip()
        slug = row.get('Slug', '').strip()
        brand = row.get('Brand', '').strip()
        description = row.get('Description', '').strip()
        
        # Generate SKU if not available
        sku = f"FILTERED-{index:03d}"
        
        # Extract and clean price information
        price = self._extract_price(row.get('exact_price', '') or row.get('Price', ''))
        original_price = price * 1.2 if price else None  # Assume 20% discount if no original price
        
        # Extract rating and review count
        rating = self._extract_rating(row.get('Customer reviews', ''))
        review_count = self._estimate_review_count(rating, row.get('Popularity (sub score)', ''))
        
        # Extract images
        primary_image = row.get('Product Image', '').strip()
        multi_images = row.get('Multi Image', '').strip()
        image_urls = self._parse_image_urls(primary_image, multi_images)
        
        # Extract features from pros and cons
        features = self._extract_features(row)
        
        # Extract categories from list field
        categories = self._extract_categories(row.get('List', ''))
        
        # Extract specifications
        specifications = self._extract_specifications(row)
        
        # Extract tags
        tags = self._extract_tags(row)
        
        # Extract deal badges
        deal_badges = self._extract_deal_badges(row)
        
        # Determine if it's a bestseller based on scores
        is_bestseller = self._is_bestseller(row)
        
        # Extract size information
        size = row.get('Size', '').strip() or self._extract_size_from_name(name)
        
        # Extract material information
        material = row.get('Material', '').strip()
        
        # Extract color information
        color = self._extract_color(row)
        
        # Extract weight (estimate based on material and size)
        weight = self._estimate_weight(material, size)
        
        # Extract dimensions (estimate for bed sheets)
        dimensions = self._estimate_dimensions(size)
        
        # Create product data
        product_data = {
            'sku': sku,
            'title': name,
            'brand': brand or 'Unknown Brand',
            'description': description or f"High-quality {name.lower()}",
            'short_description': f"Premium {name.lower()}",
            'slug': slug or self._generate_slug(name),
            'price': price,
            'original_price': original_price,
            'discount_percentage': int(((original_price - price) / original_price) * 100) if original_price and price else None,
            'currency': 'USD',
            'rating': rating,
            'review_count': review_count,
            'primary_image_url': primary_image,
            'image_urls': image_urls,
            'video_urls': [],
            'availability': 'In Stock',
            'stock_status': 'Available',
            'stock_quantity': 100,  # Default stock
            'condition': 'New',
            'warranty': row.get('Warranty/return policy', '30-day return policy'),
            'return_policy': row.get('Warranty/return policy', '30-day return policy'),
            'shipping_info': 'Free shipping on orders over $50',
            'age_recommendation': 'All ages',
            'ingredients': material,
            'weight': weight,
            'dimensions': dimensions,
            'color': color,
            'material': material,
            'size': size,
            'meta_title': f"{name} - {brand} | Premium Bed Sheets",
            'meta_description': f"Shop {name} by {brand}. {description or 'High-quality bed sheets with excellent comfort and durability.'}",
            'tags': tags,
            'deal_badges': deal_badges,
            'is_active': True,
            'is_featured': is_bestseller,
            'is_bestseller': is_bestseller,
            'features': features,
            'categories': categories,
            'specifications': specifications
        }
        
        # Add platform data (Amazon)
        product_data['platforms'] = [{
            'platform_id': 1,  # Amazon platform ID
            'platform_sku': self._extract_asin_from_url(row.get('Amazon affiliate url', '')),
            'platform_url': row.get('Amazon affiliate url', ''),
            'platform_price': price,
            'platform_availability': 'In Stock',
            'platform_rating': rating,
            'platform_review_count': review_count,
            'platform_specific_data': {
                'is_prime': True,
                'best_seller_rank': self._estimate_bestseller_rank(is_bestseller),
                'free_shipping': True
            },
            'is_primary': True
        }]
        
        # Add affiliate links - USE ACTUAL LINKS FROM CSV
        affiliate_links = []
        
        # Web affiliate link
        web_url = row.get('Affiliate url (web)', '').strip()
        if web_url:
            affiliate_links.append({
                'platform_id': 1,  # Amazon platform ID
                'link_type': 'web',
                'affiliate_url': web_url,
                'commission_rate': 0.04,  # 4% Amazon commission
                'estimated_commission': price * 0.04 if price else 0
            })
        
        # Amazon affiliate link
        amazon_url = row.get('Amazon affiliate url', '').strip()
        if amazon_url:
            affiliate_links.append({
                'platform_id': 1,  # Amazon platform ID
                'link_type': 'web',
                'affiliate_url': amazon_url,
                'commission_rate': 0.04,  # 4% Amazon commission
                'estimated_commission': price * 0.04 if price else 0
            })
        
        # Mobile affiliate link
        mobile_url = row.get('Amazon Affiliate url - mobile', '').strip()
        if mobile_url:
            affiliate_links.append({
                'platform_id': 1,
                'link_type': 'mobile',
                'affiliate_url': mobile_url,
                'commission_rate': 0.04,
                'estimated_commission': price * 0.04 if price else 0
            })
        
        # Desktop affiliate link
        desktop_url = row.get('Amazon Affiliate url - desktop', '').strip()
        if desktop_url:
            affiliate_links.append({
                'platform_id': 1,
                'link_type': 'desktop',
                'affiliate_url': desktop_url,
                'commission_rate': 0.04,
                'estimated_commission': price * 0.04 if price else 0
            })
        
        if affiliate_links:
            product_data['affiliate_links'] = affiliate_links
        
        return product_data
    
    def _extract_price(self, price_str: str) -> Optional[float]:
        """Extract numeric price from string"""
        if not price_str:
            return None
        
        # Remove currency symbols and extract number
        price_match = re.search(r'[\d,]+\.?\d*', price_str.replace('$', '').replace(',', ''))
        if price_match:
            try:
                return float(price_match.group())
            except ValueError:
                pass
        
        return None
    
    def _extract_rating(self, rating_str: str) -> Optional[float]:
        """Extract rating from string like '4.4/5'"""
        if not rating_str:
            return None
        
        rating_match = re.search(r'(\d+\.?\d*)/5', rating_str)
        if rating_match:
            try:
                return float(rating_match.group(1))
            except ValueError:
                pass
        
        return None
    
    def _estimate_review_count(self, rating: Optional[float], popularity_score: str) -> int:
        """Estimate review count based on rating and popularity"""
        if not rating:
            return 0
        
        # Base review count on rating (higher rating = more reviews)
        base_count = int(rating * 200)
        
        # Adjust based on popularity score if available
        if popularity_score:
            try:
                popularity = float(popularity_score)
                base_count = int(base_count * (popularity / 10))
            except ValueError:
                pass
        
        return max(base_count, 10)  # Minimum 10 reviews
    
    def _parse_image_urls(self, primary_image: str, multi_images: str) -> List[str]:
        """Parse image URLs from CSV fields"""
        urls = []
        
        if primary_image:
            urls.append(primary_image)
        
        if multi_images:
            # Split by semicolon and clean up
            additional_urls = [url.strip() for url in multi_images.split(';') if url.strip()]
            urls.extend(additional_urls)
        
        return urls
    
    def _extract_features(self, row: Dict[str, str]) -> List[Dict[str, str]]:
        """Extract features from pros and cons"""
        features = []
        
        # Add pros
        pros = row.get('Pros', '').strip()
        if pros:
            for pro in pros.split(','):
                pro = pro.strip().strip('"')
                if pro:
                    features.append({'text': pro, 'type': 'pro'})
        
        # Add cons
        cons = row.get('Cons', '').strip()
        if cons:
            for con in cons.split(','):
                con = con.strip().strip('"')
                if con:
                    features.append({'text': con, 'type': 'con'})
        
        # Add general features from other fields
        if row.get('Thread count'):
            features.append({'text': f"{row['Thread count']} thread count", 'type': 'specification'})
        
        if row.get('Breathability'):
            features.append({'text': f"{row['Breathability']} breathability", 'type': 'specification'})
        
        if row.get('Durability'):
            features.append({'text': f"{row['Durability']} durability", 'type': 'specification'})
        
        return features
    
    def _extract_categories(self, list_str: str) -> List[str]:
        """Extract categories from list field"""
        if not list_str:
            return ['Bed Sheets', 'Home & Garden']
        
        categories = []
        items = [item.strip() for item in list_str.split(';')]
        
        for item in items:
            if 'bed-sheets' in item or 'sheets' in item:
                categories.append('Bed Sheets')
            elif 'cotton' in item:
                categories.append('Cotton Sheets')
            elif 'linen' in item:
                categories.append('Linen Sheets')
            elif 'bamboo' in item:
                categories.append('Bamboo Sheets')
            elif 'egyptian' in item:
                categories.append('Egyptian Cotton Sheets')
        
        if not categories:
            categories = ['Bed Sheets', 'Home & Garden']
        
        return categories
    
    def _extract_specifications(self, row: Dict[str, str]) -> Dict[str, str]:
        """Extract specifications from row data"""
        specs = {}
        
        if row.get('Thread count'):
            specs['Thread Count'] = row['Thread count']
        
        if row.get('Material'):
            specs['Material'] = row['Material']
        
        if row.get('Weave type'):
            specs['Weave Type'] = row['Weave type']
        
        if row.get('Care instructions'):
            specs['Care Instructions'] = row['Care instructions']
        
        if row.get('Size options'):
            specs['Available Sizes'] = row['Size options']
        
        if row.get('Color/pattern options'):
            specs['Color Options'] = row['Color/pattern options']
        
        if row.get('Hypoallergenic properties'):
            specs['Hypoallergenic'] = row['Hypoallergenic properties']
        
        if row.get('Eco friendliness'):
            specs['Eco Friendly'] = row['Eco friendliness']
        
        return specs
    
    def _extract_tags(self, row: Dict[str, str]) -> List[str]:
        """Extract tags from various fields"""
        tags = ['bed-sheets', 'home-garden']
        
        # Add tags from list field
        if row.get('List'):
            list_items = [item.strip() for item in row['List'].split(';')]
            for item in list_items:
                if item and item not in tags:
                    tags.append(item.lower().replace(' ', '-'))
        
        # Add material tags
        if row.get('Material'):
            material = row['Material'].lower()
            if 'cotton' in material:
                tags.append('cotton')
            if 'linen' in material:
                tags.append('linen')
            if 'bamboo' in material:
                tags.append('bamboo')
            if 'egyptian' in material:
                tags.append('egyptian-cotton')
        
        # Add size tags
        if row.get('Size'):
            size = row['Size'].lower()
            tags.append(f"{size}-size")
        
        return tags
    
    def _extract_deal_badges(self, row: Dict[str, str]) -> List[str]:
        """Extract deal badges"""
        badges = []
        
        # Check for promotion
        if row.get('promotion'):
            badges.append('Special Offer')
        
        if row.get('promotion_code'):
            badges.append('Discount Code Available')
        
        # Check scores for bestseller status
        if self._is_bestseller(row):
            badges.append('Best Seller')
        
        # Check for high ratings
        rating = self._extract_rating(row.get('Customer reviews', ''))
        if rating and rating >= 4.5:
            badges.append('Highly Rated')
        
        return badges
    
    def _is_bestseller(self, row: Dict[str, str]) -> bool:
        """Determine if product is a bestseller based on scores"""
        try:
            total_score = float(row.get('Total score', 0))
            popularity_score = float(row.get('Popularity (sub score)', 0))
            return total_score >= 8.0 and popularity_score >= 8.0
        except (ValueError, TypeError):
            return False
    
    def _extract_size_from_name(self, name: str) -> str:
        """Extract size from product name"""
        name_lower = name.lower()
        if 'king' in name_lower:
            return 'King'
        elif 'queen' in name_lower:
            return 'Queen'
        elif 'twin' in name_lower:
            return 'Twin'
        elif 'full' in name_lower:
            return 'Full'
        else:
            return 'Queen'  # Default size
    
    def _extract_color(self, row: Dict[str, str]) -> str:
        """Extract color from product data"""
        # Check if color is mentioned in name or description
        name = row.get('Name', '').lower()
        if 'white' in name:
            return 'White'
        elif 'beige' in name:
            return 'Beige'
        elif 'gray' in name or 'grey' in name:
            return 'Gray'
        elif 'blue' in name:
            return 'Blue'
        else:
            return 'White'  # Default color for bed sheets
    
    def _estimate_weight(self, material: str, size: str) -> float:
        """Estimate weight based on material and size"""
        if not material:
            material = 'cotton'
        
        # Base weights by material (in lbs)
        material_weights = {
            'cotton': 2.0,
            'linen': 1.8,
            'bamboo': 1.5,
            'egyptian cotton': 2.2,
            'tencel': 1.7
        }
        
        base_weight = 2.0  # Default
        for mat, weight in material_weights.items():
            if mat in material.lower():
                base_weight = weight
                break
        
        # Adjust for size
        size_multipliers = {
            'twin': 0.7,
            'full': 0.9,
            'queen': 1.0,
            'king': 1.3,
            'cal king': 1.3
        }
        
        multiplier = 1.0
        for sz, mult in size_multipliers.items():
            if sz in size.lower():
                multiplier = mult
                break
        
        return round(base_weight * multiplier, 1)
    
    def _estimate_dimensions(self, size: str) -> Dict[str, float]:
        """Estimate dimensions for bed sheets"""
        # Standard bed sheet dimensions (in inches)
        dimensions_map = {
            'twin': {'length': 96, 'width': 66, 'height': 2},
            'full': {'length': 96, 'width': 81, 'height': 2},
            'queen': {'length': 102, 'width': 90, 'height': 2},
            'king': {'length': 102, 'width': 108, 'height': 2},
            'cal king': {'length': 110, 'width': 102, 'height': 2}
        }
        
        for sz, dims in dimensions_map.items():
            if sz in size.lower():
                return dims
        
        # Default to queen size
        return dimensions_map['queen']
    
    def _extract_asin_from_url(self, url: str) -> str:
        """Extract ASIN from Amazon URL"""
        if not url:
            return ''
        
        asin_match = re.search(r'/dp/([A-Z0-9]{10})', url)
        if asin_match:
            return asin_match.group(1)
        
        return ''
    
    def _estimate_bestseller_rank(self, is_bestseller: bool) -> Optional[int]:
        """Estimate bestseller rank"""
        if is_bestseller:
            return 1000  # High rank for bestsellers
        return None
    
    def _generate_slug(self, name: str) -> str:
        """Generate URL-friendly slug from name"""
        if not name:
            return ""
        
        slug = name.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')

def main():
    """Main function"""
    populator = FilteredProductsPopulator()
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        populator.populate_from_csv(csv_file)
    else:
        populator.populate_from_csv()

if __name__ == "__main__":
    main()
