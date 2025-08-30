import pandas as pd
from sqlalchemy import create_engine, text
import os
from dotenv import load_dotenv

load_dotenv()

DATABASE_URL = "postgresql://neondb_owner:npg_qV9a3dQRAeBm@ep-still-field-a17hi4xm-pooler.ap-southeast-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require"

def get_db_connection():
    """Create and return a database connection"""
    return create_engine(DATABASE_URL)

def test_connection():
    """Test the database connection"""
    try:
        engine = get_db_connection()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT COUNT(*) as total_records FROM argo_floats"))
            count = result.fetchone()[0]
        return count
    except Exception as e:
        print(f"Connection error: {e}")
        return 0

def execute_query(sql_query):
    """Execute a SQL query and return results as DataFrame"""
    try:
        engine = get_db_connection()
        df = pd.read_sql(text(sql_query), engine)
        return df, None
    except Exception as e:
        return None, f"Database error: {str(e)}"

# Test it works!
if __name__ == "__main__":
    count = test_connection()
    print(f"🎉 Connected! We have {count} records in our ocean database!")