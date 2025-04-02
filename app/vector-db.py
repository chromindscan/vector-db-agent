import os
import sys
import json
from getpass import getpass
from openai import OpenAI

EMBEDDING_MODEL = "text-embedding-3-small"

def setup_openai():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        api_key = getpass("Enter your OpenAI API key: ")
        os.environ["OPENAI_API_KEY"] = api_key
    return OpenAI(api_key=api_key)

def get_embedding(client, text):
    response = client.embeddings.create(
        model=EMBEDDING_MODEL,
        input=text,
    )
    return response.data[0].embedding

def format_vector(vector):
    return [round(float(val), 6) for val in vector]

def main():
    if len(sys.argv) > 1:
        text = sys.argv[1]
    else:
        text = input("Enter text to embed: ")
        
    client = setup_openai()
    embedding = get_embedding(client, text)
    formatted_vector = format_vector(embedding)
    
    print(json.dumps(formatted_vector))
    
if __name__ == "__main__":
    main()
