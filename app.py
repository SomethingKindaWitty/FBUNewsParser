from flask import Flask, json, request, jsonify
from newspaper import Article
import newspaper
app = Flask(__name__)

@app.route("/getarticle", methods=["POST"])
def hello():
    data = request.json
    url = data["url"]
    article = Article(url)
    article.download()
    article.parse()
    returnData = {
        "text": article.text
    }
    # cnn_paper = newspaper.build('http://cnn.com')
    # for article in cnn_paper.articles:
    #     print(article.url)

    return jsonify(returnData)
