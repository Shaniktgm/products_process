#!/usr/bin/env python3
"""
Sample data generator for multi-platform product catalog
Demonstrates how to add products from different platforms
"""

import sys
import os
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService

class MultiPlatformSampleDataGenerator:
    """Generate sample data for multi-platform product catalog"""
    
    def __init__(self):
        self.db = MultiPlatformDatabaseService("sample_multi_platform.db")
    
    def generate_sample_products(self, count: int = 50):
        """Generate sample products from different platforms"""
        print("🚀 Generating Multi-Platform Sample Products")
        print("=" * 50)
        
        # Sample product templates
        amazon_products = self._get_amazon_product_templates()
        d2c_products = self._get_d2c_product_templates()
        walmart_products = self._get_walmart_product_templates()
        etsy_products = self._get_etsy_product_templates()
        
        all_templates = amazon_products + d2c_products + walmart_products + etsy_products
        
        success_count = 0
        
        for i in range(count):
            try:
                # Select random template
                template = all_templates[i % len(all_templates)]
                
                # Generate product data
                product_data = self._generate_product_from_template(template, i)
                
                # Insert into database
                product_id = self.db.insert_product(product_data)
                
                if product_id:
                    success_count += 1
                
                if (i + 1) % 10 == 0:
                    print(f"   Progress: {i + 1}/{count} products generated ({success_count} successful)")
            
            except Exception as e:
                print(f"   ❌ Error generating product {i + 1}: {str(e)}")
                continue
        
        print(f"\n✅ Successfully generated {success_count}/{count} products")
        
        # Show statistics
        stats = self.db.get_database_stats()
        print("\n📊 Sample Database Statistics:")
        for key, value in stats.items():
            if key == 'platform_breakdown':
                print(f"   {key}:")
                for platform in value:
                    print(f"     - {platform['display_name']}: {platform['product_count']} products")
            else:
                print(f"   {key}: {value}")
    
    def _get_amazon_product_templates(self) -> List[Dict[str, Any]]:
        """Amazon product templates"""
        return [
            {
                'platform': 'amazon',
                'category': 'Electronics',
                'brands': ['Apple', 'Samsung', 'Sony', 'Bose', 'Anker'],
                'products': [
                    'Wireless Bluetooth Headphones',
                    'Smartphone Case with Wireless Charging',
                    'Portable Bluetooth Speaker',
                    'USB-C Fast Charging Cable',
                    'Wireless Charging Pad'
                ],
                'features': [
                    'Fast charging capability',
                    'Wireless connectivity',
                    'Premium build quality',
                    'Long battery life',
                    'Noise cancellation'
                ],
                'price_range': (29.99, 299.99),
                'rating_range': (4.0, 4.8),
                'review_count_range': (100, 50000)
            },
            {
                'platform': 'amazon',
                'category': 'Home & Kitchen',
                'brands': ['Instant Pot', 'Ninja', 'KitchenAid', 'Cuisinart', 'Hamilton Beach'],
                'products': [
                    'Multi-Cooker Pressure Cooker',
                    'High-Speed Blender',
                    'Stand Mixer with Attachments',
                    'Coffee Maker with Grinder',
                    'Air Fryer with Digital Display'
                ],
                'features': [
                    'Multiple cooking functions',
                    'Easy-to-use digital controls',
                    'Dishwasher safe components',
                    'Energy efficient',
                    'Compact design'
                ],
                'price_range': (49.99, 399.99),
                'rating_range': (4.1, 4.7),
                'review_count_range': (500, 25000)
            }
        ]
    
    def _get_d2c_product_templates(self) -> List[Dict[str, Any]]:
        """Direct-to-Consumer product templates"""
        return [
            {
                'platform': 'd2c',
                'category': 'Health & Wellness',
                'brands': ['Glossier', 'Allbirds', 'Warby Parker', 'Casper', 'Outdoor Voices'],
                'products': [
                    'Natural Skincare Set',
                    'Sustainable Running Shoes',
                    'Prescription Eyeglasses',
                    'Memory Foam Mattress',
                    'Athletic Wear Collection'
                ],
                'features': [
                    'Sustainable materials',
                    'Direct-to-consumer pricing',
                    'Premium quality',
                    'Ethical manufacturing',
                    'Personalized experience'
                ],
                'price_range': (39.99, 899.99),
                'rating_range': (4.2, 4.9),
                'review_count_range': (50, 5000)
            },
            {
                'platform': 'd2c',
                'category': 'Fashion & Accessories',
                'brands': ['Everlane', 'Reformation', 'Away', 'Allbirds', 'Glossier'],
                'products': [
                    'Minimalist Handbag',
                    'Sustainable Denim Jeans',
                    'Hard-shell Luggage',
                    'Comfortable Sneakers',
                    'Clean Beauty Kit'
                ],
                'features': [
                    'Transparent pricing',
                    'Sustainable practices',
                    'High-quality materials',
                    'Modern design',
                    'Social responsibility'
                ],
                'price_range': (79.99, 599.99),
                'rating_range': (4.0, 4.8),
                'review_count_range': (25, 2000)
            }
        ]
    
    def _get_walmart_product_templates(self) -> List[Dict[str, Any]]:
        """Walmart product templates"""
        return [
            {
                'platform': 'walmart',
                'category': 'Grocery & Household',
                'brands': ['Great Value', 'Equate', 'Mainstays', 'Better Homes & Gardens', 'Ozark Trail'],
                'products': [
                    'Organic Whole Wheat Bread',
                    'Multi-Purpose Cleaner',
                    'Storage Containers Set',
                    'Outdoor Camping Chair',
                    'Bed Sheet Set'
                ],
                'features': [
                    'Everyday low prices',
                    'Wide availability',
                    'Quality guarantee',
                    'Easy returns',
                    'Bulk options available'
                ],
                'price_range': (2.99, 89.99),
                'rating_range': (3.8, 4.5),
                'review_count_range': (200, 15000)
            }
        ]
    
    def _get_etsy_product_templates(self) -> List[Dict[str, Any]]:
        """Etsy product templates"""
        return [
            {
                'platform': 'etsy',
                'category': 'Handmade & Vintage',
                'brands': ['Handmade by Sarah', 'Vintage Finds Co', 'Artisan Crafts', 'Custom Creations', 'Local Artisan'],
                'products': [
                    'Handmade Ceramic Mug',
                    'Vintage Wooden Jewelry Box',
                    'Custom Engraved Cutting Board',
                    'Hand-knitted Scarf',
                    'Personalized Photo Frame'
                ],
                'features': [
                    'Handmade quality',
                    'Unique designs',
                    'Customizable options',
                    'Supporting small businesses',
                    'One-of-a-kind items'
                ],
                'price_range': (15.99, 199.99),
                'rating_range': (4.3, 5.0),
                'review_count_range': (5, 500)
            }
        ]
    
    def _generate_product_from_template(self, template: Dict[str, Any], index: int) -> Dict[str, Any]:
        """Generate product data from template"""
        import random
        
        # Select random values
        brand = random.choice(template['brands'])
        product_name = random.choice(template['products'])
        title = f"{brand} {product_name}"
        
        # Generate pricing
        price = round(random.uniform(*template['price_range']), 2)
        original_price = round(price * random.uniform(1.1, 1.5), 2)
        discount_percentage = int(((original_price - price) / original_price) * 100)
        
        # Generate ratings
        rating = round(random.uniform(*template['rating_range']), 1)
        review_count = random.randint(*template['review_count_range'])
        
        # Generate SKU
        sku = f"{template['platform'].upper()}-{index:06d}"
        
        # Generate slug
        slug = f"{brand.lower().replace(' ', '-')}-{product_name.lower().replace(' ', '-')}-{index}"
        
        # Platform-specific data
        platform_id = self._get_platform_id(template['platform'])
        
        product_data = {
            'sku': sku,
            'title': title,
            'brand': brand,
            'description': f"High-quality {product_name.lower()} from {brand}. {random.choice(template['features'])}.",
            'short_description': f"Premium {product_name.lower()} by {brand}",
            'slug': slug,
            'price': price,
            'original_price': original_price,
            'discount_percentage': discount_percentage,
            'currency': 'USD',
            'rating': rating,
            'review_count': review_count,
            'primary_image_url': f"https://example.com/images/{sku}.jpg",
            'image_urls': [
                f"https://example.com/images/{sku}-1.jpg",
                f"https://example.com/images/{sku}-2.jpg",
                f"https://example.com/images/{sku}-3.jpg"
            ],
            'availability': random.choice(['In Stock', 'Limited Stock', 'Pre-order']),
            'stock_status': random.choice(['Available', 'Low Stock', 'Out of Stock']),
            'stock_quantity': random.randint(0, 100),
            'condition': 'New',
            'warranty': random.choice(['1 Year', '2 Years', 'Limited Warranty', 'No Warranty']),
            'return_policy': random.choice(['30 Days', '60 Days', '90 Days', 'No Returns']),
            'weight': round(random.uniform(0.5, 10.0), 2),
            'dimensions': {
                'length': round(random.uniform(5, 20), 1),
                'width': round(random.uniform(3, 15), 1),
                'height': round(random.uniform(1, 8), 1)
            },
            'color': random.choice(['Black', 'White', 'Blue', 'Red', 'Green', 'Gray', 'Brown']),
            'material': random.choice(['Plastic', 'Metal', 'Wood', 'Fabric', 'Glass', 'Ceramic']),
            'size': random.choice(['Small', 'Medium', 'Large', 'One Size', 'XL']),
            'tags': [template['category'].lower(), template['platform'], brand.lower()],
            'deal_badges': random.sample(['Best Seller', 'New Arrival', 'Sale', 'Limited Time'], random.randint(0, 2)),
            'is_active': True,
            'is_featured': random.choice([True, False]),
            'is_bestseller': rating > 4.5 and review_count > 1000,
            'features': random.sample(template['features'], random.randint(2, 4)),
            'categories': [template['category']],
            'platforms': [{
                'platform_id': platform_id,
                'platform_sku': f"{template['platform'].upper()}{index:06d}",
                'platform_url': f"https://{template['platform']}.com/product/{sku}",
                'platform_price': price,
                'platform_availability': 'In Stock',
                'platform_rating': rating,
                'platform_review_count': review_count,
                'platform_specific_data': self._get_platform_specific_data(template['platform']),
                'is_primary': True
            }],
            'affiliate_links': [{
                'platform_id': platform_id,
                'link_type': 'web',
                'affiliate_url': f"https://{template['platform']}.com/affiliate/{sku}",
                'commission_rate': self._get_commission_rate(template['platform']),
                'estimated_commission': round(price * self._get_commission_rate(template['platform']), 2)
            }]
        }
        
        return product_data
    
    def _get_platform_id(self, platform_name: str) -> int:
        """Get platform ID by name"""
        platform_map = {
            'amazon': 1,
            'd2c': 2,
            'walmart': 3,
            'target': 4,
            'etsy': 5,
            'shopify': 6,
            'other': 7
        }
        return platform_map.get(platform_name, 7)
    
    def _get_commission_rate(self, platform_name: str) -> float:
        """Get commission rate by platform"""
        commission_map = {
            'amazon': 0.04,
            'd2c': 0.10,
            'walmart': 0.03,
            'target': 0.05,
            'etsy': 0.08,
            'shopify': 0.12,
            'other': 0.05
        }
        return commission_map.get(platform_name, 0.05)
    
    def _get_platform_specific_data(self, platform_name: str) -> Dict[str, Any]:
        """Get platform-specific data"""
        if platform_name == 'amazon':
            return {
                'is_prime': True,
                'best_seller_rank': 1234,
                'free_shipping': True
            }
        elif platform_name == 'd2c':
            return {
                'direct_shipping': True,
                'customization_available': True,
                'sustainability_score': 8.5
            }
        elif platform_name == 'walmart':
            return {
                'pickup_available': True,
                'walmart_plus_eligible': True
            }
        elif platform_name == 'etsy':
            return {
                'handmade': True,
                'vintage': False,
                'customizable': True
            }
        else:
            return {}

def main():
    """Main function"""
    generator = MultiPlatformSampleDataGenerator()
    
    if len(sys.argv) > 1:
        try:
            count = int(sys.argv[1])
            generator.generate_sample_products(count)
        except ValueError:
            print("❌ Please provide a valid number of products")
            print("Usage: python3 multi_platform_sample_data.py [number]")
    else:
        # Default: generate 50 sample products
        generator.generate_sample_products(50)

if __name__ == "__main__":
    main()
