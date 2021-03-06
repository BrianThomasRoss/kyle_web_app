# web_app/routes/twitter_routes.py

from flask import Blueprint, render_template, jsonify #, request

from web_app.models import db, User, Tweet, parse_records
from web_app.services.twitter_service import api_client
from web_app.services.basilica_service import connection as basilica_client

twitter_routes = Blueprint("twitter_routes", __name__)

def store_twitter_user_data(screen_name):
    api = api_client()
    twitter_user = api.get_user(screen_name)
    #statuses = api.user_timeline(screen_name, tweet_mode="extended", count=150, exclude_replies=True, include_rts=False)
    statuses = api.user_timeline(screen_name, tweet_mode="extended", count=150)
    #return jsonify({"user": user._json, "tweets": [s._json for s in statuses]})

    db_user = User.query.get(twitter_user.id) or User(id=twitter_user.id)
    db_user.screen_name = twitter_user.screen_name
    db_user.name = twitter_user.name
    db_user.location = twitter_user.location
    db_user.followers_count = twitter_user.followers_count
    db.session.add(db_user)
    db.session.commit()
    #return "OK"
    #breakpoint()

    print("STATUS COUNT:", len(statuses))
    # basilica_api = basilica_client()
    all_tweet_texts = [status.full_text for status in statuses]
    embeddings = list(basilica_client.embed_sentences(all_tweet_texts, model="twitter"))
    print("NUMBER OF EMBEDDINGS", len(embeddings))

    # TODO: explore using the zip() function maybe...
    counter = 0
    for status in statuses:
        print(status.full_text)
        print("----")
        #print(dir(status))

        # Find or create database tweet:
        db_tweet = Tweet.query.get(status.id) or Tweet(id=status.id)
        db_tweet.user_id = status.author.id # or db_user.id
        db_tweet.full_text = status.full_text
        #embedding = basilica_client.embed_sentence(status.full_text, model="twitter") # todo: prefer to make a single request to basilica with all the tweet texts, instead of a request per tweet
        embedding = embeddings[counter]
        print(len(embedding))
        db_tweet.embedding = embedding
        db.session.add(db_tweet)
        counter+=1
    db.session.commit()

    return db_user, statuses

@twitter_routes.route("/users")
@twitter_routes.route("/users.json")
def list_users():
    # assigns the result of querying the user table from the sqlite database that is assigned in the __init__ file "kyle_twitter_db.db" to
    # the variable db_users
    db_users = User.query.all()

    users = parse_records(db_users)
    return jsonify(users)

@twitter_routes.route("/users/<screen_name>")
def get_user(screen_name=None):
    print(screen_name)
    db_user, statuses = store_twitter_user_data(screen_name)
    #breakpoint()
    #return "OK"
    return render_template("user.html", user=db_user, tweets=statuses) # tweets=db_tweets