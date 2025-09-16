import os
from langchain.llms import OpenAI
from langchain.prompts import PromptTemplate
from langchain.chains import LLMChain
from typing import Dict, Any, List, Tuple
import asyncio
from fuzzy_matcher import FuzzyColumnMatcher, ColumnMatch

class SQLGenerator:
    def __init__(self):
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OPENAI_API_KEY environment variable is required")
        
        self.llm = OpenAI(
            temperature=0,
            model_name="gpt-4o-mini",
            openai_api_key=self.api_key
        )
        
        # Initialize fuzzy matcher for column name handling
        self.fuzzy_matcher = FuzzyColumnMatcher()
    
    async def generate_sql(self, natural_query: str, schema_info: Dict[str, Any], sample_data: Dict[str, Any] = None) -> str:
        """Generate SQL from natural language query with enhanced context and fuzzy matching"""
        # Pre-process the query to identify and suggest column name corrections
        enhanced_query, suggestions = await self._preprocess_query_with_fuzzy_matching(
            natural_query, schema_info
        )
        
        schema_prompt = self._format_enhanced_schema_for_prompt(schema_info, sample_data)
        
        # Add column suggestions to the schema prompt if any were found
        if suggestions:
            schema_prompt += "\n\nCOLUMN NAME SUGGESTIONS:\n"
            schema_prompt += "Based on fuzzy matching analysis of the user query, consider these column suggestions:\n"
            for suggestion in suggestions:
                schema_prompt += f"• {suggestion}\n"
        
        prompt_template = PromptTemplate(
            input_variables=["query", "schema"],
            template="""
You are a SQL expert for a STEM education program management system. Convert the following natural language query to SQL.
Use the provided database schema, relationships, and sample data to ensure accurate queries.

BUSINESS CONTEXT:
This is a comprehensive Salesforce-based system for managing JerseySTEM education programs with complex organizational relationships. Key concepts:
- Accounts = Organizations, schools, corporations, households, grantmakers, and other groups. Includes hierarchical relationships (ERGs → Corporate, Departments → Universities)
- Contacts = People associated with Accounts (employees, donors, teachers, program instructors). Can have multiple Account relationships via AccountContactRelation
- Opportunities = Time-bound or event-specific interactions between Accounts and JerseySTEM (grants, classes, donations)
- Sessions = Individual STEM class sessions in middle schools, linked to program opportunities
- ProgramInstructorAvailability = Instructor availability and assignments for program opportunities
- Deliverables = Promises/obligations to partners, connected to Opportunities
- Leads = Unqualified prospects, can be converted to Accounts/Contacts/Opportunities
- Campaigns & CampaignMembers = Coordinated outreach efforts with tracking per contact/lead
- Students & SessionAttendance = Student participation tracking in sessions
- AccountContactRelation = Many-to-many relationship between Accounts and Contacts (ERG memberships, secondary roles)
- History Tables = Audit trails for field-level changes over time
- RecordTypes = Business logic partitioning (College vs Corporate vs ERG accounts, Program Instructor vs Donor contacts)

SEMESTER AND PROGRAM STATUS LOGIC:
- Active/completed programs: Opportunities with StageName = 'Closed Won'
- Current semester: Check actual data - sample shows '2024/2025 Fall' format
- Semester format: "YYYY/YYYY Season" like "2024/2025 Fall", "2025/2026 Spring"
- Ignore prospective dates (Prospective_Start_Date__c, Prospective_End_Date__c) for active program queries
- Schools being taught = Accounts linked to 'Closed Won' opportunities for the specified semester
- Instructor information comes from ProgramInstructorAvailability.Account_Name__c field

QUERY GUIDELINES:
1. Use case-insensitive comparisons with LOWER() for text searches
2. When looking for "programs" or "classes", query the Session table
3. When looking for "instructors" or "teachers", query ProgramInstructorAvailability table for Account_Name__c field
4. When looking for "schools" or "organizations", query the Account table
5. For enrollment or participation data, check Opportunity and Session tables
6. For "schools we are teaching", join Account and Opportunity with StageName = 'Closed Won'
7. For semester queries, use Semesters__c field (double underscore + c)
8. Always ignore prospective dates when querying for active/current programs
9. Use proper JOIN conditions based on the relationships shown below
10. Apply business logic patterns rather than hardcoded values when possible
11. Use DISTINCT for listing entities to avoid duplicates from multiple relationships
12. Consider the business context: "teaching" implies active programs, "this semester" implies current semester
13. Always filter out deleted records with IsDeleted = 0 (FALSE)
14. For instructor availability, check day-specific time fields like Monday_Start_Time__c, Friday_End_Time__c

DATABASE SCHEMA WITH RELATIONSHIPS AND SAMPLE DATA:
{schema}

Natural language query: {query}

SQL Query:
"""
        )
        
        chain = LLMChain(llm=self.llm, prompt=prompt_template)
        
        try:
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                None,
                chain.run,
                {"query": enhanced_query, "schema": schema_prompt}
            )
            
            # Clean up the result
            sql = result.strip()
            if sql.startswith("```sql"):
                sql = sql[6:]
            if sql.endswith("```"):
                sql = sql[:-3]
            
            return sql.strip()
            
        except Exception as e:
            raise Exception(f"Failed to generate SQL: {str(e)}")
    
    def _format_enhanced_schema_for_prompt(self, schema_info: Dict[str, Any], sample_data: Dict[str, Any] = None) -> str:
        """Format enhanced schema information with relationships, business context, and sample data"""
        schema_text = ""
        
        # Define table relationships and business context - COMPREHENSIVE SALESFORCE SCHEMA
        table_context = {
            'Account': {
                'description': 'Organizations, schools, corporations, households, grantmakers, and other groups. Hierarchical with ParentId relationships.',
                'relationships': ['Contact (1:Many via AccountId)', 'Opportunity (1:Many via AccountId)', 'AccountContactRelation (1:Many)', 'Account (hierarchical via ParentId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'Name': 'Organization name (schools, colleges, companies, ERGs)',
                    'Type': 'Student Organization, Department, Corporate, DEVT, etc.',
                    'Industry': 'Professional Services, Education, etc.',
                    'RecordTypeId': 'Defines account type/department distinctions',
                    'Record_Type_Name__c': 'Human-readable record type (College, Corporate, Community, Household, GrantMaker, Organization)',
                    'ParentId': 'Self-referential hierarchy (ERG → Corporate, Department → University)',
                    'IsDeleted': 'FALSE for active accounts, TRUE for deleted ones'
                },
                'record_types': ['College', 'Department', 'Student Organization', 'University', 'Corporate', 'School', 'School District', 'ERG', 'Foundation']
            },
            'Contact': {
                'description': 'People associated with Accounts (employees, donors, teachers, program instructors). Can have multiple Account relationships via AccountContactRelation.',
                'relationships': ['Account (Many:1 via AccountId - primary)', 'AccountContactRelation (1:Many - secondary relationships)', 'CampaignMember (1:Many)', 'ProgramInstructorAvailability (1:Many)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'FirstName': 'Person\'s first name',
                    'LastName': 'Person\'s last name', 
                    'Title': 'Job title or role (Director, Professor, etc.)',
                    'Department': 'Department within organization',
                    'AccountId': 'Primary Account relationship',
                    'Email': 'Contact email address',
                    'RecordTypeId': 'Role classification',
                    'Record_Type_Name__c': 'Human-readable role (General Contact, Program Instructor, Donor)',
                    'IsDeleted': 'FALSE for active contacts, TRUE for deleted ones'
                },
                'record_types': ['General Contact', 'Program Instructor', 'Donor']
            },
            'Opportunity': {
                'description': 'Time-bound or event-specific interactions between Accounts and JerseySTEM (grants, classes, donations)',
                'relationships': ['Account (Many:1 via AccountId)', 'Session (1:Many via Opportunity__c)', 'ProgramInstructorAvailability (1:Many via Opportunity__c)', 'Deliverable (1:Many)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'Name': 'Opportunity name (donations, programs, etc.)',
                    'StageName': 'Closed Won (active/completed), other stages for pipeline',
                    'Amount': 'Monetary value of opportunity',
                    'CloseDate': 'Date opportunity was/will be closed',
                    'Type': 'Business type classification',
                    'RecordTypeId': 'Opportunity type classification',
                    'Record_Type_Name__c': 'Human-readable type (College, Community, Corporate)',
                    'Semesters__c': 'Semester info like "2024/2025 Fall", "2025/2026 Spring"',
                    'AccountId': 'Links to related organization',
                    'IsDeleted': 'FALSE for active opportunities, TRUE for deleted ones'
                },
                'record_types': ['College', 'Community', 'Corporate']
            },
            'Session': {
                'description': 'Individual STEM class sessions linked to program opportunities',
                'relationships': ['Opportunity (Many:1 via Opportunity__c)', 'ProgramInstructorAvailability (1:Many via Opportunity__c)'],
                'key_fields': {
                    'Name': 'Session identifier (e.g., SES-000052)',
                    'Session_Date__c': 'Date when the session occurs',
                    'Opportunity__c': 'Links to the related program opportunity',
                    'MMDD__c': 'Month/day format of session date',
                    'Weekday_Short__c': 'Day of week (Mon, Tue, Wed, etc.)',
                    'Session_Activity__c': 'Activity status (Available, etc.)',
                    'IsDeleted': 'FALSE for active sessions, TRUE for deleted ones'
                }
            },
            'ProgramInstructorAvailability': {
                'description': 'Instructor availability and assignments for program opportunities',
                'relationships': ['Opportunity (Many:1 via Opportunity__c)', 'Contact (Many:1 via Program_Instructor_s_Contact__c)'],
                'key_fields': {
                    'Account_Name__c': 'Name of the instructor/person',
                    'Opportunity__c': 'Links to the related program opportunity',
                    'Program_Instructor_s_Contact__c': 'Links to Contact record',
                    'Monday_Start_Time__c': 'Available start time on Monday',
                    'Monday_End_Time__c': 'Available end time on Monday',
                    'Tuesday_Start_Time__c': 'Available start time on Tuesday',
                    'Tuesday_End_Time__c': 'Available end time on Tuesday',
                    'Wednesday_Start_Time__c': 'Available start time on Wednesday',
                    'Wednesday_End_Time__c': 'Available end time on Wednesday',
                    'Thursday_Start_Time__c': 'Available start time on Thursday',
                    'Thursday_End_Time__c': 'Available end time on Thursday',
                    'Friday_Start_Time__c': 'Available start time on Friday',
                    'Friday_End_Time__c': 'Available end time on Friday',
                    'Program_Instructor_Application_Stages__c': 'Application status (Offer Accepted, Offer Declined, etc.)',
                    'Semester_Teaching__c': 'Semester being taught (2024/2025 Fall, etc.)',
                    'IsDeleted': 'FALSE for active records, TRUE for deleted ones'
                }
            },
            'Deliverable': {
                'description': 'Promises/joint activities/obligations to partners, connected to Opportunities',
                'relationships': ['Opportunity (Many:1 via OpportunityId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'OpportunityId': 'Links to parent Opportunity',
                    'Type': 'Type of deliverable (field trip, report, newsletter, invitation)',
                    'IsDeleted': 'FALSE for active deliverables, TRUE for deleted ones'
                }
            },
            'Lead': {
                'description': 'Unqualified prospective Accounts/Contacts/Opportunities, typically from web forms or imports',
                'relationships': ['Campaign (Many:Many via CampaignMember)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'FirstName': 'Lead\'s first name',
                    'LastName': 'Lead\'s last name',
                    'Company': 'Organization name',
                    'Status': 'Lead qualification status',
                    'Email': 'Contact email address',
                    'IsConverted': 'TRUE if converted to Account/Contact/Opportunity',
                    'IsDeleted': 'FALSE for active leads, TRUE for deleted ones'
                }
            },
            'Campaign': {
                'description': 'Coordinated outreach efforts (e.g., mass emails)',
                'relationships': ['Campaign (hierarchical via ParentId)', 'CampaignMember (1:Many)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'Name': 'Campaign name',
                    'Type': 'Campaign type',
                    'Status': 'Campaign status',
                    'ParentId': 'Parent campaign for hierarchy',
                    'IsDeleted': 'FALSE for active campaigns, TRUE for deleted ones'
                }
            },
            'CampaignMember': {
                'description': 'Join table linking Campaigns to Contacts/Leads; records status of outreach per contact',
                'relationships': ['Campaign (Many:1 via CampaignId)', 'Contact (Many:1 via ContactId)', 'Lead (Many:1 via LeadId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'CampaignId': 'Links to Campaign',
                    'ContactId': 'Links to Contact (mutually exclusive with LeadId)',
                    'LeadId': 'Links to Lead (mutually exclusive with ContactId)',
                    'Status': 'Member status (Sent, Responded, etc.)',
                    'IsDeleted': 'FALSE for active members, TRUE for deleted ones'
                }
            },
            'Student': {
                'description': 'Middle school students participating in sessions',
                'relationships': ['SessionAttendance (1:Many)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'FirstName': 'Student\'s first name',
                    'LastName': 'Student\'s last name',
                    'Grade': 'Student grade level',
                    'School': 'School name',
                    'IsDeleted': 'FALSE for active students, TRUE for deleted ones'
                }
            },
            'SessionAttendance': {
                'description': 'Join table - one record per person (student/instructor) per session with attendance status',
                'relationships': ['Session (Many:1 via SessionId)', 'Student (Many:1 via StudentId)', 'Contact (Many:1 via ContactId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'SessionId': 'Links to Session',
                    'StudentId': 'Links to Student (for student attendance)',
                    'ContactId': 'Links to Contact (for instructor attendance)',
                    'AttendanceStatus': 'Attendance status (Present, Absent, etc.)',
                    'IsDeleted': 'FALSE for active records, TRUE for deleted ones'
                }
            },
            'AccountContactRelation': {
                'description': 'Maps a Contact to multiple Accounts, useful for ERG and College roles (Work-Study Coordinator, etc.)',
                'relationships': ['Account (Many:1 via AccountId)', 'Contact (Many:1 via ContactId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'AccountId': 'Links to Account',
                    'ContactId': 'Links to Contact',
                    'Roles': 'Role/context data for this relationship',
                    'IsDeleted': 'FALSE for active relations, TRUE for deleted ones'
                }
            },
            'AccountHistory': {
                'description': 'Track field-level changes over time for Account records',
                'relationships': ['Account (Many:1 via AccountId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'AccountId': 'Links to Account',
                    'Field': 'Field that was changed',
                    'OldValue': 'Previous field value',
                    'NewValue': 'New field value',
                    'CreatedDate': 'When change occurred'
                }
            },
            'ContactHistory': {
                'description': 'Track field-level changes over time for Contact records',
                'relationships': ['Contact (Many:1 via ContactId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'ContactId': 'Links to Contact',
                    'Field': 'Field that was changed',
                    'OldValue': 'Previous field value',
                    'NewValue': 'New field value',
                    'CreatedDate': 'When change occurred'
                }
            },
            'LeadHistory': {
                'description': 'Track field-level changes over time for Lead records',
                'relationships': ['Lead (Many:1 via LeadId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'LeadId': 'Links to Lead',
                    'Field': 'Field that was changed',
                    'OldValue': 'Previous field value',
                    'NewValue': 'New field value',
                    'CreatedDate': 'When change occurred'
                }
            },
            'OpportunityHistory': {
                'description': 'Track field-level changes over time for Opportunity records',
                'relationships': ['Opportunity (Many:1 via OpportunityId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'OpportunityId': 'Links to Opportunity',
                    'Field': 'Field that was changed',
                    'OldValue': 'Previous field value',
                    'NewValue': 'New field value',
                    'CreatedDate': 'When change occurred'
                }
            },
            'OpportunityPipelineHistory': {
                'description': 'Weekly snapshot of Opportunity statuses/summary',
                'relationships': ['Opportunity (Many:1 via OpportunityId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'OpportunityId': 'Links to Opportunity',
                    'SnapshotDate': 'Date of the snapshot',
                    'StageName': 'Stage at time of snapshot',
                    'Amount': 'Amount at time of snapshot'
                }
            },
            'CommunicationLogEntry': {
                'description': 'Tracks non-email communications with contacts',
                'relationships': ['Contact (Many:1 via ContactId)', 'Account (Many:1 via AccountId)'],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'ContactId': 'Links to Contact',
                    'AccountId': 'Links to Account',
                    'Subject': 'Communication subject',
                    'Type': 'Communication type (Phone, Meeting, etc.)',
                    'Date': 'Communication date',
                    'IsDeleted': 'FALSE for active logs, TRUE for deleted ones'
                }
            },
            'DataDictionaryFields': {
                'description': 'Metadata for fields—used for dynamic UI/data dictionaries',
                'relationships': [],
                'key_fields': {
                    'Id': '18-character Salesforce key (Primary Key)',
                    'ObjectName': 'Salesforce object/table name',
                    'FieldName': 'Field name',
                    'FieldLabel': 'Human-readable field label',
                    'FieldType': 'Field data type',
                    'Description': 'Field description'
                }
            }
        }
        
        for table_name, columns in schema_info.items():
            context = table_context.get(table_name, {})
            
            schema_text += f"\n=== {table_name} Table ===\n"
            if context.get('description'):
                schema_text += f"Purpose: {context['description']}\n"
            
            if context.get('relationships'):
                schema_text += f"Relationships: {', '.join(context['relationships'])}\n"
            
            schema_text += "Columns:\n"
            for col in columns:
                key_info = f" (PRIMARY KEY)" if col['key'] == 'PRI' else f" (FOREIGN KEY)" if col['key'] == 'MUL' else ""
                nullable_info = "" if col['nullable'] == 'YES' else " NOT NULL"
                
                # Add business context for key fields
                field_context = ""
                if table_name in table_context and col['column'] in table_context[table_name].get('key_fields', {}):
                    field_context = f" - {table_context[table_name]['key_fields'][col['column']]}"
                
                schema_text += f"  • {col['column']}: {col['type']}{key_info}{nullable_info}{field_context}\n"
            
            # Add sample data if available
            if sample_data and table_name in sample_data and sample_data[table_name]:
                schema_text += f"\nSample {table_name} records:\n"
                sample_records = sample_data[table_name][:3]  # Show up to 3 sample records
                for i, record in enumerate(sample_records, 1):
                    schema_text += f"  Example {i}: "
                    # Show key fields from sample data
                    key_values = []
                    for key_field in ['Id', 'Name', 'Title', 'StageName', 'Status', 'IsAvailable']:
                        if key_field in record and record[key_field] is not None:
                            key_values.append(f"{key_field}='{record[key_field]}'")
                    schema_text += ", ".join(key_values[:3]) + "\n"
            
            schema_text += "\n"
        
        # Add comprehensive JOIN patterns and business logic
        schema_text += """
COMMON JOIN PATTERNS:
• Account → Contact: JOIN Contact ON Contact.AccountId = Account.Id
• Account → Opportunity: JOIN Opportunity ON Opportunity.AccountId = Account.Id  
• Session → ProgramInstructorAvailability: JOIN ProgramInstructorAvailability ON Session.Opportunity__c = ProgramInstructorAvailability.Opportunity__c
• Opportunity → Session: JOIN Session ON Session.Opportunity__c = Opportunity.Id
• Opportunity → ProgramInstructorAvailability: JOIN ProgramInstructorAvailability ON ProgramInstructorAvailability.Opportunity__c = Opportunity.Id
• ProgramInstructorAvailability → Contact: JOIN Contact ON Contact.Id = ProgramInstructorAvailability.Program_Instructor_s_Contact__c
• Account → AccountContactRelation: JOIN AccountContactRelation ON AccountContactRelation.AccountId = Account.Id
• Contact → AccountContactRelation: JOIN AccountContactRelation ON AccountContactRelation.ContactId = Contact.Id
• Account Hierarchy: JOIN Account child ON child.ParentId = parent.Id
• Campaign → CampaignMember: JOIN CampaignMember ON CampaignMember.CampaignId = Campaign.Id
• Contact → CampaignMember: JOIN CampaignMember ON CampaignMember.ContactId = Contact.Id
• Lead → CampaignMember: JOIN CampaignMember ON CampaignMember.LeadId = Lead.Id
• Opportunity → Deliverable: JOIN Deliverable ON Deliverable.OpportunityId = Opportunity.Id
• Session → SessionAttendance: JOIN SessionAttendance ON SessionAttendance.SessionId = Session.Id
• Student → SessionAttendance: JOIN SessionAttendance ON SessionAttendance.StudentId = Student.Id

COMMON QUERIES:
• Find instructors: Query ProgramInstructorAvailability table for Account_Name__c field (NOT Contact table)
• Find active sessions: Query Session table filtering by IsDeleted = 0 (FALSE)
• Find available instructors for sessions: Join Session and ProgramInstructorAvailability on Opportunity__c field where both IsDeleted = 0
• Find schools being taught: Join Account and Opportunity tables where StageName = 'Closed Won' and filter by semester
• Session with instructor availability: JOIN Session s and ProgramInstructorAvailability p ON s.Opportunity__c = p.Opportunity__c WHERE s.IsDeleted = 0 AND p.IsDeleted = 0
• Find instructor contact details: JOIN ProgramInstructorAvailability p and Contact c ON p.Program_Instructor_s_Contact__c = c.Id

DOMAIN-SPECIFIC TERMINOLOGY PATTERNS:
• "programs", "classes", "sessions" → Primary table: Session (fields: Name, Session_Date__c, Opportunity__c)
• "instructors", "teachers", "staff" → Primary table: ProgramInstructorAvailability (key field: Account_Name__c)
• "schools", "organizations", "institutions" → Primary table: Account (fields: Name, Type, Industry)
• "enrollment", "registration", "participation" → Primary table: Opportunity (fields: StageName, Type, Amount)
• "availability", "scheduling" → Focus on time fields: [Day]_Start_Time__c, [Day]_End_Time__c where Day = Monday|Tuesday|Wednesday|Thursday|Friday
• "active" records → Always apply: WHERE IsDeleted = 0 (or IS NULL)
• "available" instructors → Check time fields: WHERE [Day]_Start_Time__c IS NOT NULL
• When joining Session + Instructor data → Use: s.Opportunity__c = p.Opportunity__c pattern

SEMESTER AND SCHOOL QUERY PATTERNS:
• "schools we are teaching" → Join Account and Opportunity where StageName = 'Closed Won'
• "current semester" or "this semester" → Use Semesters__c = '2024/2025 Fall' (check actual current semester data)
• "next semester" → Use Semesters__c = '2025/2026 Spring' (check actual data for correct values)
• "active programs" → Opportunities with StageName = 'Closed Won' (ignore prospective dates)
• Field name for semester: Semesters__c (note the double underscore and 'c')
• Semester format: "YYYY/YYYY Season" like "2024/2025 Fall", "2025/2026 Spring"

BUSINESS LOGIC PATTERNS:
• Active/completed programs are identified by StageName = 'Closed Won' in Opportunity table
• Semester information is stored in Semesters__c field with values like '2024/2025 Fall', '2025/2026 Spring'
• When querying for current/active programs, ignore Prospective_Start_Date__c and Prospective_End_Date__c fields
• Schools being taught = Accounts that have 'Closed Won' opportunities for the specified semester
• Use DISTINCT when listing schools to avoid duplicates from multiple opportunities
• Always join Account.Id = Opportunity.AccountId when connecting schools to their programs
• Instructor names come from ProgramInstructorAvailability.Account_Name__c, NOT Contact table
• Session information comes from Session table with Opportunity__c linking to programs

ERG AND HIERARCHY PATTERNS:
• ERGs are separate Account records with Record_Type_Name__c = 'ERG-Employee Resource Group'
• ERGs have ParentId pointing to their corporate Account (ERG → Corporate hierarchy)
• ERG Contacts are linked via AccountContactRelation table (many-to-many relationship)
• Corporate Account hierarchy: Parent Company → ERG (via ParentId)
• University hierarchy: University → Department (via ParentId), University → Student Organization (via ParentId)
• To find ERG members: JOIN Account erg, AccountContactRelation acr, Contact c WHERE erg.Record_Type_Name__c = 'ERG-Employee Resource Group' AND acr.AccountId = erg.Id AND c.Id = acr.ContactId
• To find companies with ERGs: JOIN Account parent, Account erg WHERE erg.ParentId = parent.Id AND erg.Record_Type_Name__c LIKE '%ERG%'
• ERG categories can be inferred from ERG Account names (Women, Hispanic, etc.)

RECORD TYPE FILTERING PATTERNS:
• Use RecordTypeId for exact matching, Record_Type_Name__c for readable filtering
• Account types: 'College', 'Department', 'Student Organization', 'University', 'Corporate', 'School', 'School District', 'ERG', 'Foundation'
• Contact types: 'General Contact', 'Program Instructor', 'Donor'
• Opportunity types: 'College', 'Community', 'Corporate'
• Filter by role: WHERE Record_Type_Name__c = 'Program Instructor' (for contacts who can instruct)
• Filter by org type: WHERE Record_Type_Name__c = 'Corporate' AND Type = 'DEVT' (for development-focused companies)
• Combined filtering: WHERE Record_Type_Name__c = 'ERG-Employee Resource Group' AND ParentId IS NOT NULL

MULTI-VALUED FIELD PATTERNS:
• Some fields contain semicolon-separated lists (rare cases, breaks relational norm)
• Use LIKE '%value%' or string functions to search within multi-valued fields
• Example: WHERE Skills__c LIKE '%JavaScript%' for skill searches

AUDIT AND HISTORY PATTERNS:
• Use *History tables for tracking changes: AccountHistory, ContactHistory, LeadHistory, OpportunityHistory
• OpportunityPipelineHistory provides weekly snapshots of opportunity status
• History records include Field, OldValue, NewValue, CreatedDate for audit trails
• Join pattern: JOIN AccountHistory ah ON ah.AccountId = Account.Id WHERE ah.Field = 'Status'

IMPORTANT FIELD NAMES AND PATTERNS:
• Semester field: Semesters__c (double underscore + c)
• Active/completed programs: StageName = 'Closed Won'
• Instructor names: ProgramInstructorAvailability.Account_Name__c
• Session dates: Session.Session_Date__c
• Active records: IsDeleted = 0 (FALSE)
• Availability times: [Day]_Start_Time__c and [Day]_End_Time__c (Monday through Friday)
• Program links: Opportunity__c field connects Session and ProgramInstructorAvailability to Opportunity

BUSINESS CONTEXT UNDERSTANDING:
• "Teaching" or "active programs" = Opportunities with StageName = 'Closed Won'
• "This semester" = Current semester value in Semesters__c field
• "Schools we work with" = Accounts that have active opportunities
• "Programs running" = Active sessions or closed won opportunities
• "Instructor availability" = ProgramInstructorAvailability records with time fields populated
• Always consider the business meaning behind natural language terms
• Apply appropriate filters based on business context rather than literal interpretation

SALESFORCE FIELD NAMING PATTERNS:
• Custom fields always end with '__c' (double underscore + c): Session_Date__c, Account_Name__c, Friday_Start_Time__c
• Standard fields never have '__c': Id, Name, CreatedDate, IsDeleted
• Lookup/relationship fields end with '__c': Opportunity__c (links to Opportunity.Id)
• Boolean fields often start with 'Is': IsDeleted (0 = active, 1 = deleted)

RELATIONSHIP PATTERNS:
• Session ↔ ProgramInstructorAvailability: Both link via Opportunity__c field
• To join: s.Opportunity__c = p.Opportunity__c (where s=Session, p=ProgramInstructorAvailability)
• This creates a many-to-many relationship through the Opportunity entity
• Always use table aliases for clarity: Session s, ProgramInstructorAvailability p

ACTIVE RECORD FILTERING PATTERNS:
• Always filter out deleted records: WHERE IsDeleted = 0 (or IS NULL if field might not exist)
• For availability queries: Check time fields IS NOT NULL (e.g., Friday_Start_Time__c IS NOT NULL)
• Combine filters with AND: WHERE s.IsDeleted = 0 AND p.Friday_Start_Time__c IS NOT NULL

TIME AVAILABILITY FIELD PATTERNS:
• Day-specific availability: Monday_Start_Time__c, Tuesday_Start_Time__c, ..., Friday_End_Time__c
• Always check both start AND end times for complete availability
• Use appropriate day fields based on query context (Friday for "Friday availability")

INSTRUCTOR IDENTIFICATION PATTERNS:
• Instructor names are stored in ProgramInstructorAvailability.Account_Name__c (NOT in Contact table)
• To find instructors: Query ProgramInstructorAvailability table, not Contact table
• Use Account_Name__c field for instructor names in results
• For instructor contact details: Join ProgramInstructorAvailability with Contact via Program_Instructor_s_Contact__c

SESSION INFORMATION PATTERNS:
• Session identifiers: Session.Name field (e.g., SES-000052)
• Session dates: Session.Session_Date__c field (datetime type)
• Session day info: Session.Weekday_Short__c (Mon, Tue, Wed, etc.)
• Session month/day: Session.MMDD__c (MM/DD format)
• Always include IsDeleted = 0 filter for active sessions

QUERY CONSTRUCTION PRINCIPLES:
• When user asks for "X with Y" → JOIN the primary tables for X and Y
• When user asks for "active/available" → Add IsDeleted = 0 and time field IS NOT NULL filters
• When user asks for specific day availability → Use [Day]_Start_Time__c and [Day]_End_Time__c fields
• When user asks for instructor info → Always use ProgramInstructorAvailability.Account_Name__c
• When user wants session details → Always include Session.Name, Session.Session_Date__c, Session.Weekday_Short__c
• For readability → Use meaningful column aliases: AS SessionName, AS InstructorName, AS SessionDate, etc.
• For performance → Always filter deleted records early in WHERE clause: WHERE IsDeleted = 0

SAMPLE COMPLEX QUERIES FOR AI ORCHESTRATION:

1. List Companies with Hispanic ERG and Contacts:
SELECT DISTINCT parent.Name AS CompanyName, erg.Name AS ERGName, c.FirstName, c.LastName, c.Email, c.Title
FROM Account parent
JOIN Account erg ON erg.ParentId = parent.Id
JOIN AccountContactRelation acr ON acr.AccountId = erg.Id  
JOIN Contact c ON c.Id = acr.ContactId
WHERE parent.Record_Type_Name__c = 'Corporate'
AND erg.Record_Type_Name__c = 'ERG-Employee Resource Group'
AND (erg.Name LIKE '%Hispanic%' OR erg.Name LIKE '%Latino%')
AND parent.IsDeleted = 0 AND erg.IsDeleted = 0 AND c.IsDeleted = 0;

2. Find Companies lacking a specific ERG (with contact fallback):
SELECT DISTINCT a.Name AS CompanyName, c.FirstName, c.LastName, c.Email
FROM Account a
LEFT JOIN Account erg ON erg.ParentId = a.Id AND erg.Record_Type_Name__c = 'ERG-Employee Resource Group' AND erg.Name LIKE '%Women%'
LEFT JOIN Contact c ON c.AccountId = a.Id
WHERE a.Record_Type_Name__c = 'Corporate' 
AND a.Type = 'DEVT'
AND erg.Id IS NULL  -- No Women ERG found
AND a.IsDeleted = 0;

3. Rank Colleges by number of Program Instructor emails:
SELECT a.Name AS CollegeName, COUNT(DISTINCT c.Email) AS InstructorEmailCount
FROM Account a
JOIN Contact c ON c.AccountId = a.Id
WHERE a.Record_Type_Name__c = 'College'
AND c.Record_Type_Name__c = 'Program Instructor'
AND c.Email IS NOT NULL
AND a.IsDeleted = 0 AND c.IsDeleted = 0
GROUP BY a.Id, a.Name
ORDER BY InstructorEmailCount DESC;

4. Find Grant applications that are active/in-process but not complete:
SELECT o.Name AS GrantName, a.Name AS OrganizationName, o.StageName, o.Amount, o.CloseDate
FROM Opportunity o
JOIN Account a ON a.Id = o.AccountId
WHERE o.Type LIKE '%Grant%'
AND o.StageName NOT IN ('Closed Won', 'Closed Lost')
AND o.StageName IN ('Prospecting', 'Qualification', 'Needs Analysis', 'Proposal')
AND o.IsDeleted = 0 AND a.IsDeleted = 0
ORDER BY o.CloseDate;

5. ERG Relationship Mapping Example:
SELECT 
    parent.Name AS CompanyName,
    parent.Type AS CompanyType,
    erg.Name AS ERGName,
    CASE 
        WHEN erg.Name LIKE '%Women%' THEN 'Women'
        WHEN erg.Name LIKE '%Hispanic%' OR erg.Name LIKE '%Latino%' THEN 'Hispanic'
        WHEN erg.Name LIKE '%Black%' OR erg.Name LIKE '%African%' THEN 'Black'
        ELSE 'Other'
    END AS ERGCategory,
    COUNT(acr.ContactId) AS MemberCount
FROM Account parent
JOIN Account erg ON erg.ParentId = parent.Id
LEFT JOIN AccountContactRelation acr ON acr.AccountId = erg.Id
WHERE parent.Record_Type_Name__c = 'Corporate'
AND erg.Record_Type_Name__c = 'ERG-Employee Resource Group'
AND parent.IsDeleted = 0 AND erg.IsDeleted = 0
GROUP BY parent.Id, parent.Name, parent.Type, erg.Id, erg.Name
ORDER BY parent.Name, ERGCategory;

6. Find missing/incomplete data patterns:
SELECT 
    a.Name AS CollegeName,
    COUNT(DISTINCT dept.Id) AS DepartmentCount,
    COUNT(DISTINCT org.Id) AS StudentOrgCount,
    COUNT(DISTINCT c.Id) AS ContactCount,
    COUNT(DISTINCT CASE WHEN c.Email IS NOT NULL THEN c.Id END) AS ContactsWithEmail
FROM Account a
LEFT JOIN Account dept ON dept.ParentId = a.Id AND dept.Record_Type_Name__c = 'Department'
LEFT JOIN Account org ON org.ParentId = a.Id AND org.Record_Type_Name__c = 'Student Organization'  
LEFT JOIN Contact c ON c.AccountId = a.Id
WHERE a.Record_Type_Name__c = 'College'
AND a.IsDeleted = 0
GROUP BY a.Id, a.Name
HAVING ContactsWithEmail = 0  -- Colleges without any email contacts
ORDER BY a.Name;

SALESFORCE-SPECIFIC CONSIDERATIONS:
• Custom fields always end with '__c': Session_Date__c, Account_Name__c, Semesters__c
• Package fields (ignore): Fields with double-underscore prefixes from installed packages
• Multi-valued fields: Rare semicolon-delimited text fields, use LIKE '%value%' to search
• RecordType awareness: Always filter by Record_Type_Name__c for business logic
• Hierarchy navigation: Use ParentId for Account hierarchies (ERG → Corporate, Dept → University)
• Many-to-many relationships: AccountContactRelation, CampaignMember, SessionAttendance
• Audit trails: Use *History tables for change tracking and compliance
• Data quality: Use DataDictionaryFields for dynamic field metadata and validation
"""
        
        return schema_text

    def _format_schema_for_prompt(self, schema_info: Dict[str, Any]) -> str:
        """Legacy method - kept for backward compatibility"""
        return self._format_enhanced_schema_for_prompt(schema_info)
    
    async def _preprocess_query_with_fuzzy_matching(self, natural_query: str, 
                                                   schema_info: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Pre-process natural language query to identify potential column names and suggest corrections.
        
        Args:
            natural_query: Original natural language query
            schema_info: Database schema information
            
        Returns:
            Tuple of (enhanced_query, list_of_suggestions)
        """
        suggestions = []
        enhanced_query = natural_query
        
        # Extract potential column references from natural language
        potential_columns = self._extract_potential_column_names(natural_query)
        
        for potential_col in potential_columns:
            # Find fuzzy matches for this potential column
            matches = self.fuzzy_matcher.find_column_matches(potential_col, schema_info, top_n=3)
            
            if matches:
                best_match = matches[0]
                
                # If the best match isn't perfect, provide suggestions
                if best_match.similarity_score < 95:
                    suggestion = f"For '{potential_col}', consider: {best_match.table_name}.{best_match.matched_column}"
                    if best_match.similarity_score < 85:
                        suggestion += f" (similarity: {best_match.similarity_score:.1f}%)"
                    suggestions.append(suggestion)
                    
                    # Optionally enhance the query with the correction
                    if best_match.similarity_score > 80:
                        # Replace the potential column with the best match in the query
                        enhanced_query = enhanced_query.replace(
                            potential_col, 
                            f"{best_match.table_name}.{best_match.matched_column}"
                        )
        
        return enhanced_query, suggestions
    
    def _extract_potential_column_names(self, natural_query: str) -> List[str]:
        """
        Extract potential column names from natural language query.
        
        This is a heuristic-based approach that looks for words that might be column names.
        """
        import re
        
        # Common patterns that suggest column names
        column_indicators = [
            r'by (\w+)',  # "order by name", "group by status"
            r'where (\w+)',  # "where email", "where status"
            r'select (\w+)',  # "select name", "select email"
            r'show (\w+)',  # "show name", "show status"
            r'find (\w+)',  # "find email", "find status"
            r'with (\w+)',  # "with name", "with status"
            r'(\w+) is',  # "name is", "status is"
            r'(\w+) equals',  # "name equals", "status equals"
            r'(\w+) contains',  # "name contains", "email contains"
        ]
        
        potential_columns = set()
        query_lower = natural_query.lower()
        
        # Extract using patterns
        for pattern in column_indicators:
            matches = re.findall(pattern, query_lower)
            potential_columns.update(matches)
        
        # Also look for common database field names mentioned directly
        common_fields = [
            'name', 'email', 'phone', 'status', 'type', 'date', 'id', 'title',
            'description', 'amount', 'address', 'city', 'state', 'country',
            'created', 'modified', 'updated', 'deleted', 'active', 'inactive',
            'first_name', 'last_name', 'full_name', 'company', 'organization',
            'semester', 'session', 'program', 'course', 'instructor', 'teacher',
            'student', 'school', 'grade', 'subject', 'availability', 'schedule'
        ]
        
        for field in common_fields:
            if field in query_lower:
                potential_columns.add(field)
        
        # Filter out very short words and common English words
        stop_words = {'a', 'an', 'the', 'is', 'are', 'was', 'were', 'be', 'been',
                     'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would',
                     'could', 'should', 'may', 'might', 'can', 'must', 'shall',
                     'to', 'of', 'in', 'on', 'at', 'by', 'for', 'with', 'from',
                     'up', 'about', 'into', 'through', 'during', 'before', 'after',
                     'above', 'below', 'between', 'among', 'and', 'or', 'but',
                     'if', 'then', 'else', 'when', 'where', 'why', 'how', 'what',
                     'who', 'which', 'that', 'this', 'these', 'those', 'all',
                     'any', 'some', 'many', 'much', 'more', 'most', 'other',
                     'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
                     'than', 'too', 'very', 'just', 'now'}
        
        filtered_columns = []
        for col in potential_columns:
            if len(col) > 2 and col not in stop_words and col.isalpha():
                filtered_columns.append(col)
        
        return filtered_columns
    
    async def validate_and_suggest_sql(self, sql_query: str, schema_info: Dict[str, Any]) -> Tuple[str, List[str]]:
        """
        Validate SQL query for column name issues and provide suggestions.
        
        Args:
            sql_query: Generated SQL query
            schema_info: Database schema information
            
        Returns:
            Tuple of (validated_sql, list_of_suggestions)
        """
        is_valid, suggestions = self.fuzzy_matcher.validate_sql_columns(sql_query, schema_info)
        
        if not is_valid:
            # The SQL has potential issues, but we return it anyway with suggestions
            return sql_query, suggestions
        
        return sql_query, []
    
    async def handle_sql_error(self, error_message: str, original_sql: str, 
                              schema_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle SQL execution errors and provide intelligent suggestions.
        
        Args:
            error_message: SQL error message
            original_sql: The SQL query that failed
            schema_info: Database schema information
            
        Returns:
            Dictionary with error analysis and suggestions
        """
        suggestions = self.fuzzy_matcher.suggest_column_corrections(error_message, schema_info)
        
        # Try to extract the problematic column and suggest a corrected SQL
        corrected_sql = original_sql
        column_corrections = {}
        
        # Look for column name corrections in the suggestions
        for suggestion in suggestions:
            if "Did you mean:" in suggestion:
                # This is a more complex parsing task - for now, just provide suggestions
                pass
        
        return {
            'error_type': 'column_name_error',
            'original_error': error_message,
            'suggestions': suggestions,
            'corrected_sql': corrected_sql,
            'column_corrections': column_corrections
        }
