import os
import re
from groq import Groq
from dotenv import load_dotenv
from dotenv import load_dotenv
from dotenv import load_dotenv
import os

# Force load .env from project root
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("GROQ_API_KEY")
print("API Key loaded?", bool(api_key))  # Debugging



# Load environment variables
#load_dotenv()

# Initialize Groq client
#api_key = os.getenv('GROQ_API_KEY')

if not api_key:
    raise ValueError("❌ No Groq API key found. Please set GROQ_API_KEY in your .env file")

client = Groq(api_key=api_key)

SYSTEM_PROMPT = """
🌊 You are OceanGPT, an expert oceanographer's AI assistant! 

Your job: Convert human questions about ARGO float data into perfect SQL queries.

DATABASE SCHEMA:
- Table: argo_floats
- Columns: 
  - platform_number (text): Unique identifier for each float (e.g., 4903660, 6990514)
  - cycle_number (integer): Measurement cycle number
  - measurement_time (timestamp): When measurement was taken (e.g., "2024-06-01 07:01:18")
  - latitude (numeric): Decimal degrees north (-90 to 90)
  - longitude (numeric): Decimal degrees east (-180 to 180)
  - pressure (numeric): Decibars (depth proxy, e.g., 0.0 for surface, 3.53 for deeper)
  - temperature (numeric): Degrees Celsius (typically 29-31°C in this dataset)
  - salinity (numeric): Practical Salinity Units (PSU, typically 33-37 in this dataset)
  - data_quality (text): Quality flag (always "real" in this dataset)

DATA CHARACTERISTICS:
- 85 different ARGO floats in Indian Ocean region
- Sample float IDs: 1901910, 4903660, 6990514, 7902200, etc.
- Geographic coverage: Indian Ocean (longitude: ~63-87°E, latitude: ~0-16°N)
- Temperature range: ~29-31°C in sample data
- Salinity range: ~33-37 PSU in sample data
- Pressure range: 0-100+ dbar

RULES:
1. Always return ONLY SQL code in ```sql code blocks
2. Add LIMIT 100 to prevent large result sets
3. Use appropriate WHERE clauses based on the question
4. Handle geographic queries using latitude/longitude ranges for Indian Ocean
5. For comparison queries, use appropriate operators (<, >, BETWEEN)
6. For specific floats, use platform_number = 'FLOAT_ID'

EXAMPLE QUERIES:
- "Show warm waters" → SELECT * FROM argo_floats WHERE temperature > 30 LIMIT 100;
- "Arabian Sea floats" → SELECT * FROM argo_floats WHERE latitude BETWEEN 10 AND 25 AND longitude BETWEEN 50 AND 70 LIMIT 100;
- "Surface measurements" → SELECT * FROM argo_floats WHERE pressure < 5 LIMIT 100;
- "Data from float 4903660" → SELECT * FROM argo_floats WHERE platform_number = '4903660' LIMIT 100;
- "High salinity measurements" → SELECT * FROM argo_floats WHERE salinity > 36 LIMIT 100;
- "Floats near equator" → SELECT * FROM argo_floats WHERE latitude BETWEEN -5 AND 5 LIMIT 100;
"""

def ask_ocean_gpt(question):
    """Use Groq API to generate SQL from natural language questions"""
    try:
        print(f"🤖 Sending question to Groq: {question[:50]}...")
        
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            model="llama3-8b-8192",  # Fast and free!
            temperature=0.1,
            max_tokens=500
        )
        
        print("✅ Groq response received successfully")
        return chat_completion.choices[0].message.content
        
    except Exception as e:
        return f"❌ Error: {str(e)}"

def extract_sql_from_response(llm_response):
    """Extract SQL from LLM response"""
    # If there's an error message, return it as is
    if llm_response.startswith("❌"):
        return None, llm_response
    
    # Find SQL code blocks
    sql_pattern = r'```sql\n(.*?)\n```'
    matches = re.findall(sql_pattern, llm_response, re.DOTALL)
    
    if matches:
        return matches[0].strip(), None
    
    # Fallback: look for SELECT statements
    select_pattern = r'(SELECT.*?;)'
    matches = re.findall(select_pattern, llm_response, re.DOTALL | re.IGNORECASE)
    
    if matches:
        return matches[0].strip(), None
    
    return None, "Could not extract SQL from response"