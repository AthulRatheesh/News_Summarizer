import json
import os
import aiohttp
from dotenv import load_dotenv
load_dotenv()
from Database import create_connection,create_table
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

    async def raw_get_data(self):
        conn = temp_connection()
        if conn is None:
            print("Error connecting to PostgreSQL database")
        else:
            cursor = conn.cursor()
            async with aiohttp.ClientSession() as session:
                async with session.get(self.url) as response:
                    if response.status != 200:
                        print(f"Error: {response.status}")
                        return None
                    data = json.loads(response.read().decode("utf-8"))
                    articles = data["articles"]
                    print(len(articles))

                    for i in range(len(articles)):
                        # articles[i].title
                        print(f"Title: {articles[i]['title']}")
                        # articles[i].description
                        print(f"Description: {articles[i]['description']}")
                        # You can replace {property} below with any of the article properties returned by the API.
                        # articles[i].{property}
                        # print(f"{articles[i]['{property}']}")
                        print(f"PublishedAt: {articles[i]['publishedAt']}")
                        try:
                            query = """INSERT INTO raw_articles (title, description, publishedAt) VALUES (%s, %s, %s)"""

                            cursor.execute(query,(articles[i]['title'], articles[i]['description'], articles[i]['publishedAt']))
                            conn.commit()
                        except Error as e:
                            print(f"Error: {e}")
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
            print("Raw Data")
            print(i[1])
            print(i[2])
            print(i[3])
            print("--------------------------------------------------")
            print("Processed Data")
            article = self.preprocessor.preprocess_article(i)
            print(article)
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

if __name__ == "__main__":
    gnews1 = NewsDownloader()
    gnews1.raw_get_data()
    process = NewsProcessor()
    process.process_data()

