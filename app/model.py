import requests
import ollama
from tools.Database import create_connection
import json
ollama.chat(
    model='qwen2.5:0.5b',
    messages=[
        {"role": "system", "content": "You are a helpful assistant that can use tools."},
        {"role": "user", "content": "Give me 3 news summaries"}
    ],
    tools=[{
  "name": "get_latest_news",
  "description": "Returns the latest summarized news articles.",
  "parameters": {
    "type": "object",
    "properties": {
      "limit": {
        "type": "integer",
        "description": "The number of news items to return."
      }
    },
    "required": ["limit"]
  }
}
]
)

def get_latest_news(limit=5):
    conn = create_connection()
    cursor = conn.cursor()
    cursor.execute(f"SELECT title, description FROM processed_articles ORDER BY publishedAt DESC LIMIT {limit}")
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


def chat(user_input):
    # Step 1: Ask Qwen what to do
    full_prompt = TOOL_SCHEMA + f"\n\nUser: {user_input}"
    llm_response = call_qwen(full_prompt)

    # Step 2: Try to parse as JSON
    try:
        action = json.loads(llm_response)
        if action["function"] == "query_news_by_date":
            lim = action["args"]["limit"]
            result = get_latest_news(lim)
            # Step 3: Summarize result
            summary = call_qwen(f"Summarize this news for {lim}:\n{result}")
            return {"response": summary}
    except Exception:
        return {"response": llm_response}
    # from fastapi import FastAPI
    # from pydantic import BaseModel
    #
    # app = FastAPI()
    #
    # class ChatInput(BaseModel):
    #     message: str
    #
    # @app.post("/chat")
    # async def chat_endpoint(msg: ChatInput):
    #     full_prompt = TOOL_SCHEMA + f"\nUser: {msg.message}"
    #     initial_response = call_qwen(full_prompt)
    #     final_response = route_response(initial_response)
    #     return {"response": final_response}

while True:
    user_input = input("User: ")
    if user_input.lower() == "exit":
        break
    full_prompt = TOOL_SCHEMA + f"\nUser: {user_input}"
    initial_response = call_qwen(full_prompt)
    final_response = route_response(initial_response)
    print("Assistant:", final_response)
# print(chat("Give me the latest 5 news summaries"))