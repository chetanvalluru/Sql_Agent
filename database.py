import pymysql
import sqlite3
import os
from typing import List, Dict, Any
import asyncio
from concurrent.futures import ThreadPoolExecutor

class DatabaseManager:
    def __init__(self):
        self.host = os.getenv("DB_HOST", "localhost")
        self.port = int(os.getenv("DB_PORT", 3306))
        self.user = os.getenv("DB_USER", "root")
        self.password = os.getenv("DB_PASSWORD", "")
        self.database = os.getenv("DB_NAME", "Salesforce")
        self.use_sqlite = os.getenv("USE_SQLITE", "False").lower() == "true"
        self.executor = ThreadPoolExecutor(max_workers=4)
    
    async def execute_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQL query and return results as list of dictionaries"""
        try:
            # Run database operation in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor, 
                self._execute_query_sync, 
                sql
            )
            return results
        except Exception as e:
            raise Exception(f"Database error: {str(e)}")
    
    def _execute_query_sync(self, sql: str) -> List[Dict[str, Any]]:
        """Synchronous database query execution"""
        if self.use_sqlite:
            return self._execute_sqlite_query(sql)
        else:
            return self._execute_mysql_query(sql)
    
    def _execute_sqlite_query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute SQLite query"""
        conn = None
        try:
            conn = sqlite3.connect(self.database)
            conn.row_factory = sqlite3.Row  # This makes rows dict-like
            
            cursor = conn.cursor()
            cursor.execute(sql)
            
            # Handle different types of queries
            if sql.strip().upper().startswith(('SELECT', 'PRAGMA')):
                results = cursor.fetchall()
                return [dict(row) for row in results]
            else:
                # For INSERT, UPDATE, DELETE
                conn.commit()
                return [{"affected_rows": cursor.rowcount, "message": "Query executed successfully"}]
                
        except Exception as e:
            if conn:
                conn.rollback()
            raise e
        finally:
            if conn:
                conn.close()
    
    def _execute_mysql_query(self, sql: str, params=None) -> List[Dict[str, Any]]:
        """Execute MySQL query"""
        connection = None
        try:
            connection = pymysql.connect(
                host=self.host,
                port=self.port,
                user=self.user,
                password=self.password,
                database=self.database,
                charset='utf8mb4',
                cursorclass=pymysql.cursors.DictCursor
            )
            
            with connection.cursor() as cursor:
                if params:
                    cursor.execute(sql, params)
                else:
                    cursor.execute(sql)
                
                # Handle different types of queries
                if sql.strip().upper().startswith(('SELECT', 'SHOW', 'DESCRIBE')):
                    results = cursor.fetchall()
                    return results
                else:
                    # For INSERT, UPDATE, DELETE
                    connection.commit()
                    return [{"affected_rows": cursor.rowcount, "message": "Query executed successfully"}]
                    
        except Exception as e:
            if connection:
                connection.rollback()
            raise e
        finally:
            if connection:
                connection.close()
    
    async def get_schema_info(self) -> Dict[str, Any]:
        """Get database schema information for context"""
        try:
            if self.use_sqlite:
                return await self._get_sqlite_schema_info()
            else:
                return await self._get_mysql_schema_info()
        except Exception as e:
            raise Exception(f"Failed to get schema info: {str(e)}")
    
    async def _get_sqlite_schema_info(self) -> Dict[str, Any]:
        """Get schema information from SQLite database"""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._execute_sqlite_query,
                "SELECT name FROM sqlite_master WHERE type='table'"
            )
            
            schema = {}
            for table_row in results:
                table_name = table_row['name']
                
                # Get table info
                table_info = await loop.run_in_executor(
                    self.executor,
                    self._execute_sqlite_query,
                    f"PRAGMA table_info({table_name})"
                )
                
                schema[table_name] = []
                for col in table_info:
                    schema[table_name].append({
                        'column': col['name'],
                        'type': col['type'],
                        'nullable': 'YES' if col['notnull'] == 0 else 'NO',
                        'key': 'PRI' if col['pk'] == 1 else ''
                    })
            
            return schema
            
        except Exception as e:
            raise Exception(f"Failed to get SQLite schema info: {str(e)}")
    
    async def _get_mysql_schema_info(self) -> Dict[str, Any]:
        """Get schema information from MySQL database"""
        try:
            schema_query = """
            SELECT 
                TABLE_NAME,
                COLUMN_NAME,
                DATA_TYPE,
                IS_NULLABLE,
                COLUMN_KEY
            FROM INFORMATION_SCHEMA.COLUMNS 
            WHERE TABLE_SCHEMA = %s
            ORDER BY TABLE_NAME, ORDINAL_POSITION
            """
            
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                self.executor,
                self._execute_mysql_query,
                schema_query,
                (self.database,)
            )
            
            # Organize schema by table
            schema = {}
            for row in results:
                table_name = row['TABLE_NAME']
                if table_name not in schema:
                    schema[table_name] = []
                schema[table_name].append({
                    'column': row['COLUMN_NAME'],
                    'type': row['DATA_TYPE'],
                    'nullable': row['IS_NULLABLE'],
                    'key': row['COLUMN_KEY']
                })
            
            return schema
            
        except Exception as e:
            raise Exception(f"Failed to get MySQL schema info: {str(e)}")
    
    def test_connection(self) -> bool:
        """Test database connection"""
        if self.use_sqlite:
            try:
                conn = sqlite3.connect(self.database)
                conn.close()
                return True
            except Exception:
                return False
        else:
            try:
                connection = pymysql.connect(
                    host=self.host,
                    port=self.port,
                    user=self.user,
                    password=self.password,
                    database=self.database,
                    charset='utf8mb4'
                )
                connection.close()
                return True
            except Exception:
                return False

    async def get_sample_data(self) -> Dict[str, Any]:
        """Get sample data from all tables"""
        try:
            if self.use_sqlite:
                return await self._get_sqlite_sample_data()
            else:
                return await self._get_mysql_sample_data()
        except Exception as e:
            raise Exception(f"Failed to get sample data: {str(e)}")
    
    async def _get_sqlite_sample_data(self) -> Dict[str, Any]:
        """Get enhanced sample data from SQLite database with context"""
        tables = ['Account', 'Contact', 'Opportunity', 'Session', 'ProgramInstructorAvailability']
        sample_data = {}
        
        for table in tables:
            try:
                loop = asyncio.get_event_loop()
                
                # Get sample data with more context-relevant queries
                if table == 'Contact':
                    # Show variety of contact types/roles
                    query = f"SELECT * FROM {table} ORDER BY Title LIMIT 5"
                elif table == 'Session':
                    # Show different session types and statuses
                    query = f"SELECT * FROM {table} ORDER BY Status, Name LIMIT 5"
                elif table == 'Opportunity':
                    # Show different opportunity stages
                    query = f"SELECT * FROM {table} ORDER BY StageName LIMIT 5"
                else:
                    query = f"SELECT * FROM {table} LIMIT 5"
                
                results = await loop.run_in_executor(
                    self.executor,
                    self._execute_sqlite_query,
                    query
                )
                sample_data[table] = results
            except Exception:
                sample_data[table] = []
        
        return sample_data
    
    async def _get_mysql_sample_data(self) -> Dict[str, Any]:
        """Get enhanced sample data from MySQL database with context"""
        tables = ['Account', 'Contact', 'Opportunity', 'Session', 'ProgramInstructorAvailability']
        sample_data = {}
        
        for table in tables:
            try:
                loop = asyncio.get_event_loop()
                
                # Get sample data with more context-relevant queries
                if table == 'Contact':
                    # Show variety of contact types/roles
                    query = f"SELECT * FROM {table} ORDER BY Title LIMIT 5"
                elif table == 'Session':
                    # Show different session types and statuses
                    query = f"SELECT * FROM {table} ORDER BY Status, Name LIMIT 5"
                elif table == 'Opportunity':
                    # Show different opportunity stages
                    query = f"SELECT * FROM {table} ORDER BY StageName LIMIT 5"
                else:
                    query = f"SELECT * FROM {table} LIMIT 5"
                
                results = await loop.run_in_executor(
                    self.executor,
                    self._execute_mysql_query,
                    query
                )
                sample_data[table] = results
            except Exception:
                sample_data[table] = []
        
        return sample_data
