#!/usr/bin/env python3
"""
Extract product data from Amazon URL
"""

import requests
from bs4 import BeautifulSoup
import re
import json
from urllib.parse import urlparse, parse_qs

def clean_amazon_url(url):
    """Clean Amazon URL by removing referral parameters and keeping only the product URL"""
    try:
        # Parse the URL
        parsed = urlparse(url)
        
        # Extract ASIN from the path
        asin = None
        if '/dp/' in parsed.path:
            asin = parsed.path.split('/dp/')[1].split('/')[0]
        elif '/product/' in parsed.path:
            asin = parsed.path.split('/product/')[1].split('/')[0]
        elif 'asin=' in parsed.query:
            asin = parse_qs(parsed.query).get('asin', [None])[0]
        
        if asin:
            # Reconstruct clean URL: https://www.amazon.com/dp/ASIN
            clean_url = f"https://www.amazon.com/dp/{asin}"
            return clean_url
        
        return url  # Return original if we can't clean it
    except Exception:
        return url  # Return original if there's an error

def extract_asin_from_url(url):
    """Extract ASIN from Amazon URL"""
    # Try different patterns
    patterns = [
        r'/dp/([A-Z0-9]{10})',
        r'/product/([A-Z0-9]{10})',
        r'asin=([A-Z0-9]{10})',
        r'/([A-Z0-9]{10})/'
    ]
    
    for pattern in patterns:
        match = re.search(pattern, url)
        if match:
            return match.group(1)
    return None

def extract_product_data(url):
    """Extract product data from Amazon URL"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        # Clean the URL to remove referral parameters
        clean_url = clean_amazon_url(url)
        print(f"🔗 Original URL: {url}")
        print(f"🧹 Cleaned URL: {clean_url}")
        print(f"🔍 Fetching URL: {clean_url}")
        response = requests.get(clean_url, headers=headers, timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # Extract ASIN
        asin = extract_asin_from_url(url)
        
        # Extract product title
        title_selectors = [
            '#productTitle',
            'h1.a-size-large',
            'h1[data-automation-id="product-title"]',
            '.product-title',
            'h1'
        ]
        
        title = None
        for selector in title_selectors:
            title_elem = soup.select_one(selector)
            if title_elem:
                title = title_elem.get_text(strip=True)
                break
        
        # Extract breadcrumb navigation (category path)
        breadcrumb_selectors = [
            '#wayfinding-breadcrumbs_feature_div ul li',
            '.breadcrumb ul li',
            '#wayfinding-breadcrumbs_feature_div a',
            '.breadcrumb a'
        ]
        
        breadcrumbs = []
        for selector in breadcrumb_selectors:
            breadcrumb_elems = soup.select(selector)
            if breadcrumb_elems:
                breadcrumbs = [elem.get_text(strip=True) for elem in breadcrumb_elems if elem.get_text(strip=True)]
                break
        
        # Extract price
        price_selectors = [
            '.a-price-whole',
            '.a-price .a-offscreen',
            '#priceblock_dealprice',
            '#priceblock_ourprice',
            '.a-price-range'
        ]
        
        price = None
        for selector in price_selectors:
            price_elem = soup.select_one(selector)
            if price_elem:
                price = price_elem.get_text(strip=True)
                break
        
        # Extract rating
        rating_selectors = [
            '.a-icon-alt',
            '[data-hook="rating-out-of-text"]',
            '.a-star-mini .a-icon-alt'
        ]
        
        rating = None
        for selector in rating_selectors:
            rating_elem = soup.select_one(selector)
            if rating_elem:
                rating_text = rating_elem.get_text(strip=True)
                # Extract number from "4.5 out of 5 stars"
                rating_match = re.search(r'(\d+\.?\d*)', rating_text)
                if rating_match:
                    rating = float(rating_match.group(1))
                break
        
        # Extract review count
        review_selectors = [
            '[data-hook="total-review-count"]',
            '#acrCustomerReviewText',
            '.a-size-base'
        ]
        
        review_count = None
        for selector in review_selectors:
            review_elem = soup.select_one(selector)
            if review_elem:
                review_text = review_elem.get_text(strip=True)
                # Extract number from "1,234 ratings"
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    review_count = int(review_match.group(1).replace(',', ''))
                break
        
        # Extract product description
        description_selectors = [
            '#feature-bullets ul',
            '.a-unordered-list',
            '#productDescription'
        ]
        
        description = None
        for selector in description_selectors:
            desc_elem = soup.select_one(selector)
            if desc_elem:
                description = desc_elem.get_text(strip=True)
                break
        
        # Extract images
        image_selectors = [
            '#landingImage',
            '.a-dynamic-image',
            '#imgTagWrapperId img'
        ]
        
        image_url = None
        for selector in image_selectors:
            img_elem = soup.select_one(selector)
            if img_elem:
                image_url = img_elem.get('src') or img_elem.get('data-src')
                break
        
        # Determine category from breadcrumbs and title
        category = None
        if breadcrumbs:
            # Use the last breadcrumb as main category
            category = breadcrumbs[-1] if breadcrumbs else None
        
        # Also try to extract from title
        if title:
            title_lower = title.lower()
            if 'sheet' in title_lower:
                category = 'Bed Sheets'
            elif 'pillow' in title_lower:
                category = 'Pillows'
            elif 'comforter' in title_lower:
                category = 'Comforters'
            elif 'blanket' in title_lower:
                category = 'Blankets'
            elif 'duvet' in title_lower:
                category = 'Duvets'
            elif 'mattress' in title_lower:
                category = 'Mattress Accessories'
        
        product_data = {
            'asin': asin,
            'title': title,
            'category': category,
            'breadcrumbs': breadcrumbs,
            'price': price,
            'rating': rating,
            'review_count': review_count,
            'description': description,
            'image_url': image_url,
            'url': url
        }
        
        return product_data
        
    except requests.RequestException as e:
        print(f"❌ Error fetching URL: {e}")
        return None
    except Exception as e:
        print(f"❌ Error parsing content: {e}")
        return None

def main():
    url = "https://www.amazon.com/dp/B0CS9RQTFC?ref=t_ac_view_request_product_image&campaignId=amzn1.campaign.2D36SCEUF8IN1&linkCode=tr1&tag=homeprinciple-20&linkId=amzn1.campaign.2D36SCEUF8IN1_1757854568771"
    
    print("🚀 Extracting Amazon Product Data")
    print("=" * 50)
    
    product_data = extract_product_data(url)
    
    if product_data:
        print("✅ Product Data Extracted Successfully!")
        print("=" * 50)
        print(json.dumps(product_data, indent=2, ensure_ascii=False))
        
        # Save to file
        with open('amazon_product_data.json', 'w', encoding='utf-8') as f:
            json.dump(product_data, f, indent=2, ensure_ascii=False)
        print("\n💾 Data saved to amazon_product_data.json")
    else:
        print("❌ Failed to extract product data")

if __name__ == "__main__":
    main()
