from flask import Flask, json, request, jsonify
from newspaper import Article
import newspaper
import nltk
app = Flask(__name__)
nltk.download('punkt')
@app.route("/getArticle", methods=["POST"])
def hello():
    data = request.json
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
