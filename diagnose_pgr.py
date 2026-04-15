import os
from dotenv import load_dotenv
from sqlalchemy import create_engine, text

load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)

def diagnose_pgrouting():
    print("🔍 Diagnosing pgRouting Functions...")
    with engine.connect() as conn:
        # 1. Check if pgr_nodeNetwork exists and what its arguments are
        sql = text("""
            SELECT n.nspname as schema, p.proname as function, pg_get_function_arguments(p.oid) as args
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE p.proname ILIKE 'pgr_nodeNetwork%';
        """)
        res = conn.execute(sql).fetchall()
        if not res:
            print("❌ Could not find pgr_nodeNetwork in any schema!")
        for r in res:
            print(f"Found: {r.schema}.{r.function}({r.args})")

        # 2. Check if pgr_createTopology exists
        sql = text("""
            SELECT n.nspname as schema, p.proname as function, pg_get_function_arguments(p.oid) as args
            FROM pg_proc p
            JOIN pg_namespace n ON p.pronamespace = n.oid
            WHERE p.proname ILIKE 'pgr_createTopology%';
        """)
        res = conn.execute(sql).fetchall()
        for r in res:
            print(f"Found: {r.schema}.{r.function}({r.args})")

if __name__ == "__main__":
    diagnose_pgrouting()
