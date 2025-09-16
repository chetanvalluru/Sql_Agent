#!/usr/bin/env python3
"""
Salesforce Database Setup for Chat with DB
This creates the Salesforce database with the 5 required tables and sample data
"""

import pymysql
import os
from dotenv import load_dotenv

def create_salesforce_database():
    """Create Salesforce database with required tables"""
    print("🔧 Creating Salesforce database...")
    
    # Load environment variables
    load_dotenv()
    
    # Database connection parameters
    host = os.getenv("DB_HOST", "localhost")
    port = int(os.getenv("DB_PORT", 3306))
    user = os.getenv("DB_USER", "root")
    password = os.getenv("DB_PASSWORD", "")
    
    try:
        # Connect to MySQL server (without specifying database)
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create Salesforce database
            cursor.execute("CREATE DATABASE IF NOT EXISTS Salesforce")
            print("✅ Salesforce database created successfully!")
            
        connection.close()
        
        # Now connect to the Salesforce database
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database="Salesforce",
            charset='utf8mb4'
        )
        
        with connection.cursor() as cursor:
            # Create Account table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Account (
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
                )
            ''')
            
            # Create Contact table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Contact (
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
                )
            ''')
            
            # Create Opportunity table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Opportunity (
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
                )
            ''')
            
            # Create Session table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS Session (
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
                )
            ''')
            
            # Create ProgramInstructorAvailability table
            cursor.execute('''
                CREATE TABLE IF NOT EXISTS ProgramInstructorAvailability (
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
                )
            ''')
            
            print("✅ All tables created successfully!")
            
            # Insert sample data
            insert_sample_data(cursor)
            
        connection.commit()
        connection.close()
        
        print("🎉 Salesforce database setup complete!")
        
    except Exception as e:
        print(f"❌ Error creating Salesforce database: {str(e)}")
        raise

def insert_sample_data(cursor):
    """Insert sample data into the tables"""
    print("📊 Inserting sample data...")
    
    # Insert sample Accounts
    accounts = [
        ('001000000000001', 'JerseySTEM Academy', 'Educational Institution', 'Education', '555-0101', 'https://jerseystem.org', '123 Education Blvd', 'Princeton', 'NJ', '08540', 'USA'),
        ('001000000000002', 'Tech Solutions Inc', 'Customer', 'Technology', '555-0102', 'https://techsolutions.com', '456 Tech Drive', 'Newark', 'NJ', '07102', 'USA'),
        ('001000000000003', 'Future Leaders Foundation', 'Partner', 'Non-Profit', '555-0103', 'https://futureleaders.org', '789 Community St', 'Jersey City', 'NJ', '07302', 'USA')
    ]
    
    for account in accounts:
        cursor.execute('''
            INSERT IGNORE INTO Account (Id, Name, Type, Industry, Phone, Website, BillingStreet, BillingCity, BillingState, BillingPostalCode, BillingCountry)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', account)
    
    # Insert sample Contacts
    contacts = [
        ('003000000000001', '001000000000001', 'Sarah', 'Johnson', 'sarah.johnson@jerseystem.org', '555-0201', 'Program Director', 'Education'),
        ('003000000000002', '001000000000001', 'Michael', 'Chen', 'michael.chen@jerseystem.org', '555-0202', 'Lead Instructor', 'STEM Programs'),
        ('003000000000003', '001000000000002', 'Emily', 'Rodriguez', 'emily.rodriguez@techsolutions.com', '555-0203', 'Partnership Manager', 'Business Development'),
        ('003000000000004', '001000000000003', 'David', 'Kim', 'david.kim@futureleaders.org', '555-0204', 'Executive Director', 'Leadership'),
        ('003000000000005', '001000000000001', 'Lisa', 'Thompson', 'lisa.thompson@jerseystem.org', '555-0205', 'STEM Coordinator', 'Education')
    ]
    
    for contact in contacts:
        cursor.execute('''
            INSERT IGNORE INTO Contact (Id, AccountId, FirstName, LastName, Email, Phone, Title, Department)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
        ''', contact)
    
    # Insert sample Opportunities
    opportunities = [
        ('006000000000001', '001000000000002', 'STEM Program Partnership 2024', 'Negotiation', 50000.00, '2024-06-30', 75.00, 'New Business', 'Partner Referral', 'Annual partnership for STEM education programs'),
        ('006000000000002', '001000000000003', 'Summer Camp Collaboration', 'Proposal/Price Quote', 25000.00, '2024-04-15', 60.00, 'Existing Business', 'Web', 'Collaboration on summer STEM camps'),
        ('006000000000003', '001000000000001', 'Equipment Upgrade Initiative', 'Closed Won', 75000.00, '2024-03-31', 100.00, 'Existing Business', 'Internal', 'Upgrading lab equipment for better learning outcomes')
    ]
    
    for opportunity in opportunities:
        cursor.execute('''
            INSERT IGNORE INTO Opportunity (Id, AccountId, Name, StageName, Amount, CloseDate, Probability, Type, LeadSource, Description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', opportunity)
    
    # Insert sample Sessions
    sessions = [
        ('800000000000001', 'Introduction to Programming', '2024-04-01 09:00:00', '2024-04-01 12:00:00', 'Computer Lab A', 20, 15, 'Active', 'Basic programming concepts for beginners'),
        ('800000000000002', 'Robotics Workshop', '2024-04-02 13:00:00', '2024-04-02 16:00:00', 'Robotics Lab', 15, 12, 'Active', 'Hands-on robotics building and programming'),
        ('800000000000003', 'Data Science Fundamentals', '2024-04-03 10:00:00', '2024-04-03 15:00:00', 'Computer Lab B', 25, 20, 'Planned', 'Introduction to data analysis and visualization'),
        ('800000000000004', 'AI and Machine Learning', '2024-04-05 09:00:00', '2024-04-05 17:00:00', 'Conference Room', 30, 8, 'Planned', 'Overview of AI concepts and practical applications')
    ]
    
    for session in sessions:
        cursor.execute('''
            INSERT IGNORE INTO Session (Id, Name, StartDateTime, EndDateTime, Location, MaxCapacity, CurrentEnrollment, Status, Description)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
        ''', session)
    
    # Insert sample ProgramInstructorAvailability
    availabilities = [
        ('900000000000001', '003000000000002', '800000000000001', '2024-04-01 08:30:00', '2024-04-01 12:30:00', True, 'Available for full session'),
        ('900000000000002', '003000000000005', '800000000000002', '2024-04-02 12:30:00', '2024-04-02 16:30:00', True, 'Available with setup time'),
        ('900000000000003', '003000000000002', '800000000000003', '2024-04-03 09:30:00', '2024-04-03 15:30:00', True, 'Available for full day session'),
        ('900000000000004', '003000000000001', '800000000000004', '2024-04-05 08:00:00', '2024-04-05 18:00:00', False, 'Conflict with other commitments'),
        ('900000000000005', '003000000000005', '800000000000004', '2024-04-05 08:00:00', '2024-04-05 18:00:00', True, 'Available as backup instructor')
    ]
    
    for availability in availabilities:
        cursor.execute('''
            INSERT IGNORE INTO ProgramInstructorAvailability (Id, ContactId, SessionId, AvailableStartTime, AvailableEndTime, IsAvailable, Notes)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
        ''', availability)
    
    print("✅ Sample data inserted successfully!")
    print("📊 Inserted:")
    print("   - 3 Accounts")
    print("   - 5 Contacts")
    print("   - 3 Opportunities")
    print("   - 4 Sessions")
    print("   - 5 Program Instructor Availabilities")

def update_env_for_salesforce():
    """Update .env file to use Salesforce database"""
    print("\n🔧 Updating .env file for Salesforce database...")
    
    env_file = '.env'
    
    # Check if .env exists
    if not os.path.exists(env_file):
        print("⚠️  .env file not found. Please create one from config_template.txt")
        return
    
    # Read current .env
    with open(env_file, 'r') as f:
        content = f.read()
    
    # Update database name to Salesforce
    if 'DB_NAME=' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('DB_NAME='):
                lines[i] = 'DB_NAME=Salesforce'
                break
        content = '\n'.join(lines)
    else:
        content += '\nDB_NAME=Salesforce\n'
    
    # Ensure USE_SQLITE is set to False
    if 'USE_SQLITE=' in content:
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.startswith('USE_SQLITE='):
                lines[i] = 'USE_SQLITE=False'
                break
        content = '\n'.join(lines)
    else:
        content += '\nUSE_SQLITE=False\n'
    
    # Write updated .env
    with open(env_file, 'w') as f:
        f.write(content)
    
    print("✅ .env file updated for Salesforce database")

if __name__ == "__main__":
    try:
        create_salesforce_database()
        update_env_for_salesforce()
        print("\n🎉 Salesforce database setup complete!")
        print("You can now run: python test_setup.py")
        print("Then start the application with: python main.py")
    except Exception as e:
        print(f"\n❌ Setup failed: {str(e)}")
        print("\nPlease check your database connection settings in .env file")
