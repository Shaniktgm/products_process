#!/usr/bin/env python3
"""
Populate multi-platform database from products_three_rows CSV
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

class ThreeRowsPopulator:
    """Populate database from products_three_rows CSV"""
    
    def __init__(self):
        self.db = MultiPlatformDatabaseService("multi_platform_products.db")
    
    def populate_from_csv(self, csv_file_path: str = "sheets_raw_data/products_three_rows.csv"):
        """Populate database from CSV file"""
        print("🚀 Populating Multi-Platform Database from Products Three Rows")
        print("=" * 60)
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                products = list(reader)
            
            print(f"Found {len(products)} products to process")
            
            success_count = 0
            
            for i, row in enumerate(products, 1):
                try:
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
        title = row.get('title', '').strip()
        brand = row.get('brand', '').strip()
        asin = row.get('asin', '').strip()
        retailer = row.get('retailer', '').strip()
        
        # Generate SKU with timestamp to avoid duplicates
        timestamp = datetime.now().strftime("%H%M%S")
        sku = f"THREE-{timestamp}-{index:03d}"
        
        # Extract price based on size_selected or use king as default
        size_selected = row.get('size_selected', '').strip()
        price = self._extract_price_for_size(row, size_selected)
        
        # Extract rating and review count
        rating = self._extract_rating(row.get('rating', ''))
        review_count = self._extract_review_count(row.get('review_count', ''))
        
        # Extract material and specifications
        material = row.get('material', '').strip()
        thread_count = row.get('thread_count', '').strip()
        
        # Extract features
        features = self._extract_features(row.get('features', ''))
        
        # Extract size and color
        size = size_selected or 'King'  # Default to King
        color = self._extract_color(row.get('color_selected', ''))
        
        # Extract weight and dimensions
        weight = self._extract_weight(row.get('item_weight', ''))
        dimensions = self._extract_dimensions(row.get('item_dimensions', ''))
        
        # Generate slug with timestamp to avoid duplicates
        slug = self._generate_slug(title) + f"-{timestamp}"
        
        # Create product data
        product_data = {
            'sku': sku,
            'title': title,
            'brand': brand or 'Unknown Brand',
            'description': f"High-quality {title.lower()}",
            'short_description': f"Premium {title.lower()}",
            'slug': slug,
            'price': price,
            'original_price': price * 1.2 if price else None,  # Assume 20% markup
            'discount_percentage': 16,  # 16% discount
            'currency': 'USD',
            'rating': rating,
            'review_count': review_count,
            'primary_image_url': f"https://example.com/images/{asin}.jpg",
            'image_urls': [f"https://example.com/images/{asin}.jpg"],
            'video_urls': [],
            'availability': row.get('availability', 'In Stock'),
            'stock_status': 'Available',
            'stock_quantity': 100,
            'condition': 'New',
            'warranty': row.get('returns', '30-day return policy'),
            'return_policy': row.get('returns', '30-day return policy'),
            'shipping_info': f"Ships from {row.get('ships_from', 'Amazon')}",
            'age_recommendation': 'All ages',
            'ingredients': material,
            'weight': weight,
            'dimensions': dimensions,
            'color': color,
            'material': material,
            'size': size,
            'meta_title': f"{title} - {brand} | Premium Bed Sheets",
            'meta_description': f"Shop {title} by {brand}. High-quality bed sheets with excellent comfort and durability.",
            'tags': self._generate_tags(row),
            'deal_badges': ['Best Seller'] if rating and rating >= 4.4 else [],
            'is_active': True,
            'is_featured': rating and rating >= 4.4,
            'is_bestseller': rating and rating >= 4.4,
            'features': features,
            'categories': self._generate_categories(row),
            'specifications': self._generate_specifications(row)
        }
        
        # Add platform data (Amazon)
        product_data['platforms'] = [{
            'platform_id': 1,  # Amazon platform ID
            'platform_sku': asin,
            'platform_url': f"https://amazon.com/dp/{asin}",
            'platform_price': price,
            'platform_availability': row.get('availability', 'In Stock'),
            'platform_rating': rating,
            'platform_review_count': review_count,
            'platform_specific_data': {
                'is_prime': True,
                'best_seller_rank': 1000 if rating and rating >= 4.4 else None,
                'free_shipping': True,
                'sold_by': row.get('sold_by', ''),
                'ships_from': row.get('ships_from', '')
            },
            'is_primary': True
        }]
        
        # Add affiliate links (use actual referral links from CSV)
        affiliate_links = []
        
        # Use the actual referral link from CSV if available
        referral_link = row.get('referral_link', '').strip()
        if referral_link:
            affiliate_links.append({
                'platform_id': 1,  # Amazon platform ID
                'link_type': 'web',
                'affiliate_url': referral_link,
                'commission_rate': 0.04,  # 4% Amazon commission
                'estimated_commission': price * 0.04 if price else 0
            })
        elif asin:
            # Fallback to generated affiliate URL
            affiliate_url = f"https://amazon.com/dp/{asin}?tag=homeprinciple-20"
            affiliate_links.append({
                'platform_id': 1,  # Amazon platform ID
                'link_type': 'web',
                'affiliate_url': affiliate_url,
                'commission_rate': 0.04,  # 4% Amazon commission
                'estimated_commission': price * 0.04 if price else 0
            })
        
        if affiliate_links:
            product_data['affiliate_links'] = affiliate_links
        
        return product_data
    
    def _extract_price_for_size(self, row: Dict[str, str], size_selected: str) -> Optional[float]:
        """Extract price based on selected size"""
        price_fields = {
            'King': 'price_king',
            'Twin': 'price_twin', 
            'Queen': 'price_queen',
            'Cal King': 'price_cal_king',
            '5 Pack - Split King': 'price_twin'  # Use twin price for split king
        }
        
        # Try to get price for selected size
        if size_selected in price_fields:
            price_str = row.get(price_fields[size_selected], '')
            if price_str:
                return self._extract_price(price_str)
        
        # Fallback to king price
        king_price = row.get('price_king', '')
        if king_price:
            return self._extract_price(king_price)
        
        # Fallback to any available price
        for price_field in ['price_king', 'price_queen', 'price_twin', 'price_cal_king']:
            price_str = row.get(price_field, '')
            if price_str:
                return self._extract_price(price_str)
        
        return None
    
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
        """Extract rating from string"""
        if not rating_str:
            return None
        
        try:
            return float(rating_str)
        except ValueError:
            return None
    
    def _extract_review_count(self, review_count_str: str) -> int:
        """Extract review count from string"""
        if not review_count_str:
            return 0
        
        try:
            return int(review_count_str)
        except ValueError:
            return 0
    
    def _extract_features(self, features_str: str) -> List[Dict[str, str]]:
        """Extract features from string"""
        if not features_str:
            return []
        
        features = []
        feature_list = [f.strip() for f in features_str.split(';')]
        
        for feature in feature_list:
            if feature:
                features.append({
                    'text': feature,
                    'type': 'general'
                })
        
        return features
    
    def _extract_color(self, color_str: str) -> str:
        """Extract color from string"""
        if not color_str:
            return 'White'
        
        # Remove number prefix (e.g., "01 - White" -> "White")
        color = re.sub(r'^\d+\s*-\s*', '', color_str)
        return color.strip() or 'White'
    
    def _extract_weight(self, weight_str: str) -> Optional[float]:
        """Extract weight from string"""
        if not weight_str:
            return None
        
        # Extract number from weight string (e.g., "5.5 lb" -> 5.5)
        weight_match = re.search(r'[\d,]+\.?\d*', weight_str.replace(',', ''))
        if weight_match:
            try:
                return float(weight_match.group())
            except ValueError:
                pass
        
        return None
    
    def _extract_dimensions(self, dimensions_str: str) -> Dict[str, Any]:
        """Extract dimensions from string"""
        if not dimensions_str:
            return {}
        
        # Simple parsing for dimensions like "11x9x5 in" or "80"L x 39"W"
        dimensions = {}
        
        # Try to extract LxWxH format
        dim_match = re.search(r'(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)\s*[xX]\s*(\d+(?:\.\d+)?)', dimensions_str)
        if dim_match:
            dimensions = {
                'length': float(dim_match.group(1)),
                'width': float(dim_match.group(2)),
                'height': float(dim_match.group(3))
            }
        else:
            # Try to extract LxW format
            dim_match = re.search(r'(\d+(?:\.\d+)?)"?\s*[xX]\s*(\d+(?:\.\d+)?)"?', dimensions_str)
            if dim_match:
                dimensions = {
                    'length': float(dim_match.group(1)),
                    'width': float(dim_match.group(2)),
                    'height': 2.0  # Default height for sheets
                }
        
        return dimensions
    
    def _generate_tags(self, row: Dict[str, str]) -> List[str]:
        """Generate tags from row data"""
        tags = ['bed-sheets', 'home-garden']
        
        # Add material tags
        material = row.get('material', '').lower()
        if 'bamboo' in material:
            tags.append('bamboo')
        if 'cotton' in material:
            tags.append('cotton')
        if 'flannel' in material:
            tags.append('flannel')
        if 'viscose' in material:
            tags.append('viscose')
        
        # Add size tags
        size = row.get('size_selected', '').lower()
        if 'king' in size:
            tags.append('king-size')
        if 'queen' in size:
            tags.append('queen-size')
        if 'twin' in size:
            tags.append('twin-size')
        
        # Add pattern/style tags
        pattern = row.get('pattern', '').lower()
        if pattern:
            tags.append(pattern.replace(' ', '-'))
        
        return tags
    
    def _generate_categories(self, row: Dict[str, str]) -> List[str]:
        """Generate categories from row data"""
        categories = ['Bed Sheets', 'Home & Garden']
        
        material = row.get('material', '').lower()
        if 'bamboo' in material:
            categories.append('Bamboo Sheets')
        if 'cotton' in material:
            categories.append('Cotton Sheets')
        if 'flannel' in material:
            categories.append('Flannel Sheets')
        
        return categories
    
    def _generate_specifications(self, row: Dict[str, str]) -> Dict[str, str]:
        """Generate specifications from row data"""
        specs = {}
        
        if row.get('thread_count'):
            specs['Thread Count'] = row['thread_count']
        
        if row.get('material'):
            specs['Material'] = row['material']
        
        if row.get('pocket_depth'):
            specs['Pocket Depth'] = row['pocket_depth']
        
        if row.get('unit_count'):
            specs['Unit Count'] = row['unit_count']
        
        if row.get('included_components'):
            specs['Included Components'] = row['included_components']
        
        if row.get('pillowcases'):
            specs['Pillowcases'] = row['pillowcases']
        
        if row.get('fit'):
            specs['Fit'] = row['fit']
        
        return specs
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        if not title:
            return ""
        
        slug = title.lower()
        slug = re.sub(r'[^a-z0-9\s-]', '', slug)
        slug = re.sub(r'\s+', '-', slug)
        slug = re.sub(r'-+', '-', slug)
        return slug.strip('-')[:100]  # Limit length

def main():
    """Main function"""
    populator = ThreeRowsPopulator()
    
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
        populator.populate_from_csv(csv_file)
    else:
        populator.populate_from_csv()

if __name__ == "__main__":
    main()
