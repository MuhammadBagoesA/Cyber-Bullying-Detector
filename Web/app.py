from flask import Flask, request, render_template
import feedparser
from bs4 import BeautifulSoup

import re

app = Flask(__name__)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/display', methods=['POST', 'GET'])
def display():
    if request.method == 'POST':
        reddit_url = request.form['reddit_url']
    else:
        reddit_url = request.args.get('reddit_url')
    
    if not reddit_url:
        return "Error: 'reddit_url' not provided", 400
    
    feed_url = reddit_url + '.rss'
    feed = feedparser.parse(feed_url)
    comments = []
    for entry in feed.entries:
        author = entry.get('author', 'Unknown').replace('/u/', '')
        summary = entry.summary
        soup = BeautifulSoup(summary, 'lxml')
        clean_text = soup.get_text()
        # clean_text = re.sub(r'submitted by /u/\w+ \[link\] \[comments\]', '', clean_text).strip()
        clean_text = re.sub(r'^\s*$', '', clean_text) 
        if clean_text: 
            comments.append({'author': author, 'summary': clean_text})
    return render_template('display.html', comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
