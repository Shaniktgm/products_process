#!/usr/bin/env python3
"""
Mock data generator for dental products
Creates realistic product data for testing and development
"""

import random
import sqlite3
from datetime import datetime, timedelta
from typing import List, Dict, Any

class MockDataGenerator:
    """Generate realistic mock data for dental products"""
    
    def __init__(self):
        """Initialize the mock data generator"""
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
            "ADA approved", "Vegan", "Cruelty-free", "Gluten-free"
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
            "premium", "fast-acting", "long-lasting", "gentle", "effective"
        ]
    
    def generate_product(self, index: int) -> Dict[str, Any]:
        """Generate a single mock product"""
        # Generate realistic ASIN
        asin = f"B{random.randint(1000000000, 9999999999)}"
        
        # Select category and generate appropriate title
        category = random.choice(self.categories)
        brand = random.choice(self.brands)
        
        title = self._generate_title(category, brand)
        
        # Generate realistic price range based on category
        base_price = self._get_base_price(category)
        price_variation = random.uniform(0.7, 1.3)
        price = round(base_price * price_variation, 2)
        
        # Sometimes add original price for "discounts"
        original_price = None
        if random.random() < 0.3:  # 30% chance of having a discount
            original_price = round(price * random.uniform(1.1, 1.4), 2)
        
        # Generate rating and review count
        rating = round(random.uniform(3.5, 5.0), 1)
        review_count = random.randint(50, 5000)
        
        # Generate features
        num_features = random.randint(3, 8)
        product_features = random.sample(self.features, min(num_features, len(self.features)))
        
        # Generate categories
        product_categories = [category]
        if random.random() < 0.4:  # 40% chance of additional category
            additional_category = random.choice([c for c in self.categories if c != category])
            product_categories.append(additional_category)
        
        # Generate tags
        num_tags = random.randint(4, 8)
        product_tags = random.sample(self.tags, min(num_tags, len(self.tags)))
        product_tags.extend([category, brand.lower().replace(' ', '-')])
        
        # Generate image URL (using placeholder service)
        image_url = f"https://via.placeholder.com/300x300/4A90E2/FFFFFF?text={category.replace(' ', '+')}"
        
        # Generate affiliate link
        partner_tag = "homeprinciple-20"
        affiliate_link = f"https://www.amazon.com/dp/{asin}?tag={partner_tag}"
        
        # Generate timestamps
        now = datetime.now()
        search_timestamp = (now - timedelta(days=random.randint(0, 30))).isoformat()
        fetch_timestamp = now.isoformat()
        
        return {
            'asin': asin,
            'title': title,
            'brand': brand,
            'description': f"Professional {category} for optimal oral health. {random.choice(product_features)}.",
            'price': price,
            'original_price': original_price,
            'rating': rating,
            'review_count': review_count,
            'image_url': image_url,
            'availability': random.choice(self.availability),
            'condition': random.choice(self.conditions),
            'is_prime': random.choice([True, True, True, False]),  # 75% Prime eligible
            'affiliate_link': affiliate_link,
            'upc': f"{random.randint(100000000000, 999999999999)}",
            'isbn': '',
            'search_timestamp': search_timestamp,
            'fetch_timestamp': fetch_timestamp,
            'features': product_features,
            'categories': product_categories,
            'tags': list(set(product_tags))  # Remove duplicates
        }
    
    def _generate_title(self, category: str, brand: str) -> str:
        """Generate realistic product titles"""
        if category == "toothpaste":
            variants = [
                "Toothpaste", "Whitening Toothpaste", "Sensitive Toothpaste", 
                "Fresh Breath Toothpaste", "Anti-Cavity Toothpaste", "Natural Toothpaste"
            ]
            size_variants = ["4.6 oz", "6.4 oz", "8.2 oz", "Family Size"]
            return f"{brand} {random.choice(variants)}, {random.choice(size_variants)}"
            
        elif category == "toothbrush":
            variants = [
                "Electric Toothbrush", "Manual Toothbrush", "Soft Bristle Toothbrush",
                "Medium Bristle Toothbrush", "Travel Toothbrush", "Kids Toothbrush"
            ]
            return f"{brand} {random.choice(variants)}"
            
        elif category == "mouthwash":
            variants = [
                "Antiseptic Mouthwash", "Fresh Breath Mouthwash", "Whitening Mouthwash",
                "Sensitive Mouthwash", "Alcohol-Free Mouthwash", "Therapeutic Mouthwash"
            ]
            size_variants = ["16 oz", "32 oz", "1 Liter"]
            return f"{brand} {random.choice(variants)}, {random.choice(size_variants)}"
            
        elif category == "dental floss":
            variants = [
                "Waxed Dental Floss", "Unwaxed Dental Floss", "Mint Dental Floss",
                "Flavored Dental Floss", "Glide Dental Floss", "Tape Dental Floss"
            ]
            size_variants = ["55 yards", "100 yards", "200 yards"]
            return f"{brand} {random.choice(variants)}, {random.choice(size_variants)}"
            
        elif category == "teeth whitening":
            variants = [
                "Whitening Strips", "Whitening Gel", "Whitening Pen", 
                "Whitening Rinse", "Professional Whitening Kit", "LED Whitening Device"
            ]
            return f"{brand} {random.choice(variants)}"
            
        else:
            return f"{brand} {category.title()}"
    
    def _get_base_price(self, category: str) -> float:
        """Get base price for different categories"""
        price_ranges = {
            "toothpaste": (3.0, 8.0),
            "toothbrush": (2.0, 15.0),
            "mouthwash": (4.0, 12.0),
            "dental floss": (2.0, 8.0),
            "oral probiotics": (15.0, 35.0),
            "teeth whitening": (20.0, 80.0),
            "bad breath": (8.0, 25.0),
            "gum health": (8.0, 25.0),
            "sensitive teeth": (6.0, 20.0),
            "dental tools": (5.0, 30.0),
            "oral care kits": (15.0, 50.0),
            "tongue cleaners": (3.0, 12.0)
        }
        
        min_price, max_price = price_ranges.get(category, (5.0, 15.0))
        return random.uniform(min_price, max_price)
    
    def generate_products(self, count: int) -> List[Dict[str, Any]]:
        """Generate multiple mock products"""
        print(f"🔧 Generating {count} mock dental products...")
        
        products = []
        for i in range(count):
            if i % 100 == 0:
                print(f"   Generated {i}/{count} products...")
            products.append(self.generate_product(i))
        
        print(f"✅ Generated {len(products)} mock products")
        return products

def main():
    """Main function to generate and display sample products"""
    generator = MockDataGenerator()
    
    # Generate 10 sample products to show
    sample_products = generator.generate_products(10)
    
    print("\n📋 Sample Generated Products:")
    print("=" * 50)
    
    for i, product in enumerate(sample_products, 1):
        print(f"\n{i}. {product['title']}")
        print(f"   Brand: {product['brand']}")
        print(f"   Price: ${product['price']}")
        if product['original_price']:
            print(f"   Original: ${product['original_price']} (Save ${product['original_price'] - product['price']:.2f})")
        print(f"   Rating: {product['rating']} ⭐ ({product['review_count']} reviews)")
        print(f"   Category: {', '.join(product['categories'])}")
        print(f"   Features: {', '.join(product['features'][:3])}...")
        print(f"   Tags: {', '.join(product['tags'][:5])}...")
    
    print(f"\n🎉 Successfully generated {len(sample_products)} sample products!")
    print("\n📖 To generate more products and populate database:")
    print("   python3 populate_mock_database.py")

if __name__ == "__main__":
    main()
