from flask import Flask, json, request, jsonify
from newspaper import Article
import newspaper
import nltk

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

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


@app.route("/test")
def test():
    # Imports the Google Cloud client library

    # Instantiates a client
    client = language.LanguageServiceClient()

    # The text to analyze
    text = u'Hello, world!'
    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    # Detects the sentiment of the text
    sentiment = client.analyze_sentiment(document=document).document_sentiment

    print('Text: {}'.format(text))
    print('Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude))
    return 'Sentiment: {}, {}'.format(sentiment.score, sentiment.magnitude)


def classify_text(text):
    """Classifies content categories of the provided text."""
    client = language.LanguageServiceClient()

    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    categories = client.classify_text(document).categories

    return categories
