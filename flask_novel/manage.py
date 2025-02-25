from flask.cli import FlaskGroup

from novel import app, db


cli = FlaskGroup(app)

tables = {'./novel/tables/choice.csv': {
    'fields': 'choice_id, choice_text, text_uk',
    'name': 'choice'},
    './novel/tables/outcome.csv': {
    'fields': 'outcome_id, story_id, choice_id, next_story_id',
    'name': 'outcome'},
    './novel/tables/story.csv': {
    'fields': 'story_id, story_text, text_uk, chapter, chapter_uk, location, location_uk, img_path',
    'name': 'story'}}


def import_data_from_csv(table_dict):

    conn = db.engine.raw_connection()
    c = conn.cursor()

    for table in table_dict:
        table_name = table_dict[table]['name']
        fields = table_dict[table]['fields']

        sql_command = f"""
        COPY {table_name} ({fields})
        FROM STDIN WITH CSV HEADER DELIMITER AS ','
        """
        # Execute the COPY command using the cursor's copy_expert method
        with open(table, 'r') as file:
            c.copy_expert(sql=sql_command, file=file)
            print(f"{table} done!")

    conn.commit()
    c.close()
    conn.close()


@cli.command("create_db")
def create_db():
    db.drop_all()
    db.create_all()
    db.session.commit()


@cli.command("seed_db")
def seed_db():
    import_data_from_csv(tables)


if __name__ == "__main__":
    cli()
