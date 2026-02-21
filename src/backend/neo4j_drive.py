from neo4j import GraphDatabase, basic_auth
import os

def neo4j_driver_set():
    uri = os.getenv("NEO4J_URI", "neo4j://localhost:7687")
    user = os.getenv("NEO4J_USERNAME", "neo4j")
    password = os.getenv("MY_NEO4J_PASSWORD", "")
    driver_n4j = GraphDatabase.driver(uri, auth=(user, password))
    return driver_n4j



