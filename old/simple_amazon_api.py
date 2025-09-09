#!/usr/bin/env python3
"""
Simple Amazon Product Advertising API implementation using requests library
"""

import os
import json
import time
import hashlib
import hmac
import requests
from datetime import datetime
from typing import List, Dict, Any, Optional
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

class SimpleAmazonAPI:
    """Simple Amazon Product Advertising API implementation"""
    
    def __init__(self):
        """Initialize the API with credentials from environment variables"""
        # Load credentials from environment variables
        self.access_key = os.getenv('PAAPI_ACCESS_KEY')
        self.secret_key = os.getenv('PAAPI_SECRET_ACCESS_KEY')
        self.partner_tag = os.getenv('PAAPI_PARTNER_TAG')
        self.region =  'us-east-1' #os.getenv('PAAPI_REGION', 'us-east-1')
        self.service = 'ProductAdvertisingAPI'
        self.host = os.getenv('PAAPI_HOST', 'webservices.amazon.com')
        
        # Validate required credentials
        if not all([self.access_key, self.secret_key, self.partner_tag]):
            raise ValueError(
                "Missing required environment variables. Please set:\n"
                "PAAPI_ACCESS_KEY, PAAPI_SECRET_ACCESS_KEY, PAAPI_PARTNER_TAG\n"
                "Create a .env file or export them in your shell."
            )
        
        print(f"✅ Simple Amazon API initialized")
        print(f"   Partner Tag: {self.partner_tag}")
        print(f"   Host: {self.host}")
        print(f"   Access Key: {self.access_key[:8]}...")
    
    def _generate_signature(self, string_to_sign: str, date_stamp: str) -> str:
        """Generate AWS Signature Version 4 signature"""
        # Create signing key
        k_date = hmac.new(f'AWS4{self.secret_key}'.encode('utf-8'), 
                         date_stamp.encode('utf-8'), hashlib.sha256).digest()
        k_region = hmac.new(k_date, self.region.encode('utf-8'), hashlib.sha256).digest()
        k_service = hmac.new(k_region, self.service.encode('utf-8'), hashlib.sha256).digest()
        k_signing = hmac.new(k_service, 'aws4_request'.encode('utf-8'), hashlib.sha256).digest()
        
        # Generate signature
        signature = hmac.new(k_signing, string_to_sign.encode('utf-8'), hashlib.sha256).hexdigest()
        return signature
    
    def _make_request(self, operation: str, payload: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Make authenticated request to Amazon API"""
        try:
            # Prepare request
            timestamp = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')
            date_stamp = datetime.utcnow().strftime('%Y%m%d')
            
            # Create canonical request
            http_method = 'POST'
            canonical_uri = '/paapi5/searchitems' if operation == 'SearchItems' else '/paapi5/getitems'

            canonical_query_string = ''
            
            # Prepare headers
            # headers = {
            #     'Content-Type': 'application/json; charset=UTF-8',
            #     'X-Amz-Date': timestamp,
            #     'X-Amz-Target': f'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}',
            #     'Host': self.host
            # }

            payload_string = json.dumps(payload, separators=(',', ':'))
            payload_hash = hashlib.sha256(payload_string.encode('utf-8')).hexdigest()

            headers = {
            'Content-Type': 'application/json; charset=UTF-8',
            'Content-Encoding': 'amz-1.0',
            'Accept': 'application/json',
            'X-Amz-Date': timestamp,
            'X-Amz-Target': f'com.amazon.paapi5.v1.ProductAdvertisingAPIv1.{operation}',
            'X-Amz-Content-Sha256': payload_hash,
            'Host': self.host
        }
            
            # Create canonical headers
            sorted_keys = sorted(headers.keys(), key=lambda k: k.lower())
            canonical_headers = '\n'.join(f'{k.lower()}:{headers[k]}' for k in sorted_keys) + '\n'
            signed_headers = ';'.join(k.lower() for k in sorted_keys)
            # Create payload hash
            
            # Create canonical request
            canonical_request = '\n'.join([
                http_method,
                canonical_uri,
                canonical_query_string,
                canonical_headers,
                signed_headers,
                payload_hash
            ])
            
            # Create string to sign
            algorithm = 'AWS4-HMAC-SHA256'
            credential_scope = f'{date_stamp}/{self.region}/{self.service}/aws4_request'
            string_to_sign = '\n'.join([
                algorithm,
                timestamp,
                credential_scope,
                hashlib.sha256(canonical_request.encode('utf-8')).hexdigest()
            ])
            
            # Generate signature
            signature = self._generate_signature(string_to_sign, date_stamp)
            
            # Create authorization header
            authorization_header = f'{algorithm} Credential={self.access_key}/{credential_scope}, SignedHeaders={signed_headers}, Signature={signature}'
            headers['Authorization'] = authorization_header
            
            # Make request
            url = f'https://{self.host}{canonical_uri}'
            
            print(f"   Making request to: {url}")
            print(f"   Operation: {operation}")
            
            response = requests.post(url, headers=headers, data=payload_string, timeout=30)

            if response.status_code == 200:
                return response.json()
            else:
                print(f"   ❌ API Error: {response.status_code}")
                print(f"   Response: {response.text}")
                return None
                
        except Exception as e:
            print(f"   ❌ Request error: {str(e)}")
            return None
    
    def search_products(self, keywords: str, item_count: int = 10) -> List[Dict[str, Any]]:
        """Search for products using SearchItems operation"""
        try:
            print(f"🔍 Searching for: {keywords}")
            
            payload = {
                'PartnerTag': self.partner_tag,
                'PartnerType': 'Associates',
                'Marketplace': 'www.amazon.com',
                'Keywords': keywords,
                'ItemCount': min(item_count, 10),  # PA-API max for SearchItems is 10

                'SearchIndex': 'All',
                'Resources': [
                    'ItemInfo.Title',
                    'ItemInfo.ByLineInfo',
                    'ItemInfo.Classifications',
                    'Offers.Listings.Price',
                    'Images.Primary.Medium',
                    'CustomerReviews.Count',
                    'CustomerReviews.StarRating', 
                    'BrowseNodeInfo.BrowseNodes'
                ]
            }
            
            response = self._make_request('SearchItems', payload)
            
            if not response or 'SearchResult' not in response:
                print(f"   ❌ No search results for: {keywords}")
                return []
            
            items = response['SearchResult'].get('Items', [])
            products = []
            
            for item in items:
                try:
                    product = {
                        'asin': item.get('ASIN', ''),
                        'title': item.get('ItemInfo', {}).get('Title', {}).get('DisplayValue', 'Unknown Title'),
                        'brand': item.get('ItemInfo', {}).get('ByLineInfo', {}).get('Brand', {}).get('DisplayValue', 'Unknown Brand'),
                        'price': self._extract_price(item.get('Offers', {}).get('Listings', [{}])[0].get('Price')),
                        'rating': item.get('CustomerReviews', {}).get('StarRating', {}).get('Value', 0),
                        'review_count': item.get('CustomerReviews', {}).get('Count', 0),
                        'image': item.get('Images', {}).get('Primary', {}).get('Medium', {}).get('URL'),
                        'affiliate_link': f"https://www.amazon.com/dp/{item.get('ASIN', '')}?tag={self.partner_tag}",
                        'search_timestamp': datetime.now().isoformat()
                    }
                    products.append(product)
                except Exception as e:
                    print(f"   ⚠️ Error processing item: {str(e)}")
                    continue
            
            print(f"   ✅ Found {len(products)} products")
            return products
            
        except Exception as e:
            print(f"   ❌ Search error: {str(e)}")
            return []
    
    def _extract_price(self, price_info: Dict[str, Any]) -> Optional[float]:
        """Extract price from price info"""
        if not price_info or 'Amount' not in price_info:
            return None
        try:
            return float(price_info['Amount'])
        except (ValueError, TypeError):
            return None
    
    def search_dental_categories(self) -> List[Dict[str, Any]]:
        """Search for products in multiple dental categories"""
        categories = [
            'toothpaste',
            'toothbrush', 
            'mouthwash',
            'dental floss',
            'oral probiotics',
            'teeth whitening'
        ]
        
        all_products = []
        
        for category in categories:
            try:
                print(f"\n🔍 Searching category: {category}")
                products = self.search_products(category, 20)
                all_products.extend(products)
                
                # Rate limiting
                time.sleep(1)
                
            except Exception as e:
                print(f"   ❌ Error searching category {category}: {str(e)}")
                continue
        
        # Remove duplicates by ASIN
        unique_products = []
        seen_asins = set()
        
        for product in all_products:
            asin = product.get('asin')
            if asin and asin not in seen_asins:
                unique_products.append(product)
                seen_asins.add(asin)
        
        print(f"\n✅ Total unique products found: {len(unique_products)}")
        return unique_products
    
    def test_api(self):
        """Test the API with a simple search"""
        print("\n🧪 Testing Simple Amazon API...")
        print("=" * 40)
        
        try:
            # Test basic search
            print("\n1. Testing basic search...")
            products = self.search_products("toothpaste", 3)
            
            if products:
                print(f"   ✅ Found {len(products)} products")
                for i, product in enumerate(products[:2], 1):
                    print(f"      {i}. {product.get('title', 'Unknown')[:50]}...")
                    print(f"         ASIN: {product.get('asin', 'Unknown')}")
                    print(f"         Price: ${product.get('price', 'Unknown')}")
                    print(f"         Brand: {product.get('brand', 'Unknown')}")
            else:
                print("   ❌ No products found")
            
            print("\n✅ API test completed!")
            
        except Exception as e:
            print(f"❌ API test failed: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    # Initialize and test the API
    api = SimpleAmazonAPI()
    api.test_api()
