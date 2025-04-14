![Cryptocurrency Research Agent](https://github.com/chromindscan/vector-db-agent/blob/main/public/header.png)

This project combines Chromia Vector DB with CoinGecko API to create a cryptocurrency research agent that provides historical context and current market data.

Live Demo - https://vector-db-agent-sandbox.vercel.app/


Video Demo

[Ingest](https://github.com/chromindscan/vector-db-agent/blob/main/public/ingest.mp4)


[Conversation](https://github.com/chromindscan/vector-db-agent/blob/main/public/chat.mp4)

## Features

- **Vector Database**: Store and retrieve cryptocurrency historical information using Chromia's vector database
- **CoinGecko Integration**: Access real-time cryptocurrency market data
- **Conversational Agent**: Ask questions about cryptocurrencies and get AI-generated responses

## Setup

### Prerequisites

- Docker (for running local Chromia node)
- Python 3.8+
- OpenAI API key
- Chromia tools (pmc, chr)

### Installation

1. Clone this repository:
   ```
   git clone https://github.com/yourusername/chromia-vector-db-extension.git
   cd chromia-vector-db-extension
   ```

2. Install Python dependencies:
   ```
   pip install fastapi uvicorn openai pydantic pyyaml aiohttp
   ```

3. Set your OpenAI API key:
   ```
   export OPENAI_API_KEY="your-openai-api-key"
   ```

4. Start a local Chromia node (see LOCAL.md for detailed instructions):
   ```
   docker run --rm -it -p 7740:7740 registry.gitlab.com/chromaway/example-projects/directory1-example/managed-single:latest
   ```

5. Deploy the Vector DB blockchain (see LOCAL.md)

## Usage

Run the startup script which handles the full setup process:

```bash
sh start_vector_db.sh
```

This script will:
1. Install the local Chromia node if not already installed
2. Set up the blockchain and build the dapp with the local node
3. Run the API backend server automatically

No need to manually run separate scripts for embedding data or starting the API server.

## API Endpoints

The cryptocurrency research agent provides the following REST API endpoints:

### Vector Database Operations

#### POST /v1/text_embedding
Embeds text into the vector database.
- **Request Body**: 
  ```json
  {
    "text": "String of text to embed"
  }
  ```
- **Response**: Success status and error message if applicable

#### POST /v1/text_search
Searches the vector database for similar text.
- **Request Body**: 
  ```json
  {
    "text": "Text to search for",
    "max_results": 5
  }
  ```
- **Response**: List of results with text and distance metrics

### Conversation

#### POST /v1/text_conversation
Submit a question about cryptocurrencies and get an AI-powered response.
- **Request Body**: 
  ```json
  {
    "question": "What is Bitcoin?",
    "top_k": 3
  }
  ```
- **Response**: Answer with related information and market data if available

#### GET /v1/conversation_history
Retrieve recent conversation history.
- **Query Parameters**:
  - `limit`: Maximum number of conversations to return (default: 10)
- **Response**: List of recent conversations with questions, answers, and timestamps

### System

#### GET /health
Check the health and status of the API and connected services.
- **Response**: Status information about the API, Docker container, and vector blockchain

