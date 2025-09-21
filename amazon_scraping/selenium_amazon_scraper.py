#!/usr/bin/env python3
"""
Selenium-based Amazon scraper to bypass bot detection
"""

import time
import json
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class SeleniumAmazonScraper:
    def __init__(self, headless=True):
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with realistic options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless')
        
        # Make it look like a real browser
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
        chrome_options.add_experimental_option('useAutomationExtension', False)
        
        # Set realistic user agent
        chrome_options.add_argument('--user-agent=Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36')
        
        # Set window size
        chrome_options.add_argument('--window-size=1920,1080')
        
        # Path to Chrome (macOS)
        chrome_options.binary_location = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome'
        
        self.driver = webdriver.Chrome(options=chrome_options)
        
        # Execute script to remove webdriver property
        self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
        
        return self.driver
    
    def extract_product_details(self, url):
        """Extract product details using Selenium"""
        if not self.driver:
            self.setup_driver()
        
        try:
            print(f"🔍 Loading: {url}")
            self.driver.get(url)
            
            # Wait for page to load
            time.sleep(3)
            
            # Check if we got a CAPTCHA or error page
            page_source = self.driver.page_source.lower()
            if 'captcha' in page_source or 'robot' in page_source:
                print("❌ CAPTCHA or bot detection detected")
                return None
            
            details = {}
            
            # Extract title
            try:
                title_element = WebDriverWait(self.driver, 10).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                )
                details['title'] = title_element.text.strip()
                print(f"✅ Title: {details['title'][:50]}...")
            except TimeoutException:
                print("⚠️  Title not found")
                details['title'] = None
            
            # Extract price
            try:
                price_selectors = [
                    "span.a-price-whole",
                    ".a-price .a-offscreen",
                    "#price_inside_buybox",
                    ".a-price-range"
                ]
                
                for selector in price_selectors:
                    try:
                        price_element = self.driver.find_element(By.CSS_SELECTOR, selector)
                        price_text = price_element.text.strip()
                        if price_text and '$' in price_text:
                            details['price'] = price_text
                            print(f"✅ Price: {price_text}")
                            break
                    except NoSuchElementException:
                        continue
                        
                if 'price' not in details:
                    details['price'] = None
                    
            except Exception as e:
                print(f"⚠️  Price extraction failed: {e}")
                details['price'] = None
            
            # Extract rating
            try:
                rating_element = self.driver.find_element(By.CSS_SELECTOR, "span.a-icon-alt")
                rating_text = rating_element.get_attribute('innerHTML')
                if 'out of' in rating_text:
                    rating = rating_text.split('out of')[0].strip()
                    details['rating'] = float(rating)
                    print(f"✅ Rating: {rating}")
                else:
                    details['rating'] = None
            except NoSuchElementException:
                details['rating'] = None
            
            # Extract review count
            try:
                review_element = self.driver.find_element(By.ID, "acrCustomerReviewText")
                review_text = review_element.text
                import re
                review_match = re.search(r'([\d,]+)', review_text)
                if review_match:
                    details['review_count'] = int(review_match.group(1).replace(',', ''))
                    print(f"✅ Reviews: {details['review_count']}")
                else:
                    details['review_count'] = None
            except NoSuchElementException:
                details['review_count'] = None
            
            # Extract Amazon breadcrumbs
            try:
                breadcrumb_selectors = [
                    '#wayfinding-breadcrumbs_feature_div ul li',
                    '.breadcrumb ul li',
                    '#wayfinding-breadcrumbs_feature_div a',
                    '.breadcrumb a'
                ]
                
                breadcrumbs = []
                for selector in breadcrumb_selectors:
                    try:
                        breadcrumb_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if breadcrumb_elements:
                            breadcrumbs = [elem.text.strip() for elem in breadcrumb_elements if elem.text.strip()]
                            break
                    except:
                        continue
                
                if breadcrumbs:
                    details['amazon_breadcrumbs'] = breadcrumbs
                    details['amazon_category_path'] = ' > '.join(breadcrumbs)
                    print(f"✅ Breadcrumbs: {' > '.join(breadcrumbs)}")
                else:
                    details['amazon_breadcrumbs'] = None
                    details['amazon_category_path'] = None
                    
            except Exception as e:
                print(f"⚠️  Breadcrumb extraction failed: {e}")
                details['amazon_breadcrumbs'] = None
                details['amazon_category_path'] = None
            
            # Extract description
            try:
                desc_element = self.driver.find_element(By.ID, "feature-bullets")
                bullet_elements = desc_element.find_elements(By.CSS_SELECTOR, "span.a-list-item")
                descriptions = []
                for bullet in bullet_elements:
                    text = bullet.text.strip()
                    if text and not text.startswith('Make sure this fits'):
                        descriptions.append(text)
                details['description'] = ' '.join(descriptions)
                print(f"✅ Description: {len(descriptions)} bullet points")
            except NoSuchElementException:
                details['description'] = None
            
            return details
            
        except Exception as e:
            print(f"❌ Error extracting details: {e}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def test_selenium_scraper():
    """Test the Selenium scraper"""
    scraper = SeleniumAmazonScraper(headless=False)  # Set to False to see browser
    
    try:
        # Test with one product
        test_url = "https://www.amazon.com/dp/B07ZYXGP6N"
        details = scraper.extract_product_details(test_url)
        
        if details:
            print("\n🎉 Success! Extracted data:")
            for key, value in details.items():
                if key == 'amazon_breadcrumbs' and value:
                    print(f"  {key}: {value}")
                elif key != 'amazon_breadcrumbs':
                    print(f"  {key}: {value}")
        else:
            print("❌ Failed to extract data")
            
    finally:
        scraper.close()

if __name__ == "__main__":
    test_selenium_scraper()
