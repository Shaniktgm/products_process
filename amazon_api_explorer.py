#!/usr/bin/env python3
"""
Amazon API Explorer
Test and explore Amazon API functionality to enhance database
"""

import requests
import json
import time
import hashlib
import hmac
import base64
from urllib.parse import quote, urlencode
from datetime import datetime
import sqlite3
from typing import Dict, Any, Optional, List

class AmazonAPIExplorer:
    """Explore Amazon API capabilities for product data enhancement"""
    
    def __init__(self, access_key: str, secret_key: str, associate_tag: str = None):
        self.access_key = access_key
        self.secret_key = secret_key
        self.associate_tag = associate_tag or "homeprinciple-20"  # Use your associate tag
        
        # Amazon API endpoints - PA-API 5.0
        self.base_url = "https://webservices.amazon.com"
        self.region = "us-east-1"
        self.service = "ProductAdvertisingAPI"
        self.version = "5.0"
        self.host = "webservices.amazon.com"
        
        # Rate limiting
        self.request_delay = 1  # seconds between requests
        self.last_request_time = 0
        
    def _rate_limit(self):
        """Ensure we don't exceed API rate limits"""
        current_time = time.time()
        time_since_last = current_time - self.last_request_time
        
        if time_since_last < self.request_delay:
            sleep_time = self.request_delay - time_since_last
            print(f"⏳ Rate limiting: waiting {sleep_time:.1f} seconds...")
            time.sleep(sleep_time)
        
        self.last_request_time = time.time()
    
    def _generate_signature(self, method: str, uri: str, query_string: str, payload: str = "") -> str:
        """Generate AWS signature for API authentication"""
        # Create canonical request
        canonical_request = f"{method}\n{uri}\n{query_string}\n"
        canonical_request += f"host:webservices.amazon.com\n"
        canonical_request += f"x-amz-date:{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
        canonical_request += f"\nhost;x-amz-date\n"
        canonical_request += hashlib.sha256(payload.encode()).hexdigest()
        
        # Create string to sign
        string_to_sign = f"AWS4-HMAC-SHA256\n"
        string_to_sign += f"{datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')}\n"
        string_to_sign += f"{datetime.utcnow().strftime('%Y%m%d')}/us-east-1/ProductAdvertisingAPI/aws4_request\n"
        string_to_sign += hashlib.sha256(canonical_request.encode()).hexdigest()
        
        # Calculate signature
        def sign(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()
        
        date_key = sign(f"AWS4{self.secret_key}".encode(), datetime.utcnow().strftime('%Y%m%d'))
        date_region_key = sign(date_key, self.region)
        date_region_service_key = sign(date_region_key, self.service)
        signing_key = sign(date_region_service_key, "aws4_request")
        
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        return signature
    
    def _generate_paapi5_signature(self, headers: Dict[str, str], payload: str, amz_date: str) -> str:
        """Generate AWS signature for PA-API 5.0"""
        # Create canonical request
        canonical_headers = '\n'.join([f"{k.lower()}:{v}" for k, v in sorted(headers.items())])
        signed_headers = ';'.join([k.lower() for k in sorted(headers.keys())])
        
        payload_hash = hashlib.sha256(payload.encode()).hexdigest()
        
        # Use the correct path based on operation
        operation = headers.get('X-Amz-Target', '').split('.')[-1]
        path = f"/paapi5/{operation.lower()}"
        
        canonical_request = f"POST\n{path}\n\n{canonical_headers}\n\n{signed_headers}\n{payload_hash}"
        
        # Create string to sign
        date_stamp = amz_date[:8]  # Extract date from amz_date
        
        credential_scope = f"{date_stamp}/{self.region}/{self.service}/aws4_request"
        string_to_sign = f"AWS4-HMAC-SHA256\n{amz_date}\n{credential_scope}\n{hashlib.sha256(canonical_request.encode()).hexdigest()}"
        
        # Calculate signature
        def sign(key, msg):
            return hmac.new(key, msg.encode(), hashlib.sha256).digest()
        
        date_key = sign(f"AWS4{self.secret_key}".encode(), date_stamp)
        date_region_key = sign(date_key, self.region)
        date_region_service_key = sign(date_region_key, self.service)
        signing_key = sign(date_region_service_key, "aws4_request")
        
        signature = hmac.new(signing_key, string_to_sign.encode(), hashlib.sha256).hexdigest()
        
        # Return authorization header
        return f"AWS4-HMAC-SHA256 Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}"
    
    def _make_request(self, operation: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Amazon PA-API 5.0"""
        self._rate_limit()
        
        try:
            # PA-API 5.0 uses JSON payload
            request_payload = {
                'PartnerTag': self.associate_tag,
                'PartnerType': 'Associates',
                'Marketplace': 'www.amazon.com',
                **payload
            }
            
            # Convert to JSON
            json_payload = json.dumps(request_payload)
            
            # Create headers (based on your working curl example)
            amz_date = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            headers = {
                'Host': 'webservices.amazon.com',
                'Content-Type': 'application/json; charset=UTF-8',
                'X-Amz-Date': amz_date,
                'X-Amz-Target': f'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}',
                'Content-Encoding': 'amz-1.0',
                'User-Agent': 'paapi-docs-curl/1.0.0'
            }
            
            # Create signature for PA-API 5.0
            signature = self._generate_paapi5_signature(headers, json_payload, amz_date)
            headers['Authorization'] = signature
            
            # Make request to PA-API 5.0 endpoint
            url = f"{self.base_url}/paapi5/{operation.lower()}"
            
            print(f"🔍 Making PA-API 5.0 request: {operation}")
            print(f"   URL: {url}")
            print(f"   Payload: {json_payload[:100]}...")
            
            response = requests.post(url, data=json_payload, headers=headers, timeout=10)
            response.raise_for_status()
            
            # Parse JSON response
            return response.json()
            
        except Exception as e:
            print(f"❌ API request failed: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"   Response: {e.response.text[:200]}...")
            return None
    
    def _xml_to_dict(self, element) -> Dict[str, Any]:
        """Convert XML element to dictionary"""
        result = {}
        
        # Add attributes
        if element.attrib:
            result['@attributes'] = element.attrib
        
        # Add text content
        if element.text and element.text.strip():
            result['text'] = element.text.strip()
        
        # Add children
        for child in element:
            child_dict = self._xml_to_dict(child)
            if child.tag in result:
                if not isinstance(result[child.tag], list):
                    result[child.tag] = [result[child.tag]]
                result[child.tag].append(child_dict)
            else:
                result[child.tag] = child_dict
        
        return result
    
    def search_products(self, keywords: str, search_index: str = "All") -> Optional[Dict[str, Any]]:
        """Search for products using keywords - PA-API 5.0"""
        payload = {
            'Keywords': keywords,
            'SearchIndex': search_index,
            'ItemCount': 3,
            'Resources': [
                'Images.Primary.Large',
                'ItemInfo.Title',
                'Offers.Listings.Price'
            ]
        }
        
        return self._make_request('SearchItems', payload)
    
    def get_product_by_asin(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get product details by ASIN - PA-API 5.0"""
        payload = {
            'ItemIds': [asin],
            'Resources': [
                'Images.Primary.Large',
                'ItemInfo.Title',
                'Offers.Listings.Price'
            ]
        }
        
        return self._make_request('GetItems', payload)
    
    def get_comprehensive_product_data(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive product data with all available information"""
        payload = {
            'ItemIds': [asin],
            'Resources': [
                'Images.Primary.Large',
                'ItemInfo.Title',
                'ItemInfo.Features',
                'ItemInfo.ProductInfo',
                'Offers.Listings.Price',
                'Offers.Listings.Availability',
                'Offers.Listings.Condition',
                'Offers.Listings.MerchantInfo',
                'CustomerReviews.StarRating',
                'CustomerReviews.Count',
                'BrowseNodeInfo.BrowseNodes'
            ]
        }
        
        return self._make_request('GetItems', payload)
    
    def get_product_categories(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get product categories - PA-API 5.0"""
        payload = {
            'ItemIds': [asin],
            'Resources': [
                'BrowseNodeInfo.BrowseNodes',
                'ItemInfo.Classifications'
            ]
        }
        
        return self._make_request('GetItems', payload)
    
    def test_api_connection(self) -> bool:
        """Test if API connection is working"""
        print("🧪 Testing Amazon PA-API 5.0 Connection...")
        
        # Try a simple search
        result = self.search_products("cotton sheets", "All")
        
        if result and 'SearchResult' in result:
            print("✅ PA-API 5.0 connection successful!")
            return True
        else:
            print("❌ PA-API 5.0 connection failed!")
            if result:
                print(f"   Response: {result}")
            return False
    
    def explore_api_capabilities(self):
        """Explore what the PA-API 5.0 can do"""
        print("🔍 Exploring Amazon PA-API 5.0 Capabilities...")
        print("=" * 50)
        
        # Test 1: Search functionality
        print("\n📋 Test 1: Product Search")
        search_result = self.search_products("cotton sheets king size", "All")
        if search_result and 'SearchResult' in search_result:
            print("✅ Search functionality working")
            # Print some sample data
            items = search_result['SearchResult'].get('Items', [])
            if items:
                first_item = items[0]
                title = first_item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'No title')
                print(f"   Sample product: {title}")
        else:
            print("❌ Search functionality failed")
            if search_result:
                print(f"   Response: {search_result}")
        
        # Test 2: Product lookup by ASIN
        print("\n📋 Test 2: Product Lookup by ASIN")
        # Use a known ASIN from your database
        asin_result = self.get_product_by_asin("B01M7Z2IIC")  # ASIN from your database
        if asin_result and 'ItemsResult' in asin_result:
            print("✅ Product lookup working")
            items = asin_result['ItemsResult'].get('Items', [])
            if items:
                first_item = items[0]
                title = first_item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'No title')
                print(f"   Product title: {title}")
        else:
            print("❌ Product lookup failed")
            if asin_result:
                print(f"   Response: {asin_result}")
        
        # Test 3: Category information
        print("\n📋 Test 3: Category Information")
        category_result = self.get_product_categories("B01M7Z2IIC")
        if category_result and 'ItemsResult' in category_result:
            print("✅ Category lookup working")
            items = category_result['ItemsResult'].get('Items', [])
            if items:
                browse_nodes = items[0].get('BrowseNodeInfo', {}).get('BrowseNodes', [])
                if browse_nodes:
                    print(f"   Categories: {len(browse_nodes)} browse nodes found")
        else:
            print("❌ Category lookup failed")
    
    def compare_with_database_products(self, db_path: str = "multi_platform_products.db"):
        """Compare API data with existing database products"""
        print("🔄 Comparing API data with database products...")
        
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        try:
            # Get some products from database
            cursor.execute("""
                SELECT id, amazon_product_id, title, price, rating, review_count, brand
                FROM products 
                WHERE amazon_product_id IS NOT NULL 
                LIMIT 5
            """)
            
            products = cursor.fetchall()
            print(f"📊 Found {len(products)} products to compare")
            
            for product_id, asin, title, price, rating, review_count, brand in products:
                print(f"\n🔍 Comparing product {product_id} (ASIN: {asin})")
                print(f"   Database title: {title}")
                print(f"   Database price: ${price}")
                print(f"   Database rating: {rating}")
                print(f"   Database reviews: {review_count}")
                
                # Get API data
                api_result = self.get_product_by_asin(asin)
                if api_result and 'ItemLookupResponse' in api_result:
                    items = api_result['ItemLookupResponse'].get('Items', {}).get('Item', {})
                    if items:
                        api_attrs = items.get('ItemAttributes', {})
                        api_offers = items.get('Offers', {})
                        
                        print(f"   API title: {api_attrs.get('Title', 'No title')}")
                        print(f"   API price: {api_offers.get('Offer', {}).get('OfferListing', {}).get('Price', {}).get('Amount', 'No price')}")
                        print(f"   API brand: {api_attrs.get('Brand', 'No brand')}")
                        print(f"   API features: {api_attrs.get('Feature', 'No features')}")
                        
                        # Compare data quality
                        self._compare_data_quality(
                            db_data={'title': title, 'price': price, 'rating': rating, 'reviews': review_count},
                            api_data={'title': api_attrs.get('Title'), 'price': api_offers.get('Offer', {}).get('OfferListing', {}).get('Price', {}).get('Amount')}
                        )
                else:
                    print("   ❌ No API data available")
                
                time.sleep(2)  # Be respectful to API limits
        
        finally:
            conn.close()
    
    def _compare_data_quality(self, db_data: Dict[str, Any], api_data: Dict[str, Any]):
        """Compare data quality between database and API"""
        print("   📊 Data Quality Comparison:")
        
        # Title comparison
        db_title = db_data.get('title', '')
        api_title = api_data.get('title', '')
        if db_title and api_title:
            if len(api_title) > len(db_title):
                print("     ✅ API title is more detailed")
            elif len(db_title) > len(api_title):
                print("     ✅ Database title is more detailed")
            else:
                print("     ⚖️ Titles are similar length")
        
        # Price comparison
        db_price = db_data.get('price')
        api_price = api_data.get('price')
        if db_price and api_price:
            try:
                db_price_float = float(db_price)
                api_price_float = float(api_price) / 100  # Amazon API returns price in cents
                if abs(db_price_float - api_price_float) < 1.0:
                    print("     ✅ Prices match closely")
                else:
                    print(f"     ⚠️ Price difference: DB=${db_price_float}, API=${api_price_float}")
            except:
                print("     ❌ Could not compare prices")
    
    def get_enhanced_product_data(self, asin: str) -> Optional[Dict[str, Any]]:
        """Get comprehensive product data from API"""
        print(f"🔍 Getting enhanced data for ASIN: {asin}")
        
        # Get comprehensive product data
        result = self.get_product_by_asin(asin)
        if not result or 'ItemLookupResponse' not in result:
            return None
        
        items = result['ItemLookupResponse'].get('Items', {}).get('Item', {})
        if not items:
            return None
        
        # Extract comprehensive data
        attrs = items.get('ItemAttributes', {})
        offers = items.get('Offers', {})
        images = items.get('ImageSets', {}).get('ImageSet', [])
        reviews = items.get('CustomerReviews', {})
        
        enhanced_data = {
            'asin': asin,
            'title': attrs.get('Title'),
            'brand': attrs.get('Brand'),
            'manufacturer': attrs.get('Manufacturer'),
            'model': attrs.get('Model'),
            'color': attrs.get('Color'),
            'size': attrs.get('Size'),
            'material': attrs.get('MaterialType'),
            'features': attrs.get('Feature', []),
            'description': attrs.get('Feature', []),  # Use features as description
            'price': offers.get('Offer', {}).get('OfferListing', {}).get('Price', {}).get('Amount'),
            'currency': offers.get('Offer', {}).get('OfferListing', {}).get('Price', {}).get('CurrencyCode'),
            'availability': offers.get('Offer', {}).get('OfferListing', {}).get('Availability'),
            'images': self._extract_images(images),
            'categories': self._extract_categories(items.get('BrowseNodes', {})),
            'reviews': self._extract_reviews(reviews)
        }
        
        return enhanced_data
    
    def _extract_images(self, images_data) -> List[str]:
        """Extract image URLs from API response"""
        image_urls = []
        if isinstance(images_data, list):
            for img_set in images_data:
                if isinstance(img_set, dict):
                    for key, value in img_set.items():
                        if 'URL' in key and isinstance(value, str):
                            image_urls.append(value)
        elif isinstance(images_data, dict):
            for key, value in images_data.items():
                if 'URL' in key and isinstance(value, str):
                    image_urls.append(value)
        
        return image_urls[:5]  # Limit to 5 images
    
    def _extract_categories(self, browse_nodes) -> List[str]:
        """Extract category information"""
        categories = []
        if isinstance(browse_nodes, dict):
            browse_node = browse_nodes.get('BrowseNode', {})
            if isinstance(browse_node, dict):
                name = browse_node.get('Name')
                if name:
                    categories.append(name)
        return categories
    
    def _extract_reviews(self, reviews_data) -> Dict[str, Any]:
        """Extract review information"""
        if not reviews_data:
            return {}
        
        return {
            'average_rating': reviews_data.get('AverageRating'),
            'total_reviews': reviews_data.get('TotalReviews'),
            'url': reviews_data.get('IFrameURL')
        }
    
    def display_comprehensive_product_info(self, asin: str):
        """Display comprehensive product information in a readable format"""
        print(f"🔍 Getting comprehensive data for ASIN: {asin}")
        print("=" * 80)
        
        result = self.get_comprehensive_product_data(asin)
        if not result or 'ItemsResult' not in result:
            print("❌ Failed to get product data")
            return
        
        items = result['ItemsResult'].get('Items', [])
        if not items:
            print("❌ No product found")
            return
        
        item = items[0]
        
        # Basic Information
        print("📋 BASIC INFORMATION")
        print("-" * 40)
        title = item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'N/A')
        print(f"Title: {title}")
        print(f"ASIN: {asin}")
        
        # Product Information
        item_info = item.get('ItemInfo', {})
        if item_info:
            print("\n📦 PRODUCT DETAILS")
            print("-" * 40)
            
            # Features
            features = item_info.get('Features', {}).get('DisplayValues', [])
            if features:
                print("Features:")
                for i, feature in enumerate(features[:5], 1):  # Show first 5 features
                    print(f"  {i}. {feature}")
                if len(features) > 5:
                    print(f"  ... and {len(features) - 5} more features")
            
            # Product Info
            product_info = item_info.get('ProductInfo', {})
            if product_info:
                print("\nProduct Information:")
                for key, value in product_info.items():
                    if isinstance(value, dict) and 'DisplayValue' in value:
                        print(f"  {key}: {value['DisplayValue']}")
            
            # Classifications
            classifications = item_info.get('Classifications', {})
            if classifications:
                print("\nClassifications:")
                for key, value in classifications.items():
                    if isinstance(value, dict) and 'DisplayValue' in value:
                        print(f"  {key}: {value['DisplayValue']}")
        
        # Pricing Information
        offers = item.get('Offers', {})
        if offers:
            print("\n💰 PRICING INFORMATION")
            print("-" * 40)
            
            # Current listings
            listings = offers.get('Listings', [])
            if listings:
                for i, listing in enumerate(listings, 1):
                    print(f"Listing {i}:")
                    price = listing.get('Price', {})
                    if price:
                        amount = price.get('Amount', 'N/A')
                        currency = price.get('Currency', 'N/A')
                        print(f"  Price: {currency} {amount}")
                    
                    availability = listing.get('Availability', {})
                    if availability:
                        message = availability.get('Message', 'N/A')
                        type_info = availability.get('Type', 'N/A')
                        print(f"  Availability: {message} ({type_info})")
                    
                    condition = listing.get('Condition', {})
                    if condition:
                        display_value = condition.get('DisplayValue', 'N/A')
                        print(f"  Condition: {display_value}")
                    
                    merchant = listing.get('MerchantInfo', {})
                    if merchant:
                        name = merchant.get('Name', 'N/A')
                        print(f"  Merchant: {name}")
            
            # Price summaries
            summaries = offers.get('Summaries', [])
            if summaries:
                summary = summaries[0]
                highest = summary.get('HighestPrice', {})
                lowest = summary.get('LowestPrice', {})
                offer_count = summary.get('OfferCount', 0)
                
                if highest:
                    print(f"\nPrice Range:")
                    print(f"  Highest: {highest.get('Currency', 'N/A')} {highest.get('Amount', 'N/A')}")
                if lowest:
                    print(f"  Lowest: {lowest.get('Currency', 'N/A')} {lowest.get('Amount', 'N/A')}")
                print(f"  Total Offers: {offer_count}")
        
        # Customer Reviews
        reviews = item.get('CustomerReviews', {})
        if reviews:
            print("\n⭐ CUSTOMER REVIEWS")
            print("-" * 40)
            star_rating = reviews.get('StarRating', {})
            if star_rating:
                value = star_rating.get('Value', 'N/A')
                print(f"Star Rating: {value}")
            
            count = reviews.get('Count', 0)
            print(f"Review Count: {count:,}")
        
        # Images
        images = item.get('Images', {})
        if images:
            print("\n🖼️ IMAGES")
            print("-" * 40)
            
            # Primary image
            primary = images.get('Primary', {})
            if primary:
                large = primary.get('Large', {})
                medium = primary.get('Medium', {})
                small = primary.get('Small', {})
                
                if large:
                    print(f"Primary Large: {large.get('URL', 'N/A')}")
                if medium:
                    print(f"Primary Medium: {medium.get('URL', 'N/A')}")
                if small:
                    print(f"Primary Small: {small.get('URL', 'N/A')}")
            
            # Variant images
            variants = images.get('Variants', [])
            if variants:
                print(f"Variant Images: {len(variants)} available")
                for i, variant in enumerate(variants[:3], 1):  # Show first 3
                    large = variant.get('Large', {})
                    if large:
                        print(f"  Variant {i}: {large.get('URL', 'N/A')}")
        
        # Browse Node Information
        browse_node_info = item.get('BrowseNodeInfo', {})
        if browse_node_info:
            print("\n📂 CATEGORY INFORMATION")
            print("-" * 40)
            
            browse_nodes = browse_node_info.get('BrowseNodes', [])
            if browse_nodes:
                print("Categories:")
                for i, node in enumerate(browse_nodes, 1):
                    name = node.get('DisplayName', 'N/A')
                    node_id = node.get('Id', 'N/A')
                    print(f"  {i}. {name} (ID: {node_id})")
            
            sales_rank = browse_node_info.get('WebsiteSalesRank', {})
            if sales_rank:
                rank = sales_rank.get('DisplayValue', 'N/A')
                context = sales_rank.get('ContextDisplayName', 'N/A')
                print(f"\nSales Rank: #{rank} in {context}")
        
        print("\n" + "=" * 80)
        print("✅ Comprehensive product data retrieved successfully!")

def main():
    """Test Amazon API functionality"""
    print("🚀 Amazon API Explorer")
    print("=" * 50)
    
    # Initialize API explorer
    api = AmazonAPIExplorer(
        access_key="AKPATKWXAM1758523929",
        secret_key="YxW3wUc6a96fsRZYxOhHAI5+lIYvszrmqV3Qawfs",
        associate_tag="your-associate-tag"  # You'll need to provide this
    )
    
    # Test API connection
    if api.test_api_connection():
        # Explore capabilities
        api.explore_api_capabilities()
        
        # Compare with database
        api.compare_with_database_products()
        
        # Test enhanced data extraction
        print("\n🔍 Testing Enhanced Data Extraction")
        enhanced_data = api.get_enhanced_product_data("B08N5WRWNW")
        if enhanced_data:
            print("✅ Enhanced data extraction successful!")
            print(f"   Title: {enhanced_data.get('title')}")
            print(f"   Brand: {enhanced_data.get('brand')}")
            print(f"   Price: {enhanced_data.get('price')}")
            print(f"   Features: {len(enhanced_data.get('features', []))} features")
            print(f"   Images: {len(enhanced_data.get('images', []))} images")
        else:
            print("❌ Enhanced data extraction failed")
    
    else:
        print("❌ Cannot proceed without API connection")

if __name__ == "__main__":
    main()
