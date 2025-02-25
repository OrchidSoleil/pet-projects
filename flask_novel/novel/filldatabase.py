import sqlite3
import csv

# connect to the database
conn = sqlite3.connect('game_uk.db')
cursor = conn.cursor()

tables = ['']

for table in tables:
    with open('tables/outcome.csv', 'r', encoding='utf-8') as csv_file:
        csv_reader = csv.reader(csv_file)

        # Skip the header row if it exists
        next(csv_reader, None)

        for row in csv_reader:
            conn.execute("PRAGMA encoding = 'UTF-8';")
            # cursor.execute("INSERT INTO outcome (outcome_id, story_id, choice_id, next_story_id) VALUES (?, ?, ?, ?);", row)

# Commit the changes and close the connection
conn.commit()
conn.close()
