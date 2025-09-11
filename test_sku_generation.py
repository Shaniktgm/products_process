#!/usr/bin/env python3
"""
Test script for SKU generation
"""

import re

def generate_sku_from_url(url: str) -> str:
    """Generate SKU from URL - always returns AMAZON-{ASIN} format"""
    # Extract ASIN from various Amazon URL patterns
    asin_patterns = [
        r'/dp/([A-Z0-9]{10})',  # Standard Amazon URL format
        r'/product/([A-Z0-9]{10})',  # Alternative format
        r'asin=([A-Z0-9]{10})',  # ASIN parameter
    ]
    
    for pattern in asin_patterns:
        asin_match = re.search(pattern, url, re.IGNORECASE)
        if asin_match:
            asin = asin_match.group(1).upper()
            return f"AMAZON-{asin}"
    
    # If no ASIN found, this should not happen for valid Amazon URLs
    # But if it does, we'll create a hash-based SKU
    import hashlib
    url_hash = hashlib.md5(url.encode()).hexdigest()[:8].upper()
    return f"AMAZON-{url_hash}"

def main():
    # Test URLs
    test_urls = [
        'https://www.amazon.com/dp/B0CS9RQTFC?maas=maas_adg_api_58472',
        'https://amazon.com/dp/B08HWNLDPC?maas=maas_adg_api_584724442',
        'https://www.amazon.com/product/B0BRYKPH9J?tag=homeprinciple-20'
    ]

    print('🧪 Testing SKU Generation:')
    print('=' * 50)

    for url in test_urls:
        sku = generate_sku_from_url(url)
        print(f'URL: {url[:60]}...')
        print(f'SKU: {sku}')
        print()

if __name__ == "__main__":
    main()
