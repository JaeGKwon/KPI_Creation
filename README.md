# Metabase KPI Extractor

A Python tool that extracts table metadata from Metabase API and generates useful KPIs using OpenAI's LLM.

## Features

- 🔐 **Metabase Authentication**: Secure API access with session management
- 📊 **Table Metadata Extraction**: Comprehensive table and column information
- 🔗 **Related Table Discovery**: Automatically finds and includes related table information
- 🤖 **AI-Powered KPI Generation**: Uses OpenAI GPT-4 to generate business-relevant KPIs
- 📝 **SQL Query Generation**: Provides ready-to-use SQL queries for each KPI
- 💾 **JSON Output**: Structured output for easy integration with other tools

## Prerequisites

- Python 3.8+
- Metabase instance with API access
- OpenAI API key
- Network access to both Metabase and OpenAI APIs

## Installation

1. **Clone or download the project files**
2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the project root with:
   ```bash
   # Metabase Configuration
   METABASE_URL=http://your-metabase-instance.com
   METABASE_USERNAME=your_username
   METABASE_PASSWORD=your_password
   
   # OpenAI Configuration
   OPENAI_API_KEY=your_openai_api_key_here
   ```

## Usage

### Quick Start

Run the main script with default table names:
```bash
python metabase_kpi_extractor.py
```

### Custom Table Names

Modify the `table_names` list in the `main()` function:
```python
table_names = [
    "your_table_name",
    "another_table",
    "custom_table"
]
```

### Programmatic Usage

```python
from metabase_kpi_extractor import MetabaseKPIExtractor

# Initialize
extractor = MetabaseKPIExtractor()

# Process specific tables
results = extractor.process_table_list(["users", "orders", "products"])

# Save results
extractor.save_results(results, "my_kpis.json")
```

## Testing

The project includes individual test scripts for each step:

### Step 1: Authentication Test
```bash
python test_step1_auth.py
```
Tests Metabase connection and authentication.

### Step 2: Metadata Extraction Test
```bash
python test_step2_auth.py
```
Tests table discovery and metadata extraction.

### Step 3: LLM KPI Generation Test
```bash
python test_step3_llm.py
```
Tests OpenAI integration and KPI generation.

### Step 4: Full Integration Test
```bash
python test_step4_integration.py
```
Tests the complete end-to-end workflow.

## Output Format

The tool generates a structured JSON output:

```json
{
  "table_name": {
    "table_name": "string",
    "table_id": "number",
    "metadata": {
      "table_info": {...},
      "fields": [...],
      "related_tables": [...]
    },
    "kpis": [
      {
        "kpi_name": "string",
        "description": "string",
        "business_value": "string",
        "sql_query": "string",
        "output_format": "string"
      }
    ]
  }
}
```

## API Endpoints Used

- `POST /api/session` - Authentication
- `GET /api/database` - List databases
- `GET /api/database/{id}/tables` - List tables in database
- `GET /api/table/{id}` - Get table metadata
- `GET /api/table/{id}/query_metadata` - Get table fields

## Error Handling

The tool includes comprehensive error handling for:
- Authentication failures
- Network connectivity issues
- API rate limiting
- Invalid responses
- LLM generation failures

## Rate Limiting

Built-in delays (2 seconds) between API calls to respect Metabase rate limits.

## Security Notes

- Credentials are stored in environment variables
- Session tokens are managed securely
- No sensitive data is logged

## Troubleshooting

### Common Issues

1. **Authentication Failed**
   - Verify Metabase URL, username, and password
   - Check if Metabase instance is accessible
   - Ensure user has API access permissions

2. **No Tables Found**
   - Verify table names exist in your Metabase instance
   - Check database permissions
   - Ensure tables are not hidden or restricted

3. **LLM Generation Failed**
   - Verify OpenAI API key is valid
   - Check API quota and billing
   - Ensure network access to OpenAI API

4. **Rate Limiting**
   - Increase delays in the code if needed
   - Check Metabase server logs for rate limit errors

### Debug Mode

Enable verbose logging by modifying the print statements in the code.

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Test thoroughly
5. Submit a pull request

## License

This project is provided as-is for educational and business use.

## Support

For issues and questions:
1. Check the troubleshooting section
2. Review the test scripts
3. Check Metabase and OpenAI documentation
4. Create an issue with detailed error information 