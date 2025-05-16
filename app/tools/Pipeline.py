import json
import os
import requests
from dotenv import load_dotenv
load_dotenv()
from tools.Database import create_connection,create_table
from psycopg2 import Error
import nltk
from nltk.corpus import stopwords
from nltk.tokenize import word_tokenize
from nltk.stem import WordNetLemmatizer
nltk.download('punkt')
nltk.download('punkt_tab')
nltk.download('stopwords')
nltk.download('wordnet')



def temp_connection():
    conn = create_connection()
    if conn is None:
        print("Error connecting to PostgreSQL database")
        return None
    else:
        print("PostgreSQL connection is established")
        return conn


class NewsDownloader:
    def __init__(self):
        self.apikey = os.getenv('GNEWS_API_KEY')
        self.category = "general"
        self.url = f"https://gnews.io/api/v4/top-headlines?category={self.category}&lang=en&country=us&max=10&apikey={self.apikey}"
        create_table()

    def raw_get_data(self):
        conn = temp_connection()
        if conn is None:
            print("Error connecting to PostgreSQL database")
            return

        try:
            cursor = conn.cursor()
            with requests.Session() as session:
                response = session.get(self.url)
                if response.status_code != 200:
                    print(f"Error: {response.status_code}")
                    return None

                data = response.json()  # Use json() instead of json.loads()
                articles = data["articles"]
                print(len(articles))

                for article in articles:
                    print(f"Title: {article['title']}")
                    print(f"Description: {article['description']}")
                    print(f"PublishedAt: {article['publishedAt']}")

                    try:
                        query = """INSERT INTO raw_articles (title, description, publishedAt) 
                                 VALUES (%s, %s, %s)"""
                        cursor.execute(query, (
                            article['title'],
                            article['description'],
                            article['publishedAt']
                        ))
                        conn.commit()
                    except Error as e:
                        print(f"Error: {e}")

        except Exception as e:
            print(f"Error during data fetching: {e}")
        finally:
            conn.close()


class NewsProcessor:
    def __init__(self):
        self.conn = temp_connection()
        self.cursor = self.conn.cursor()
        self.cursor.execute("CREATE TABLE IF NOT EXISTS processed_articles (id SERIAL PRIMARY KEY, title VARCHAR(255), description TEXT, publishedAt TIMESTAMP);")
        self.conn.commit()
        self.cursor.execute("SELECT * FROM raw_articles")
        self.articles = self.cursor.fetchall()
        self.conn.close()
        self.preprocessor = TextPreprocessor()
        print(type(self.articles))


    def process_data(self):
        for i in self.articles:
            # print("Raw Data")
            # print(i[1])
            # print(i[2])
            # print(i[3])
            # print("--------------------------------------------------")
            # print("Processed Data")
            article = self.preprocessor.preprocess_article(i)
            # print(article)
            self.conn = temp_connection()
            self.conn.cursor().execute("INSERT INTO processed_articles (title, description, publishedAt) VALUES (%s, %s, %s)", (article['title'], article['description'], article['publishedAt']))
            self.conn.commit()
            self.conn.close()

class TextPreprocessor:
    def __init__(self):
        self.stop_words = set(stopwords.words('english'))
        self.lemmatizer = WordNetLemmatizer()

    def preprocess_text(self, text):
        tokens = word_tokenize(text.lower())
        tokens = [token for token in tokens if token.isalnum()]
        tokens = [token for token in tokens if token not in self.stop_words]
        tokens = [self.lemmatizer.lemmatize(token) for token in tokens]
        print(' '.join(tokens))
        return ' '.join(tokens)

    def preprocess_timestamp(self,timestamp):
        try:
            print(timestamp)
            if timestamp is None:
                return None
            else:
                return timestamp.strftime('%Y-%m-%d %H:%M:%S')
        except Exception as e:
            print(f"Error: {e}")
            return None

    def preprocess_article(self,article):
        try:
            preprocessed_article = {}
            preprocessed_article['id'] = article[0]
            preprocessed_article['title'] = self.preprocess_text(article[1])
            preprocessed_article['description'] = self.preprocess_text(article[2])
            preprocessed_article['publishedAt'] = self.preprocess_timestamp(article[3])
            return preprocessed_article
        except Exception as e:
            print(f"Error: {e}")
