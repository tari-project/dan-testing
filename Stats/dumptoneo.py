import sqlite3
from py2neo import Graph
import json


num_vns = 8

neo4j_graph = Graph("bolt://localhost:7687", auth=("neo4j", "password123"))

# delete
neo4j_graph.run("MATCH (n) DETACH DELETE n")

for i in range(num_vns):
    # Connect to SQLite database
    conn = sqlite3.connect(f"vn_{i}/localnet/data/validator_node/state.db")
    cursor = conn.cursor()

    # Read data from "nodes" table
    cursor.execute("SELECT id, node_hash, parent_node_hash, payload_height, justify FROM nodes;")
    rows = cursor.fetchall()

    # Generate genesis
    genesis = "CREATE (genesis: Node {id: '0000000000000000000000000000000000000000000000000000000000000000'})"
    neo4j_graph.run(genesis)

    # Iterate over rows and create nodes
    for row in rows:
        node_id, node_hash, parent, plh, j = row
        node_hash_hex = node_hash.hex()
        create_statement = f"MERGE (node_{node_hash_hex}: Node {{id: '{node_hash_hex}', source: 'vn_{i}'}}) "
        neo4j_graph.run(create_statement)

    # Remove trailing comma and space

    # Connect to Neo4j and run the CREATE statement

    print("Nodes created in Neo4j.")

    for row in rows:
        node_id, node_hash, parent, payload_height, justify = row
        node_hash_hex = node_hash.hex()
        parent_hash_hex = parent.hex()
        justify_data = json.loads(justify)
        validators_metadata = justify_data.get("validators_metadata")
        print(payload_height)
        print(validators_metadata)
        relname = "CHILD_OF"
        match payload_height:
            case 1:
                relname = "PREPARE"
            case 2:
                relname = "PRECOMMIT"
            case 3:
                relname = "COMMIT"
            case 4:
                relname = "DECIDE"
        create_rel = (
            f"MATCH (a:Node {{id: '{node_hash_hex}'}}), (b:Node {{id: '{parent_hash_hex}'}}) MERGE (a)-[hs_{node_hash_hex}_{parent_hash_hex}:{relname}]->(b)"
        )
        print(create_rel)
        neo4j_graph.run(create_rel)
        if validators_metadata:
            for vn_vote in validators_metadata:
                public_key = vn_vote.get("public_key")
                print(public_key)
                neo4j_graph.run(f"MERGE (vn_{public_key}: Validator {{id: '{public_key}'}})")
                neo4j_graph.run(
                    f"MATCH (a:Node {{id: '{parent_hash_hex}'}}), (b:Validator {{id: '{public_key}'}}) MERGE (b)-[vote_{parent_hash_hex}_{public_key}:VOTED]->(a) "
                )
                neo4j_graph.run(
                    f"MATCH (a:Node {{id: '{node_hash_hex}'}}), (b:Validator {{id: '{public_key}'}}) MERGE (b)-[justify_{node_hash_hex}_{public_key}:JUSTIFIES]->(a)"
                )

    # Close the SQLite connection
    conn.close()
