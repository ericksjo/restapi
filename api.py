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





def get_url_title(url):
    try:
        response = urllib2.urlopen(url)
        url_data = response.read()
    except:
        return "Couldn't connect to url %s" % url
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



if __name__ == "__main__":
    app.run(debug=True)

