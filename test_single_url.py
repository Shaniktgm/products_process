#!/usr/bin/env python3
"""
Test script to extract data from a single Amazon URL
"""

import requests
from bs4 import BeautifulSoup
import re

def test_single_url():
    # Test with one URL from the CSV
    test_url = "https://www.amazon.com/dp/B08M9SMVSG"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,image/apng,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.9',
        'Accept-Encoding': 'gzip, deflate, br',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    })
    
    try:
        print(f"Testing URL: {test_url}")
        response = session.get(test_url, timeout=15)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Check for bot detection
            if "Robot Check" in response.text or "captcha" in response.text.lower():
                print("❌ Bot detection triggered")
                return
            
            # Try to find title
            title_elem = soup.select_one('#productTitle')
            if title_elem:
                title = title_elem.get_text().strip()
                print(f"✅ Title found: {title[:100]}...")
            else:
                print("❌ No title found")
            
            # Try to find price
            price_elem = soup.select_one('.a-price-whole')
            if price_elem:
                price = price_elem.get_text().strip()
                print(f"✅ Price found: ${price}")
            else:
                print("❌ No price found")
            
            # Try to find rating
            rating_elem = soup.select_one('.a-icon-alt')
            if rating_elem:
                rating_text = rating_elem.get_text()
                print(f"✅ Rating found: {rating_text}")
            else:
                print("❌ No rating found")
            
            # Check page content
            print(f"Page length: {len(response.text)} characters")
            print(f"Contains 'product': {'product' in response.text.lower()}")
            print(f"Contains 'amazon': {'amazon' in response.text.lower()}")
            
        else:
            print(f"❌ HTTP Error: {response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_single_url()
