#!/usr/bin/env python3
"""
Migration script to convert existing Amazon-focused database to multi-platform schema
"""

import sys
import os
import sqlite3
import json
from datetime import datetime
from typing import List, Dict, Any

# Add current directory to path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from multi_platform_database import MultiPlatformDatabaseService, PlatformType

class DatabaseMigrator:
    """Migrate existing databases to multi-platform schema"""
    
    def __init__(self):
        self.multi_db = MultiPlatformDatabaseService("migrated_products.db")
    
    def migrate_amazon_products_db(self, source_db_path: str = "amazon_products.db"):
        """Migrate from amazon_products.db to multi-platform schema"""
        print("🚀 Migrating Amazon Products Database")
        print("=" * 50)
        
        try:
            with sqlite3.connect(source_db_path) as source_conn:
                source_conn.row_factory = sqlite3.Row
                source_cursor = source_conn.cursor()
                
                # Get all products from source
                source_cursor.execute('SELECT * FROM products')
                products = source_cursor.fetchall()
                
                print(f"Found {len(products)} products to migrate")
                
                migrated_count = 0
                
                for product in products:
                    try:
                        # Convert to multi-platform format
                        product_data = self._convert_amazon_product(product, source_cursor)
                        
                        # Insert into multi-platform database
                        product_id = self.multi_db.insert_product(product_data)
                        
                        if product_id:
                            migrated_count += 1
                        
                        if migrated_count % 50 == 0:
                            print(f"   Progress: {migrated_count}/{len(products)} products migrated")
                    
                    except Exception as e:
                        print(f"   ❌ Error migrating product {product.get('asin', 'Unknown')}: {str(e)}")
                        continue
                
                print(f"\n✅ Successfully migrated {migrated_count}/{len(products)} products")
                
                # Show statistics
                stats = self.multi_db.get_database_stats()
                print("\n📊 Migration Statistics:")
                for key, value in stats.items():
                    if key == 'platform_breakdown':
                        print(f"   {key}:")
                        for platform in value:
                            print(f"     - {platform['display_name']}: {platform['product_count']} products")
                    else:
                        print(f"   {key}: {value}")
        
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")
    
    def migrate_enhanced_products_db(self, source_db_path: str = "enhanced_products.db"):
        """Migrate from enhanced_products.db to multi-platform schema"""
        print("🚀 Migrating Enhanced Products Database")
        print("=" * 50)
        
        try:
            with sqlite3.connect(source_db_path) as source_conn:
                source_conn.row_factory = sqlite3.Row
                source_cursor = source_conn.cursor()
                
                # Get all products from source
                source_cursor.execute('SELECT * FROM products')
                products = source_cursor.fetchall()
                
                print(f"Found {len(products)} products to migrate")
                
                migrated_count = 0
                
                for product in products:
                    try:
                        # Convert to multi-platform format
                        product_data = self._convert_enhanced_product(product, source_cursor)
                        
                        # Insert into multi-platform database
                        product_id = self.multi_db.insert_product(product_data)
                        
                        if product_id:
                            migrated_count += 1
                        
                        if migrated_count % 50 == 0:
                            print(f"   Progress: {migrated_count}/{len(products)} products migrated")
                    
                    except Exception as e:
                        print(f"   ❌ Error migrating product {product.get('asin', 'Unknown')}: {str(e)}")
                        continue
                
                print(f"\n✅ Successfully migrated {migrated_count}/{len(products)} products")
                
                # Show statistics
                stats = self.multi_db.get_database_stats()
                print("\n📊 Migration Statistics:")
                for key, value in stats.items():
                    if key == 'platform_breakdown':
                        print(f"   {key}:")
                        for platform in value:
                            print(f"     - {platform['display_name']}: {platform['product_count']} products")
                    else:
                        print(f"   {key}: {value}")
        
        except Exception as e:
            print(f"❌ Migration error: {str(e)}")
    
    def _convert_amazon_product(self, product: sqlite3.Row, cursor) -> Dict[str, Any]:
        """Convert Amazon product to multi-platform format"""
        
        # Get related data
        features = self._get_features(cursor, product['id'])
        categories = self._get_categories(cursor, product['id'])
        tags = self._get_tags(cursor, product['id'])
        
        # Generate slug from title
        slug = self._generate_slug(product['title'])
        
        # Create product data
        product_data = {
            'sku': f"AMZ-{product['asin']}",  # Amazon-specific SKU
            'title': product['title'],
            'brand': product['brand'],
            'description': product['description'],
            'slug': slug,
            'price': product['price'],
            'original_price': product['original_price'],
            'discount_percentage': product.get('discount_percentage'),
            'currency': 'USD',
            'rating': product['rating'],
            'review_count': product['review_count'],
            'primary_image_url': product['image_url'],
            'image_urls': [product['image_url']] if product['image_url'] else [],
            'availability': product['availability'],
            'stock_status': product.get('stock_status'),
            'condition': product['condition'],
            'warranty': product.get('warranty'),
            'return_policy': product.get('return_policy'),
            'age_recommendation': product.get('age_recommendation'),
            'ingredients': product.get('ingredients'),
            'weight': product.get('shipping_weight'),
            'dimensions': self._parse_dimensions(product.get('package_dimensions')),
            'tags': tags,
            'deal_badges': self._parse_deal_badges(product.get('deal_badges')),
            'is_active': True,
            'is_bestseller': product.get('best_seller_rank', 0) > 0,
            'features': features,
            'categories': categories
        }
        
        # Add Amazon platform data
        product_data['platforms'] = [{
            'platform_id': 1,  # Amazon platform ID
            'platform_sku': product['asin'],
            'platform_url': product['affiliate_link'],
            'platform_price': product['price'],
            'platform_availability': product['availability'],
            'platform_rating': product['rating'],
            'platform_review_count': product['review_count'],
            'platform_specific_data': {
                'is_prime': product.get('is_prime', False),
                'best_seller_rank': product.get('best_seller_rank'),
                'upc': product.get('upc'),
                'isbn': product.get('isbn'),
                'free_shipping': product.get('free_shipping', False)
            },
            'is_primary': True
        }]
        
        # Add affiliate links
        product_data['affiliate_links'] = [{
            'platform_id': 1,  # Amazon platform ID
            'link_type': 'web',
            'affiliate_url': product['affiliate_link'],
            'commission_rate': product.get('commission_rate'),
            'estimated_commission': product.get('estimated_commission')
        }]
        
        return product_data
    
    def _convert_enhanced_product(self, product: sqlite3.Row, cursor) -> Dict[str, Any]:
        """Convert enhanced product to multi-platform format"""
        
        # Get related data
        features = self._get_features(cursor, product['id'])
        categories = self._get_categories(cursor, product['id'])
        tags = self._get_tags(cursor, product['id'])
        
        # Generate slug from title
        slug = self._generate_slug(product['title'])
        
        # Create product data
        product_data = {
            'sku': f"AMZ-{product['asin']}",  # Amazon-specific SKU
            'title': product['title'],
            'brand': product['brand'],
            'description': product['description'],
            'slug': slug,
            'price': product['price'],
            'original_price': product['original_price'],
            'discount_percentage': product.get('discount_percentage'),
            'currency': 'USD',
            'rating': product['rating'],
            'review_count': product['review_count'],
            'primary_image_url': product['image_url'],
            'image_urls': [product['image_url']] if product['image_url'] else [],
            'availability': product['availability'],
            'stock_status': product.get('stock_status'),
            'condition': product['condition'],
            'warranty': product.get('warranty'),
            'return_policy': product.get('return_policy'),
            'age_recommendation': product.get('age_recommendation'),
            'ingredients': product.get('ingredients'),
            'weight': product.get('shipping_weight'),
            'dimensions': self._parse_dimensions(product.get('package_dimensions')),
            'tags': tags,
            'deal_badges': self._parse_deal_badges(product.get('deal_badges')),
            'is_active': True,
            'is_bestseller': product.get('best_seller_rank', 0) > 0,
            'features': features,
            'categories': categories
        }
        
        # Add specifications from enhanced fields
        specifications = {}
        enhanced_fields = [
            'material', 'softness', 'breathability', 'thread_count', 'durability',
            'size_options', 'care_instructions', 'color_pattern_options', 'weave_type',
            'hypoallergenic_properties', 'eco_friendliness', 'brand_reputation'
        ]
        
        for field in enhanced_fields:
            if product.get(field):
                specifications[field.replace('_', ' ').title()] = product[field]
        
        if specifications:
            product_data['specifications'] = specifications
        
        # Add Amazon platform data
        product_data['platforms'] = [{
            'platform_id': 1,  # Amazon platform ID
            'platform_sku': product['asin'],
            'platform_url': product['affiliate_link'],
            'platform_price': product['price'],
            'platform_availability': product['availability'],
            'platform_rating': product['rating'],
            'platform_review_count': product['review_count'],
            'platform_specific_data': {
                'is_prime': product.get('is_prime', False),
                'best_seller_rank': product.get('best_seller_rank'),
                'upc': product.get('upc'),
                'isbn': product.get('isbn'),
                'free_shipping': product.get('free_shipping', False)
            },
            'is_primary': True
        }]
        
        # Add affiliate links
        affiliate_links = []
        
        # Amazon affiliate link
        if product.get('affiliate_link'):
            affiliate_links.append({
                'platform_id': 1,  # Amazon platform ID
                'link_type': 'web',
                'affiliate_url': product['affiliate_link'],
                'commission_rate': product.get('commission_rate'),
                'estimated_commission': product.get('estimated_commission')
            })
        
        # D2C affiliate links if available
        if product.get('d2c_affiliation_link_web'):
            affiliate_links.append({
                'platform_id': 2,  # D2C platform ID
                'link_type': 'web',
                'affiliate_url': product['d2c_affiliation_link_web'],
                'commission_rate': 0.10  # Default D2C commission
            })
        
        if product.get('d2c_affiliation_link_mobile'):
            affiliate_links.append({
                'platform_id': 2,  # D2C platform ID
                'link_type': 'mobile',
                'affiliate_url': product['d2c_affiliation_link_mobile'],
                'commission_rate': 0.10  # Default D2C commission
            })
        
        if affiliate_links:
            product_data['affiliate_links'] = affiliate_links
        
        return product_data
    
    def _get_features(self, cursor, product_id: int) -> List[str]:
        """Get product features"""
        cursor.execute('SELECT feature_text FROM product_features WHERE product_id = ?', (product_id,))
        return [row[0] for row in cursor.fetchall()]
    
    def _get_categories(self, cursor, product_id: int) -> List[str]:
        """Get product categories"""
        cursor.execute('SELECT category_name FROM product_categories WHERE product_id = ?', (product_id,))
        return [row[0] for row in cursor.fetchall()]
    
    def _get_tags(self, cursor, product_id: int) -> List[str]:
        """Get product tags"""
        cursor.execute('SELECT tag FROM product_tags WHERE product_id = ?', (product_id,))
        return [row[0] for row in cursor.fetchall()]
    
    def _generate_slug(self, title: str) -> str:
        """Generate URL-friendly slug from title"""
        if not title:
            return ""
        
        # Simple slug generation
        slug = title.lower()
        slug = ''.join(c if c.isalnum() or c in '- ' else '' for c in slug)
        slug = '-'.join(slug.split())
        return slug[:100]  # Limit length
    
    def _parse_dimensions(self, dimensions_str: str) -> Dict[str, Any]:
        """Parse dimensions string to JSON"""
        if not dimensions_str:
            return {}
        
        # Simple parsing - you might want to improve this
        try:
            # Try to parse as JSON first
            return json.loads(dimensions_str)
        except:
            # Fallback to simple parsing
            return {"raw": dimensions_str}
    
    def _parse_deal_badges(self, badges_str: str) -> List[str]:
        """Parse deal badges string to list"""
        if not badges_str:
            return []
        
        if isinstance(badges_str, str):
            return [badge.strip() for badge in badges_str.split(',') if badge.strip()]
        
        return badges_str if isinstance(badges_str, list) else []

def main():
    """Main migration function"""
    migrator = DatabaseMigrator()
    
    if len(sys.argv) > 1:
        source_db = sys.argv[1]
        
        if source_db == "amazon_products.db":
            migrator.migrate_amazon_products_db()
        elif source_db == "enhanced_products.db":
            migrator.migrate_enhanced_products_db()
        else:
            print(f"❌ Unknown source database: {source_db}")
            print("Available options: amazon_products.db, enhanced_products.db")
    else:
        print("🚀 Migrating Both Databases to Multi-Platform Schema")
        print("=" * 60)
        
        # Migrate both databases
        print("\n1. Migrating Amazon Products Database...")
        migrator.migrate_amazon_products_db()
        
        print("\n2. Migrating Enhanced Products Database...")
        migrator.migrate_enhanced_products_db()
        
        print("\n🎉 Migration completed!")
        print("New multi-platform database: migrated_products.db")

if __name__ == "__main__":
    main()
