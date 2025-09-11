-- Fix Downloaded Images SQL Script
-- Run this when the database is unlocked

-- Product 2: 100% Egyptian Cotton Sheets King Size
UPDATE products 
SET primary_image_url = '/images/products/2.webp',
    image_urls = '["/images/products/2.webp", "/images/products/2_1.jpeg", "/images/products/2_2.jpeg", "/images/products/2_3.jpeg", "/images/products/2_4.jpeg", "/images/products/2_5.jpeg"]',
    updated_at = datetime('now')
WHERE id = 2;

-- Product 4: Coop Home Goods Comphy SoftSpa Bed Sheet
UPDATE products 
SET primary_image_url = '/images/products/4.png',
    image_urls = '["/images/products/4.png"]',
    updated_at = datetime('now')
WHERE id = 4;

-- Product 5: DreamChill Cooling Bamboo Sheets
UPDATE products 
SET primary_image_url = '/images/products/5.jpeg',
    image_urls = '["/images/products/5.jpeg", "/images/products/5_1.jpeg", "/images/products/5_2.jpeg", "/images/products/5_3.jpeg", "/images/products/5_4.jpeg", "/images/products/5_5.jpeg"]',
    updated_at = datetime('now')
WHERE id = 5;

-- Product 6: DreamCool 100% Egyptian Cotton Cooling Bed Sheet
UPDATE products 
SET primary_image_url = '/images/products/6.jpeg',
    image_urls = '["/images/products/6.jpeg", "/images/products/6_1.jpeg", "/images/products/6_2.jpeg", "/images/products/6_3.jpeg", "/images/products/6_4.jpeg", "/images/products/6_5.jpeg"]',
    updated_at = datetime('now')
WHERE id = 6;

-- Product 9: Signature Hemmed Sheet Set
UPDATE products 
SET primary_image_url = '/images/products/9.jpeg',
    image_urls = '["/images/products/9.jpeg", "/images/products/9_1.jpeg", "/images/products/9_2.jpeg", "/images/products/9_3.jpeg", "/images/products/9_4.jpeg", "/images/products/9_5.jpeg"]',
    updated_at = datetime('now')
WHERE id = 9;

-- Verify the updates
SELECT id, sku, primary_image_url, image_urls FROM products WHERE id IN (2, 4, 5, 6, 9);
