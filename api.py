#!/usr/bin/env python
# -*- coding: utf-8 -*-
from flask import Flask, request
from lxml.html import fromstring
import json
import HTMLParser
import urllib2
import requests
import re
from credentials import *
import MySQLdb
import oauth2 as oauth

app = Flask(__name__)

@app.route("/")
def index():
    return "test"

@app.route("/url/title", methods=['GET', 'POST'])
def title():
    """Returns the title for a URL. The URL is passed using JSON"""
    if request.method == 'POST': 
        try:
            json_data = request.get_json()
        except:
            return "Must POST json with a value for URL"
        if "URL" in json_data:
            return get_url_title(json_data['URL'])
        else:
            return "JSON must contain URL field"
    else:
        url = request.args.get('URL', None)
        if url:
            return get_url_title(urllib2.unquote(url))
        else:
            return "No URL specified"
if credentials.has_section('twitter'):
    def get_tweet(id):
        CONSUMER_KEY    = credentials.get('twitter', 'CONSUMER_KEY', None)
        CONSUMER_SECRET = credentials.get('twitter', 'CONSUMER_SECRET', None)
        ACCESS_KEY      = credentials.get('twitter', 'ACCESS_KEY', None)
        ACCESS_SECRET   = credentials.get('twitter', 'ACCESS_SECRET', None)
        consumer = oauth.Consumer(key=CONSUMER_KEY, secret=CONSUMER_SECRET)
        access_token = oauth.Token(key=ACCESS_KEY, secret=ACCESS_SECRET)
        client = oauth.Client(consumer, access_token)

        timeline_endpoint = "https://api.twitter.com/1.1/statuses/show.json?id={id}".format(id=id)
        try:
            response, data = client.request(timeline_endpoint)
            with open('test.json', 'w') as file:
                file.write(data)
            tweet = json.loads(data)
        except Exception as e:
            return "ERROR: {0}".format(e)
        text = tweet['text']
        name = tweet['user']['name']
        verified = "" if tweet['user']['verified'] == False else "✓"
        screen_name = tweet['user']['screen_name']
        timestamp = tweet['created_at']

        return "{verified}@{screen_name} ({name}): {text} ({timestamp})".format(**locals())

    def get_tweet_id_from_url(url):
        mo = re.search(r'.*twitter.*status/([0-9]+)', url)
        if mo:
            return mo.group(1)
        else:
            return None

 
if credentials.has_section('alphavantage'):
    @app.route("/stockquote", methods=['GET', 'POST'])
    def stockquote():
        """Returns a batch stock market quote for the given symbols"""

        url = 'https://www.alphavantage.co/query?function=BATCH_STOCK_QUOTES&apikey={api_key}&symbols={symbols}'
        apikey = credentials.get('alphavantage', 'apikey', None)
        url_data = {}
        url_data['api_key'] = apikey

        if request.method == 'POST':
            try:
                json_data = request.get_json()
            except:
                return "Must post json data with symbol field"
            symbol = json_data.get('symbol', None)
        else:
            symbol = request.args.get('symbol').split(',')

        url_data['symbols'] = ','.join(symbol)

        try:
            resp = requests.get(url.format(**url_data), timeout=10)
        except Exception as e:
            return "Couldn't connect! {}".format(e)
        if resp.status_code == 200:
            data = json.loads(resp.text)
        else:
            return "Status code wasn't 200: %d" % resp.status_code

        return resp.text




if credentials.has_section('omdb'):
    @app.route("/movie", methods=['GET', 'POST'])
    def movie():
        """Returns a nice movie summary with plot and review scores"""
        omdb_url = 'http://www.omdbapi.com/'
        apikey = credentials.get("omdb", "apikey", None)

        # Check input data
        if request.method == "POST":
            try:
                json_data = request.get_json()
            except:
                return "Must post json data with title field"
            title = json_data.get('title',None)
            year = json_data.get('year',None)
        else:
            title = request.args.get('title',None)
            year = request.args.get('year',None)
        if title == None:
            return "Must supply a title"
        # Do the search first, ignore pagination for now
        if year:
            url = '%s?apikey=%s&s=%s&r=json&y=%s' % (omdb_url, apikey, urllib2.quote(title), year)
        else:
            url = '%s?apikey=%s&s=%s&r=json' % (omdb_url, apikey, urllib2.quote(title))
        try:
            resp = requests.get(url, timeout=10)
        except Exception as e:
            return "Couldn't connect to omdb: %s" % e
        if resp.status_code == 200:
            data = json.loads(resp.text)
        else:
            return "Status code wasn't 200: %d" % resp.status_code
        if data.get('Response','False') == 'True':
            results = data.get('Search')
            # Grab specific movie results
            exact_matches = filter(lambda x: x.get('Title').lower() == title.lower(), results)
            if len(exact_matches) > 0:
                imdb_id = exact_matches[0].get('imdbID')
            else:
                imdb_id = results[0].get('imdbID')

            url = '%s?apikey=%s&i=%s&plot=short&r=json&tomatoes=true' % (omdb_url, apikey, imdb_id)
            try:
                resp = requests.get(url, timeout=5)
            except Exception as e:
                return "Couldn't connect to omdb: %s" % e
            if resp.status_code == 200:
                movie_data = json.loads(resp.text)
            else:
                return "Status code wasn't 200: %d" % resp.status_code
            tomatoImage = movie_data.get('tomatoImage',None)
            if tomatoImage != "NA" and tomatoImage != "N/A":
                if tomatoImage == "rotten":
                    color = "03"
                else:
                    color = "04"
                movie_data['tomatoMeter'] = "\003%s%s%%\003" % (color, movie_data['tomatoMeter'])
            blurb =  "%(Title)s (%(Year)s) - Metascore: %(Metascore)s IMDB: %(imdbRating)s RT: %(tomatoMeter)s - %(Plot)s %(tomatoURL)s" % movie_data
            return blurb.replace(u'–', '-')
        else:
            return data.get('Error','Unknown error')

if credentials.has_section('mysql'):
    @app.route("/url/store", methods=['POST', 'GET'])
    def api_urlstore():
        """Endpoint for storing URLS seen on IRC"""
        if request.method == 'POST':
            try:
                json_data = request.get_json()
            except:
                return "Must POST json data"
            try:
                return mysql_store_url(url=json_data['URL'], channel=json_data['channel'], nickname=json_data['nickname'])
            except KeyError:
                return "Must supply URL, channel and nickname in the json object"
        else:
            url = request.args.get('URL', None)
            channel = request.args.get('channel', None)
            nickname = request.args.get('nickname', None)
            if url and channel and nickname:
                return mysql_store_url(url=url, channel=channel, nickname=nickname)
            else:
                return "Must supply URL, channel and nickname"

def mysql_store_url(url, channel, nickname):
    """Stores URLs to a URL logging database. These URLs are qualified by channel and nickname because the typical source is from an IRC bot"""
    hostname = credentials.get("mysql", "hostname", None)
    database = credentials.get("mysql", "database", None)
    username = credentials.get("mysql", "username", None)
    password = credentials.get("mysql", "password", None)

    try:
        db = MySQLdb.connect(host=hostname, user=username, passwd=password, db=database)
    except:
        return "Couldn't connect to the database"
    cur = db.cursor()
    try:
        cur.execute("""insert into urls (url, channel, nickname) values (%s, %s, %s);""", (url, channel, nickname))
        return "OK"
    except:
        return "Couldn't add to the database"

def get_url_title(url):
    """Gets the string value of the first title tag from the supplied URL and returns it. If LXML fails to parse the html document, it will default to regular expression parsing. If no title can be found, it simply returns a blank string"""
    headers = {
        'User-Agent': """Mozilla/5.0 (Windows NT 5.1) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/27.0.1453.94 Safari/537.36"""
    }
    # Twitter is stupid
    if credentials.has_section('twitter'):
        tweet_id = get_tweet_id_from_url(url)
        if tweet_id:
            return get_tweet(tweet_id) 
    try:
        response = requests.get(url, headers=headers, timeout=5, verify=False)
    except:
        return "Couldn't connect to url %s" % url
    try:
        tree = fromstring(response.content)
        title = tree.findtext('.//title')
    except:
        mo = re.search(r'<title>(.*)</title>', response.content)
        if mo:
            title = mo.group(1)
        else:
            title = ""
    if title:
        parser = HTMLParser.HTMLParser()
        print title
        return parser.unescape(title).strip().replace('\n',' ')
    else:
        return ""

if __name__ == "__main__":
    app.run(debug=True)

