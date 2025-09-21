#!/usr/bin/env python3
"""
Test script to demonstrate Amazon category extraction and mapping
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from main_pipeline import CompleteProductPipeline
from amazon_category_mapper import AmazonCategoryMapper

def test_amazon_category_extraction():
    """Test Amazon category extraction with the sample URL"""
    
    # Initialize pipeline
    pipeline = CompleteProductPipeline()
    
    # Test URL (the one we used earlier)
    test_url = "https://www.amazon.com/dp/B0CS9RQTFC?ref=t_ac_view_request_product_image&campaignId=amzn1.campaign.2D36SCEUF8IN1&linkCode=tr1&tag=homeprinciple-20&linkId=amzn1.campaign.2D36SCEUF8IN1_1757854568771"
    
    print("🚀 Testing Amazon Category Extraction")
    print("=" * 60)
    
    # Extract product details
    print(f"🔍 Extracting details from: {test_url}")
    details = pipeline.extract_product_details(test_url)
    
    if details:
        print("\n✅ Product Details Extracted:")
        print(f"   Title: {details.get('title', 'N/A')[:100]}...")
        print(f"   Price: ${details.get('price', 'N/A')}")
        print(f"   Rating: {details.get('rating', 'N/A')}/5")
        print(f"   Review Count: {details.get('review_count', 'N/A')}")
        
        # Show Amazon categories
        if 'amazon_breadcrumbs' in details:
            print(f"\n🏷️  Amazon Breadcrumbs:")
            for i, breadcrumb in enumerate(details['amazon_breadcrumbs']):
                indent = "   " + "  " * i
                print(f"{indent}{breadcrumb}")
        
        if 'amazon_category_path' in details:
            print(f"\n📂 Amazon Category Path:")
            print(f"   {details['amazon_category_path']}")
        
        # Test category mapping
        print(f"\n🔄 Testing Category Mapping:")
        mapper = AmazonCategoryMapper()
        
        category_name, parent_category, source = mapper.map_amazon_category(
            details.get('amazon_breadcrumbs', []),
            details.get('amazon_category_path', '')
        )
        
        print(f"   Mapped Category: {category_name}")
        print(f"   Parent Category: {parent_category}")
        print(f"   Source: {source}")
        
        # Show comparison with current system
        print(f"\n📊 Comparison:")
        print(f"   Current System: Would categorize as 'Sheet Sets' (custom)")
        print(f"   Amazon System:  Would categorize as '{category_name}' (amazon)")
        
        return details
    else:
        print("❌ Failed to extract product details")
        return None

def show_amazon_category_benefits():
    """Show the benefits of using Amazon categories"""
    
    print("\n🎯 Benefits of Using Amazon Categories:")
    print("=" * 60)
    
    benefits = [
        "✅ More accurate categorization based on Amazon's taxonomy",
        "✅ Consistent with how customers actually browse products",
        "✅ Automatic updates when Amazon changes their categories",
        "✅ Better SEO and search relevance",
        "✅ Easier integration with Amazon's product data",
        "✅ Reduced manual categorization work",
        "✅ Support for Amazon's breadcrumb navigation",
        "✅ Fallback to custom categories when Amazon data unavailable"
    ]
    
    for benefit in benefits:
        print(f"   {benefit}")
    
    print(f"\n📈 Implementation Strategy:")
    print(f"   1. Extract Amazon breadcrumbs during product scraping")
    print(f"   2. Map Amazon categories to our parent categories")
    print(f"   3. Store both Amazon and custom categories")
    print(f"   4. Use Amazon categories as primary, custom as fallback")
    print(f"   5. Gradually migrate existing products to Amazon categories")

if __name__ == "__main__":
    # Test the extraction
    details = test_amazon_category_extraction()
    
    # Show benefits
    show_amazon_category_benefits()
    
    if details:
        print(f"\n💾 Sample data saved to amazon_product_data.json")
        import json
        with open('amazon_product_data.json', 'w', encoding='utf-8') as f:
            json.dump(details, f, indent=2, ensure_ascii=False)
