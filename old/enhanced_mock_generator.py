#!/usr/bin/env python3
"""
Enhanced Mock Data Generator for Dental Products
Creates realistic product data optimized for affiliate marketing
"""

import random
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any

class EnhancedMockDataGenerator:
    """Generate enhanced mock data for dental products with affiliate marketing focus"""
    
    def __init__(self):
        """Initialize the enhanced mock data generator"""
        self.brands = [
            "Colgate", "Crest", "Oral-B", "Sensodyne", "Arm & Hammer", 
            "Tom's of Maine", "Hello", "Quip", "Philips", "Waterpik",
            "GUM", "Reach", "Plackers", "Glide", "Listerine",
            "ACT", "Biotene", "TheraBreath", "SmartMouth", "PerioBrite"
        ]
        
        self.categories = [
            "toothpaste", "toothbrush", "mouthwash", "dental floss", 
            "oral probiotics", "teeth whitening", "bad breath", "gum health",
            "sensitive teeth", "dental tools", "oral care kits", "tongue cleaners"
        ]
        
        self.features = [
            "Fluoride-free", "Whitening formula", "Sensitive teeth relief", 
            "Fresh breath", "Anti-cavity", "Anti-plaque", "Anti-gingivitis",
            "Natural ingredients", "BPA-free", "Recyclable packaging",
            "Long-lasting freshness", "Gentle on gums", "Removes surface stains",
            "Strengthens enamel", "Fights bad breath", "Soothes sensitive teeth",
            "Professional strength", "Clinically proven", "Dentist recommended",
            "ADA approved", "Vegan", "Cruelty-free", "Gluten-free",
            "Kills 99.9% of germs", "24-hour protection", "Fresh mint flavor",
            "Gentle whitening", "Advanced formula", "Pro-health benefits"
        ]
        
        self.conditions = [
            "New", "New", "New", "New", "New", "New", "New", "New", "New", "New",
            "Used - Like New", "Used - Good", "Used - Acceptable"
        ]
        
        self.availability = [
            "In Stock", "In Stock", "In Stock", "In Stock", "In Stock",
            "In Stock", "In Stock", "In Stock", "In Stock", "In Stock",
            "Limited Stock", "Usually ships in 2-3 days", "Back in stock soon"
        ]
        
        self.tags = [
            "dental", "oral-care", "hygiene", "health", "fresh-breath",
            "whitening", "sensitive", "natural", "organic", "professional",
            "travel-friendly", "family-size", "eco-friendly", "budget-friendly",
            "premium", "fast-acting", "long-lasting", "gentle", "effective",
            "best-seller", "amazon-choice", "prime-eligible", "top-rated"
        ]
        
        # Enhanced product images with realistic URLs
        self.product_images = {
            "toothpaste": [
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop",
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&sat=-50",
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&hue=180"
            ],
            "toothbrush": [
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&brightness=0.8",
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&contrast=1.2"
            ],
            "mouthwash": [
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&saturation=1.5"
            ],
            "dental floss": [
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&blur=1"
            ],
            "teeth whitening": [
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop&brightness=1.1"
            ],
            "default": [
                "https://images.unsplash.com/photo-1559591935-c6c92d7c2d8c?w=400&h=400&fit=crop"
            ]
        }
        
        # Commission rates (typical Amazon Associates rates)
        self.commission_rates = {
            "toothpaste": 0.04,      # 4% commission
            "toothbrush": 0.04,      # 4% commission
            "mouthwash": 0.04,       # 4% commission
            "dental floss": 0.04,    # 4% commission
            "oral probiotics": 0.06,  # 6% commission (health category)
            "teeth whitening": 0.06,  # 6% commission (health category)
            "bad breath": 0.04,      # 4% commission
            "gum health": 0.04,      # 4% commission
            "sensitive teeth": 0.04, # 4% commission
            "dental tools": 0.04,    # 4% commission
            "oral care kits": 0.05,  # 5% commission
            "tongue cleaners": 0.04  # 4% commission
        }
    
    def generate_enhanced_product(self, index: int) -> Dict[str, Any]:
        """Generate a single enhanced mock product"""
        # Generate realistic ASIN
        asin = f"B{random.randint(1000000000, 9999999999)}"
        
        # Select category and generate appropriate title
        category = random.choice(self.categories)
        brand = random.choice(self.brands)
        
        title = self._generate_enhanced_title(category, brand)
        
        # Generate realistic price range based on category
        base_price = self._get_enhanced_price(category)
        price_variation = random.uniform(0.8, 1.2)
        price = round(base_price * price_variation, 2)
        
        # Sometimes add original price for "discounts"
        original_price = None
        discount_percentage = 0
        if random.random() < 0.4:  # 40% chance of having a discount
            discount_percentage = random.randint(10, 35)
            original_price = round(price / (1 - discount_percentage/100), 2)
        
        # Generate rating and review count
        rating = round(random.uniform(3.8, 5.0), 1)
        review_count = random.randint(100, 8000)
        
        # Generate features
        num_features = random.randint(4, 10)
        product_features = random.sample(self.features, min(num_features, len(self.features)))
        
        # Generate categories
        product_categories = [category]
        if random.random() < 0.4:  # 40% chance of additional category
            additional_category = random.choice([c for c in self.categories if c != category])
            product_categories.append(additional_category)
        
        # Generate tags
        num_tags = random.randint(5, 10)
        product_tags = random.sample(self.tags, min(num_tags, len(self.tags)))
        product_tags.extend([category, brand.lower().replace(' ', '-')])
        
        # Generate enhanced image URL
        image_url = self._get_product_image(category)
        
        # Generate affiliate link with tracking
        partner_tag = "homeprinciple-20"
        affiliate_link = f"https://www.amazon.com/dp/{asin}?tag={partner_tag}&linkCode=ogi&language=en_US"
        
        # Calculate commission
        commission_rate = self.commission_rates.get(category, 0.04)
        estimated_commission = round(price * commission_rate, 2)
        
        # Generate enhanced description
        description = self._generate_enhanced_description(category, brand, product_features)
        
        # Generate timestamps
        now = datetime.now()
        search_timestamp = (now - timedelta(days=random.randint(0, 30))).isoformat()
        fetch_timestamp = now.isoformat()
        
        # Generate additional affiliate marketing data
        best_seller_rank = random.randint(1, 5000) if random.random() < 0.7 else None
        is_prime = random.choice([True, True, True, False])  # 75% Prime eligible
        free_shipping = random.choice([True, True, False])   # 67% free shipping
        
        return {
            'asin': asin,
            'title': title,
            'brand': brand,
            'description': description,
            'price': price,
            'original_price': original_price,
            'discount_percentage': discount_percentage,
            'rating': rating,
            'review_count': review_count,
            'image_url': image_url,
            'availability': random.choice(self.availability),
            'condition': random.choice(self.conditions),
            'is_prime': is_prime,
            'free_shipping': free_shipping,
            'affiliate_link': affiliate_link,
            'commission_rate': commission_rate,
            'estimated_commission': estimated_commission,
            'best_seller_rank': best_seller_rank,
            'upc': f"{random.randint(100000000000, 999999999999)}",
            'isbn': '',
            'search_timestamp': search_timestamp,
            'fetch_timestamp': fetch_timestamp,
            'features': product_features,
            'categories': product_categories,
            'tags': list(set(product_tags)),  # Remove duplicates
            'stock_status': 'In Stock' if random.random() < 0.9 else 'Limited Stock',
            'shipping_weight': round(random.uniform(0.1, 2.0), 2),
            'package_dimensions': f"{random.randint(2, 8)} x {random.randint(2, 8)} x {random.randint(1, 4)} inches",
            'warranty': '1 Year Limited Warranty' if random.random() < 0.6 else 'No Warranty',
            'return_policy': '30-Day Return Policy',
            'age_recommendation': self._get_age_recommendation(category),
            'ingredients': self._get_ingredients(category),
            'deal_badges': self._get_deal_badges(original_price, discount_percentage, best_seller_rank)
        }
    
    def _get_product_image(self, category: str) -> str:
        """Get a realistic product image URL"""
        if category in self.product_images:
            return random.choice(self.product_images[category])
        return random.choice(self.product_images["default"])
    
    def _generate_enhanced_title(self, category: str, brand: str) -> str:
        """Generate enhanced, realistic product titles"""
        if category == "toothpaste":
            variants = [
                "Advanced Whitening Toothpaste", "Pro-Relief Sensitive Toothpaste", 
                "Fresh Breath Anti-Cavity Toothpaste", "Natural Whitening Toothpaste",
                "Professional Strength Toothpaste", "Fresh Mint Anti-Plaque Toothpaste"
            ]
            size_variants = ["4.6 oz", "6.4 oz", "8.2 oz", "Family Size 12 oz"]
            return f"{brand} {random.choice(variants)}, {random.choice(size_variants)}"
            
        elif category == "toothbrush":
            variants = [
                "Smart Electric Toothbrush", "Professional Manual Toothbrush", 
                "Soft Bristle Sensitive Toothbrush", "Medium Bristle Deep Clean Toothbrush",
                "Travel Size Toothbrush", "Kids Electric Toothbrush with Timer"
            ]
            return f"{brand} {random.choice(variants)}"
            
        elif category == "mouthwash":
            variants = [
                "Antiseptic Mouthwash for Bad Breath", "Fresh Breath Whitening Mouthwash", 
                "Sensitive Teeth Alcohol-Free Mouthwash", "Therapeutic Gum Health Mouthwash",
                "Natural Fresh Breath Mouthwash", "Professional Strength Antiseptic"
            ]
            size_variants = ["16 oz", "32 oz", "1 Liter", "Travel Size 3 oz"]
            return f"{brand} {random.choice(variants)}, {random.choice(size_variants)}"
            
        elif category == "dental floss":
            variants = [
                "Waxed Dental Floss for Easy Gliding", "Mint Flavored Dental Floss", 
                "Glide Dental Floss Tape", "Unwaxed Natural Dental Floss",
                "Flavored Dental Floss Picks", "Professional Dental Floss"
            ]
            size_variants = ["55 yards", "100 yards", "200 yards", "300 yards"]
            return f"{brand} {random.choice(variants)}, {random.choice(size_variants)}"
            
        elif category == "teeth whitening":
            variants = [
                "Professional Whitening Strips", "LED Teeth Whitening Kit", 
                "Whitening Gel with Applicator", "Whitening Pen for Touch-Ups", 
                "Professional Whitening Rinse", "At-Home Whitening System"
            ]
            return f"{brand} {random.choice(variants)}"
            
        else:
            return f"{brand} Professional {category.title()}"
    
    def _get_enhanced_price(self, category: str) -> float:
        """Get enhanced price ranges for different categories"""
        price_ranges = {
            "toothpaste": (4.0, 12.0),
            "toothbrush": (3.0, 25.0),
            "mouthwash": (5.0, 18.0),
            "dental floss": (3.0, 15.0),
            "oral probiotics": (18.0, 45.0),
            "teeth whitening": (25.0, 120.0),
            "bad breath": (10.0, 35.0),
            "gum health": (10.0, 35.0),
            "sensitive teeth": (8.0, 25.0),
            "dental tools": (8.0, 40.0),
            "oral care kits": (20.0, 80.0),
            "tongue cleaners": (5.0, 20.0)
        }
        
        min_price, max_price = price_ranges.get(category, (8.0, 20.0))
        return random.uniform(min_price, max_price)
    
    def _generate_enhanced_description(self, category: str, brand: str, features: List[str]) -> str:
        """Generate enhanced product descriptions"""
        base_desc = f"Professional {category} from {brand} designed for optimal oral health. "
        
        feature_desc = "Features include " + ", ".join(features[:3]) + " for maximum effectiveness. "
        
        benefits = {
            "toothpaste": "This advanced formula helps remove surface stains, strengthen enamel, and provide long-lasting fresh breath.",
            "toothbrush": "Engineered with precision bristles for thorough cleaning and gentle care of your gums and teeth.",
            "mouthwash": "Provides powerful antiseptic protection while maintaining a refreshing taste for all-day confidence.",
            "dental floss": "Glides smoothly between teeth to remove plaque and food particles for complete oral hygiene.",
            "teeth whitening": "Professional-grade whitening technology that safely brightens your smile in the comfort of your home.",
            "default": "Clinically proven to improve oral health and maintain a healthy, beautiful smile."
        }
        
        benefit_desc = benefits.get(category, benefits["default"])
        
        return base_desc + feature_desc + benefit_desc
    
    def _get_age_recommendation(self, category: str) -> str:
        """Get age recommendations for products"""
        if category == "toothbrush" and random.random() < 0.3:
            return "Ages 3+"
        elif category in ["toothpaste", "mouthwash"] and random.random() < 0.2:
            return "Ages 6+"
        else:
            return "All Ages"
    
    def _get_ingredients(self, category: str) -> str:
        """Get ingredient information"""
        if category == "toothpaste":
            return "Active: Sodium Fluoride 0.24%, Inactive: Water, Sorbitol, Hydrated Silica, Glycerin, PEG-8, Sodium Lauryl Sulfate, Flavor, Cellulose Gum, Sodium Saccharin, Xanthan Gum, Sodium Benzoate, Carrageenan, Titanium Dioxide, Blue 1"
        elif category == "mouthwash":
            return "Active: Cetylpyridinium Chloride 0.05%, Inactive: Water, Alcohol 21.6%, Glycerin, Flavor, Poloxamer 407, Benzoic Acid, Sodium Saccharin, Blue 1"
        else:
            return "See package for complete ingredient list"
    
    def _get_deal_badges(self, original_price: float, discount_percentage: int, best_seller_rank: int) -> List[str]:
        """Generate deal badges for products"""
        badges = []
        
        if original_price and discount_percentage > 20:
            badges.append("Limited Time Deal")
        
        if discount_percentage > 15:
            badges.append("Save Big")
        
        if best_seller_rank and best_seller_rank < 100:
            badges.append("Best Seller")
        
        if random.random() < 0.3:
            badges.append("Amazon Choice")
        
        if random.random() < 0.2:
            badges.append("New Release")
        
        return badges
    
    def generate_enhanced_products(self, count: int) -> List[Dict[str, Any]]:
        """Generate multiple enhanced mock products"""
        print(f"🔧 Generating {count} enhanced mock dental products...")
        
        products = []
        for i in range(count):
            if i % 100 == 0:
                print(f"   Generated {i}/{count} products...")
            products.append(self.generate_enhanced_product(i))
        
        print(f"✅ Generated {len(products)} enhanced mock products")
        return products

def main():
    """Main function to generate and display sample enhanced products"""
    generator = EnhancedMockDataGenerator()
    
    # Generate 5 sample products to show
    sample_products = generator.generate_enhanced_products(5)
    
    print("\n📋 Sample Enhanced Products:")
    print("=" * 60)
    
    for i, product in enumerate(sample_products, 1):
        print(f"\n{i}. {product['title']}")
        print(f"   Brand: {product['brand']}")
        print(f"   Price: ${product['price']}")
        if product['original_price']:
            print(f"   Original: ${product['original_price']} (Save {product['discount_percentage']}%)")
        print(f"   Rating: {product['rating']} ⭐ ({product['review_count']} reviews)")
        print(f"   Commission: ${product['estimated_commission']} ({product['commission_rate']*100}%)")
        print(f"   Category: {', '.join(product['categories'])}")
        print(f"   Prime: {'✅' if product['is_prime'] else '❌'}")
        print(f"   Free Shipping: {'✅' if product['free_shipping'] else '❌'}")
        if product['best_seller_rank']:
            print(f"   Best Seller Rank: #{product['best_seller_rank']}")
        if product['deal_badges']:
            print(f"   Badges: {', '.join(product['deal_badges'])}")
        print(f"   Features: {', '.join(product['features'][:3])}...")
        print(f"   Tags: {', '.join(product['tags'][:5])}...")
    
    print(f"\n🎉 Successfully generated {len(sample_products)} enhanced sample products!")
    print("\n📖 To generate more enhanced products and update database:")
    print("   python3 update_database_enhanced.py")

if __name__ == "__main__":
    main()
