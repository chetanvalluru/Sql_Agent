"""
Fuzzy Column Name Matching System

This module provides fuzzy matching capabilities for database column names,
helping to handle typos, case differences, and similar variations in column names.
"""

from typing import Dict, List, Tuple, Any, Optional
from rapidfuzz import fuzz, process
import re
from dataclasses import dataclass


@dataclass
class ColumnMatch:
    """Represents a fuzzy match result for a column name"""
    original_term: str
    matched_column: str
    table_name: str
    similarity_score: float
    match_type: str  # 'exact', 'fuzzy', 'alias', 'pattern'
    suggestion: str = None


class FuzzyColumnMatcher:
    """
    Handles fuzzy matching of column names with support for:
    - Typo correction using string similarity
    - Common aliases and abbreviations
    - Salesforce field naming patterns
    - Business terminology mapping
    """
    
    def __init__(self):
        self.similarity_threshold = 70  # Minimum similarity score (0-100)
        self.exact_threshold = 90  # Score above which we consider it an exact match
        
        # Common column aliases and business terms
        self.column_aliases = {
            # Common abbreviations
            'id': ['identifier', 'key', 'pk'],
            'name': ['title', 'label', 'description'],
            'email': ['mail', 'e-mail', 'email_address'],
            'phone': ['telephone', 'tel', 'mobile', 'cell'],
            'date': ['dt', 'datetime', 'timestamp'],
            'created': ['created_date', 'creation_date', 'date_created'],
            'modified': ['updated', 'modified_date', 'last_modified', 'date_modified'],
            'status': ['state', 'condition', 'stage'],
            'type': ['category', 'kind', 'classification'],
            'amount': ['value', 'cost', 'price', 'total'],
            
            # Business domain specific
            'instructor': ['teacher', 'staff', 'educator', 'facilitator'],
            'student': ['pupil', 'learner', 'participant'],
            'school': ['institution', 'organization', 'org', 'academy'],
            'program': ['course', 'class', 'session', 'workshop'],
            'semester': ['term', 'period', 'academic_year'],
            'contact': ['person', 'individual', 'user'],
            'account': ['organization', 'company', 'client', 'customer'],
            'opportunity': ['deal', 'project', 'engagement'],
            
            # Salesforce specific patterns
            'account_name': ['organization_name', 'company_name'],
            'contact_name': ['person_name', 'full_name'],
            'record_type': ['type', 'category', 'classification'],
            'stage_name': ['status', 'stage', 'phase'],
            'close_date': ['end_date', 'completion_date'],
            'is_deleted': ['deleted', 'active', 'inactive'],
        }
        
        # Reverse mapping for quick lookup
        self.alias_to_column = {}
        for column, aliases in self.column_aliases.items():
            for alias in aliases:
                self.alias_to_column[alias.lower()] = column.lower()
        
        # Common typo patterns
        self.typo_patterns = [
            # Common character substitutions
            (r'ph', 'f'),  # phone -> fone
            (r'tion', 'sion'),  # creation -> creacion
            (r'ie', 'ei'),  # field -> feild
            (r'ei', 'ie'),  # receive -> recieve
            (r'ss', 's'),  # address -> adress
            (r'mm', 'm'),  # comment -> coment
            (r'nn', 'n'),  # connection -> conection
        ]
    
    def find_column_matches(self, search_term: str, schema_info: Dict[str, Any], 
                          top_n: int = 5) -> List[ColumnMatch]:
        """
        Find the best matching columns for a search term across all tables.
        
        Args:
            search_term: The column name or term to search for
            schema_info: Database schema information
            top_n: Maximum number of matches to return
            
        Returns:
            List of ColumnMatch objects sorted by similarity score
        """
        matches = []
        search_term_lower = search_term.lower().strip()
        
        # Build a flat list of all columns with their table context
        all_columns = []
        for table_name, columns in schema_info.items():
            for col_info in columns:
                column_name = col_info['column']
                all_columns.append({
                    'column': column_name,
                    'table': table_name,
                    'column_lower': column_name.lower(),
                    'searchable_text': self._create_searchable_text(column_name, table_name)
                })
        
        # 1. Exact matches (case insensitive)
        for col in all_columns:
            if col['column_lower'] == search_term_lower:
                matches.append(ColumnMatch(
                    original_term=search_term,
                    matched_column=col['column'],
                    table_name=col['table'],
                    similarity_score=100.0,
                    match_type='exact'
                ))
        
        # 2. Alias matches
        if search_term_lower in self.alias_to_column:
            canonical_term = self.alias_to_column[search_term_lower]
            for col in all_columns:
                if canonical_term in col['column_lower']:
                    matches.append(ColumnMatch(
                        original_term=search_term,
                        matched_column=col['column'],
                        table_name=col['table'],
                        similarity_score=95.0,
                        match_type='alias',
                        suggestion=f"'{search_term}' matched as alias for '{col['column']}'"
                    ))
        
        # 3. Fuzzy matching using rapidfuzz
        if len(matches) < top_n:  # Only do fuzzy matching if we need more results
            # Try fuzzy matching against column names directly first
            column_names = [col['column_lower'] for col in all_columns]
            fuzzy_results = process.extract(
                search_term_lower, 
                column_names, 
                scorer=fuzz.WRatio,  # Weighted ratio for better results
                limit=top_n * 3  # Get more candidates to filter
            )
            
            for match_text, score, idx in fuzzy_results:
                if score >= self.similarity_threshold:
                    col = all_columns[idx]
                    # Avoid duplicates from exact/alias matches
                    if not any(m.matched_column == col['column'] and m.table_name == col['table'] 
                              for m in matches):
                        match_type = 'exact' if score >= self.exact_threshold else 'fuzzy'
                        matches.append(ColumnMatch(
                            original_term=search_term,
                            matched_column=col['column'],
                            table_name=col['table'],
                            similarity_score=float(score),
                            match_type=match_type,
                            suggestion=f"Did you mean '{col['column']}'?" if match_type == 'fuzzy' else None
                        ))
            
            # Also try fuzzy matching against searchable text for more complex matches
            if len(matches) < top_n:
                searchable_texts = [col['searchable_text'] for col in all_columns]
                fuzzy_results2 = process.extract(
                    search_term_lower, 
                    searchable_texts, 
                    scorer=fuzz.partial_ratio,  # Partial ratio for searchable text
                    limit=top_n * 2
                )
                
                for match_text, score, idx in fuzzy_results2:
                    if score >= max(60, self.similarity_threshold - 10):  # Lower threshold for searchable text
                        col = all_columns[idx]
                        # Avoid duplicates
                        if not any(m.matched_column == col['column'] and m.table_name == col['table'] 
                                  for m in matches):
                            matches.append(ColumnMatch(
                                original_term=search_term,
                                matched_column=col['column'],
                                table_name=col['table'],
                                similarity_score=float(score),
                                match_type='fuzzy',
                                suggestion=f"Did you mean '{col['column']}'? (context match)"
                            ))
        
        # 4. Pattern-based matching (Salesforce custom fields, etc.)
        if len(matches) < top_n:
            pattern_matches = self._find_pattern_matches(search_term, all_columns)
            matches.extend(pattern_matches)
        
        # Sort by similarity score (descending) and return top N
        matches.sort(key=lambda x: x.similarity_score, reverse=True)
        return matches[:top_n]
    
    def suggest_column_corrections(self, error_message: str, schema_info: Dict[str, Any]) -> List[str]:
        """
        Extract potential column names from SQL error messages and suggest corrections.
        
        Args:
            error_message: SQL error message
            schema_info: Database schema information
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        # Common SQL error patterns for unknown columns
        column_patterns = [
            r"Unknown column '([^']+)'",
            r"Column '([^']+)' doesn't exist",
            r"Invalid column name '([^']+)'",
            r"column \"([^\"]+)\" does not exist",
            r"no such column: ([^\s]+)",
        ]
        
        for pattern in column_patterns:
            matches = re.findall(pattern, error_message, re.IGNORECASE)
            for column_name in matches:
                # Clean up the column name (remove table prefixes if present)
                clean_column = column_name.split('.')[-1]
                
                # Find fuzzy matches
                column_matches = self.find_column_matches(clean_column, schema_info, top_n=3)
                
                if column_matches:
                    suggestions.append(f"Column '{column_name}' not found. Did you mean:")
                    for match in column_matches[:3]:  # Top 3 suggestions
                        suggestions.append(
                            f"  • {match.table_name}.{match.matched_column} "
                            f"(similarity: {match.similarity_score:.1f}%)"
                        )
                    suggestions.append("")  # Empty line for readability
        
        return suggestions
    
    def _create_searchable_text(self, column_name: str, table_name: str) -> str:
        """
        Create searchable text that includes variations and context.
        
        Args:
            column_name: Original column name
            table_name: Table name for context
            
        Returns:
            Searchable text string
        """
        # Start with the original column name
        searchable = column_name.lower()
        
        # Add variations without underscores and __c suffixes
        clean_name = column_name.replace('_', '').replace('__c', '').lower()
        if clean_name != searchable:
            searchable += ' ' + clean_name
        
        # Add space-separated version
        spaced_name = column_name.replace('_', ' ').replace('__c', '').lower()
        if spaced_name not in searchable:
            searchable += ' ' + spaced_name
        
        # Add table context for business meaning
        table_context = self._get_table_context(table_name)
        if table_context:
            searchable += ' ' + table_context
        
        return searchable
    
    def _get_table_context(self, table_name: str) -> str:
        """Get business context terms for a table to improve matching."""
        table_contexts = {
            'Account': 'organization company school client customer',
            'Contact': 'person individual user staff instructor teacher',
            'Opportunity': 'deal project program engagement grant donation',
            'Session': 'class workshop program course meeting',
            'ProgramInstructorAvailability': 'instructor teacher staff availability schedule',
            'Student': 'pupil learner participant child',
            'Campaign': 'marketing outreach communication email',
            'Lead': 'prospect potential customer inquiry',
        }
        return table_contexts.get(table_name, '')
    
    def _find_pattern_matches(self, search_term: str, all_columns: List[Dict]) -> List[ColumnMatch]:
        """Find matches based on common patterns (e.g., Salesforce custom fields)."""
        matches = []
        search_lower = search_term.lower()
        
        # Salesforce custom field patterns
        if not search_term.endswith('__c'):
            # Try adding __c suffix
            salesforce_term = search_term + '__c'
            for col in all_columns:
                if col['column_lower'] == salesforce_term.lower():
                    matches.append(ColumnMatch(
                        original_term=search_term,
                        matched_column=col['column'],
                        table_name=col['table'],
                        similarity_score=90.0,
                        match_type='pattern',
                        suggestion=f"Salesforce custom field: '{search_term}' -> '{col['column']}'"
                    ))
        
        # Partial word matching for compound field names
        for col in all_columns:
            col_parts = col['column_lower'].replace('_', ' ').replace('__c', '').split()
            if search_lower in col_parts or any(search_lower in part for part in col_parts):
                if not any(m.matched_column == col['column'] and m.table_name == col['table'] 
                          for m in matches):
                    matches.append(ColumnMatch(
                        original_term=search_term,
                        matched_column=col['column'],
                        table_name=col['table'],
                        similarity_score=80.0,
                        match_type='pattern',
                        suggestion=f"Partial match: '{search_term}' found in '{col['column']}'"
                    ))
        
        return matches
    
    def validate_sql_columns(self, sql_query: str, schema_info: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Validate column names in a SQL query and provide suggestions for invalid ones.
        
        Args:
            sql_query: SQL query to validate
            schema_info: Database schema information
            
        Returns:
            Tuple of (is_valid, list_of_suggestions)
        """
        suggestions = []
        is_valid = True
        
        # Extract potential column references from SQL
        # This is a simple regex-based approach - could be enhanced with proper SQL parsing
        column_patterns = [
            r'SELECT\s+(.+?)\s+FROM',
            r'WHERE\s+([^=<>!]+?)(?:\s*[=<>!]|\s+LIKE|\s+IN)',
            r'ORDER\s+BY\s+([^,\s]+)',
            r'GROUP\s+BY\s+([^,\s]+)',
            r'JOIN\s+\w+\s+ON\s+([^=\s]+)',
        ]
        
        # Build a set of all valid column names (with table prefixes)
        valid_columns = set()
        for table_name, columns in schema_info.items():
            for col_info in columns:
                column_name = col_info['column']
                valid_columns.add(column_name.lower())
                valid_columns.add(f"{table_name.lower()}.{column_name.lower()}")
        
        # Check for potential column references
        for pattern in column_patterns:
            matches = re.findall(pattern, sql_query, re.IGNORECASE | re.DOTALL)
            for match in matches:
                # Split by comma and clean up each potential column
                potential_columns = [col.strip() for col in match.split(',')]
                
                for col in potential_columns:
                    # Clean up the column reference
                    clean_col = re.sub(r'\s*(ASC|DESC)\s*$', '', col.strip(), flags=re.IGNORECASE)
                    clean_col = clean_col.strip('`"\'')  # Remove quotes
                    
                    # Skip SQL functions, keywords, and literals
                    if self._is_sql_keyword_or_function(clean_col):
                        continue
                    
                    # Check if column exists
                    if clean_col.lower() not in valid_columns:
                        # Try to find fuzzy matches
                        column_matches = self.find_column_matches(clean_col, schema_info, top_n=3)
                        if column_matches and column_matches[0].similarity_score < 95:
                            is_valid = False
                            suggestions.append(f"Potential issue with column '{clean_col}':")
                            for match in column_matches[:3]:
                                suggestions.append(
                                    f"  • Did you mean {match.table_name}.{match.matched_column}? "
                                    f"(similarity: {match.similarity_score:.1f}%)"
                                )
                            suggestions.append("")
        
        return is_valid, suggestions
    
    def _is_sql_keyword_or_function(self, term: str) -> bool:
        """Check if a term is likely a SQL keyword or function."""
        sql_keywords = {
            'select', 'from', 'where', 'join', 'inner', 'left', 'right', 'outer', 
            'on', 'and', 'or', 'not', 'in', 'like', 'between', 'is', 'null',
            'count', 'sum', 'avg', 'max', 'min', 'distinct', 'as', 'order', 'by',
            'group', 'having', 'limit', 'offset', 'union', 'all', 'case', 'when',
            'then', 'else', 'end', 'if', 'exists', 'any', 'some', '*'
        }
        
        term_lower = term.lower().strip()
        
        # Check for SQL keywords
        if term_lower in sql_keywords:
            return True
        
        # Check for function calls (contains parentheses)
        if '(' in term or ')' in term:
            return True
        
        # Check for numeric literals
        if re.match(r'^[\d\.\-\+]+$', term_lower):
            return True
        
        # Check for string literals
        if term.startswith("'") and term.endswith("'"):
            return True
        if term.startswith('"') and term.endswith('"'):
            return True
        
        return False
