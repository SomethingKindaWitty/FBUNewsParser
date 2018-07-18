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
    returnData = {
        "text": article.text,
        "keywords": article.keywords
    }
    # cnn_paper = newspaper.build('http://cnn.com')
    # for article in cnn_paper.articles:
    #     print(article.url)

    return jsonify(returnData)

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
