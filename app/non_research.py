from fastapi import FastAPI, HTTPException, Body
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
import os
import json
import asyncio
from typing import List, Dict, Any, Optional
from openai import OpenAI

app = FastAPI(title="Chromia's Vector DB with Chat Completion")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    question: str = Field(..., description="User question to answer")
    max_results: int = Field(5, description="Maximum number of vector results to retrieve")
    temperature: float = Field(0.7, description="Temperature for OpenAI response generation")

class QueryResponse(BaseModel):
    answer: str
    sources: List[Dict[str, Any]] = []

class AddTextRequest(BaseModel):
    text: str = Field(..., description="Text to add to the vector database")

class AddTextResponse(BaseModel):
    success: bool

class VectorSearchRequest(BaseModel):
    text: str = Field(..., description="Text to search for")
    max_results: int = Field(5, description="Maximum number of results to return")

class VectorSearchResponse(BaseModel):
    results: List[Dict[str, Any]]

class LlmQueryRequest(BaseModel):
    question: str = Field(..., description="Question to answer")
    top_k: int = Field(3, description="Number of vector results to include in context")

class LlmQueryResponse(BaseModel):
    answer: str
    results: List[Dict[str, Any]]

def get_openai_client():
    api_key = os.environ.get("OPENAI_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OpenAI API key not found")
    return OpenAI(api_key=api_key)

async def get_embedding(client, text: str) -> List[float]:
    try:
        response = await asyncio.to_thread(
            lambda: client.embeddings.create(
                model="text-embedding-3-small",
                input=text
            )
        )
        return response.data[0].embedding
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating embedding: {str(e)}")

async def query_vector_db(vector: List[float], max_results: int) -> List[Dict[str, Any]]:
    try:
        process = await asyncio.create_subprocess_shell(
            "pmc blockchains | jq -r '.[] | select(.Name == \"vector_blockchain\") | .Rid'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await process.communicate()        
        
        cmd = (
            f"chr query -brid {stdout.decode().strip()} query_closest_objects "
            f"context=0 q_vector='{json.dumps(vector)}' max_distance=1.0 "
            f"max_vectors={max_results} 'query_template=[\"type\":\"get_messages_with_distance\"]'"
        )
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await process.communicate()
        
        results = stdout.decode().strip()
        if not results or results == "[]":
            return []
        
        valid_json = results.replace('[\n  [\n', '[\n  {\n')
        valid_json = valid_json.replace('  ],\n  [\n', '  },\n  {\n')
        valid_json = valid_json.replace('  ]\n]', '  }\n]')
        valid_json = valid_json.replace('"distance":', '"distance":')
        valid_json = valid_json.replace('"text":', '"text":')
        
        results_data = json.loads(valid_json)
        
        processed_results = []
        for item in results_data:
            processed_results.append({
                "text": item.get("text", ""),
                "distance": float(item.get("distance", 1.0))
            })
            
        return processed_results
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error querying vector database: {str(e)}")

async def generate_completion(client, question: str, context: List[Dict[str, Any]], temperature: float) -> str:
    try:
        context_text = "\n".join([f"- {item['text']} (relevance: {1-item['distance']:.2f})" for item in context])
        
        system_prompt = f"""You are a helpful assistant with access to a knowledge base.
            Answer the user's question based on the following retrieved information:

            {context_text}

            If the information doesn't answer the question, say you don't know but avoid mentioning the internal details of the retrieval system."""

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": question}
                ],
                temperature=temperature
            )
        )
        
        return response.choices[0].message.content
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating completion: {str(e)}")

@app.post("/v1/text_embedding", response_model=AddTextResponse)
async def add_text(request: AddTextRequest = Body(...)):
    client = get_openai_client()
    
    try:
        embedding = await get_embedding(client, request.text)
        
        vector_str = json.dumps(embedding)
        
        process = await asyncio.create_subprocess_shell(
            "pmc blockchains | jq -r '.[] | select(.Name == \"vector_blockchain\") | .Rid'",
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await process.communicate()
        
        vector_brid = stdout.decode().strip()
        if not vector_brid:
            raise HTTPException(status_code=500, detail="Brid not found")
        
        cmd = f"chr tx -brid {vector_brid} add_message \"{request.text}\" '{vector_str}'"
        
        process = await asyncio.create_subprocess_shell(
            cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE,
            shell=True
        )
        stdout, stderr = await process.communicate()
        result = stdout.decode()
        
        if "CONFIRMED" in result:                    
            return AddTextResponse(
                success=True,
            )
        else:
            return AddTextResponse(
                success=False,
            )
            
    except Exception as e:
        return AddTextResponse(
            success=False,
        )

@app.post("/v1/text_search", response_model=VectorSearchResponse)
async def vector_search(request: VectorSearchRequest = Body(...)):
    client = get_openai_client()
    
    embedding = await get_embedding(client, request.text)
    
    results = await query_vector_db(embedding, request.max_results)
    
    return VectorSearchResponse(results=results)

@app.post("/v1/text_conversation", response_model=LlmQueryResponse)
async def conversation(request: LlmQueryRequest = Body(...)):
    client = get_openai_client()
    
    embedding = await get_embedding(client, request.question)
    
    results = await query_vector_db(embedding, request.top_k)
    
    try:
        context_text = "\n".join([f"- {item['text']} (relevance: {1-item['distance']:.2f})" for item in results])
        
        system_prompt = f"""You are a helpful assistant with access to a knowledge base.
        
                        Use only the following pieces of context to answer the question.

                        This is the raw data from the vector database:

                        {context_text}

                        Format the answer in a way that is easy to understand and use"""

        response = await asyncio.to_thread(
            lambda: client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": request.question}
                ],
                temperature=0.7
            )
        )
        
        return LlmQueryResponse(
            answer=response.choices[0].message.content,
            results=results[0:request.top_k]
        )
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating LLM response: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)