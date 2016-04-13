#!/usr/bin/env python
from flask import Flask, request
import lxml.html
import json
import HTMLParser
from BeautifulSoup import BeautifulSoup
import urllib2
import re

app = Flask(__name__)

@app.route("/")
def index():
    return "test"
@app.route("/url/title", methods=['POST'])
def title():
    """Returns the title for a URL. The URL is passed using JSON"""
    try:
        json_data = request.get_json()
    except:
        return "Must POST json with a value for URL"
    if "URL" in json_data:
        try:
            response = urllib2.urlopen(json_data['URL'])
            url_data = response.read()
        except:
            return "Couldn't connect to url %(URL)s" % json_data
        try:
            soup = BeautifulSoup(url_data)
            title = soup.title.string
        except:
            mo = re.search(r'<title>(.*)</title>', url_data)
            if mo:
                title = mo.group(1)
            else:
                title = ""
        parser = HTMLParser.HTMLParser()
        return parser.unescape(title)
    else:
        return "JSON must contain URL field"

if __name__ == "__main__":
    app.run(debug=True)
