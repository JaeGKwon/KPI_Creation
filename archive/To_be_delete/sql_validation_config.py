#!/usr/bin/env python3
"""
Configuration file for SQL validation and fixing
"""

# Common SQL patterns to check
SQL_PATTERNS = {
    'missing_select': r'SELECT',
    'missing_from': r'FROM',
    'missing_where': r'WHERE',
    'missing_join_on': r'JOIN.*ON',
    'missing_null_check': r'(AVG|SUM|COUNT)\s*\(',
    'missing_date_check': r'(DATEDIFF|DATE_ADD|DATE_SUB|DATE_TRUNC)',
    'missing_interval': r'(MONTH|WEEK|DAY|YEAR)\s+',
    'missing_type_cast': r'CAST\s*\(',
    'missing_coalesce': r'COALESCE\s*\(',
}

# Common SQL fixes
SQL_FIXES = {
    'add_null_check': {
        'pattern': r'(AVG|SUM|COUNT)\s*\(([^)]+)\)',
        'replacement': r'\1(CASE WHEN \2 IS NOT NULL THEN \2 ELSE NULL END)'
    },
    'add_date_check': {
        'pattern': r'(DATEDIFF|DATE_ADD|DATE_SUB|DATE_TRUNC)\s*\(([^)]+)\)',
        'replacement': r'CASE WHEN \2 IS NOT NULL THEN \1(\2) ELSE NULL END'
    },
    'add_default_duration': {
        'pattern': r'WHERE\s+(.+)',
        'replacement': r'WHERE \1 AND create_date >= DATE_SUB(CURRENT_DATE, INTERVAL 1 MONTH)'
    }
}

# Default values
DEFAULT_VALUES = {
    'duration': 'INTERVAL 1 MONTH',
    'date_column': 'create_date',
    'timeout_seconds': 30,
    'max_retries': 3
}

# Error messages to look for
ERROR_PATTERNS = {
    'table_not_found': ['table', 'doesn\'t exist', 'not found'],
    'column_not_found': ['column', 'doesn\'t exist', 'unknown column'],
    'syntax_error': ['syntax error', 'syntax near', 'unexpected'],
    'type_mismatch': ['type mismatch', 'incompatible types', 'cannot convert'],
    'permission_error': ['access denied', 'permission denied', 'insufficient privileges']
} 