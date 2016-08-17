#!/usr/bin/env python
from flask import Flask, request
from lxml.html import fromstring
import json
import HTMLParser
import urllib2
import requests
import re
from credentials import *
import MySQLdb

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
    try:
        response = requests.get(url)
    except:
        return "Couldn't connect to url %s" % url
    try:
        tree = fromstring(response.content)
        title = tree.findtext('.//title')
    except:
        mo = re.search(r'<title>(.*)</title>', url_data)
        if mo:
            title = mo.group(1)
        else:
            title = ""
    parser = HTMLParser.HTMLParser()
    return parser.unescape(title)

if __name__ == "__main__":
    app.run(debug=True)

