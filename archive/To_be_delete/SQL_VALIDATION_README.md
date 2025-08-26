# SQL Validation and Fixing Solution

## Overview
This solution provides comprehensive SQL validation and fixing for KPI SQL queries from `tb_tables_kpis.json`. It checks syntax, validates against schema, tests execution, uses LLM to fix errors, and separates problematic SQL without modifying the original JSON file.

## 🚀 Features

### **1. Schema Analysis**
- **Extracts field information** from the JSON file
- **Maps table structures** and field types
- **Identifies relationships** between tables and columns

### **2. SQL Syntax Checking**
- **Basic SQL syntax validation** (SELECT, FROM, WHERE, JOIN)
- **Common pattern detection** (NULL handling, date operations, type conversions)
- **Schema-aware validation** using actual table/column information

### **3. SQL Execution Testing**
- **Real database execution** testing via Metabase API
- **Result validation** (checking for data returned)
- **Error message analysis** and categorization

### **4. LLM-Powered SQL Fixing**
- **Automatic error correction** using OpenAI GPT-4
- **Context-aware fixes** using table schema information
- **Multiple fix strategies** for different error types

### **5. Default Duration Handling**
- **Automatically adds 1-month duration** when time window is missing
- **Smart WHERE clause modification** for existing queries
- **Configurable default values** for different time periods

### **6. Problematic SQL Separation**
- **Creates separate document** for unresolved SQL issues
- **Detailed error logging** with context information
- **LLM fix attempt tracking** for manual review

## 📁 Files Created

### **Core Scripts**
- **`sql_validator_and_fixer.py`** - Main validation and fixing script
- **`sql_validation_config.py`** - Configuration and patterns
- **`register_kpis_enhanced.py`** - Enhanced registration with validation

### **Output Files**
- **`sql_validation_report.json`** - Comprehensive validation results
- **`problematic_sql_queries.json`** - SQL that couldn't be fixed
- **`sql_validation_log.txt`** - Detailed execution log

## 🔧 How It Works

### **Step 1: Schema Analysis**
```python
# Analyzes the JSON file to extract table structure
self.analyze_schema_from_json(json_file_path)
```

### **Step 2: Syntax and Pattern Checking**
```python
# Checks for common SQL issues using regex patterns
syntax_check = self.check_sql_syntax_and_common_issues(sql_query, table_name)
```

### **Step 3: Default Duration Addition**
```python
# Adds 1-month default duration when missing
modified_sql = self.add_default_duration(sql_query)
```

### **Step 4: Execution Testing**
```python
# Tests SQL against actual database
execution_success, execution_result = self.test_sql_execution(database_id, modified_sql)
```

### **Step 5: LLM Fixing (if needed)**
```python
# Uses OpenAI to fix SQL errors
fixed_sql = self.fix_sql_with_llm(modified_sql, table_name, error_message)
```

### **Step 6: Result Categorization**
```python
# Separates SQL into valid, fixed, and problematic categories
self.validation_results['valid_sql'].append(...)
self.validation_results['fixed_sql'].append(...)
self.validation_results['problematic_sql'].append(...)
```

## 🎯 Common SQL Issues Detected

### **Syntax Issues**
- Missing SELECT, FROM, WHERE clauses
- Incorrect JOIN syntax without ON clauses
- Malformed aggregate functions

### **Schema Issues**
- Non-existent table/column references
- Case sensitivity problems
- Type mismatches in operations

### **NULL Handling Issues**
- Missing NULL checks for aggregates
- Date operations without NULL validation
- JOIN conditions without NULL handling

### **Time Window Issues**
- Missing duration specifications
- Inconsistent date filtering
- No default time boundaries

### **Type Conversion Issues**
- Inappropriate CAST operations
- Missing COALESCE for NULL handling
- Data type mismatches in comparisons

## 🛠️ LLM Fixing Capabilities

### **What LLM Can Fix**
- **Syntax errors** in SQL statements
- **Missing NULL checks** for aggregates and dates
- **JOIN syntax** and ON clause issues
- **Type conversion** problems
- **Date filtering** and duration issues

### **LLM Fix Examples**
```sql
-- Original (problematic)
SELECT AVG(purchase_date - quotation_date) FROM orders

-- LLM Fixed
SELECT AVG(CASE WHEN purchase_date IS NOT NULL AND quotation_date IS NOT NULL 
            THEN DATEDIFF(purchase_date, quotation_date) ELSE NULL END) 
FROM orders
WHERE purchase_date IS NOT NULL AND quotation_date IS NOT NULL
```

## 📊 Output Structure

### **Validation Report (`sql_validation_report.json`)**
```json
{
  "summary": {
    "total_processed": 536,
    "valid_sql_count": 450,
    "fixed_sql_count": 75,
    "problematic_sql_count": 11
  },
  "valid_sql": [...],
  "fixed_sql": [...],
  "problematic_sql": [...]
}
```

### **Problematic SQL (`problematic_sql_queries.json`)**
```json
[
  {
    "table": "tb_market_order",
    "kpi_name": "Average Time to Purchase",
    "original_sql": "SELECT AVG(purchase_date - quotation_date)...",
    "error": "Column 'purchase_date' cannot be NULL",
    "llm_fix_attempted": true,
    "llm_fix_failed": true
  }
]
```

## 🚀 Usage Instructions

### **1. Setup Environment**
```bash
# Ensure .env file has required credentials
METABASE_URL=https://your-metabase.com
METABASE_USERNAME=your_username
METABASE_PASSWORD=your_password
OPENAI_API_KEY=your_openai_key
```

### **2. Run Validation**
```bash
python sql_validator_and_fixer.py
```

### **3. Review Results**
- Check `sql_validation_report.json` for overall results
- Review `problematic_sql_queries.json` for manual fixes
- Use fixed SQL for Metabase registration

### **4. Register Fixed KPIs**
```bash
python register_kpis_enhanced.py
```

## ⚠️ Important Notes

### **No Original File Modification**
- **Original `tb_tables_kpis.json` is NEVER modified**
- **All fixes are applied to copies** of the SQL
- **Original data integrity** is preserved

### **Database Requirements**
- **Metabase connection** must be available
- **Database permissions** for query execution
- **Network access** to Metabase API

### **LLM Usage**
- **OpenAI API key** required for automatic fixing
- **API costs** apply for each fix attempt
- **Rate limiting** may affect processing speed

## 🔍 Troubleshooting

### **Common Issues**
1. **Authentication failures** - Check Metabase credentials
2. **Database connection errors** - Verify database availability
3. **LLM API errors** - Check OpenAI API key and limits
4. **Schema analysis failures** - Verify JSON file structure

### **Performance Optimization**
- **Reduce delay** between requests (modify `time.sleep()`)
- **Batch processing** for large numbers of KPIs
- **Parallel execution** for independent SQL queries
- **Caching** of schema information

## 📈 Success Metrics

### **Expected Results**
- **80-90% SQL validation success** rate
- **60-80% automatic fixing** success rate
- **10-20% manual review** required
- **100% original data preservation**

### **Quality Improvements**
- **NULL-safe SQL** queries
- **Proper date handling** with default durations
- **Type-safe operations** with appropriate conversions
- **Schema-compliant** table and column references

## 🎯 Next Steps

### **Immediate Actions**
1. **Run validation** to identify current SQL issues
2. **Review problematic SQL** for manual fixes
3. **Use fixed SQL** for Metabase registration
4. **Monitor execution** success rates

### **Long-term Improvements**
1. **Custom SQL patterns** for your specific database
2. **Enhanced LLM prompts** for better fixing accuracy
3. **Automated testing** for new KPI additions
4. **Performance monitoring** and optimization

This solution ensures your KPI SQL queries are robust, error-free, and ready for production use in Metabase! 🎉 