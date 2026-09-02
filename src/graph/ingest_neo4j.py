import os
import pandas as pd
from pathlib import Path
from neo4j import GraphDatabase
from dotenv import load_dotenv
import time

def create_constraints(session):
    print("Creating constraints...")
    # Using AuraDB Neo4j 5.x syntax
    constraints = [
        "CREATE CONSTRAINT IF NOT EXISTS FOR (m:Merchant) REQUIRE m.merchant_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (t:Transaction) REQUIRE t.transaction_id IS UNIQUE",
        "CREATE CONSTRAINT IF NOT EXISTS FOR (e:Entity) REQUIRE e.entity_id IS UNIQUE"
    ]
    for q in constraints:
        session.run(q)
    print("Constraints created.")

def ingest_merchants(session, data_dir):
    print("Ingesting Merchants...")
    df = pd.read_csv(data_dir / "merchants.csv")
    df = df.fillna("") # Handle nulls for Neo4j properties
    
    query = """
    UNWIND $batch AS row
    MERGE (m:Merchant {merchant_id: row.merchant_id})
    SET m.merchant_name = CASE WHEN row.merchant_name = "" THEN null ELSE row.merchant_name END,
        m.category = CASE WHEN row.category = "" THEN null ELSE row.category END,
        m.onboarding_date = CASE WHEN row.onboarding_date = "" THEN null ELSE row.onboarding_date END,
        m.kyc_status = CASE WHEN row.kyc_status = "" THEN null ELSE row.kyc_status END
    """
    
    batch = df.to_dict('records')
    # Use chunking if large, but 5000 is small enough for one transaction on Aura if careful, let's chunk to 1000
    chunk_size = 1000
    for i in range(0, len(batch), chunk_size):
        session.run(query, batch=batch[i:i+chunk_size])
    print(f"Ingested {len(batch)} merchants.")

def ingest_transactions(session, data_dir):
    print("Ingesting Transactions...")
    df = pd.read_csv(data_dir / "transactions.csv")
    df = df.fillna("")
    
    query = """
    UNWIND $batch AS row
    MERGE (t:Transaction {transaction_id: row.transaction_id})
    SET t.customer_id = CASE WHEN row.customer_id = "" THEN null ELSE row.customer_id END,
        t.timestamp = row.timestamp,
        t.amount = toFloat(row.amount),
        t.payment_method = CASE WHEN row.payment_method = "" THEN null ELSE row.payment_method END,
        t.device_id = CASE WHEN row.device_id = "" THEN null ELSE row.device_id END,
        t.ip_id = CASE WHEN row.ip_id = "" THEN null ELSE row.ip_id END,
        t.status = CASE WHEN row.status = "" THEN null ELSE row.status END
    
    WITH t, row
    MATCH (m:Merchant {merchant_id: row.merchant_id})
    MERGE (m)-[:PERFORMED]->(t)
    """
    batch = df.to_dict('records')
    chunk_size = 1000
    for i in range(0, len(batch), chunk_size):
        session.run(query, batch=batch[i:i+chunk_size])
    print(f"Ingested {len(batch)} transactions.")

def ingest_entities_and_relationships(session, data_dir):
    print("Ingesting Entities and Relationships...")
    df = pd.read_csv(data_dir / "relationships.csv")
    df = df.fillna("")
    
    query = """
    UNWIND $batch AS row
    MERGE (e:Entity {entity_id: row.entity_id})
    SET e.type = row.entity_type
    
    WITH e, row
    MATCH (m:Merchant {merchant_id: row.merchant_id})
    MERGE (m)-[r:SHARES {
        start_time: row.start_time,
        end_time: row.end_time
    }]->(e)
    """
    batch = df.to_dict('records')
    chunk_size = 1000
    for i in range(0, len(batch), chunk_size):
        session.run(query, batch=batch[i:i+chunk_size])
    print(f"Ingested {len(batch)} relationships.")

def verify_counts(session, data_dir):
    print("--- VERIFICATION COUNTS ---")
    
    m_csv = len(pd.read_csv(data_dir / "merchants.csv"))
    t_csv = len(pd.read_csv(data_dir / "transactions.csv"))
    rels_df = pd.read_csv(data_dir / "relationships.csv")
    r_csv = len(rels_df)
    e_csv = len(rels_df["entity_id"].unique())

    m_neo = session.run("MATCH (n:Merchant) RETURN count(n) AS c").single()["c"]
    t_neo = session.run("MATCH (n:Transaction) RETURN count(n) AS c").single()["c"]
    e_neo = session.run("MATCH (n:Entity) RETURN count(n) AS c").single()["c"]
    
    rel_p_neo = session.run("MATCH ()-[r:PERFORMED]->() RETURN count(r) AS c").single()["c"]
    rel_s_neo = session.run("MATCH ()-[r:SHARES]->() RETURN count(r) AS c").single()["c"]

    print(f"Merchant Count   | CSV: {m_csv:6d} | Neo4j: {m_neo:6d}")
    print(f"Transaction Count| CSV: {t_csv:6d} | Neo4j: {t_neo:6d}")
    print(f"Entity Count     | CSV: {e_csv:6d} | Neo4j: {e_neo:6d}")
    print(f"PERFORMED Count  | CSV: {t_csv:6d} | Neo4j: {rel_p_neo:6d}")
    print(f"SHARES Count     | CSV: {r_csv:6d} | Neo4j: {rel_s_neo:6d}")
    
    return {
        "m_csv": m_csv, "m_neo": m_neo,
        "t_csv": t_csv, "t_neo": t_neo,
        "e_csv": e_csv, "e_neo": e_neo,
        "rel_p_csv": t_csv, "rel_p_neo": rel_p_neo,
        "rel_s_csv": r_csv, "rel_s_neo": rel_s_neo
    }

def main():
    load_dotenv()
    uri = os.getenv("NEO4J_URI")
    user = os.getenv("NEO4J_USER")
    password = os.getenv("NEO4J_PASSWORD")
    
    data_dir = Path("data/synthetic_v2")
    
    if not uri or not password:
        print("Missing credentials in .env")
        return
        
    driver = GraphDatabase.driver(uri, auth=(user, password))
    with driver.session() as session:
        t0 = time.time()
        create_constraints(session)
        ingest_merchants(session, data_dir)
        ingest_transactions(session, data_dir)
        ingest_entities_and_relationships(session, data_dir)
        t1 = time.time()
        print(f"Ingestion completed in {t1-t0:.2f} seconds.")
        
        counts = verify_counts(session, data_dir)
        
    driver.close()

if __name__ == "__main__":
    main()
