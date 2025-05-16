import requests
import ollama
from tools.Database import create_connection
from tools.Pipeline import NewsDownloader, NewsProcessor
import json


def get_latest_news(limit=10):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT title, description FROM processed_articles ORDER BY publishedAt DESC LIMIT 10")
    news = cursor.fetchall()
    return news

def call_qwen(prompt: str):
    res = requests.post("http://localhost:11434/api/generate", json={
        "model": "qwen2.5:0.5b",
        "prompt": prompt,
        "stream": False
    })
    return res.json()['response']


TOOL_SCHEMA = """
You are an assistant with access to the following tools.

Function: get_latest_news()
Description: Returns the 10 most recent news entries with title, description, and published date.

Respond ONLY with JSON in this format if the tool is needed:
{
  "function": "get_latest_news",
  "args": {}
}

Otherwise, answer normally.
"""

def route_response(llm_output: str) -> str:
    try:
        call = json.loads(llm_output)
        if call["function"] == "get_latest_news":
            news = get_latest_news()  # your PostgreSQL function
            news_text = "\n".join([f"{n[0]}" for n in news])
            return call_qwen(f"Summarize these news for the user:\n{news_text}")
        else:
            return "Function not recognized."
    except json.JSONDecodeError:
        return llm_output  # direct LLM response

if __name__ == "__main__":
    #print(chat("Give me the latest 5 news summaries"))
    NewsDownloader().raw_get_data()
    NewsProcessor().process_data()
    while True:
        user_input = "Summarize latest headlines."
        # if user_input.lower() == "exit":
        #     break
        full_prompt = TOOL_SCHEMA + f"\nUser: {user_input}"
        initial_response = call_qwen(full_prompt)
        final_response = route_response(initial_response)
        print("Assistant:", final_response)
        break
    # print(chat("Give me the latest 5 news summaries"))
