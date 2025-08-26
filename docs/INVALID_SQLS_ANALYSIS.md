# Invalid SQLs Analysis Report

## 📊 Overview
- **Total Invalid SQLs**: 70
- **Generated At**: 2025-08-25 18:43:40
- **Success Rate**: 84.9% (395 out of 465 KPIs registered successfully)

## 🔍 Common Error Patterns

### 1. **Missing Column Errors** (Most Common - ~40% of failures)
**Pattern**: Column referenced in SQL doesn't exist in the actual table schema

**Examples**:
- `log_date` column missing from `tb_user` and `tb_user_activity_log`
- `cancelled_date` column missing from `tb_market_order_log`
- `status` column missing from `tb_market_cart`
- `return_date` column missing from `tb_market_cart`

**Root Cause**: LLM generated SQL based on assumed schema that doesn't match reality

### 2. **Non-Existent Table References** (~25% of failures)
**Pattern**: SQL tries to JOIN with tables that don't exist

**Examples**:
- `tb_order` table doesn't exist (referenced in `tb_market_order_log` queries)
- `tb_product` table doesn't exist (referenced in cart-related queries)
- `tb_purchase` table doesn't exist (referenced in cart completion queries)

**Root Cause**: LLM assumed table relationships that don't exist in the actual database

### 3. **JSON Operator Syntax Issues** (~20% of failures)
**Pattern**: Incorrect JSON operator syntax for PostgreSQL

**Examples**:
- Using `→` instead of `->` or `->>`
- `kc_value → import_type` should be `kc_value ->> 'import_type'`
- `tax_invoice_info → partner_name` should be `tax_invoice_info ->> 'partner_name'`

**Root Cause**: LLM used arrow symbols instead of proper PostgreSQL JSON operators

### 4. **Function Compatibility Issues** (~10% of failures)
**Pattern**: Using functions not available in PostgreSQL

**Examples**:
- `DATEDIFF()` function doesn't exist in PostgreSQL
- Should use `EXTRACT(EPOCH FROM (end_date - start_date))` or similar

**Root Cause**: LLM used SQL Server/MySQL syntax instead of PostgreSQL

### 5. **Nested Aggregate Function Errors** (~5% of failures)
**Pattern**: Invalid nesting of aggregate functions

**Examples**:
- `AVG(COUNT(*))` - cannot nest COUNT inside AVG
- `SUM(COUNT(DISTINCT column))` - invalid nesting

**Root Cause**: LLM generated complex aggregations that violate SQL rules

## 📋 Error Distribution by Table

### **High-Failure Tables**:
1. **`tb_user`** - 8 failures (all related to missing `log_date` column)
2. **`tb_user_activity_log`** - 6 failures (all related to missing `log_date` column)
3. **`tb_market_cart`** - 8 failures (missing `status` column and non-existent table references)
4. **`tb_market_order_log`** - 5 failures (missing `order_value` column and non-existent `tb_order` table)

### **Medium-Failure Tables**:
1. **`tb_payment_market`** - 4 failures (JSON operator syntax issues)
2. **`tb_oem_market_product`** - 3 failures (JSON operator syntax issues)

## 🎯 Recommendations for Future KPI Generation

### **1. Schema Validation**
- Always verify column existence before generating SQL
- Use actual table schemas, not assumed structures
- Validate table relationships before suggesting JOINs

### **2. Database-Specific Syntax**
- Use PostgreSQL-compatible functions only
- Proper JSON operators: `->` (returns JSON), `->>` (returns text)
- Use `EXTRACT()` instead of `DATEDIFF()`

### **3. Table Relationship Mapping**
- Create accurate table relationship documentation
- Only suggest JOINs between tables that actually exist
- Validate foreign key relationships

### **4. Error Prevention**
- Generate simpler SQL first, then enhance
- Avoid complex nested aggregations
- Test SQL against actual schema before finalizing

## 💡 Impact Analysis

### **Business Impact**:
- **70 KPIs** cannot be used for business analysis
- **Missing metrics** for user activity, cart analysis, and order tracking
- **Data gaps** in key business areas

### **Technical Impact**:
- **Schema mismatches** between generated SQL and actual database
- **Function compatibility** issues between different SQL dialects
- **Table relationship** assumptions that don't match reality

## 🔧 Next Steps

1. **Fix Schema Issues**: Update table schemas or adjust SQL generation
2. **Create Table Mapping**: Document actual table relationships
3. **Improve Validation**: Add schema validation to KPI generation process
4. **Fix High-Priority KPIs**: Address the most business-critical failed SQLs first

---

**Generated**: 2025-08-25 18:43:40  
**Analysis**: AI Assistant  
**Status**: Complete 