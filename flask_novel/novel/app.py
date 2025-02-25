import os

import sqlite3
from flask import Flask, flash, redirect, render_template, request, session, jsonify, url_for
from flask_session import Session
from tempfile import mkdtemp
from flask_babel import Babel, gettext, _
from dotenv import load_dotenv


# configure localization
def get_locale():
    return session.get('user_language')


# Configure application
app = Flask(__name__)

load_dotenv()
SECRET_KEY = os.environ.get('SECRET_KEY')
# configure translations
babel = Babel(app, locale_selector=get_locale)

# setup session
app.config["SESSION_FILE_DIR"] = mkdtemp()
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# configure language app to support Ukrainian
app.config['BABEL_DEFAULT_LOCALE'] = 'en'
app.config['BABEL_SUPPORTED_LOCALES'] = ['en', 'uk']


# configure database
# db = sqlite3("sqlite:///game.db")

# Set up global anchor for the story, to keep up with language change and guest users
STORY_ID = 1


@app.route('/game', methods=["GET", "POST"])
def game(lang=None):
    # refresh story on 'New Game'
    outcome_id = 1
    if request.method == "POST":
        # AJAX to identify story_id
        data = request.get_json()
        # print(data)
        outcome_id = data.get('choiceOutcome')
        # update STORY_ID with current story
        global STORY_ID
        STORY_ID = outcome_id
        if int(outcome_id) == 0:
            return redirect(url_for('gameover'))

    # to prevent falling back to the start of the story on language change, update var with current story_id
    if request.method == "GET":
        if lang:
            outcome_id = STORY_ID

    game_data = get_data(outcome_id)
    story_text = game_data[0][0]
    location = game_data[0][1]
    chapter = game_data[0][2]
    img_path = 'static/img/' + game_data[0][3]
    choices = {}
    choices_uk = {}
    for i in range(len(game_data)):
        choices[game_data[i][4]] = game_data[i][5]
        choices_uk[game_data[i][9]] = game_data[i][5]
    story_uk = game_data[0][6]
    location_uk = game_data[0][7]
    chapter_uk = game_data[0][8]

    if session.get('user_language', 'en') == 'uk':
        story_text, location, chapter, choices = story_uk, location_uk, chapter_uk, choices_uk

    if request.method == "GET":
        return render_template("game.html", story_text=story_text, img_path=img_path, location=location, chapter=chapter, choices=choices)
    elif request.method == "POST":
        return jsonify(story_text=story_text, img_path=img_path, location=location, chapter=chapter, choices=choices)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/set_language")
def set_language():
    selected_language = request.args.get('language')
    session['user_language'] = selected_language
    referrer = request.referrer
    print(f"lang: {session['user_language']} referrer: {referrer}")

    if referrer.endswith('/game') or 'set_language?' in referrer:
        if STORY_ID == '0':
            # since ajax, the response is modified for gameover
            return gameover()
        return game(selected_language)

    return redirect(request.referrer or url_for('index'))


def get_data(outcome):
    conn = sqlite3.connect('game.db')
    cursor = conn.cursor()
    try:
        cursor.execute("""
            SELECT story.story_text, story.location, story.chapter, story.img_path, choice.choice_text, outcome.next_story_id, story.text_uk, story.location_uk, story.chapter_uk, choice.text_uk
            FROM outcome
            INNER JOIN story ON outcome.story_id = story.story_id
            INNER JOIN choice ON outcome.choice_id = choice.choice_id
            WHERE story.story_id = ?;
        """, (outcome,))
        game_data = cursor.fetchall()
    except Exception as e:
        error_message = gettext(u'There was a problem with your request. Please try again later.')
        game_data = [(error_message, "", "", "", "", "")]
        print(str(e), '500')
    finally:
        cursor.close()
        conn.close()
        return game_data


@app.route('/gameover', methods=["GET", "POST"])
def gameover():
    msg_text = gettext(u'Thank you for playing my game!')
    msg = [(msg_text, "", "", "", "", "")]
    print('def gameover')
    return render_template("about.html", msg=msg)


@app.route("/about.html")
def about():
    return render_template("about.html")

# this feature might be implemented later
# @app.route("/add_user")
# def add_user():
    # conn = sqlite3.connect("mydatabase.db")  # Replace with your database name
#     cursor = conn.cursor()
#     cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("user1", "hashed_password"))
#     conn.commit()
#     conn.close()
#     return "User added successfully!"

# basic db functions
# def get_db_connection():
#     conn = sqlite3.connect('your_database.db')
#     cursor = conn.cursor()
#     return conn, cursor

# def close_db_connection(conn):
#     conn.commit()
#     conn.close()

# def some_function():
#     conn, cursor = get_db_connection()

#     # Use the cursor to execute your queries
#     cursor.execute('SELECT * FROM your_table')
#     data = cursor.fetchall()

#     close_db_connection(conn)

# # Call the function
# some_function()


if __name__ == '__main__':
    app.run()
