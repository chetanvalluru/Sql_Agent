from fastapi import FastAPI, Request, HTTPException
from fastapi.templating import Jinja2Templates
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from pydantic import BaseModel
import os
from dotenv import load_dotenv
from database import DatabaseManager
from sql_generator import SQLGenerator

# Load environment variables
load_dotenv()

app = FastAPI(title="SQL Agent", description="Natural Language to SQL Chat Interface")

# Mount static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

# Initialize components
db_manager = DatabaseManager()
sql_generator = SQLGenerator()

class QueryRequest(BaseModel):
    query: str

class QueryResponse(BaseModel):
    sql: str
    results: list
    error: str = None
    suggestions: list = None
    fuzzy_matches: list = None

@app.get("/", response_class=HTMLResponse)
async def home(request: Request):
    """Render the main chat interface"""
    return templates.TemplateResponse("index.html", {"request": request})

@app.post("/api/query", response_model=QueryResponse)
async def process_query(request: QueryRequest):
    """Process natural language query and return SQL results with fuzzy matching support"""
    try:
        # Get database schema information and sample data
        schema_info = await db_manager.get_schema_info()
        sample_data = await db_manager.get_sample_data()
        
        # Generate SQL from natural language with enhanced context and fuzzy matching
        sql_query = await sql_generator.generate_sql(request.query, schema_info, sample_data)
        
        # Validate the generated SQL and get suggestions
        validated_sql, validation_suggestions = await sql_generator.validate_and_suggest_sql(
            sql_query, schema_info
        )
        
        try:
            # Execute the query
            results = await db_manager.execute_query(validated_sql)
            
            return QueryResponse(
                sql=validated_sql,
                results=results,
                suggestions=validation_suggestions if validation_suggestions else None
            )
            
        except Exception as db_error:
            # Handle SQL execution errors with intelligent suggestions
            error_analysis = await sql_generator.handle_sql_error(
                str(db_error), validated_sql, schema_info
            )
            
            return QueryResponse(
                sql=validated_sql,
                results=[],
                error=str(db_error),
                suggestions=error_analysis.get('suggestions', []),
                fuzzy_matches=error_analysis.get('column_corrections', {})
            )
    
    except Exception as e:
        return QueryResponse(
            sql="",
            results=[],
            error=str(e)
        )

@app.get("/api/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "healthy", "message": "Chat with DB is running"}

@app.get("/api/schema")
async def get_schema():
    """Get database schema information"""
    try:
        schema_info = await db_manager.get_schema_info()
        return {"schema": schema_info}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/sample-data")
async def get_sample_data():
    """Get sample data from all tables"""
    try:
        sample_data = await db_manager.get_sample_data()
        return {"sample_data": sample_data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/data-dictionary")
async def get_data_dictionary():
    """Get comprehensive data dictionary with business context"""
    try:
        schema_info = await db_manager.get_schema_info()
        sample_data = await db_manager.get_sample_data()
        
        # Generate comprehensive data dictionary using the enhanced schema formatter
        data_dictionary = sql_generator._format_enhanced_schema_for_prompt(schema_info, sample_data)
        
        return {
            "data_dictionary": data_dictionary,
            "business_context": {
                "domain": "STEM Education Program Management",
                "system_type": "Salesforce-based CRM",
                "primary_entities": [
                    "Schools/Organizations (Account)",
                    "People (Contact)", 
                    "Program Opportunities (Opportunity)",
                    "Classes/Workshops (Session)",
                    "Instructor Scheduling (ProgramInstructorAvailability)"
                ],
                "common_use_cases": [
                    "Find available instructors for specific sessions",
                    "Track program enrollment and opportunities",
                    "Manage school partnerships and contacts",
                    "Schedule STEM classes and workshops",
                    "Monitor program success and completion rates"
                ]
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/fuzzy-match")
async def fuzzy_match_column(request: dict):
    """Test fuzzy matching for column names"""
    try:
        column_name = request.get("column_name", "")
        if not column_name:
            raise HTTPException(status_code=400, detail="column_name is required")
        
        schema_info = await db_manager.get_schema_info()
        
        # Use the fuzzy matcher directly
        matches = sql_generator.fuzzy_matcher.find_column_matches(
            column_name, schema_info, top_n=10
        )
        
        return {
            "query": column_name,
            "matches": [
                {
                    "column": match.matched_column,
                    "table": match.table_name,
                    "similarity": match.similarity_score,
                    "match_type": match.match_type,
                    "suggestion": match.suggestion
                }
                for match in matches
            ]
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "main:app",
        host=os.getenv("HOST", "0.0.0.0"),
        port=int(os.getenv("PORT", 8000)),
        reload=os.getenv("DEBUG", "True").lower() == "true"
    )
