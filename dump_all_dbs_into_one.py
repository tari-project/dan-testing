import sqlite3

def copy_data(source_db, destination_db, source_name):
    # Connect to the source database
    source_conn = sqlite3.connect(source_db)
    source_cursor = source_conn.cursor()

    # Connect to the destination database
    destination_conn = sqlite3.connect(destination_db)
    destination_cursor = destination_conn.cursor()

    # Get a list of all tables in the source database
    source_cursor.execute("SELECT name FROM sqlite_master WHERE type='table'  AND name != 'sqlite_sequence';")
    tables = source_cursor.fetchall()

    # Iterate over each table
    for table in tables:
        table_name = table[0]

        # Retrieve the column names and types of the table in the source database
        source_cursor.execute(f"PRAGMA table_info({table_name});")
        columns = source_cursor.fetchall()

        # Build the CREATE TABLE statement for the destination database
        create_table_statement = f"CREATE TABLE IF NOT EXISTS {table_name} ("
        column_names = []
        for column in columns:
            column_name = column[1]
            column_type = column[2]
            column_names.append(column_name)
            create_table_statement += f"{column_name} {column_type}, "
        create_table_statement += "Source TEXT);"

        # Create the table in the destination database
        destination_cursor.execute(create_table_statement)

        # Copy data from the source to the destination database
        source_cursor.execute(f"SELECT * FROM {table_name};")
        rows = source_cursor.fetchall()

        for row in rows:
            # Add the source name to the row data
            row_data = list(row)
            row_data.append(source_name)

            # Build the INSERT statement for the destination database
            insert_statement = f"INSERT INTO {table_name} VALUES ({', '.join(['?'] * (len(columns) + 1))});"

            # Insert the row data into the destination database
            destination_cursor.execute(insert_statement, row_data)

    # Commit the changes and close the connections
    destination_conn.commit()
    source_conn.close()
    destination_conn.close()


num_vns = 8
for i in range(num_vns):
    copy_data(f"vn_{i}/localnet/data/validator_node/state.db", "stdout/all.db", f"vn_{i}")
