from flask import Flask, json, request, jsonify, g
import newspaper
from newspaper import Article
import newspaper
import nltk
import sqlite3
from datetime import datetime

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



@app.route("/getKeywords", methods=["POST"])
def keywords():
    data = request.json
    print(data)
    url = data["url"]
    article = Article(url)
    article.download()
    article.parse()
    article.nlp()

    returnData = {
        "keywords": article.keywords
    }

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

def classify_text(text):
    """Classifies content categories of the provided text."""
    client = language.LanguageServiceClient()

    document = types.Document(
        content=text,
        type=enums.Document.Type.PLAIN_TEXT)

    categories = client.classify_text(document).categories

    return categories

#    # References
#    # sqlite: https://docs.python.org/2/library/sqlite3.html
#    # Flask: http://flask.pocoo.org/docs/1.0/patterns/sqlite3/
#    # DB browser: https://sqlitebrowser.org/

@app.route("/login", methods=["POST"])
def register():
    c = get_db().cursor()

    # gets data from request
    data = request.json
    print(data)

    # gets the username from the data
    username = data["username"]
    password = data["password"]

    #change this to return the whole user to create the user object.
    user = c.execute('SELECT * FROM User WHERE username=? AND password=?', (username, password)).fetchone();
    # if (user is None):
    #     dict = {"UID":-1}
    #     print("User doesn't exist")
    # else:
    #     dict = {"UID":user[0]}
    #     print("User exists")
    # print(user)
    # print(dict)

    #turn user into dictionary
    names = ["UID","username", "password","categories", "url", "politicalPreference", "numUpvoted"]
    dict = {}
    i=0
    if user is None:
        dict = {"UID": -1}
    else:
        for item in user:
            dict[names[i]] = item
            i += 1
    return jsonify(dict)


@app.route("/signin", methods=["POST"])
def create():
    # user doesn't exist, is assumed to be false
    condition = False;
    # create cursor into database
    c = get_db().cursor()

    # gets data from request
    data = request.json
    print(data)

    # gets the username from the data
    username = data["username"]
    password = data["password"]
    poli_pref = data["bias"]

    # make sure table exists
    c.execute('''CREATE TABLE IF NOT EXISTS User (id INT PRIMARY KEY, username TEXT, password TEXT, image TEXT, categories TEXT, political_preference REAL, num_upvoted INTEGER)''')

    # check to see if user is already in table
    user = c.execute('SELECT * FROM User WHERE username=? AND password=?', (username, password)).fetchone();

    if (user is None):
        # user truly doesn't exist, sign them up
        condition = True
        c.execute('''INSERT INTO User (username, password, image,categories, political_preference, num_upvoted)
          VALUES(?,?,?,?,?,?)''', (username, password, None, None, poli_pref, 10))
        user = c.execute('SELECT * FROM User WHERE username=? AND password=?', (username, password)).fetchone();
        print(user)

    # saves the results of the query
    get_db().commit()
    # closes database access
    get_db().close()

    # if the user did not already exist, sign them up
    if (condition):
        #turn user into dictionary
        names = ["UID","username", "password","categories", "url", "politicalPreference", "numUpvoted"]
        dict = {}
        i=0
        for item in user:
            dict[names[i]] = item
            i += 1
        return jsonify(dict)
    
    print("User already existed")
    dict = {"UID":-1}
    print(dict)
    return jsonify(dict)

@app.route("/like", methods=["POST"])
def update_post():
    try:
        #create cursor into database
        c = get_db().cursor()

        # gets data from request
        data = request.json

        # get required fields
        url = data["url"]
        uid = data["UID"]
        poly_bias = data["bias"]

        # create table if it doesn't exist
        c.execute('''CREATE TABLE IF NOT EXISTS Likes (id INT PRIMARY KEY, url TEXT,
                uid INTEGER)''')
        # saves the results of the query
        get_db().commit()


        # add like to table
        c.execute('''INSERT INTO Likes (url, uid)
                  VALUES(?,?)''', (url, uid))
        # saves the results of the query
        get_db().commit()

        # get user
        user = c.execute('''SELECT * FROM User WHERE id=?''',(uid,)).fetchone();
        # saves the results of the query
        get_db().commit()

        num_vote = user[6]
        num_pol = user[5]

        if (num_vote is None):
            num_vote = 0
        if (num_pol is None):
            num_pol = 0

        # update user
        c.execute('''UPDATE User SET num_upvoted=? WHERE id=?''', (num_vote+1 , uid))
        # saves the results of the query
        get_db().commit()
        c.execute('''UPDATE User SET political_preference=? WHERE id=?''', ((num_vote*num_pol+poly_bias)/(num_vote+1) , uid))
        # saves the results of the query
        get_db().commit()
        # closes database access
        get_db().close()

        dict = {}
        dict["isLiked"] = True
        return jsonify(dict)
    except:
        dict = {}
        dict["isLiked"] = False
        return jsonify(dict)

@app.route("/getlikes", methods=["POST"])
def likes_get():
    # create cursor into database
    c = get_db().cursor()

    # gets data from request
    data = request.json

    # get required fields
    uid = data["UID"]

    # get the user's likes
    likes = c.execute('''SELECT * FROM Likes WHERE uid=?''',(uid,)).fetchall();

    list_likes = []

    for like in likes:
        list_likes.append(like[1])

    dict_likes = {"likes":list_likes}

    return jsonify(dict_likes)


@app.route("/getlike", methods=["POST"])
def update_get():
    # create cursor into database
    c = get_db().cursor()

    # gets data from request
    data = request.json
    print(data)

    # get required fields
    uid = data["UID"]
    url = data["url"]

    # see if the post been liked by the user
    post = c.execute('''SELECT * FROM Likes WHERE uid=? AND url=?''',(uid, url)).fetchone()

    # saves the results of the query
    get_db().commit()
    # closes database access
    get_db().close()
    dict = {}
    if (post is None):
        dict["isLiked"]= False
    else:
        dict["isLiked"]= True

    return jsonify(dict)

@app.route("/like", methods=["DELETE"])
def update_delete():
    try:
        # create cursor into database
        c = get_db().cursor()

        # gets data from request
        data = request.json
        print(data)

        # get required fields
        url = data["url"]
        uid = data["UID"]
        poly_bias = data["bias"]

        try:
            # remove like from table
            c.execute('''DELETE FROM Likes WHERE url=? AND uid=?''', (url, uid))
        except:
            return jsonify({"failure":"no delete"})

        # get user
        user = c.execute('''SELECT * FROM User WHERE id=?''',(uid,)).fetchone();
        num_vote = user[6]
        num_pol = user[5]

        if ((num_vote-1) == 0):
            # update user
            c.execute('''UPDATE User SET num_upvoted=? WHERE id=?''', (0 , uid))
            c.execute('''UPDATE User SET political_preference=? WHERE id=?''', (0, uid))
        else:
            # update user
            c.execute('''UPDATE User SET num_upvoted=? WHERE id=?''', (num_vote-1 , uid))
            c.execute('''UPDATE User SET political_preference=? WHERE id=?''', ((num_vote*num_pol+poly_bias)/(num_vote-1) , uid))

        # saves the results of the query
        get_db().commit()
        # closes database access
        get_db().close()
        dict = {}
        dict["isLiked"] = False
        return jsonify(dict)
    except:
        dict = {}
        dict["isLiked"] = True
        return jsonify(dict)

@app.route("/setaff", methods=["POST"])
def set_aff():
    try:
        # create cursor into database
        c = get_db().cursor()

        # gets data from request
        data = request.json
        print(data)

        # get required fields
        uid = data["UID"]
        num_pol = data["aff"]
        num_vote = 10

        # update user
        c.execute('''UPDATE User SET num_upvoted=? WHERE id=?''', (num_vote, uid))
        c.execute('''UPDATE User SET political_preference=? WHERE id=?''', (num_pol, uid))
        # saves the results of the query
        get_db().commit()
        # closes database access
        get_db().close()
        dict = {}
        dict["isSet"] = True
        dict["UID"] = uid
        return jsonify(dict)
    except:
        dict = {}
        dict["isSet"] = False
        dict["UID"] = -1
        return jsonify(dict)

@app.route("/setimage", methods=["POST"])
def set_image():
    try:
        # create cursor into database
        c = get_db().cursor()

        # gets data from request
        data = request.json
        print(data)

        # get required fields
        uid = data["UID"]
        image_url = data["image"]

        # update user
        c.execute('''UPDATE User SET image=? WHERE id=?''', (image_url, uid))

        # saves the results of the query
        get_db().commit()
        # closes database access
        get_db().close()
        dict = {}
        dict["isSet"] = True
        return jsonify(dict)
    except:
        dict = {}
        dict["isSet"] = False
        return jsonify(dict)

@app.route("/user", methods=["POST"])
def get_user():

    # create cursor into database
    c = get_db().cursor()

    # gets data from request
    data = request.json
    print(data)

    # get required fields
    uid = data["UID"]

    print(type(uid))

    # get user
    # user = c.execute('''SELECT * FROM User WHERE id= ?''',(uid,)).fetchone();
    user = c.execute('SELECT * FROM User WHERE id=?', (uid,)).fetchone();

    # saves the results of the query
    get_db().commit()
    # closes database access
    get_db().close()

    #turn user into dictionary
    names = ["UID","username", "password","categories", "url", "politicalPreference", "numUpvoted"]
    dict = {}
    i=0
    for item in user:
        dict[names[i]] = item
        i += 1
    return jsonify(dict)

@app.route("/getcomments", methods=["POST"])
def get_comments():
    c = get_db().cursor()
    data = request.json
    uid = data["UID"]

    comments = c.execute('SELECT * FROM Comments WHERE uid=?', (uid,)).fetchall();
    get_db().commit()
    get_db().close()

    num_comments = len(comments);

    return jsonify({"num":num_comments})


@app.route("/comment", methods=["POST", "GET"])
def comment():
    if request.method == 'POST':
        c = get_db().cursor()
        data = request.json
        print(data)
        uid = data["UID"]
        body = data["body"]
        created_at = datetime.now().isoformat()
        articleUrl = data["articleUrl"]
        c.execute('''INSERT INTO Comments (uid, body, createdAt, articleUrl) VALUES(?,?,?,?)''', (uid, body, created_at, articleUrl))
        get_db().commit()
        return jsonify(data)
    else:
        c = get_db().cursor()
        articleUrl = request.args.get('articleUrl')
        comments = c.execute('''SELECT * FROM Comments WHERE articleUrl=?''',(articleUrl,)).fetchall();
        returnObject = []
        for comment in comments:
            names = ["id","uid", "body", "createdAt" ,"articleUrl"]
            dict = {}
            i=0
            for item in comment:
                dict[names[i]] = item
                i += 1
            # find the username to add to the object given the UID
            # find the user profile image to add to the object given the UID
            user = c.execute('SELECT * FROM User WHERE id=?', (dict["uid"],)).fetchone();
            dict["username"] = user[1]
            dict["profileImage"] = user[4]

            returnObject.append(dict)
        return jsonify(returnObject)


def get_db():
    db = getattr(g, '_database', None)
    if db is None:
        db = g._database = sqlite3.connect(DATABASE)
    return db
