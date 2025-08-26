#!/usr/bin/env python3
"""
Script to process Phase 1 and Phase 2 TB tables and append KPIs to existing JSON
"""

import os
import sys
import json
import time
from metabase_kpi_extractor import MetabaseKPIExtractor

def process_phase_tables():
    """Process Phase 1 and Phase 2 tables and append to existing JSON"""
    
    # Phase 1: Core Business (Top 10)
    phase1_tables = [
        "tb_rfq",              # 견적요청서 (Core business)
        "tb_quotation",        # 견적서 (Core business)
        "tb_market_product",   # 마켓 상품 (Core product)
        "tb_purchase_order",   # 발주서 (Core business)
        "tb_oem_market_product", # OEM 마켓 상품
        "tb_payment_root",     # 결제 부모 테이블
        "tb_partner",          # 파트너 상세 정보
        "tb_user_info",        # 고객 상세 정보
        "tb_market_category",  # 마켓 상품 카테고리
        "tb_statistics_partner" # 파트너 통계
    ]
    
    # Phase 2: Extended Business (Next 15)
    phase2_tables = [
        "tb_market_seller",    # 마켓 판매자
        "tb_oem_market_order", # OEM 주문
        "tb_subscribe_partner", # 파트너구독정보
        "tb_sales_factory",    # 자동영업화 공장 DB
        "tb_type_service",     # 제조 서비스
        "tb_payment_method",   # 구독결제수단
        "tb_market_cart",      # 장바구니
        "tb_user_delivery",    # 고객 배송지 정보
        "tb_partner_equipment", # 파트너 보유장비
        "tb_statistics_user",  # 고객 통계
        "tb_payment_tax_invoice", # 세금계산서
        "tb_oem_market_payment", # OEM 마켓 결제
        "tb_market_order_address", # 마켓 주문 배송정보
        "tb_rfq_file",         # RFQ 관련 파일
        "tb_partner_product"   # 생산품
    ]
    
    all_phase_tables = phase1_tables + phase2_tables
    
    print(f"🚀 Processing {len(all_phase_tables)} Phase 1 & 2 tables...")
    print(f"📊 Phase 1: {len(phase1_tables)} tables | Phase 2: {len(phase2_tables)} tables")
    print("=" * 80)
    
    # Initialize extractor
    extractor = MetabaseKPIExtractor()
    
    # Authenticate
    if not extractor.authenticate_metabase():
        print("❌ Authentication failed")
        return
    
    # Load existing data
    existing_data = {}
    try:
        with open('tb_tables_kpis.json', 'r', encoding='utf-8') as f:
            existing_data = json.load(f)
        print(f"✅ Loaded existing data with {len(existing_data)} tables")
    except FileNotFoundError:
        print("⚠️  No existing tb_tables_kpis.json found, starting fresh")
    
    # Track progress
    processed_count = 0
    skipped_count = 0
    error_count = 0
    
    # Process each table
    for i, table_name in enumerate(all_phase_tables, 1):
        print(f"\n🔄 Processing table {i}/{len(all_phase_tables)}: {table_name}")
        print("-" * 60)
        
        # Check if already processed
        if table_name in existing_data:
            print(f"⏭️  Table {table_name} already processed, skipping...")
            skipped_count += 1
            continue
        
        try:
            # First, search for the table by name to get table info (including ID)
            print(f"🔍 Searching for table: {table_name}...")
            table_info = extractor.search_tables_by_name([table_name])
            
            if not table_info:
                print(f"❌ Table {table_name} not found")
                error_count += 1
                continue
            
            # Get the first (and should be only) result
            table_basic = table_info[0]
            table_id = table_basic.get('id')
            
            print(f"✅ Found table: {table_name} (ID: {table_id})")
            print(f"📋 Table description: {table_basic.get('description', 'No description')}")
            
            # Get complete table metadata using the table ID
            print(f"🔍 Fetching complete table metadata...")
            table_metadata = extractor.get_table_metadata(table_id)
            
            if not table_metadata:
                print(f"❌ Failed to get metadata for {table_name}")
                error_count += 1
                continue
            
            # Generate KPIs for the table
            print(f"🤖 Generating KPIs for {table_name}...")
            result = extractor.generate_kpis_for_table(table_name, table_metadata)
            
            if result and 'kpis' in result:
                # Add to existing data
                existing_data[table_name] = {
                    "table_info": {
                        "name": table_name,
                        "description": table_basic.get('description', f'Phase table: {table_name}'),
                        "total_fields": result.get('total_fields', 0),
                        "fields_used": result.get('fields_used', 0),
                        "foreign_keys": result.get('foreign_keys', 0),
                        "related_tables": len(table_metadata.get('related_tables', []))
                    },
                    "field_details": result.get('field_details', []),
                    "kpis": result['kpis']
                }
                
                print(f"✅ Successfully processed {table_name} with {len(result['kpis'])} KPIs")
                processed_count += 1
                
                # Save progress after each table
                with open('tb_tables_kpis.json', 'w', encoding='utf-8') as f:
                    json.dump(existing_data, f, indent=2, ensure_ascii=False)
                print(f"💾 Progress saved to tb_tables_kpis.json")
                
            else:
                print(f"⚠️  No KPIs generated for {table_name}")
                error_count += 1
                
        except Exception as e:
            print(f"❌ Error processing {table_name}: {e}")
            error_count += 1
        
        # Add delay between requests to be respectful
        if i < len(all_phase_tables):
            print("⏳ Waiting 2 seconds before next table...")
            time.sleep(2)
    
    # Final summary
    print("\n" + "=" * 80)
    print("🎯 PROCESSING COMPLETE!")
    print("=" * 80)
    print(f"📊 SUMMARY:")
    print(f"  • Total Phase tables: {len(all_phase_tables)}")
    print(f"  • Successfully processed: {processed_count}")
    print(f"  • Skipped (already processed): {skipped_count}")
    print(f"  • Errors: {error_count}")
    print(f"  • Total tables in JSON: {len(existing_data)}")
    
    # Show newly added tables
    new_tables = [table for table in all_phase_tables if table in existing_data and table not in existing_data.get('_metadata', {}).get('original_tables', [])]
    if new_tables:
        print(f"\n🆕 Newly added tables:")
        for table in new_tables:
            print(f"  • {table}")
    
    print(f"\n💾 Final results saved to: tb_tables_kpis.json")
    
    return existing_data

if __name__ == "__main__":
    process_phase_tables() 