from flask import Flask, json, request, jsonify, g
from newspaper import Article
import newspaper
import nltk
import sqlite3

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from bs4 import BeautifulSoup

import requests

app = Flask(__name__)
nltk.download('punkt')

DATABASE = 'quack.db'


@app.route("/getArticle", methods=["POST"])
def hello():
    data = request.json
    print(str(request))
    print(data)
    url = data["url"]
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()
    articleText = article.text

    uncleanedcategories = classify_text(articleText)
    mostLikely = uncleanedcategories[0].name
    index = mostLikely.rindex("/")+1
    mostLikely = mostLikely[index:]

    returnData = {
        "text": articleText,
        "keywords": article.keywords,
        "category": mostLikely
    }

    # cnn_paper = newspaper.build('http://cnn.com')
    # for article in cnn_paper.articles:
    #     print(article.url)

    return jsonify(returnData)


@app.route("/sources")
def sources():
    url = "https://newsapi.org/sources"
    r = requests.get(url)
    data = r.text
    soup = BeautifulSoup(data, 'lxml')
    list = soup.find_all("kbd")
    sources = []
    keepTrack = False
    for tag in list:
        text = tag.string
        if text == 'abc-news':
            keepTrack = True
        if keepTrack:
            sources.append(text)
    return jsonify(sources)

@app.route("/register", methods=["POST"])
def register():
    # References
    # sqlite: https://docs.python.org/2/library/sqlite3.html
    # Flask: http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
    # DB browser: https://sqlitebrowser.org/


    # must run this command before making any SQLITE commands
    cur = get_db().cursor()

    # gets data from request
    data = request.json
    print(data)

    # gets the username from the data
    username = data["username"]
    password = data["password"]

    # executes a SQL query
    cur.execute('INSERT INTO Users (Username, Password) VALUES (?,?)', (username, password))

    #saves the results of the query
    get_db().commit()

    #returns the user
    return jsonify(data)


def classify_text(text):
    """Classifies content categories of the provided text."""
    client = language.LanguageServiceClient()

    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    categories = client.classify_text(document).categories

    return categories

def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db
