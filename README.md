# Chat with DB - Natural Language to SQL Chat Interface

A sophisticated natural language to SQL conversion system built with FastAPI, LangChain, and modern web technologies. This Level 1 implementation provides a complete foundation for chatting with your database using plain English.

## 🎯 Project Overview

**Chat with DB** transforms natural language queries into SQL and executes them against your database, presenting results in a beautiful, interactive web interface. It's designed to be both user-friendly for non-technical users and powerful enough for complex database operations.

## ✨ Features Implemented (Level 1)

### ✅ Core Functionality
- **Natural Language Processing** - Convert English queries to SQL using OpenAI GPT-3.5
- **Database Integration** - Support for both SQLite and MySQL databases
- **Real-time Query Execution** - Execute SQL and return formatted results
- **Error Handling** - Comprehensive error handling with user-friendly messages

### ✅ User Interface
- **Modern Chat Interface** - Clean, responsive design with real-time messaging
- **Database Explorer** - Interactive schema and sample data viewer
- **Results Display** - Beautiful table formatting with copy functionality
- **Loading States** - Visual feedback during query processing
- **Mobile Responsive** - Works perfectly on all device sizes

### ✅ Database Features
- **Schema Awareness** - View table structures, column types, and relationships
- **Sample Data Viewer** - Browse actual data in each table
- **Multi-Database Support** - SQLite for testing, MySQL for production
- **Query Validation** - Safe query execution with proper error handling

### ✅ Developer Experience
- **Hot Reload** - Automatic server restart on code changes
- **Comprehensive Testing** - Setup verification and health checks
- **Clear Documentation** - Detailed setup and usage instructions
- **Modular Architecture** - Clean separation of concerns

## 🏗️ Project Structure

```
chat-with-db/
├── 📁 Backend (FastAPI)
│   ├── main.py                 # Main application entry point
│   ├── database.py            # Database connection and query management
│   ├── sql_generator.py       # LangChain SQL generation logic
│   └── requirements.txt       # Python dependencies
│
├── 📁 Frontend (HTML/CSS/JS)
│   ├── templates/
│   │   └── index.html         # Main chat interface template
│   └── static/
│       ├── css/
│       │   └── style.css      # Modern responsive styles
│       └── js/
│           └── app.js          # Interactive frontend logic
│
├── 📁 Configuration & Setup
│   ├── .env                   # Environment variables (create from template)
│   ├── config_template.txt    # Environment configuration template
│   ├── test_setup.py          # Setup verification script
│   └── setup_test_db.py       # Test database creation script
│
├── 📁 Documentation
│   └── README.md              # This comprehensive guide
│
└── 📁 Data
    └── test_database.db       # SQLite test database (auto-generated)
```

## 📋 File Descriptions & Summaries

### Backend Files

#### `main.py` - FastAPI Application
**Purpose**: Main application server and API endpoints
**Key Features**:
- FastAPI application setup with static file serving
- REST API endpoints for query processing
- Database schema and sample data endpoints
- Health check endpoint
- Auto-reload development server

**Endpoints**:
- `GET /` - Main chat interface
- `POST /api/query` - Process natural language queries
- `GET /api/schema` - Get database schema information
- `GET /api/sample-data` - Get sample data from tables
- `GET /api/health` - Health check

#### `database.py` - Database Manager
**Purpose**: Database connection and query execution
**Key Features**:
- Dual database support (SQLite & MySQL)
- Async query execution with thread pooling
- Schema extraction for both database types
- Sample data retrieval
- Connection testing and error handling

**Methods**:
- `execute_query()` - Execute SQL queries
- `get_schema_info()` - Extract database schema
- `get_sample_data()` - Retrieve sample data
- `test_connection()` - Verify database connectivity

#### `sql_generator.py` - SQL Generation Engine
**Purpose**: Natural language to SQL conversion using LangChain
**Key Features**:
- OpenAI GPT-3.5 integration via LangChain
- Custom prompt engineering for SQL generation
- Schema-aware query generation (for future levels)
- Async processing with proper error handling

**Methods**:
- `generate_sql()` - Convert natural language to SQL
- `generate_sql_with_schema()` - Schema-aware generation
- `_format_schema_for_prompt()` - Format schema for prompts

### Frontend Files

#### `templates/index.html` - Main Interface
**Purpose**: HTML structure for the chat interface
**Key Features**:
- Modern, responsive layout
- Chat message container
- Database explorer with tabs
- Results display section
- Form inputs and buttons

**Sections**:
- Header with title and description
- Chat container with messages
- Database explorer (Schema & Sample Data tabs)
- Results container with SQL and data tables

#### `static/css/style.css` - Styling
**Purpose**: Modern, responsive CSS styling
**Key Features**:
- Gradient background design
- Card-based layout with shadows
- Responsive design for all screen sizes
- Interactive hover effects and animations
- Professional table styling
- Tabbed interface styling

**Sections**:
- Base styles and reset
- Layout and container styles
- Chat interface styling
- Database explorer styling
- Results table styling
- Responsive design rules

#### `static/js/app.js` - Frontend Logic
**Purpose**: Interactive JavaScript functionality
**Key Features**:
- Real-time chat functionality
- Database explorer with tab switching
- API communication
- Dynamic table generation
- Copy-to-clipboard functionality
- Loading states and error handling

**Classes & Methods**:
- `ChatWithDB` class with comprehensive functionality
- `handleQuery()` - Process user queries
- `loadDatabaseInfo()` - Load schema and sample data
- `displaySchema()` - Render database schema
- `displaySampleData()` - Render sample data tables
- `switchTab()` - Tab switching functionality

### Configuration Files

#### `requirements.txt` - Python Dependencies
**Dependencies**:
- `fastapi==0.104.1` - Web framework
- `uvicorn==0.24.0` - ASGI server
- `langchain==0.1.0` - LLM framework
- `langchain-openai==0.0.5` - OpenAI integration
- `openai>=1.10.0,<2.0.0` - OpenAI API client
- `pymysql==1.1.0` - MySQL connector
- `python-dotenv==1.0.0` - Environment management
- `jinja2==3.1.2` - Template engine
- `python-multipart==0.0.6` - Form data handling
- `pydantic==2.5.0` - Data validation

#### `config_template.txt` - Environment Configuration
**Template for**:
- OpenAI API key configuration
- Database connection settings
- Application configuration
- Debug and server settings

#### `test_setup.py` - Setup Verification
**Purpose**: Verify all components are working
**Tests**:
- Environment variable validation
- Python package imports
- Database connection testing
- OpenAI API connectivity
- Component integration testing

#### `setup_test_db.py` - Test Database Setup
**Purpose**: Create sample SQLite database with test data
**Features**:
- SQLite database creation
- Sample table creation (users, products, orders)
- Test data insertion
- Environment file updates for SQLite

#### `setup_salesforce_db.py` - Salesforce Database Setup
**Purpose**: Create Salesforce database with educational program management tables
**Features**:
- MySQL Salesforce database creation
- Create 5 main tables (Account, Contact, Opportunity, Session, ProgramInstructorAvailability)
- Insert realistic sample data for educational programs
- Automatic environment configuration

## 🚀 Quick Start Guide

### Prerequisites
- Python 3.8+
- OpenAI API key
- MySQL server (for Salesforce database)

### Installation Steps

1. **Clone or download the project**
   ```bash
   git clone <repository-url>
   cd chat-with-db
   ```

2. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**
   ```bash
   cp config_template.txt .env
   # Edit .env with your actual MySQL connection details
   ```

4. **Create Salesforce database (recommended)**
   ```bash
   python setup_salesforce_db.py
   ```

5. **Verify setup**
   ```bash
   python test_setup.py
   ```

6. **Start the application**
   ```bash
   python main.py
   ```

7. **Open your browser**
   Navigate to `http://localhost:8000`

## 🏢 Salesforce Database Setup

This application is configured to work with a **Salesforce** database containing 5 key tables for educational program management:

### Automated Setup
The easiest way to set up the Salesforce database is using the provided script:

```bash
python setup_salesforce_db.py
```

This script will:
- Create the `Salesforce` database
- Create all 5 required tables with proper relationships
- Insert sample data for testing
- Update your `.env` file automatically

### Manual Setup Instructions

If you prefer to set up the database manually:

1. **Create the Database**
   ```sql
   CREATE DATABASE Salesforce;
   USE Salesforce;
   ```

2. **Update Environment Variables**
   Edit your `.env` file:
   ```bash
   DB_NAME=Salesforce
   USE_SQLITE=False
   DB_HOST=localhost
   DB_PORT=3306
   DB_USER=your_mysql_username
   DB_PASSWORD=your_mysql_password
   ```

3. **Create the Tables**
   Run the SQL commands for each table (see table schemas below)

### Database Schema

#### Account Table
Stores information about organizations and institutions:
```sql
CREATE TABLE Account (
    Id VARCHAR(18) PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    Type VARCHAR(50),
    Industry VARCHAR(100),
    Phone VARCHAR(50),
    Website VARCHAR(255),
    BillingStreet TEXT,
    BillingCity VARCHAR(100),
    BillingState VARCHAR(50),
    BillingPostalCode VARCHAR(20),
    BillingCountry VARCHAR(50),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### Contact Table
Stores individual contact information linked to accounts:
```sql
CREATE TABLE Contact (
    Id VARCHAR(18) PRIMARY KEY,
    AccountId VARCHAR(18),
    FirstName VARCHAR(100),
    LastName VARCHAR(100) NOT NULL,
    Email VARCHAR(255),
    Phone VARCHAR(50),
    Title VARCHAR(100),
    Department VARCHAR(100),
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (AccountId) REFERENCES Account(Id)
);
```

#### Opportunity Table
Tracks business opportunities and partnerships:
```sql
CREATE TABLE Opportunity (
    Id VARCHAR(18) PRIMARY KEY,
    AccountId VARCHAR(18),
    Name VARCHAR(255) NOT NULL,
    StageName VARCHAR(50) NOT NULL,
    Amount DECIMAL(18,2),
    CloseDate DATE,
    Probability DECIMAL(5,2),
    Type VARCHAR(50),
    LeadSource VARCHAR(50),
    Description TEXT,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (AccountId) REFERENCES Account(Id)
);
```

#### Session Table
Manages educational sessions and programs:
```sql
CREATE TABLE Session (
    Id VARCHAR(18) PRIMARY KEY,
    Name VARCHAR(255) NOT NULL,
    StartDateTime DATETIME,
    EndDateTime DATETIME,
    Location VARCHAR(255),
    MaxCapacity INT,
    CurrentEnrollment INT DEFAULT 0,
    Status VARCHAR(50) DEFAULT 'Planned',
    Description TEXT,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
);
```

#### ProgramInstructorAvailability Table
Tracks instructor availability for sessions:
```sql
CREATE TABLE ProgramInstructorAvailability (
    Id VARCHAR(18) PRIMARY KEY,
    ContactId VARCHAR(18),
    SessionId VARCHAR(18),
    AvailableStartTime DATETIME,
    AvailableEndTime DATETIME,
    IsAvailable BOOLEAN DEFAULT TRUE,
    Notes TEXT,
    CreatedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    LastModifiedDate TIMESTAMP DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,
    FOREIGN KEY (ContactId) REFERENCES Contact(Id),
    FOREIGN KEY (SessionId) REFERENCES Session(Id)
);
```

## 📊 Sample Data Included

The Salesforce database includes:

### Account Table
- JerseySTEM Academy (Educational Institution)
- Tech Solutions Inc (Technology Partner)
- Future Leaders Foundation (Non-Profit Partner)

### Contact Table
- 5 contacts across the organizations including Program Directors, Instructors, and Coordinators

### Opportunity Table
- STEM Program Partnership 2024 ($50,000)
- Summer Camp Collaboration ($25,000)
- Equipment Upgrade Initiative ($75,000)

### Session Table
- Introduction to Programming
- Robotics Workshop
- Data Science Fundamentals
- AI and Machine Learning

### ProgramInstructorAvailability Table
- 5 availability records linking instructors to sessions

## 🔧 Configuration Options

### Environment Variables
```bash
# OpenAI Configuration
OPENAI_API_KEY=your_openai_api_key_here

# Salesforce Database Configuration (MySQL)
DB_HOST=localhost
DB_PORT=3306
DB_USER=your_mysql_username
DB_PASSWORD=your_mysql_password
DB_NAME=Salesforce
USE_SQLITE=False

# Application Configuration
DEBUG=True
HOST=0.0.0.0
PORT=8000
```

### Database Options
- **MySQL with Salesforce Database**: Production-ready setup with educational program management tables
- **SQLite**: Available for testing (use `USE_SQLITE=True` and run `python setup_test_db.py`)

## 🧪 Testing Examples

### Natural Language Queries for Salesforce Database
Try these example queries:
- "Show me all accounts"
- "List all contacts with their email addresses"
- "Find opportunities with amounts greater than 30000"
- "Show me all active sessions"
- "Which instructors are available for upcoming sessions?"
- "List all accounts in the Education industry"
- "Show me opportunities in the Negotiation stage"
- "Find sessions with current enrollment less than max capacity"
- "Show contacts who work for JerseySTEM Academy"
- "List all program instructor availabilities for this week"

### API Testing
```bash
# Test health endpoint
curl http://localhost:8000/api/health

# Test query endpoint
curl -X POST "http://localhost:8000/api/query" \
     -H "Content-Type: application/json" \
     -d '{"query": "Show me all accounts"}'

# Test schema endpoint
curl http://localhost:8000/api/schema

# Test sample data endpoint
curl http://localhost:8000/api/sample-data
```

## 🔍 Troubleshooting

### Common Issues

1. **Database Connection Error**
   - Verify database is running
   - Check credentials in `.env`
   - Ensure database exists

2. **OpenAI API Error**
   - Verify API key is correct
   - Check API quota/limits
   - Ensure internet connection

3. **Import Errors**
   - Run `pip install -r requirements.txt`
   - Check Python version (3.8+)

4. **Port Already in Use**
   - Change PORT in `.env`
   - Kill existing processes on port 8000

### Debug Mode
Set `DEBUG=True` in `.env` for detailed error messages and auto-reload.

## 🎯 Next Steps (Level 2+)

This Level 1 implementation provides a solid foundation. Future levels will add:

### Level 2: Schema-Aware Query Generation
- Enhanced prompt engineering with schema context
- Multi-table JOIN support
- Query validation and optimization

### Level 3: RAG-Enhanced Intelligence
- Vector database integration
- Semantic search for schema components
- Business context understanding
- Query pattern learning

### Level 4: Advanced Features
- Complex query optimization
- Performance monitoring
- Result caching
- Query history and favorites

### Level 5: Conversational Context
- Session management
- Follow-up query understanding
- Natural language explanations
- Interactive result tables

### Level 6: Agentic Capabilities
- Automated data profiling
- Suggestion engine
- Data quality insights
- Trend analysis

## 🤝 Contributing

This is a Level 1 implementation following the roadmap. The code is intentionally simple and focused on core functionality. Contributions are welcome for:

- Bug fixes and improvements
- Additional database support
- UI/UX enhancements
- Performance optimizations
- Documentation improvements

## 📄 License

This project is open source and available under the MIT License.

## 🙏 Acknowledgments

- Built with FastAPI for high-performance web APIs
- Powered by LangChain for LLM integration
- Styled with modern CSS for beautiful interfaces
- Tested with comprehensive verification scripts

---

**Ready to chat with your database?** 🚀

Open `http://localhost:8000` and start asking questions in plain English!
