#!/usr/bin/env python3
"""
Test Amazon access to check if IP is unblocked
"""

import requests
import time
from datetime import datetime

def test_amazon_access():
    """Test if Amazon is accessible"""
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
        'Accept-Encoding': 'gzip, deflate',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    test_urls = [
        'https://www.amazon.com/dp/B07ZYXGP6N',
        'https://www.amazon.com/dp/B08N5WRWNW',
    ]
    
    print(f"🕐 Testing Amazon access at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print("=" * 60)
    
    results = []
    
    for i, url in enumerate(test_urls, 1):
        print(f"\n🔍 Test {i}: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=10)
            content = response.text.lower()
            
            status = "UNKNOWN"
            if 'captcha' in content:
                status = "BLOCKED (CAPTCHA)"
            elif 'robot' in content:
                status = "BLOCKED (ROBOT)"
            elif 'product' in content and 'price' in content:
                status = "ACCESSIBLE ✅"
            elif 'asin' in content:
                status = "PARTIAL ACCESS 🟡"
            else:
                status = f"UNKNOWN (Status: {response.status_code})"
            
            print(f"   Result: {status}")
            results.append(status)
            
        except Exception as e:
            print(f"   Error: {e}")
            results.append("ERROR")
        
        if i < len(test_urls):
            time.sleep(2)
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 SUMMARY:")
    
    if any("ACCESSIBLE" in result for result in results):
        print("🎉 Amazon access appears to be restored!")
        print("   You can try running the pipeline again.")
    elif any("PARTIAL" in result for result in results):
        print("🟡 Partial access detected")
        print("   Amazon may be unblocking gradually.")
    else:
        print("🚫 Amazon is still blocking requests")
        print("   Wait a few more days and test again.")
    
    print(f"\n💡 Run this script daily to check: python3 test_amazon_access.py")

if __name__ == "__main__":
    test_amazon_access()
