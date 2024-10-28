from flask import Flask, request, render_template
import feedparser
from bs4 import BeautifulSoup
import re
import pickle
import string

app = Flask(__name__)

# Load model and vectorizer
with open('../Model/model_logistic_regression.pkl', 'rb') as model_file:
    model = pickle.load(model_file)
with open('../Model/tfidf_vectorizer.pkl', 'rb') as vectorizer_file:
    vectorizer = pickle.load(vectorizer_file)

def clean_text(text):
    # Remove URLs
    cleaned_text = re.sub(r'http\S+|www\S+|https\S+', '', text, flags=re.MULTILINE)
    # Remove mentions (@username) and hashtags (#hashtag)
    cleaned_text = re.sub(r'\@\w+|\#', '', cleaned_text)
    # Remove numbers
    cleaned_text = re.sub(r'\d+', '', cleaned_text)
    # Remove punctuation
    cleaned_text = cleaned_text.translate(str.maketrans('', '', string.punctuation))
    # Convert to lowercase
    return cleaned_text.lower()

def is_url_only(text):
    # Check if the text is only a URL (e.g., "https://giphy.com/gifs/MgDsL4CQe3xPxSL48t")
    url_pattern = re.compile(r'^(http|https)://\S+$', re.IGNORECASE)
    return bool(url_pattern.match(text.strip()))

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
        text_content = soup.get_text().strip()
        
        # Skip irrelevant comments and comments containing only URLs
        if "submitted by" in text_content.lower() or "[link]" in text_content or "[comments]" in text_content or is_url_only(text_content):
            continue

        # Clean text for model prediction
        processed_text = clean_text(text_content)
        text_vector = vectorizer.transform([processed_text])
        prediction = model.predict(text_vector)[0]
        confidence = model.predict_proba(text_vector)[0][prediction] * 100
        
        # Only add if cleaned text is not empty
        if text_content: 
            comments.append({
                'author': author, 
                'summary': text_content,
                'cyberbullying': 'CB' if prediction == 1 else 'Non_CB',
                'confidence': f"{confidence:.2f}%"
            })
    
    return render_template('display.html', comments=comments)

if __name__ == '__main__':
    app.run(debug=True)
