#!/usr/bin/env python3
import yaml
import json
import os
import asyncio
import subprocess
from openai import OpenAI

# Load OpenAI API key
api_key = os.environ.get("OPENAI_API_KEY")
if not api_key:
    raise ValueError("OpenAI API key not found. Please set the OPENAI_API_KEY environment variable.")

client = OpenAI(api_key=api_key)

async def get_blockchain_rid():
    """Get the blockchain RID for the vector database."""
    process = await asyncio.create_subprocess_shell(
        "pmc blockchains | jq -r '.[] | select(.Name == \"vector_blockchain\") | .Rid'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True
    )
    stdout, stderr = await process.communicate()
    
    vector_brid = stdout.decode().strip()
    if not vector_brid:
        raise ValueError("Could not fetch blockchain RID. Make sure the blockchain is running.")
    
    return vector_brid

def get_embedding(text):
    """Generate embeddings for text using OpenAI's API."""
    response = client.embeddings.create(
        model="text-embedding-3-small",
        input=text
    )
    return response.data[0].embedding

async def store_in_vector_db(text, vector, brid):
    """Store text and its vector embedding in the blockchain."""
    vector_str = json.dumps(vector)
    
    # Escape quotes in the text
    escaped_text = text.replace('"', '\\"')
    
    cmd = f'chr tx -brid {brid} add_message "{escaped_text}" \'{vector_str}\''
    
    process = await asyncio.create_subprocess_shell(
        cmd,
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True
    )
    stdout, stderr = await process.communicate()
    
    result = stdout.decode()
    if "CONFIRMED" not in result:
        print(f"Error storing text: {result}")
        return False
    
    print(f"Successfully stored: {text[:50]}...")
    return True

async def process_coin(name, history, brid):
    """Process a single coin, embedding both its name and history."""
    # Embed the coin name
    name_text = f"Cryptocurrency name: {name}"
    name_vector = get_embedding(name_text)
    await store_in_vector_db(name_text, name_vector, brid)
    
    # Embed the full history
    history_text = f"History of {name}: {history}"
    history_vector = get_embedding(history_text)
    await store_in_vector_db(history_text, history_vector, brid)
    
    # Break down history into smaller chunks for better retrieval
    chunk_size = 512
    words = history.split()
    for i in range(0, len(words), chunk_size):
        chunk = " ".join(words[i:i+chunk_size])
        chunk_text = f"{name} information: {chunk}"
        chunk_vector = get_embedding(chunk_text)
        await store_in_vector_db(chunk_text, chunk_vector, brid)

async def main():
    """Main function to embed cryptocurrency data."""
    print("Loading cryptocurrency data from data.yaml...")
    with open("data.yaml", "r") as file:
        data = yaml.safe_load(file)
    
    if not data or "cryptocurrencies" not in data:
        raise ValueError("Invalid data format in data.yaml")
    
    # Get the blockchain RID
    print("Getting blockchain RID...")
    brid = await get_blockchain_rid()
    print(f"Using blockchain RID: {brid}")
    
    # Process each cryptocurrency
    for coin in data["cryptocurrencies"]:
        name = coin.get("name")
        history = coin.get("history")
        
        if not name or not history:
            print(f"Skipping coin with missing data: {coin}")
            continue
        
        print(f"Processing {name}...")
        await process_coin(name, history, brid)
    
    print("Data embedding complete!")

if __name__ == "__main__":
    asyncio.run(main()) 