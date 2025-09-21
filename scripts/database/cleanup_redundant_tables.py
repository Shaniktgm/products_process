#!/usr/bin/env python3
"""
Script to clean up redundant tables from the database
This script will:
1. Identify redundant or unused tables
2. Remove them safely
3. Report what was cleaned up
"""

import sqlite3
from typing import List, Dict, Any

class DatabaseCleanup:
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Tables that are known to be redundant or unused
        self.redundant_tables = [
            'enhanced_product_features',  # Redundant with product_features
            'affiliate_links',            # Renamed to affiliation_details
            'product_specifications',     # Empty, specs stored in products table
            'product_reviews',            # Empty, review data in products table
            'product_categories',         # Empty table
            'product_platforms',          # Empty table
            'pros_cons_analysis',         # Empty table
        ]
    
    def connect_database(self):
        """Connect to database"""
        self.conn = sqlite3.connect(self.db_path)
        self.conn.row_factory = sqlite3.Row
        
    def close_database(self):
        """Close database connection"""
        if hasattr(self, 'conn'):
            self.conn.close()
    
    def get_all_tables(self) -> List[str]:
        """Get list of all tables in the database"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
        return [row[0] for row in cursor.fetchall()]
    
    def get_table_record_count(self, table_name: str) -> int:
        """Get record count for a table"""
        try:
            cursor = self.conn.cursor()
            cursor.execute(f"SELECT COUNT(*) FROM {table_name}")
            return cursor.fetchone()[0]
        except:
            return 0
    
    def cleanup_redundant_tables(self):
        """Clean up redundant tables"""
        print("🧹 Cleaning up redundant database tables...")
        print("=" * 60)
        
        self.connect_database()
        
        try:
            # Get all tables
            all_tables = self.get_all_tables()
            print(f"📊 Found {len(all_tables)} tables in database")
            
            # Check which redundant tables exist
            existing_redundant = []
            for table in self.redundant_tables:
                if table in all_tables:
                    record_count = self.get_table_record_count(table)
                    existing_redundant.append((table, record_count))
            
            if not existing_redundant:
                print("✅ No redundant tables found. Database is clean!")
                return
            
            print(f"\n📋 Found {len(existing_redundant)} redundant tables:")
            for table_name, record_count in existing_redundant:
                print(f"   - {table_name} ({record_count} records)")
            
            # Remove redundant tables
            cursor = self.conn.cursor()
            removed_count = 0
            
            for table_name, record_count in existing_redundant:
                if record_count == 0:
                    print(f"   🗑️  Removing empty table: {table_name}")
                    cursor.execute(f"DROP TABLE {table_name}")
                    removed_count += 1
                else:
                    print(f"   ⚠️  Skipping {table_name} (has {record_count} records)")
            
            self.conn.commit()
            
            print(f"\n✅ Successfully removed {removed_count} redundant tables")
            
            # Show final table list
            self.show_final_table_list()
            
        except Exception as e:
            print(f"❌ Cleanup failed: {e}")
            raise
        finally:
            self.close_database()
    
    def show_final_table_list(self):
        """Show final list of tables after cleanup"""
        cursor = self.conn.cursor()
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
        tables = [row[0] for row in cursor.fetchall()]
        
        print(f"\n📊 Final table list ({len(tables)} tables):")
        for table in tables:
            record_count = self.get_table_record_count(table)
            print(f"   - {table} ({record_count} records)")

def main():
    """Main function"""
    print("🚀 Database Table Cleanup")
    print("=" * 60)
    
    cleanup = DatabaseCleanup()
    cleanup.cleanup_redundant_tables()

if __name__ == "__main__":
    main()
