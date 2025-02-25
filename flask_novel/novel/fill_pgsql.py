# import psycopg2

tables = {
    'tables/choice.csv': {'fields': 'choice_id, choice_text, text_uk', 'name': 'choice'},
    'tables/outcome.csv': {'fields': 'outcome_id, story_id, choice_id, next_story_id', 'name': 'outcome'},
    'tables/story.csv': {'fields': 'story_id, story_text, text_uk, chapter, chapter_uk, location, location_uk, img_path', 'name': 'story'}}


def import_data_from_csv(table_dict):
    from novel import db, app

    conn = db.engine.raw_connection()
    c = conn.cursor()

    for table in tables:
        table_name = tables[table]['name']
        fields = tables[table]['fields']

        sql_command = f"""
        COPY {table_name} ({fields})
        FROM STDIN WITH CSV HEADER DELIMITER AS ','
        """

        # Execute the COPY command using the cursor's copy_expert method
        with open(table, 'r') as file:
            c.copy_expert(sql=sql_command, file=file)

    conn.commit()

    c.close()
    conn.close()


import_data_from_csv(tables)
