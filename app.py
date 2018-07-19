from flask import Flask, json, request, jsonify
from newspaper import Article
import newspaper
import nltk

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types
from bs4 import BeautifulSoup

import requests

app = Flask(__name__)
nltk.download('punkt')
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


@app.route("/getClassification", methods=["POST"])
def classify():
    data = request.json
    url = data["url"]
    article = Article(url)
    article.download()
    article.parse()

    categories = classify_text(article.text)
    for category in categories:
        print(u'=' * 20)
        print(u'{:<16}: {}'.format('name', category.name))
        print(u'{:<16}: {}'.format('confidence', category.confidence))
    return "success"


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



def classify_text(text):
    """Classifies content categories of the provided text."""
    client = language.LanguageServiceClient()

    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    categories = client.classify_text(document).categories

    return categories
