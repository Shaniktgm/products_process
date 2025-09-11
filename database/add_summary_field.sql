-- Add product_summary field to products table
-- Run this when database is unlocked

ALTER TABLE products ADD COLUMN product_summary TEXT;

-- Verify the column was added
PRAGMA table_info(products);
