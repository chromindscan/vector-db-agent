#!/usr/bin/env python3
from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import json
import asyncio
import re
from typing import List, Dict, Any, Optional
from openai import OpenAI

# Import the CoinGecko API module
from coingecko_api import get_coin_info

app = FastAPI(title="Crypto Research Agent API")

# Enable CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Models for request/response
class TextEmbeddingRequest(BaseModel):
    text: str = Field(..., description="Text to embed in the vector database")


class TextEmbeddingResponse(BaseModel):
    success: bool
    error: Optional[str] = None


class TextSearchRequest(BaseModel):
    text: str = Field(..., description="Text to search for in the vector database")
    max_results: int = Field(5, description="Maximum number of results to return")


class TextSearchResponse(BaseModel):
    results: List[Dict[str, Any]]


class TextConversationRequest(BaseModel):
    question: str = Field(..., description="Question about cryptocurrency")
    top_k: int = Field(3, description="Number of vector results to include in context")


class RelatedAnswer(BaseModel):
    answer: str
    distance: float


class MarketDataSimple(BaseModel):
    symbol: Optional[str] = None
    current_price: Optional[float] = None


class TextConversationResponse(BaseModel):
    question: str
    answer: str
    related_answers: List[RelatedAnswer]
    market_data: MarketDataSimple


# Helper functions
def get_openai_client():
    """Get OpenAI client instance."""
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not found")
    return OpenAI(api_key=api_key)


async def get_embedding(client, text: str) -> List[float]:
    """Generate embeddings for text using OpenAI's API."""
    try:
        response = await asyncio.to_thread(
            lambda: client.embeddings.create(model="text-embedding-3-small", input=text)
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating embedding: {str(e)}"
        )


async def get_blockchain_rid():
    """Get the blockchain RID for the vector database."""
    process = await asyncio.create_subprocess_shell(
        "pmc blockchains | jq -r '.[] | select(.Name == \"vector_blockchain\") | .Rid'",
        stdout=asyncio.subprocess.PIPE,
        stderr=asyncio.subprocess.PIPE,
        shell=True,
    )
    stdout, stderr = await process.communicate()

    vector_brid = stdout.decode().strip()
    if not vector_brid:
        raise HTTPException(status_code=500, detail="Could not fetch blockchain RID")

    return vector_brid


async def query_vector_db(
    vector: List[float], max_results: int
) -> List[Dict[str, Any]]:
    """Query the vector database for similar text."""
    try:
        # Get blockchain RID
        vector_brid = await get_blockchain_rid()

        # Format the vector for the query
        vector_str = json.dumps(vector)

        # Build the query command
        cmd = (
            f"chr query -brid {vector_brid} query_closest_objects "
            f"context=0 q_vector='{vector_str}' max_distance=1.0 "
            f'max_vectors={max_results} \'query_template=["type":"get_messages_with_distance"]\''
        )

        # Run the query
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = await process.communicate()

        # Parse the results
        results = stdout.decode().strip()
        if not results or results == "[]":
            return []

        # Process the results using regex
        text_pattern = re.compile(r'"text": "([^"]*)"')
        distance_pattern = re.compile(r'"distance": "([^"]*)"')

        # Find all items
        text_matches = text_pattern.findall(results)
        distance_matches = distance_pattern.findall(results)

        # Combine them into results
        processed_results = []
        for i in range(min(len(text_matches), len(distance_matches))):
            processed_results.append(
                {"text": text_matches[i], "distance": float(distance_matches[i])}
            )

        return processed_results

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error querying vector database: {str(e)}"
        )


async def extract_coin_names_from_text(client, text: str) -> List[str]:
    """
    Use OpenAI to intelligently extract cryptocurrency names from text.
    This is more flexible than a fixed list approach.
    """
    try:
        system_prompt = """You are a cryptocurrency identification expert. 
Extract any cryptocurrency names mentioned in the user's text. 
Return ONLY the standard name or symbol of the cryptocurrencies (e.g., "Bitcoin", "BTC", "Ethereum", "ETH").
If there are no cryptocurrencies mentioned, return "None".
Return multiple cryptos as a comma-separated list.
Only return the official names or symbols, nothing else."""

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": f"Extract cryptocurrencies from this text: {text}"}
                ],
                temperature=0.0,
                max_tokens=50
            )
        )
        
        extracted_text = response.choices[0].message.content.strip()
        
        # If no cryptocurrencies found
        if extracted_text.lower() == "none":
            return []
            
        # Process the comma-separated list
        coins = [coin.strip() for coin in extracted_text.split(",")]
        
        # Remove any that are empty strings
        coins = [coin for coin in coins if coin]
        
        # For symbols, map common ones to their full names for better CoinGecko API matching
        symbol_to_name = {
            "BTC": "Bitcoin",
            "ETH": "Ethereum",
            "SOL": "Solana",
            "CHR": "Chromia",
            "NEAR": "NEAR Protocol",
            "DOT": "Polkadot",
            "ADA": "Cardano",
            "XRP": "XRP",
            "DOGE": "Dogecoin",
            "SHIB": "Shiba Inu"
        }
        
        # Replace symbols with full names where possible
        coins = [symbol_to_name.get(coin, coin) for coin in coins]
        
        return coins
        
    except Exception as e:
        print(f"Error extracting coin names: {str(e)}")
        return []


async def generate_crypto_response(
    client,
    question: str,
    context: List[Dict[str, Any]],
    market_data: Optional[Dict[str, Any]] = None,
) -> str:
    """Generate a response using the LLM with context and market data."""
    try:
        # Format the context from vector DB
        context_text = "\n".join(
            [
                f"- {item['text']} (relevance: {1-item['distance']:.2f})"
                for item in context
            ]
        )

        # Format market data if available
        market_info = ""
        if market_data and not market_data.get("error"):
            market_info = f"""
                Current Market Data for {market_data.get('name', '')} ({market_data.get('symbol', '')}):
                - Current Price: ${market_data.get('current_price', 'Unknown')}
                - 24h Change: {market_data.get('price_change_24h', 'Unknown')}%
                - Market Cap: ${market_data.get('market_cap', 'Unknown')}
                - Market Rank: #{market_data.get('market_rank', 'Unknown')}
                - Genesis Date: {market_data.get('genesis_date', 'Unknown')}
                """
        # Create the system prompt
        system_prompt = f"""You are a cryptocurrency research assistant with extensive knowledge about blockchain and digital assets.

        Use the following historical information from your knowledge base:
        {context_text}

        {market_info if market_info else ''}

        Answer the user's question about cryptocurrencies based on both historical information and current market data if provided.
        Provide factual, balanced responses without speculative investment advice.
        If the knowledge base doesn't have relevant information, acknowledge the limitations.
        """

        # Generate the response
        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",  # You can use a more advanced model if needed
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question},
                ],
                temperature=0.7,
            )
        )

        return response.choices[0].message.content

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


# API Endpoints
@app.post("/v1/text_embedding", response_model=TextEmbeddingResponse)
async def embed_text(request: TextEmbeddingRequest = Body(...)):
    """Embed text in the vector database."""
    client = get_openai_client()

    try:
        # Generate embedding
        embedding = await get_embedding(client, request.text)

        # Get blockchain RID
        vector_brid = await get_blockchain_rid()

        # Store in vector DB
        vector_str = json.dumps(embedding)
        escaped_text = request.text.replace('"', '\\"')

        cmd = (
            f"chr tx -brid {vector_brid} add_message \"{escaped_text}\" '{vector_str}'"
        )

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
        )
        stdout, stderr = await process.communicate()

        result = stdout.decode()
        if "CONFIRMED" in result:
            return TextEmbeddingResponse(success=True)
        else:
            return TextEmbeddingResponse(success=False, error=result)

    except Exception as e:
        return TextEmbeddingResponse(success=False, error=str(e))


@app.post("/v1/text_search", response_model=TextSearchResponse)
async def search_text(request: TextSearchRequest = Body(...)):
    """Search for similar text in the vector database."""
    client = get_openai_client()

    # Generate embedding
    embedding = await get_embedding(client, request.text)

    # Query the vector database
    results = await query_vector_db(embedding, request.max_results)

    return TextSearchResponse(results=results)


@app.post("/v1/text_conversation", response_model=TextConversationResponse)
async def conversation(request: TextConversationRequest = Body(...)):
    """
    Generate a response to a cryptocurrency question, combining:
    1. Historical data from the vector database
    2. Current market data from CoinGecko API
    """
    client = get_openai_client()
    
    # Get embedding for the question
    embedding = await get_embedding(client, request.question)
    
    # Query the vector database
    results = await query_vector_db(embedding, request.top_k)
    
    detected_coins = await extract_coin_names_from_text(client, request.question)
    if detected_coins:
        coin_name = detected_coins[0]  # Use the first detected coin
    
    # Get market data if we have a coin name
    market_data = None
    if coin_name:
        market_data = await get_coin_info(coin_name)
    
    # Generate response
    answer = await generate_crypto_response(client, request.question, results, market_data)
    
    # Format the response according to the required structure
    formatted_response = {
        "question": request.question,
        "answer": answer,  
        "related_answers": [
            {"answer": item["text"], "distance": item["distance"]} 
            for item in results
        ],
        "market_data": {
            "symbol": market_data.get("symbol") if market_data else None,
            "current_price": market_data.get("current_price") if market_data else None
        }
    }
    
    return formatted_response


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8000)
