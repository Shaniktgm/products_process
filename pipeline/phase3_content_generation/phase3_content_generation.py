#!/usr/bin/env python3
"""
Phase 3: Content Generation Pipeline
Generates smart pros/cons, pretty titles, and product summaries from enhanced API data
"""

import os
import sys
from typing import Dict, Any

# Import our existing systems
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from core.generate_product_summaries import ProductSummaryGenerator
from core.smart_pros_cons_generator import SmartProsConsGenerator
from core.enhanced_amazon_pros_cons_generator import EnhancedAmazonProsConsGenerator
from core.smart_pretty_title_generator import SmartPrettyTitleGenerator
from improved_pretty_title_generator import ImprovedPrettyTitleGenerator
from core.material_extractor import MaterialExtractor
from core.weave_extractor import WeaveExtractor
from core.configurable_scoring_system import ConfigurableScoringSystem

# Import field extractor from phase2_content_generation
sys.path.append(os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'phase2_content_generation'))
from extract_missing_fields import ProductDataExtractor

class ContentGenerationPipeline:
    """Phase 3: Generate content from enhanced Amazon API data"""
    
    def __init__(self, db_path: str = "multi_platform_products.db"):
        self.db_path = db_path
        
        # Initialize content generation subsystems
        self.summary_generator = ProductSummaryGenerator(db_path)
        self.smart_pros_cons = SmartProsConsGenerator(db_path)
        self.enhanced_amazon_pros_cons = EnhancedAmazonProsConsGenerator(db_path)
        self.smart_pretty_titles = SmartPrettyTitleGenerator(db_path)
        self.improved_pretty_titles = ImprovedPrettyTitleGenerator(db_path)
        self.material_extractor = MaterialExtractor(db_path)
        self.weave_extractor = WeaveExtractor(db_path)
        self.field_extractor = ProductDataExtractor(db_path)
        # Initialize scoring system with correct config path
        import os
        config_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))), 'core', 'scoring_config.json')
        self.scoring_system = ConfigurableScoringSystem(config_path)
        
        # Statistics tracking
        self.stats = {
            'pros_cons_generated': 0,
            'materials_extracted': 0,
            'weaves_extracted': 0,
            'pretty_titles_generated': 0,
            'summaries_generated': 0,
            'fields_extracted': {},
            'products_with_extracted_fields': 0,
            'categories_assigned': 0,
            'scores_calculated': 0,
            'errors': 0
        }
    
    def run_content_generation(self) -> Dict[str, Any]:
        """Run Phase 3: Content Generation Pipeline"""
        print("🚀 Starting Phase 3: Content Generation Pipeline")
        print("=" * 60)
        
        # Step 1: Generate enhanced Amazon-based pros and cons
        print("\n✨ Step 1: Generating Enhanced Amazon-Based Pros and Cons")
        try:
            # Use the enhanced Amazon pros/cons generator for rich, data-driven features
            enhanced_results = self._generate_enhanced_amazon_features()
            self.stats['pros_cons_generated'] = enhanced_results.get('total_features_generated', 0)
            print(f"✅ Generated {self.stats['pros_cons_generated']} enhanced Amazon-based features for {enhanced_results.get('processed_products', 0)} products")
        except Exception as e:
            print(f"❌ Error generating enhanced Amazon pros/cons: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 2: Extract missing fields from existing data
        print("\n🔍 Step 2: Extracting Missing Fields from Existing Data")
        try:
            field_extraction_results = self.field_extractor.process_all_products()
            self.stats['fields_extracted'] = field_extraction_results['fields_extracted']
            self.stats['products_with_extracted_fields'] = field_extraction_results['products_updated']
            self.stats['categories_assigned'] = field_extraction_results['categories_assigned']
            print(f"✅ Extracted fields for {self.stats['products_with_extracted_fields']} products")
            print(f"✅ Assigned categories to {self.stats['categories_assigned']} products")
            print(f"   📊 Fields extracted: {sum(self.stats['fields_extracted'].values())} total")
        except Exception as e:
            print(f"❌ Error extracting fields: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 2.5: Enrich brands from Amazon features and reviews
        print("\n🏷️ Step 2.5: Enriching Brands from Amazon Features")
        try:
            enriched = self._enrich_brands_from_features()
            print(f"✅ Enriched {enriched.get('brands_updated', 0)} brands from Amazon features")
        except Exception as e:
            print(f"❌ Error enriching brands: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1

        # Step 2.6: Extract material types from product data
        print("\n🧵 Step 2.6: Extracting Material Types from Product Data")
        try:
            material_results = self.material_extractor.extract_all_materials()
            self.stats['materials_extracted'] = material_results.get('materials_extracted', 0)
            print(f"✅ Extracted materials for {material_results.get('processed_products', 0)} products")
            print(f"✅ Found {self.stats['materials_extracted']} products with identifiable materials")
        except Exception as e:
            print(f"❌ Error extracting materials: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1

        # Step 2.7: Extract weave types from product data
        print("\n🧶 Step 2.7: Extracting Weave Types from Product Data")
        try:
            weave_results = self.weave_extractor.extract_all_weaves()
            self.stats['weaves_extracted'] = weave_results.get('weaves_extracted', 0)
            print(f"✅ Extracted weaves for {weave_results.get('processed_products', 0)} products")
            print(f"✅ Found {self.stats['weaves_extracted']} products with identifiable weave types")
        except Exception as e:
            print(f"❌ Error extracting weaves: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1

        # Step 2.8: Generate structured smart features from Amazon bullets
        print("\n🧩 Step 2.8: Generating Structured Smart Features from Amazon Bullets")
        try:
            sf_results = self._generate_structured_features_from_amazon()
            inserted = sf_results.get('features_inserted', 0)
            print(f"✅ Inserted {inserted} structured features into smart_features")
            # Track as part of features generated for visibility
            self.stats['pros_cons_generated'] += inserted
        except Exception as e:
            print(f"❌ Error generating structured features: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 3: Generate improved pretty titles (under 10 words)
        print("\n🎨 Step 3: Generating Improved Pretty Titles (Under 10 Words)")
        try:
            pretty_title_results = self.improved_pretty_titles.update_all_pretty_titles()
            self.stats['pretty_titles_generated'] = pretty_title_results.get('titles_generated', 0)
            print(f"✅ Generated improved pretty titles for {self.stats['pretty_titles_generated']} products")
        except Exception as e:
            print(f"❌ Error generating pretty titles: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 4: Generate product summaries
        print("\n📝 Step 4: Generating Product Summaries")
        try:
            summary_results = self.summary_generator.generate_all_summaries()
            self.stats['summaries_generated'] = summary_results.get('successful', 0)
            print(f"✅ Generated summaries for {self.stats['summaries_generated']} products")
        except Exception as e:
            print(f"❌ Error generating summaries: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Step 5: Calculate product scores
        print("\n📊 Step 5: Calculating Product Scores")
        try:
            scoring_results = self.scoring_system.update_all_product_scores(self.db_path)
            if scoring_results:
                self.stats['scores_calculated'] = scoring_results.get('products_updated', 0)
                print(f"✅ Calculated scores for {self.stats['scores_calculated']} products")
            else:
                self.stats['scores_calculated'] = 0
                print("✅ No products found for score calculation")
        except Exception as e:
            print(f"❌ Error calculating scores: {e}")
            import traceback
            traceback.print_exc()
            self.stats['errors'] += 1
        
        # Final statistics
        print(f"\n📊 Phase 3 Complete!")
        print(f"   ✨ Pros/Cons generated: {self.stats['pros_cons_generated']}")
        print(f"   🎨 Pretty titles generated: {self.stats['pretty_titles_generated']}")
        print(f"   📝 Summaries generated: {self.stats['summaries_generated']}")
        print(f"   🔍 Fields extracted: {sum(self.stats['fields_extracted'].values())}")
        print(f"   📂 Categories assigned: {self.stats['categories_assigned']}")
        print(f"   📊 Scores calculated: {self.stats['scores_calculated']}")
        print(f"   ❌ Errors: {self.stats['errors']}")
        
        return self.stats
    
    def _generate_enhanced_amazon_features(self) -> Dict[str, Any]:
        """Generate enhanced pros/cons using Amazon API data"""
        import sqlite3
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        try:
            # Get all products that have Amazon data
            cursor.execute("""
                SELECT id FROM products 
                WHERE amazon_asin IS NOT NULL 
                AND amazon_asin != ''
                ORDER BY id
            """)
            
            product_ids = [row[0] for row in cursor.fetchall()]
            total_features = 0
            processed_products = 0
            
            print(f"   📦 Processing {len(product_ids)} products with Amazon data...")
            
            for i, product_id in enumerate(product_ids):
                try:
                    # Generate enhanced features for this product
                    features = self.enhanced_amazon_pros_cons.generate_enhanced_features(product_id)
                    
                    if features:
                        # Save to database
                        if self.enhanced_amazon_pros_cons.save_enhanced_features(product_id):
                            total_features += len(features)
                            processed_products += 1
                            
                            if (i + 1) % 10 == 0:
                                print(f"   ✅ Processed {i + 1}/{len(product_ids)} products...")
                    
                except Exception as e:
                    print(f"   ⚠️ Error processing product {product_id}: {e}")
                    continue
            
            print(f"   🎯 Enhanced features generated for {processed_products} products")
            
            return {
                'total_features_generated': total_features,
                'processed_products': processed_products,
                'total_products': len(product_ids)
            }
            
        except Exception as e:
            print(f"   ❌ Error in enhanced features generation: {e}")
            return {
                'total_features_generated': 0,
                'processed_products': 0,
                'total_products': 0
            }
        finally:
            conn.close()

    def _generate_structured_features_from_amazon(self) -> Dict[str, Any]:
        """Parse smart_features.feature_text from amazon_raw source into structured features.
        Creates info/pro features with categories like certification, material, weave, thread_count,
        set_specs, fit, care, comfort, sustainability, award.
        Avoids duplicates per (product_id, feature_text).
        """
        import sqlite3
        import re
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        features_inserted = 0
        try:
            cursor.execute(
                """
                SELECT sf.product_id, sf.feature_text
                FROM smart_features sf
                JOIN products p ON p.id = sf.product_id
                WHERE TRIM(sf.feature_text) != '' AND sf.source_type = 'amazon_raw'
                """
            )
            rows = cursor.fetchall()
            
            # Existing to prevent duplicates
            cursor.execute("SELECT product_id, feature_text FROM smart_features WHERE source_type = 'structured_extraction'")
            existing = set(cursor.fetchall())
            
            # Regex helpers
            tc_re = re.compile(r"(\d{3,4})\s*[- ]?thread", re.I)
            depth_re = re.compile(r"(\d{1,2})(?:\s*[-–]\s*|\s*)?(?:in|inch|\")\s*(?:deep|pocket)?", re.I)
            piece_re = re.compile(r"(\b[2-9]\b)\s*(?:pc|pcs|piece|pieces)", re.I)
            oeko = re.compile(r"oeko[- ]?tex", re.I)
            gots = re.compile(r"\bgots\b", re.I)
            fair = re.compile(r"fair\s*trade", re.I)
            percale = re.compile(r"\bpercale\b", re.I)
            sateen = re.compile(r"\bsateen\b", re.I)
            flannel = re.compile(r"\bflannel\b", re.I)
            jersey = re.compile(r"\bjersey\b", re.I)
            cooling = re.compile(r"cool(ing)?|moisture[- ]?wick|breathable|temperature regulating", re.I)
            hypo = re.compile(r"hypoallergenic|skin[- ]?friendly", re.I)
            elastic = re.compile(r"(all[- ]around|360|wide)\s*elastic|elasticized", re.I)
            envelope = re.compile(r"envelope\s*closure|zipper", re.I)
            award = re.compile(r"good housekeeping|award|gold seal", re.I)
            organic = re.compile(r"\borganic\b", re.I)
            recycled = re.compile(r"recycled", re.I)
            sustainable = re.compile(r"sustainable|eco[- ]?friendly|eco friendly", re.I)
            bamboo = re.compile(r"bamboo|viscose\s*from\s*bamboo", re.I)
            linen = re.compile(r"\blinen\b", re.I)
            microfiber = re.compile(r"microfiber|polyester", re.I)
            cotton = re.compile(r"\bcotton\b", re.I)
            long_staple = re.compile(r"(long|extra[- ]?long)\s*staple", re.I)
            
            def insert_feature(pid: int, text: str, category: str, ftype: str = 'info', importance: str = 'high', explanation: str = None, impact: float = 0.5):
                nonlocal features_inserted
                key = (pid, text)
                if key in existing:
                    return
                cursor.execute(
                    """
                    INSERT INTO smart_features
                    (product_id, feature_text, feature_type, enhanced_feature_type, category, importance, explanation, impact_score, product_specific, source_type, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, 'structured_extraction', ?)
                    """,
                    (pid, text, ftype, 'info', category, importance, explanation or '', impact, datetime.now().isoformat())
                )
                existing.add(key)
                features_inserted += 1
            
            for pid, ftxt in rows:
                t = (ftxt or '').strip()
                if not t:
                    continue
                lower = t.lower()
                
                # Certifications
                if oeko.search(lower):
                    insert_feature(pid, "OEKO-TEX certified", "certification", "pro", "trusted safety standard", 0.6)
                if gots.search(lower):
                    insert_feature(pid, "GOTS organic certified", "certification", "pro", "global organic textile standard", 0.7)
                if fair.search(lower):
                    insert_feature(pid, "Fair Trade compliant", "certification", "pro", "ethical sourcing standard", 0.5)
                
                # Material
                if bamboo.search(lower):
                    insert_feature(pid, "Bamboo viscose material", "material", "info", "soft, cooling feel", 0.4)
                if linen.search(lower):
                    insert_feature(pid, "Linen fabric", "material", "info", "breathable, textured handfeel", 0.4)
                if microfiber.search(lower):
                    insert_feature(pid, "Microfiber construction", "material", "info", "easy care synthetic", 0.3)
                if cotton.search(lower):
                    if long_staple.search(lower):
                        insert_feature(pid, "Long-staple cotton", "material", "pro", "stronger, smoother yarns", 0.6)
                    else:
                        insert_feature(pid, "Cotton fabric", "material", "info", "natural, breathable", 0.3)
                
                # Weave
                if percale.search(lower):
                    insert_feature(pid, "Percale weave (crisp & cool)", "weave", "info", "matte, cool hand", 0.5)
                if sateen.search(lower):
                    insert_feature(pid, "Sateen weave (smooth & lustrous)", "weave", "info", "silky handfeel", 0.5)
                if flannel.search(lower):
                    insert_feature(pid, "Flannel (brushed warm finish)", "weave", "info", "warm & cozy", 0.5)
                if jersey.search(lower):
                    insert_feature(pid, "Jersey knit (t-shirt soft)", "weave", "info", "stretchy comfort", 0.4)
                
                # Thread count
                m = tc_re.search(lower)
                if m:
                    insert_feature(pid, f"Thread count: {m.group(1)}", "thread_count", "info", "stated TC in bullets", 0.4)
                
                # Fit / pocket depth
                m = depth_re.search(lower)
                if m:
                    insert_feature(pid, f"Fits mattresses up to {m.group(1)}\"", "fit", "pro", "deep-pocket fitted sheet", 0.5)
                if elastic.search(lower):
                    insert_feature(pid, "All-around elastic fitted sheet", "fit", "pro", "secure fit", 0.4)
                
                # Set specs
                m = piece_re.search(lower)
                if m:
                    insert_feature(pid, f"{m.group(1)}-piece set", "set_specs", "info", "contents noted in bullets", 0.3)
                if envelope.search(lower):
                    insert_feature(pid, "Envelope/zippered pillowcases", "set_specs", "info", "secure pillow closure", 0.3)
                
                # Care & durability
                if 'machine washable' in lower or 'machine wash' in lower:
                    insert_feature(pid, "Machine washable", "care", "info", "easy care", 0.2)
                if 'wrinkle' in lower:
                    insert_feature(pid, "Wrinkle resistant", "care", "pro", "easier upkeep", 0.3)
                if 'shrink' in lower or 'shrinkage' in lower:
                    insert_feature(pid, "Shrink resistant", "care", "pro", "maintains size", 0.3)
                if 'fade' in lower:
                    insert_feature(pid, "Fade resistant", "care", "pro", "colorfast over washes", 0.3)
                
                # Comfort
                if cooling.search(lower):
                    insert_feature(pid, "Cooling & breathable", "comfort", "pro", "better temp regulation", 0.5)
                if hypo.search(lower):
                    insert_feature(pid, "Hypoallergenic/skin-friendly", "comfort", "pro", "gentle on skin", 0.4)
                
                # Sustainability & awards
                if organic.search(lower):
                    insert_feature(pid, "Organic materials", "sustainability", "pro", "lower-impact fibers", 0.4)
                if recycled.search(lower):
                    insert_feature(pid, "Recycled content", "sustainability", "pro", "reduced waste", 0.3)
                if sustainable.search(lower):
                    insert_feature(pid, "Sustainable practices", "sustainability", "info", "eco positioning", 0.3)
                if award.search(lower):
                    insert_feature(pid, "Award or seal mentioned", "award", "pro", "third-party validation", 0.4)
            
            conn.commit()
            return { 'features_inserted': features_inserted }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

    def _enrich_brands_from_features(self) -> Dict[str, Any]:
        """Parse smart_features from amazon_raw source to enrich brands table extended fields.
        Fills: company_type, environmental_certifications, sustainability_practices, brand_story, customer_satisfaction_score.
        Only sets fields when currently NULL/empty.
        """
        import sqlite3
        import re
        from datetime import datetime
        
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        brands_updated = 0
        try:
            # Get all brands
            cursor.execute("SELECT id, name, company_type, environmental_certifications, sustainability_practices, brand_story, customer_satisfaction_score FROM brands")
            brands = cursor.fetchall()
            
            for brand in brands:
                (brand_id, name, company_type, env_certs, sustain, story, csat) = brand
                
                # Gather all feature texts for products under this brand
                cursor.execute(
                    """
                    SELECT sf.feature_text
                    FROM smart_features sf
                    JOIN products p ON p.id = sf.product_id
                    WHERE p.brand_id = ? AND sf.source_type = 'amazon_raw'
                    """,
                    (brand_id,)
                )
                feature_rows = cursor.fetchall()
                feature_texts = " \n".join([row[0] for row in feature_rows if row and row[0]])
                
                if not feature_texts and company_type and env_certs and sustain and story and csat is not None:
                    continue  # nothing to enrich
                
                updates = {}
                
                text = feature_texts.lower()
                
                # company_type
                if not company_type:
                    if re.search(r"small\s+business", text):
                        updates['company_type'] = 'small_business'
                    elif 'veteran' in text:
                        updates['company_type'] = 'veteran_owned'
                    elif 'family owned' in text or 'family-owned' in text:
                        updates['company_type'] = 'family_owned'
                
                # environmental_certifications
                if not env_certs:
                    certs = []
                    if 'oeko-tex' in text or 'oekotex' in text:
                        certs.append('OEKO-TEX')
                    if 'gots' in text:
                        certs.append('GOTS')
                    if 'fair trade' in text:
                        certs.append('Fair Trade')
                    if certs:
                        updates['environmental_certifications'] = ", ".join(sorted(set(certs)))
                
                # sustainability_practices
                if not sustain:
                    practices = []
                    if 'organic' in text:
                        practices.append('organic_materials')
                    if 'sustainable' in text or 'eco-friendly' in text or 'eco friendly' in text:
                        practices.append('sustainable_practices')
                    if 'recycled' in text:
                        practices.append('recycled_materials')
                    if practices:
                        updates['sustainability_practices'] = ", ".join(sorted(set(practices)))
                
                # brand_story (simple condensed line from first two distinct features)
                if not story and feature_rows:
                    first_lines = [row[0].strip() for row in feature_rows if row and row[0].strip()]
                    if first_lines:
                        updates['brand_story'] = (" ".join(first_lines[:2]))[:500]
                
                # customer_satisfaction_score from reviews average if available (disabled - amazon_reviews table removed)
                # if csat is None:
                #     # This functionality is disabled since amazon_reviews table was removed
                #     pass
                
                if updates:
                    # Build dynamic update
                    set_clause = ", ".join([f"{k} = ?" for k in updates.keys()]) + ", amazon_last_updated = ?"
                    values = list(updates.values()) + [datetime.now().isoformat()]
                    cursor.execute(f"UPDATE brands SET {set_clause} WHERE id = ?", values + [brand_id])
                    brands_updated += 1
            
            conn.commit()
            return { 'brands_updated': brands_updated }
        except Exception as e:
            conn.rollback()
            raise e
        finally:
            conn.close()

def main():
    """Run Phase 3: Content Generation Pipeline"""
    pipeline = ContentGenerationPipeline()
    results = pipeline.run_content_generation()
    
    print(f"\n🎉 Phase 3 Complete!")
    print(f"Results: {results}")

if __name__ == "__main__":
    main()
