from fastapi import FastAPI, HTTPException, Body, Depends
from fastapi.middleware.cors import CORSMiddleware
import os
import json
import asyncio
import re
import aiohttp
from typing import List, Dict, Any, Optional
from openai import OpenAI
from dotenv import load_dotenv

load_dotenv()
from app.models import (
    TextEmbeddingResponse,
    TextSearchRequest,
    TextSearchResponse,
    TextConversationRequest,
    TextConversationResponse,
    TextEmbeddingRequest,
)

from app.coingecko_api import get_coin_info

app = FastAPI(title="Chromia Research Agent")

coingecko_api_key = os.environ.get("COINGECKO_API_KEY")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not found")
    return OpenAI(api_key=api_key)


async def get_embedding(client, text: str) -> List[float]:
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
    try:
        vector_brid = await get_blockchain_rid()

        vector_str = json.dumps(vector)

        cmd = (
            f"chr query -brid {vector_brid} query_closest_objects "
            f"context=0 q_vector='{vector_str}' max_distance=1.0 "
            f'max_vectors={max_results} \'query_template=["type":"get_messages_with_distance"]\''
        )

        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True,
        )
        stdout, _ = await process.communicate()

        results = stdout.decode().strip()
        if not results or results == "[]":
            return []

        text_pattern = re.compile(r'"text": "([^"]*)"')
        distance_pattern = re.compile(r'"distance": "([^"]*)"')

        text_matches = text_pattern.findall(results)
        distance_matches = distance_pattern.findall(results)

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
    try:
        system_prompt = """You are a cryptocurrency identification expert. 
                            Extract any cryptocurrency names mentioned in the user's text. 
                            Return ONLY the standard name or symbol of the cryptocurrencies (e.g., "Bitcoin", "BTC", "Ethereum", "ETH").
                            If there are no cryptocurrencies mentioned, return "None".
                            Return multiple cryptos as a comma-separated list.
                            Only return the official names or symbols, nothing else."""

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {
                        "role": "user",
                        "content": f"Extract the correct cryptocurrency symbol from this text: {text}",
                    },
                ],
                temperature=0.0,
                max_tokens=50,
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
            "SHIB": "Shiba Inu",
            "CHR": "Chromia",
            "AVAX": "Avalanche",
            "TON": "Toncoin",
            "MATIC": "Polygon",
            "LINK": "Chainlink",
            "UNI": "Uniswap",
            "BCH": "Bitcoin Cash",
            "LTC": "Litecoin",
            "XLM": "Stellar",
            "XMR": "Monero",
            "XRP": "Ripple"
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
                            """
        # Create the system prompt
        system_prompt = f"""You are a cryptocurrency research assistant with extensive knowledge about blockchain and digital assets.

                        Use the following historical information from your knowledge base:
                        {context_text}

                        This is the latest market data for the cryptocurrency:
                        {market_info if market_info else ''}

                        Answer the user's question about cryptocurrencies based on both historical information and current market data if provided.
                        
                        Do not provide any speculative investment advice or additional information outside the scope of the question or the {context_text}
                        
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
                temperature=0.4,
            )
        )

        return response.choices[0].message.content

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error generating response: {str(e)}"
        )


@app.post("/v1/text_embedding", response_model=TextEmbeddingResponse)
async def embed_text(request: TextEmbeddingRequest = Body(...)):
    client = get_openai_client()

    try:
        embedding = await get_embedding(client, request.text)

        vector_brid = await get_blockchain_rid()

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
    client = get_openai_client()

    embedding = await get_embedding(client, request.text)

    results = await query_vector_db(embedding, request.max_results)

    return TextSearchResponse(results=results)


@app.post("/v1/text_conversation", response_model=TextConversationResponse)
async def conversation(request: TextConversationRequest = Body(...)):

    client = get_openai_client()

    embedding = await get_embedding(client, request.question)

    results = await query_vector_db(embedding, request.top_k)

    detected_coins = await extract_coin_names_from_text(client, request.question)
    if detected_coins:
        coin_name = detected_coins[0]

    market_data = None
    if coin_name:
        market_data = await get_coin_info(coin_name, coingecko_api_key)

    answer = await generate_crypto_response(
        client, request.question, results, market_data
    )

    formatted_response = {
        "question": request.question,
        "answer": answer,
        "related_answers": [
            {"answer": item["text"], "distance": item["distance"]} for item in results
        ],
        "market_data": {
            "symbol": market_data.get("symbol") if market_data else None,
            "current_price": market_data.get("current_price") if market_data else None,
        },
    }

    return formatted_response


@app.get("/health", response_model=Dict[str, Any])
async def health_check():
    """Health check endpoint that verifies the API and Docker container status."""
    status = {
        "api_status": "healthy",
        "docker_status": "unknown",
        "vector_blockchain": "unknown"
    }
    
    # Check Docker container running on port 7740
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get("http://localhost:7740", timeout=2) as response:
                if response.status == 200:
                    status["docker_status"] = "healthy"
                else:
                    status["docker_status"] = f"unhealthy - status code: {response.status}"
    except asyncio.TimeoutError:
        status["docker_status"] = "unhealthy - timeout"
    except aiohttp.ClientError as e:
        status["docker_status"] = f"unhealthy - connection error: {str(e)}"
    
    # Check vector blockchain availability
    try:
        vector_brid = await get_blockchain_rid()
        if vector_brid:
            status["vector_blockchain"] = "available"
    except Exception as e:
        status["vector_blockchain"] = f"unavailable - {str(e)}"
    
    return status


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app, host="0.0.0.0", port=8010)
