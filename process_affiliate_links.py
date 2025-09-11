#!/usr/bin/env python3
"""
Process Product Affiliate Links CSV
Ingest affiliate links data into the database with pretty referral links
"""

import sqlite3
import csv
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path


class AffiliateLinksProcessor:
    """Process affiliate links CSV and ingest into database"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        self._init_tables()
    
    def _init_tables(self):
        """Initialize tables if needed"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Create platforms table if it doesn't exist
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS platforms (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    name TEXT NOT NULL UNIQUE,
                    base_url TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            ''')
            
            # Add amazon_product_id column to products table if it doesn't exist
            try:
                cursor.execute("ALTER TABLE products ADD COLUMN amazon_product_id TEXT")
            except sqlite3.OperationalError:
                pass  # Column already exists
            
            # Ensure affiliate_links table exists with all needed columns
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS affiliate_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    product_id INTEGER NOT NULL,
                    platform_id INTEGER NOT NULL,
                    link_type TEXT NOT NULL,
                    affiliate_url TEXT NOT NULL,
                    commission_rate REAL,
                    estimated_commission REAL,
                    is_active BOOLEAN DEFAULT TRUE,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    end_date DATE,
                    affiliate_page_internal_link TEXT,
                    pretty_referral_link TEXT,
                    FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE,
                    FOREIGN KEY (platform_id) REFERENCES platforms (id) ON DELETE CASCADE
                )
            ''')
            
            conn.commit()
    
    def process_csv_file(self, csv_file_path: str) -> Dict[str, int]:
        """Process the affiliate links CSV file"""
        stats = {
            'total_rows': 0,
            'processed_products': 0,
            'processed_links': 0,
            'errors': 0
        }
        
        try:
            with open(csv_file_path, 'r', encoding='utf-8') as file:
                reader = csv.DictReader(file)
                
                for row in reader:
                    stats['total_rows'] += 1
                    
                    try:
                        # Process each row
                        result = self._process_affiliate_row(row)
                        if result['product_created']:
                            stats['processed_products'] += 1
                        if result['link_created']:
                            stats['processed_links'] += 1
                            
                    except Exception as e:
                        print(f"⚠️  Error processing row {stats['total_rows']}: {e}")
                        stats['errors'] += 1
                        
        except Exception as e:
            print(f"❌ Error reading CSV file: {e}")
            stats['errors'] += 1
        
        return stats
    
    def _process_affiliate_row(self, row: Dict[str, str]) -> Dict[str, bool]:
        """Process a single affiliate row"""
        result = {'product_created': False, 'link_created': False}
        
        # Extract data from row
        platform = row.get('platform', '').strip()
        referral_link = row.get('referral link', '').strip()
        brand = row.get('brand', '').strip()
        price_str = row.get('price', '').strip()
        commission_str = row.get('commission', '').strip()
        end_date_str = row.get('End date', '').strip()
        internal_link = row.get('affilate_page_internal_link', '').strip()
        
        # Parse price
        price = None
        if price_str:
            try:
                price = float(price_str)
            except ValueError:
                pass
        
        # Parse commission
        commission_rate = None
        if commission_str:
            try:
                # Remove % sign if present
                commission_clean = commission_str.replace('%', '')
                commission_rate = float(commission_clean) / 100  # Convert to decimal
            except ValueError:
                pass
        
        # Parse end date
        end_date = None
        if end_date_str:
            try:
                # Parse date format: "Oct 1, 2025 09:59 GMT+3"
                end_date = self._parse_end_date(end_date_str)
            except Exception:
                pass
        
        # Extract Amazon product ID from referral link
        amazon_product_id = self._extract_amazon_product_id(referral_link)
        if not amazon_product_id:
            print(f"⚠️  Could not extract Amazon product ID from: {referral_link}")
            return result
        
        # Create pretty referral link
        pretty_referral_link = self._create_pretty_referral_link(amazon_product_id)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Get or create platform
            platform_id = self._get_or_create_platform(platform, cursor)
            
            # Get or create product
            product_id = self._get_or_create_product(
                amazon_product_id, brand, price, cursor
            )
            
            if product_id:
                result['product_created'] = True
            
            # Create affiliate link
            link_id = self._create_affiliate_link(
                product_id, platform_id, referral_link, pretty_referral_link,
                commission_rate, end_date, internal_link, cursor
            )
            
            if link_id:
                result['link_created'] = True
            
            conn.commit()
        
        return result
    
    def _extract_amazon_product_id(self, url: str) -> Optional[str]:
        """Extract Amazon product ID from URL"""
        # Pattern to match Amazon product IDs (ASIN)
        patterns = [
            r'/dp/([A-Z0-9]{10})',  # Standard /dp/ format
            r'/product/([A-Z0-9]{10})',  # Alternative /product/ format
            r'asin=([A-Z0-9]{10})',  # ASIN parameter
        ]
        
        for pattern in patterns:
            match = re.search(pattern, url, re.IGNORECASE)
            if match:
                return match.group(1).upper()
        
        return None
    
    def _create_pretty_referral_link(self, amazon_product_id: str) -> str:
        """Create a pretty referral link with homeprinciple tag"""
        return f"https://amzn.to/{amazon_product_id}?tag=homeprinciple-20"
    
    def _parse_end_date(self, date_str: str) -> Optional[str]:
        """Parse end date string to YYYY-MM-DD format"""
        try:
            # Remove timezone info and parse
            date_clean = re.sub(r'\s+GMT[+-]\d+', '', date_str)
            # Parse format: "Oct 1, 2025 09:59"
            dt = datetime.strptime(date_clean, "%b %d, %Y %H:%M")
            return dt.strftime("%Y-%m-%d")
        except Exception:
            return None
    
    def _get_or_create_platform(self, platform_name: str, cursor) -> int:
        """Get or create platform and return platform_id"""
        cursor.execute("SELECT id FROM platforms WHERE name = ?", (platform_name,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new platform
        cursor.execute("""
            INSERT INTO platforms (name, display_name, base_url)
            VALUES (?, ?, ?)
        """, (platform_name, platform_name, "https://amazon.com"))
        
        return cursor.lastrowid
    
    def _get_or_create_product(self, amazon_product_id: str, brand: str, 
                              price: float, cursor) -> Optional[int]:
        """Get or create product and return product_id"""
        cursor.execute("SELECT id FROM products WHERE amazon_product_id = ?", 
                      (amazon_product_id,))
        result = cursor.fetchone()
        
        if result:
            return result[0]
        
        # Create new product with required fields
        sku = f"AMZ-{amazon_product_id}"
        title = f"{brand} Product {amazon_product_id}"
        
        cursor.execute("""
            INSERT INTO products (sku, title, brand, price, amazon_product_id)
            VALUES (?, ?, ?, ?, ?)
        """, (sku, title, brand, price, amazon_product_id))
        
        return cursor.lastrowid
    
    def _create_affiliate_link(self, product_id: int, platform_id: int, 
                              affiliate_url: str, pretty_referral_link: str,
                              commission_rate: float, end_date: str, 
                              internal_link: str, cursor) -> Optional[int]:
        """Create affiliate link and return link_id"""
        # Check if link already exists
        cursor.execute("""
            SELECT id FROM affiliate_links 
            WHERE product_id = ? AND platform_id = ? AND affiliate_url = ?
        """, (product_id, platform_id, affiliate_url))
        
        if cursor.fetchone():
            return None  # Link already exists
        
        # Create new affiliate link
        cursor.execute("""
            INSERT INTO affiliate_links (
                product_id, platform_id, link_type, affiliate_url,
                commission_rate, end_date, affiliate_page_internal_link,
                pretty_referral_link
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (
            product_id, platform_id, 'web', affiliate_url,
            commission_rate, end_date, internal_link, pretty_referral_link
        ))
        
        return cursor.lastrowid
    
    def show_summary(self):
        """Show summary of processed data"""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.cursor()
            
            # Count products
            cursor.execute("SELECT COUNT(*) FROM products")
            product_count = cursor.fetchone()[0]
            
            # Count affiliate links
            cursor.execute("SELECT COUNT(*) FROM affiliate_links")
            link_count = cursor.fetchone()[0]
            
            # Count platforms
            cursor.execute("SELECT COUNT(*) FROM platforms")
            platform_count = cursor.fetchone()[0]
            
            print(f"\n📊 Database Summary:")
            print(f"   Products: {product_count}")
            print(f"   Affiliate Links: {link_count}")
            print(f"   Platforms: {platform_count}")
            
            # Show sample data
            print(f"\n📋 Sample Affiliate Links:")
            cursor.execute("""
                SELECT p.amazon_product_id, p.brand, p.price, 
                       al.pretty_referral_link, al.commission_rate, al.end_date
                FROM products p
                JOIN affiliate_links al ON p.id = al.product_id
                ORDER BY p.id
                LIMIT 5
            """)
            
            results = cursor.fetchall()
            for asin, brand, price, pretty_link, commission, end_date in results:
                print(f"   {asin} | {brand} | ${price} | {commission:.1%} | {end_date}")
                print(f"      Pretty Link: {pretty_link}")


def main():
    """Main function to process affiliate links CSV"""
    csv_file = "products/product_affilate_links.csv"
    db_path = "multi_platform_products.db"
    
    if not Path(csv_file).exists():
        print(f"❌ CSV file not found: {csv_file}")
        return
    
    print("🚀 Starting Affiliate Links Processing")
    print("=" * 50)
    
    # Initialize processor
    processor = AffiliateLinksProcessor(db_path)
    
    # Process CSV file
    print(f"\n📊 Processing {csv_file}...")
    stats = processor.process_csv_file(csv_file)
    
    print(f"\n✅ Processing Complete!")
    print(f"   Total Rows: {stats['total_rows']}")
    print(f"   Products Created: {stats['processed_products']}")
    print(f"   Links Created: {stats['processed_links']}")
    print(f"   Errors: {stats['errors']}")
    
    # Show summary
    processor.show_summary()


if __name__ == "__main__":
    main()
