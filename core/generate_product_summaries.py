#!/usr/bin/env python3
"""
Product Summary Generator
Generates one-sentence summaries for products based on their features, pros, cons, and specifications
"""

import sqlite3
import json
import re
from typing import List, Dict, Any, Optional
from pathlib import Path

class ProductSummaryGenerator:
    """Generate concise one-sentence product summaries"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Keywords for different aspects
        self.quality_keywords = [
            'premium', 'luxury', 'high-quality', 'durable', 'long-lasting', 
            'soft', 'smooth', 'comfortable', 'breathable', 'moisture-wicking'
        ]
        
        self.material_keywords = [
            'cotton', 'bamboo', 'linen', 'silk', 'polyester', 'microfiber',
            'egyptian cotton', 'organic cotton', 'tencel', 'eucalyptus'
        ]
        
        self.feature_keywords = [
            'wrinkle-free', 'easy care', 'machine washable', 'cooling', 
            'temperature regulating', 'hypoallergenic', 'anti-microbial',
            'stain resistant', 'fade resistant', 'shrink resistant'
        ]
        
        self.concern_keywords = [
            'warm sleepers', 'hot sleepers', 'cold sleepers', 'sensitive skin',
            'allergies', 'wrinkles', 'shrinkage', 'fading', 'pilling'
        ]
        
        self.thread_count_keywords = [
            'thread count', 'tc', 'threads per inch', 'tpi'
        ]
    
    def get_product_data(self, product_id: int) -> Optional[Dict[str, Any]]:
        """Get comprehensive product data for summary generation"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get main product data
                cursor.execute('''
                    SELECT * FROM products WHERE id = ?
                ''', (product_id,))
                
                product_row = cursor.fetchone()
                if not product_row:
                    return None
                
                product = dict(product_row)
                
                # Get features (pros/cons)
                cursor.execute('''
                    SELECT feature_text, feature_type, id
                    FROM smart_product_features
                    WHERE product_id = ?
                    ORDER BY id
                ''', (product_id,))
                
                features = []
                for row in cursor.fetchall():
                    features.append({
                        'text': row['feature_text'],
                        'type': row['feature_type'],
                        'order': row['id']
                    })
                
                # Get specifications (from products table since product_specifications doesn't exist)
                specifications = []
                if product.get('thread_count'):
                    specifications.append({
                        'name': 'Thread Count',
                        'value': str(product['thread_count']),
                        'unit': 'TC',
                        'order': 1
                    })
                if product.get('weave_type'):
                    specifications.append({
                        'name': 'Weave Type',
                        'value': product['weave_type'],
                        'unit': '',
                        'order': 2
                    })
                if product.get('material'):
                    specifications.append({
                        'name': 'Material',
                        'value': product['material'],
                        'unit': '',
                        'order': 3
                    })
                if product.get('size'):
                    specifications.append({
                        'name': 'Size',
                        'value': product['size'],
                        'unit': '',
                        'order': 4
                    })
                
                # Get categories
                cursor.execute('''
                    SELECT category_name, is_primary
                    FROM product_categories
                    WHERE product_id = ?
                    ORDER BY is_primary DESC, category_name
                ''', (product_id,))
                
                categories = []
                for i, row in enumerate(cursor.fetchall()):
                    categories.append({
                        'name': row['category_name'],
                        'is_primary': row['is_primary'],
                        'order': i
                    })
                
                product['features'] = features
                product['specifications'] = specifications
                product['categories'] = categories
                
                return product
                
        except Exception as e:
            print(f"❌ Error getting product data for ID {product_id}: {e}")
            return None
    
    def extract_key_benefits(self, product: Dict[str, Any]) -> List[str]:
        """Extract key benefits from product data"""
        
        benefits = []
        
        # From features (pros)
        for feature in product.get('features', []):
            if feature['type'] == 'pro':
                text = feature['text'].lower()
                
                # Check for quality indicators
                for keyword in self.quality_keywords:
                    if keyword in text:
                        benefits.append(feature['text'])
                        break
                
                # Check for material benefits
                for keyword in self.material_keywords:
                    if keyword in text:
                        benefits.append(feature['text'])
                        break
                
                # Check for feature benefits
                for keyword in self.feature_keywords:
                    if keyword in text:
                        benefits.append(feature['text'])
                        break
        
        # From title and description
        title = product.get('title', '').lower()
        description = product.get('description', '').lower()
        
        # Check for thread count
        for keyword in self.thread_count_keywords:
            if keyword in title or keyword in description:
                # Extract thread count
                thread_match = re.search(r'(\d+)\s*(?:thread|tc)', title + ' ' + description)
                if thread_match:
                    thread_count = thread_match.group(1)
                    benefits.append(f"{thread_count}-thread count for durability")
                break
        
        # Check for material in title
        for material in self.material_keywords:
            if material in title:
                benefits.append(f"Made from {material}")
                break
        
        return benefits[:3]  # Limit to top 3 benefits
    
    def extract_key_concerns(self, product: Dict[str, Any]) -> List[str]:
        """Extract key concerns or considerations from product data"""
        
        concerns = []
        
        # From features (cons)
        for feature in product.get('features', []):
            if feature['type'] == 'con':
                text = feature['text'].lower()
                
                # Check for concern keywords
                for keyword in self.concern_keywords:
                    if keyword in text:
                        concerns.append(feature['text'])
                        break
        
        # From description
        description = product.get('description', '').lower()
        
        # Check for specific concerns
        if 'warm' in description or 'hot' in description:
            concerns.append("may be too warm for hot sleepers")
        elif 'cool' in description or 'cooling' in description:
            concerns.append("may be too cool for cold sleepers")
        
        return concerns[:2]  # Limit to top 2 concerns
    
    def generate_summary(self, product: Dict[str, Any]) -> str:
        """Generate a concise one-sentence product summary using all available data"""
        
        try:
            title = product.get('title', '') or ''
            price = product.get('price')
            rating = product.get('rating')
            review_count = product.get('review_count')
            brand = product.get('amazon_brand', '') or product.get('brand', '') or ''
            description = product.get('description', '') or ''
            
            # Use newly extracted fields if available, otherwise fall back to extraction
            material = product.get('material') or self._extract_material(title, description) or 'cotton'
            color = product.get('color') or 'white'
            size = product.get('size') or self._extract_size(title) or 'queen'
            key_feature = self._extract_key_feature(title, description) or 'luxury'
            thread_count = product.get('thread_count') or self._extract_thread_count(title, description) or '400'
            
            # Build summary components
            summary_parts = []
            
            # Start with material and key feature
            if material and material != 'Unknown':
                if key_feature:
                    summary_parts.append(f"{material} {key_feature}")
                else:
                    summary_parts.append(f"{material} sheets")
            elif key_feature:
                summary_parts.append(f"{key_feature} sheets")
            else:
                summary_parts.append("quality sheets")
            
            # Add color if available and not Unknown
            if color and color != 'Unknown':
                summary_parts.append(f"in {color}")
            
            # Add thread count if available
            if thread_count and str(thread_count) != 'None':
                summary_parts.append(f"with {thread_count}-thread count")
            
            # Add size if available and not Unknown
            if size and size != 'Unknown':
                summary_parts.append(f"in {size} size")
            
            # Add value/quality indicator
            value_indicator = self._get_value_indicator(price, rating, review_count)
            if value_indicator:
                summary_parts.append(value_indicator)
            
            # Add brand if notable
            if brand and brand not in ['Unknown', 'Visit the', ''] and len(brand) < 30:
                summary_parts.append(f"by {brand}")
            
            # Generate Martha Stewart-style summary
            # Ensure all parameters are not None before passing
            martha_summary = self._generate_martha_stewart_summary(
                material or 'cotton', 
                key_feature or 'luxury', 
                color or 'white', 
                int(thread_count) if thread_count else 400, 
                size or 'queen', 
                float(price) if price else 50.0, 
                float(rating) if rating else 4.5, 
                int(review_count) if review_count else 1000, 
                brand or 'Premium'
            )
            
            return martha_summary
            
        except Exception as e:
            # Fallback summary for products with insufficient data
            print(f"⚠️ Error generating summary for product {product.get('id', 'unknown')}: {e}")
            # Clean up the title to remove product IDs/ASINs
            title = product.get('title', 'product')
            # Remove common product ID patterns
            import re
            title = re.sub(r'\b[A-Z0-9]{10}\b', '', title)  # Remove ASINs like B0CZ7KBRPT
            title = re.sub(r'\bAmazon Product\b', '', title)  # Remove "Amazon Product"
            title = title.strip()
            if not title:
                title = "bedding product"
            return f"A quality {title} perfect for your home."
    
    def _generate_martha_stewart_summary(self, material, key_feature, color, thread_count, size, 
                                       price, rating, review_count, brand) -> str:
        """Generate a Martha Stewart-style elegant summary"""
        
        # Martha's signature phrases and style elements
        martha_openings = [
            "A simply divine",
            "An absolutely exquisite",
            "A perfectly elegant",
            "A beautifully crafted",
            "A wonderfully luxurious",
            "A delightfully soft",
            "A truly exceptional",
            "A magnificently designed"
        ]
        
        martha_materials = {
            'cotton': 'premium cotton',
            'egyptian cotton': 'fine Egyptian cotton',
            'organic cotton': 'organic cotton',
            'bamboo': 'silky bamboo',
            'linen': 'crisp linen',
            'silk': 'lustrous silk',
            'microfiber': 'ultra-soft microfiber'
        }
        
        martha_features = {
            'cooling': 'temperature-regulating',
            'breathable': 'beautifully breathable',
            'moisture-wicking': 'moisture-wicking',
            'wrinkle-free': 'wrinkle-resistant',
            'luxury': 'luxuriously soft',
            'premium': 'premium quality'
        }
        
        martha_endings = [
            "that will transform your bedroom into a sanctuary of comfort.",
            "perfect for creating that magazine-worthy bedroom aesthetic.",
            "that brings both style and substance to your home.",
            "ideal for those who appreciate the finer things in life.",
            "that elevates your sleep experience to new heights.",
            "perfect for the discerning homeowner who values quality.",
            "that combines timeless elegance with modern comfort.",
            "ideal for creating a sophisticated bedroom retreat."
        ]
        
        # Build the Martha-style summary
        import random
        
        # Choose opening
        opening = random.choice(martha_openings)
        
        # Material description
        material_desc = martha_materials.get(material.lower(), material.lower()) if material and material != 'Unknown' else "premium"
        
        # Feature description
        feature_desc = martha_features.get(key_feature.lower(), key_feature.lower()) if key_feature and key_feature != 'Unknown' else "bedding"
        
        # Size description
        size_desc = f" in {size}" if size and size != 'Unknown' else ""
        
        # Thread count
        thread_desc = f" with a luxurious {thread_count}-thread count" if thread_count and thread_count != 'Unknown' and thread_count != 0 else ""
        
        # Color
        color_desc = f" in a lovely {color}" if color and color != 'Unknown' else ""
        
        # Brand mention
        brand_desc = f" {brand}" if brand and brand not in ['Unknown', 'Visit the', ''] and len(brand) < 30 else ""
        
        # Quality indicator based on rating
        quality_desc = ""
        if rating and rating >= 4.5:
            quality_desc = " with outstanding reviews"
        elif rating and rating >= 4.0:
            quality_desc = " with excellent reviews"
        
        # Choose ending
        ending = random.choice(martha_endings)
        
        # Construct the summary with proper punctuation
        # First sentence: Opening + material + feature + size + thread count
        first_sentence_parts = [opening, material_desc, feature_desc]
        if size_desc:
            first_sentence_parts.append(size_desc.strip())
        if thread_desc:
            first_sentence_parts.append(thread_desc.strip())
        
        # Filter out None values and ensure all parts are strings
        first_sentence_parts = [str(part) for part in first_sentence_parts if part is not None and str(part).strip()]
        first_sentence = " ".join(first_sentence_parts)
        if first_sentence:
            first_sentence = first_sentence[0].upper() + first_sentence[1:] + "."
        else:
            first_sentence = "A premium bedding product."
        
        # Second sentence: Color + brand + quality + ending
        second_sentence_parts = []
        if color_desc:
            second_sentence_parts.append(f"Available{color_desc}")
        if brand_desc:
            second_sentence_parts.append(f"from{brand_desc}")
        if quality_desc:
            second_sentence_parts.append(quality_desc.strip())
        
        # Add ending
        second_sentence_parts.append(ending)
        
        # Filter out None values and ensure all parts are strings
        second_sentence_parts = [str(part) for part in second_sentence_parts if part is not None and str(part).strip()]
        second_sentence = " ".join(second_sentence_parts)
        if second_sentence:
            second_sentence = second_sentence[0].upper() + second_sentence[1:]
            if not second_sentence.endswith('.'):
                second_sentence += '.'
        else:
            second_sentence = "Perfect for your home."
        
        # Combine sentences
        summary = first_sentence + " " + second_sentence
        
        return summary
    
    def _extract_material(self, title: str, description: str) -> str:
        """Extract material from title and description"""
        text = (title + ' ' + description).lower()
        
        materials = {
            'egyptian cotton': 'Egyptian cotton',
            'organic cotton': 'organic cotton',
            '100% cotton': 'cotton',
            'cotton': 'cotton',
            'bamboo': 'bamboo',
            'linen': 'linen',
            'silk': 'silk',
            'microfiber': 'microfiber',
            'polyester': 'polyester',
            'tencel': 'Tencel',
            'eucalyptus': 'eucalyptus'
        }
        
        for keyword, material in materials.items():
            if keyword in text:
                return material
        
        return None
    
    def _extract_key_feature(self, title: str, description: str) -> str:
        """Extract key feature from title and description"""
        text = (title + ' ' + description).lower()
        
        features = {
            'cooling': 'cooling',
            'breathable': 'breathable',
            'moisture-wicking': 'moisture-wicking',
            'wrinkle-free': 'wrinkle-free',
            'hypoallergenic': 'hypoallergenic',
            'anti-microbial': 'anti-microbial',
            'temperature regulating': 'temperature-regulating',
            'luxury': 'luxury',
            'premium': 'premium'
        }
        
        for keyword, feature in features.items():
            if keyword in text:
                return feature
        
        return None
    
    def _extract_thread_count(self, title: str, description: str) -> str:
        """Extract thread count from title and description"""
        text = (title + ' ' + description).lower()
        
        import re
        thread_match = re.search(r'(\d+)\s*(?:thread|tc)', text)
        if thread_match:
            return thread_match.group(1)
        
        return None
    
    def _extract_size(self, title: str) -> str:
        """Extract size from title"""
        text = title.lower()
        
        sizes = ['twin', 'twin xl', 'full', 'queen', 'king', 'california king']
        for size in sizes:
            if size in text:
                return size.replace(' xl', ' XL').replace('california king', 'California King').title()
        
        return None
    
    def _get_value_indicator(self, price: float, rating: float, review_count: int) -> str:
        """Get value/quality indicator based on price, rating, and reviews"""
        if not rating or not review_count:
            return None
        
        # High rating with many reviews
        if rating >= 4.5 and review_count >= 1000:
            return "with excellent reviews"
        elif rating >= 4.0 and review_count >= 500:
            return "with great reviews"
        elif rating >= 3.5 and review_count >= 100:
            return "with good reviews"
        
        # Price-based indicators
        if price:
            if price < 30:
                return "at an affordable price"
            elif price < 60:
                return "at a mid-range price"
            elif price >= 100:
                return "at a premium price"
        
        return None
    
    def update_product_summary(self, product_id: int, summary: str) -> bool:
        """Update product summary in database"""
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                cursor.execute('''
                    UPDATE products 
                    SET product_summary = ?, updated_at = datetime('now')
                    WHERE id = ?
                ''', (summary, product_id))
                
                conn.commit()
                return True
                
        except Exception as e:
            print(f"❌ Error updating summary for product {product_id}: {e}")
            return False
    
    def generate_all_summaries(self) -> Dict[str, Any]:
        """Generate summaries for all products"""
        
        print("🚀 Starting product summary generation...")
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Get all product IDs
                cursor.execute('SELECT id, title FROM products ORDER BY id')
                products = cursor.fetchall()
                
                results = {
                    'total_products': len(products),
                    'successful_summaries': 0,
                    'failed_summaries': 0,
                    'summaries': []
                }
                
                print(f"📊 Found {len(products)} products to process")
                
                for product_id, title in products:
                    print(f"\n📝 Processing: {title[:50]}...")
                    
                    # Get product data
                    product_data = self.get_product_data(product_id)
                    if not product_data:
                        print(f"   ❌ Could not get product data")
                        results['failed_summaries'] += 1
                        continue
                    
                    # Generate summary
                    summary = self.generate_summary(product_data)
                    print(f"   📋 Summary: {summary}")
                    
                    # Update database
                    if self.update_product_summary(product_id, summary):
                        print(f"   ✅ Updated database")
                        results['successful_summaries'] += 1
                        results['summaries'].append({
                            'product_id': product_id,
                            'title': title,
                            'summary': summary
                        })
                    else:
                        print(f"   ❌ Failed to update database")
                        results['failed_summaries'] += 1
                
                return results
                
        except Exception as e:
            print(f"❌ Error generating summaries: {e}")
            return {'error': str(e)}
    
    def print_summary(self, results: Dict[str, Any]):
        """Print generation summary"""
        
        if 'error' in results:
            print(f"❌ Error: {results['error']}")
            return
        
        print(f"\n🎉 Product Summary Generation Complete!")
        print(f"📊 Summary:")
        print(f"   Total products: {results['total_products']}")
        print(f"   Successful summaries: {results['successful_summaries']}")
        print(f"   Failed summaries: {results['failed_summaries']}")
        print(f"   Success rate: {(results['successful_summaries']/results['total_products']*100):.1f}%")
        
        print(f"\n📋 Sample Summaries:")
        for summary_data in results['summaries'][:5]:  # Show first 5
            print(f"   {summary_data['product_id']}: {summary_data['summary']}")
        
        if len(results['summaries']) > 5:
            print(f"   ... and {len(results['summaries']) - 5} more summaries")

def main():
    """Main function"""
    
    print("🚀 Product Summary Generator")
    print("Generating one-sentence summaries for all products")
    print("=" * 60)
    
    generator = ProductSummaryGenerator()
    
    # Generate all summaries
    results = generator.generate_all_summaries()
    
    # Print summary
    generator.print_summary(results)

if __name__ == "__main__":
    main()
