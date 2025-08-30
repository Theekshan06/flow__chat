import os
import re
from groq import Groq
from dotenv import load_dotenv

# Force load .env from project root
dotenv_path = os.path.join(os.path.dirname(__file__), "..", ".env")
load_dotenv(dotenv_path=dotenv_path)

api_key = os.getenv("GROQ_API_KEY")
print("API Key loaded?", bool(api_key))  # Debugging

if not api_key:
    raise ValueError("❌ No Groq API key found. Please set GROQ_API_KEY in your .env file")

client = Groq(api_key=api_key)

SYSTEM_PROMPT = """
🌊 You are OceanGPT, an expert oceanographer's AI assistant! 

Your job: Convert human questions about ARGO float data into perfect SQL queries.

DATABASE SCHEMA:
- Table: argo_floats
- Columns: 
  - platform_number (text)
  - cycle_number (integer)
  - measurement_time (timestamp)
  - latitude (numeric)
  - longitude (numeric)
  - pressure (numeric)
  - temperature (numeric)
  - salinity (numeric)
  - data_quality (text)

RULES:
1. Always return ONLY SQL code in ```sql``` code blocks
2. Add LIMIT 100 to queries
"""

def ask_ocean_gpt(question: str) -> str:
    """Use Groq API to generate SQL from natural language questions"""
    try:
        print(f"🤖 Sending question to Groq: {question[:50]}...")
        chat_completion = client.chat.completions.create(
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": question}
            ],
            model="llama3-8b-8192",
            temperature=0.1,
            max_tokens=500
        )
        print("✅ Groq response received successfully")
        return chat_completion.choices[0].message.content
    except Exception as e:
        return f"❌ Error: {str(e)}"

def extract_sql_from_response(llm_response: str):
    """Extract SQL string from LLM response"""
    if llm_response.startswith("❌"):
        return None
    
    # Look for SQL code block
    sql_pattern = r'```sql\n(.*?)\n```'
    matches = re.findall(sql_pattern, llm_response, re.DOTALL)
    if matches:
        return matches[0].strip()
    
    # Fallback: raw SELECT statement
    select_pattern = r'(SELECT.*?;)'
    matches = re.findall(select_pattern, llm_response, re.DOTALL | re.IGNORECASE)
    if matches:
        return matches[0].strip()
    
    return None
