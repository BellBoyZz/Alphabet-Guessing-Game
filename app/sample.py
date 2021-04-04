from pymongo import MongoClient
from flask import Flask, request, jsonify, render_template, redirect
import os
import json
import redis

# App
application = Flask(__name__)

# connect to MongoDB
mongoClient = MongoClient(
    'mongodb://' + os.environ['MONGODB_USERNAME'] + ':' + os.environ['MONGODB_PASSWORD'] + '@' + os.environ[
        'MONGODB_HOSTNAME'] + ':27017/' + os.environ['MONGODB_AUTHDB'])
db = mongoClient[os.environ['MONGODB_DATABASE']]

# connect to Redis
redisClient = redis.Redis(host=os.environ.get("REDIS_HOST", "localhost"), port=os.environ.get("REDIS_PORT", 6379),
                          db=os.environ.get("REDIS_DB", 0))


@application.route('/')
def index():
    body = '<h2>Welcome to Alphabet Guessing Game!</h2>'
    body += '<button> <a href="/start/">Start</a></button>'
    body += '<p>Press the start button to begin...</>'
    return body


@application.route('/start/')
def start():
    body = '<h2>Alphabet Guessing Game</h2>'
    game = db.game.find_one()
    if game is None:
        game_stats = {
            "question": ["_", "_", "_", "_"],
            "guessing": ["?", "?", "?", "?"],
            "answer": ["_", "_", "_", "_"],
            "attempts": 0,
            "index": 0,
            "not_start": False
        }
        db.game.insert_one(game_stats)
        body += '<h3>Please refresh this page.</h3>'

    elif game is not None:
        body = '<h1>Please select 4 characters to create a question.</h1>'
        body += '<br></br>'
        question_text = ' '.join(game['question'])
        body += 'Question :' + question_text
        body += '<br></br>'
        body += '<a href="/A/"><button>A</button></a>'
        body += '<a href="/B/"><button>B</button></a>'
        body += '<a href="/C/"><button>C</button></a>'
        body += '<a href="/D/"><button>D</button></a>'
        if game['index'] == 4:
            db.game.update_one({}, {"$set": {"not_start": True}})
            db.game.update_one({}, {"$set": {"index": 0}})
            body = '<h1>Please select 4 characters to create a question.</h1>'
            body += 'Question created.'
            body += '<br></br>'
            body += '<a href="/game-play/"><button> Press to start.</button></a>'
            return body
    return body


def create_question(game, alphabet):
    current_index = game["index"]
    db.game.update_one({}, {"$set": {"question." + str(current_index): alphabet}})
    current_index += 1
    db.game.update_one({}, {"$set": {"index": current_index}})


@application.route('/game-play/')
def game_play():
    game = db.game.find_one()
    if game['question'] == game['answer']:
        return game_over()
    answer = ' '.join(game['answer'])
    guessing = ' '.join(game['guessing'])
    body = '<h2>Alphabet Guessing Game</h2>'
    body += "Begin your guess."
    body += '<br> <br> '
    body += 'Answer: ' + answer
    body += 'Character(s) remaining: ' + guessing
    body += '<br> <br>'
    body += '<a href="/A"><button> A </button></a>'
    body += '<a href="/B"><button> B </button></a>'
    body += '<a href="/C"><button> C </button></a>'
    body += '<a href="/D"><button> D </button></a>'
    return body


@application.route('/A/')
def first_character():
    game = db.game.find_one()
    if game['not_start'] is False:
        create_question(game, 'A')
        return start()
    if game['not_start'] is True:
        insert_answer(game, 'A')
        return game_play()


@application.route('/B/')
def second_character():
    game = db.game.find_one()
    if game['not_start'] is False:
        create_question(game, 'B')
        return start()
    if game['not_start'] is True:
        insert_answer(game, 'B')
        return game_play()


@application.route('/C/')
def third_character():
    game = db.game.find_one()
    if game['not_start'] is False:
        create_question(game, 'C')
        return start()
    if game['not_start'] is True:
        insert_answer(game, 'C')
        return game_play()


@application.route('/D/')
def fourth_character():
    game = db.game.find_one()
    if game['not_start'] is False:
        create_question(game, 'D')
        return start()
    if game['not_start'] is True:
        insert_answer(game, 'D')
        return game_play()


def insert_answer(game, alphabet):
    current_index = game["index"]
    current_attempts = game["attempts"]
    current_attempts += 1
    if game['question'][current_index] == alphabet:
        db.game.update_one({}, {"$set": {"answer." + str(current_index): alphabet}})
        current_index += 1
        db.game.update_one({}, {"$set": {"index": current_index}})
        db.game.update_one({}, {"$set": {'char_remain.' + str(current_index): ""}})
    else:
        current_attempts += 1
        db.game.update_one({}, {"$set": {"incorrect": current_attempts}})


@application.route('/game-over/')
def game_over():
    game = db.game.find_one()
    body = '<h2>The game ended...</h2>'
    body += '<b>You win!</b>'
    body += '<br> <br> '
    body += '<b>Number of attempts: </b>' + str(game['attempts'])
    body += '<br> <br>'
    body += '<a href="/restart"><button> Play again? </button></a>'
    return body


@application.route('/restart')
def restart():
    game_stats = {
        "question": ["_", "_", "_", "_"],
        "guessing": ["?", "?", "?", "?"],
        "answer": ["_", "_", "_", "_"],
        "attempts": 0,
        "index": 0,
        "restart": False
    }
    db.game.update_one({}, {"$set": game_stats})
    return index()


if __name__ == "main":
    ENVIRONMENT_DEBUG = os.environ.get("FLASK_DEBUG", True)
    ENVIRONMENT_PORT = os.environ.get("FLASK_PORT", 5000)
    application.run(host='0.0.0.0', port=ENVIRONMENT_PORT, debug=ENVIRONMENT_DEBUG)
