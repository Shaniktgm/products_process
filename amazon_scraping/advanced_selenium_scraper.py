#!/usr/bin/env python3
"""
Advanced Selenium scraper with more realistic browser behavior
"""

import time
import random
import json
import sqlite3
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.common.action_chains import ActionChains
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.common.exceptions import TimeoutException, NoSuchElementException

class AdvancedSeleniumScraper:
    def __init__(self, headless=False):
        self.headless = headless
        self.driver = None
        
    def setup_driver(self):
        """Setup Chrome driver with very realistic options"""
        chrome_options = Options()
        
        if self.headless:
            chrome_options.add_argument('--headless=new')  # Use new headless mode
        
        # Make it look like a real user
        chrome_options.add_argument('--no-sandbox')
        chrome_options.add_argument('--disable-dev-shm-usage')
        chrome_options.add_argument('--disable-blink-features=AutomationControlled')
        chrome_options.add_argument('--disable-extensions')
        chrome_options.add_argument('--disable-plugins')
        chrome_options.add_argument('--disable-images')  # Faster loading
        chrome_options.add_argument('--disable-javascript')  # Try without JS first
        
        # Remove automation indicators
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
        self.driver.execute_script("Object.defineProperty(navigator, 'plugins', {get: () => [1, 2, 3, 4, 5]})")
        self.driver.execute_script("Object.defineProperty(navigator, 'languages', {get: () => ['en-US', 'en']})")
        
        return self.driver
    
    def human_like_delay(self, min_seconds=1, max_seconds=3):
        """Add human-like delays"""
        delay = random.uniform(min_seconds, max_seconds)
        time.sleep(delay)
    
    def simulate_human_behavior(self):
        """Simulate human-like mouse movements and scrolling"""
        try:
            # Random mouse movement
            actions = ActionChains(self.driver)
            actions.move_by_offset(random.randint(100, 500), random.randint(100, 300))
            actions.perform()
            
            # Random scroll
            scroll_amount = random.randint(200, 800)
            self.driver.execute_script(f"window.scrollBy(0, {scroll_amount});")
            
            self.human_like_delay(0.5, 1.5)
            
        except Exception as e:
            print(f"⚠️  Human behavior simulation failed: {e}")
    
    def extract_product_details(self, url):
        """Extract product details with human-like behavior"""
        if not self.driver:
            self.setup_driver()
        
        try:
            print(f"🔍 Loading: {url}")
            
            # First visit Amazon homepage to establish session
            print("🏠 Visiting Amazon homepage first...")
            self.driver.get("https://www.amazon.com")
            self.human_like_delay(2, 4)
            
            # Simulate human behavior on homepage
            self.simulate_human_behavior()
            
            # Now visit the product page
            print("🛍️  Visiting product page...")
            self.driver.get(url)
            self.human_like_delay(3, 5)
            
            # Simulate human behavior on product page
            self.simulate_human_behavior()
            
            # Check if we got a CAPTCHA or error page
            page_source = self.driver.page_source.lower()
            if 'captcha' in page_source or 'robot' in page_source or 'unusual traffic' in page_source:
                print("❌ CAPTCHA or bot detection detected")
                return None
            
            details = {}
            
            # Extract title
            try:
                title_element = WebDriverWait(self.driver, 15).until(
                    EC.presence_of_element_located((By.ID, "productTitle"))
                )
                details['title'] = title_element.text.strip()
                print(f"✅ Title: {details['title'][:50]}...")
            except TimeoutException:
                print("⚠️  Title not found")
                details['title'] = None
            
            # Extract Amazon breadcrumbs (most important for us)
            try:
                breadcrumb_selectors = [
                    '#wayfinding-breadcrumbs_feature_div ul li a',
                    '.breadcrumb ul li a',
                    '#wayfinding-breadcrumbs_feature_div a',
                    '.breadcrumb a'
                ]
                
                breadcrumbs = []
                for selector in breadcrumb_selectors:
                    try:
                        breadcrumb_elements = self.driver.find_elements(By.CSS_SELECTOR, selector)
                        if breadcrumb_elements:
                            breadcrumbs = [elem.text.strip() for elem in breadcrumb_elements if elem.text.strip()]
                            if breadcrumbs:
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
                    print("⚠️  No breadcrumbs found")
                    
            except Exception as e:
                print(f"⚠️  Breadcrumb extraction failed: {e}")
                details['amazon_breadcrumbs'] = None
                details['amazon_category_path'] = None
            
            # Extract basic info if available
            try:
                # Price
                price_selectors = [
                    "span.a-price-whole",
                    ".a-price .a-offscreen",
                    "#price_inside_buybox"
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
                details['price'] = None
            
            return details
            
        except Exception as e:
            print(f"❌ Error extracting details: {e}")
            return None
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()

def test_advanced_scraper():
    """Test the advanced Selenium scraper"""
    scraper = AdvancedSeleniumScraper(headless=False)  # Set to False to see browser
    
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
    test_advanced_scraper()
