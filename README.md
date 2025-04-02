# Chromia Vector DB Cryptocurrency Research Agent

This project combines Chromia Vector DB with OpenAI embeddings and CoinGecko API to create a cryptocurrency research agent that provides historical context and current market data.

## Features

- **Vector Database**: Store and retrieve cryptocurrency historical information using Chromia's vector database
- **OpenAI Embeddings**: Generate semantic embeddings for text search and retrieval
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

### 1. Embedding Cryptocurrency Data

First, embed the cryptocurrency data from `data.yaml` into the vector database:

```bash
python embed_crypto_data.py
```

This script processes the cryptocurrency histories and stores them as vector embeddings in the Chromia blockchain.

### 2. Starting the API Server

Start the cryptocurrency research agent API:

```bash
python crypto_agent.py
```

The server will run on http://localhost:8000.

### 3. API Endpoints

#### Text Embedding

**Endpoint:** `POST /v1/text_embedding`

Embeds text in the vector database.

```bash
curl -X POST http://localhost:8000/v1/text_embedding \
  -H "Content-Type: application/json" \
  -d '{"text": "Bitcoin is a decentralized digital currency."}'
```

#### Text Search

**Endpoint:** `POST /v1/text_search`

Searches for similar text in the vector database.

```bash
curl -X POST http://localhost:8000/v1/text_search \
  -H "Content-Type: application/json" \
  -d '{"text": "Tell me about Ethereum", "max_results": 3}'
```

#### Text Conversation

**Endpoint:** `POST /v1/text_conversation`

Generates a response to a cryptocurrency question, combining historical data from the vector database and current market data from CoinGecko.

```bash
curl -X POST http://localhost:8000/v1/text_conversation \
  -H "Content-Type: application/json" \
  -d '{"question": "What happened with Bitcoin in 2017?", "top_k": 3, "coin_name": "Bitcoin"}'
```

The conversation endpoint automatically:
1. Detects cryptocurrency mentions in your question
2. Retrieves relevant historical information from the vector database
3. Fetches current market data from CoinGecko
4. Generates a comprehensive response using both sources

### 4. Testing with CoinGecko API Directly

You can test the CoinGecko API module separately:

```bash
python coingecko_api.py Bitcoin
```

This will output detailed information about Bitcoin from the CoinGecko API.

## Example Questions

- "What is the history of Ethereum's development?"
- "How does Chromia's relational blockchain work?"
- "What happened to Bitcoin during the 2017 bull run?"
- "How does Solana achieve its high transaction throughput?"
- "What makes NEAR Protocol different from other blockchains?"
- "What is the current price of Bitcoin and how does it compare to its historical performance?"

## Architecture

This project consists of three main components:

1. **Vector Database (Chromia)**: Stores and retrieves historical cryptocurrency information
2. **CoinGecko API Client**: Fetches current market data
3. **Research Agent API**: Combines both data sources with an LLM to answer questions

## Limitations

- The CoinGecko free API has rate limits (about 30 requests per minute)
- The vector database contains limited historical information for the 5 cryptocurrencies in data.yaml
- Market data is fetched in real-time and may occasionally be unavailable

## License

[MIT License](LICENSE)

## Credits

- Chromia Vector DB Extension
- OpenAI API
- CoinGecko API

## Frontend

A minimalist React + TypeScript frontend has been added to the project. To use it:

1. Install frontend dependencies:
```bash
cd frontend
npm install
```

2. Start the development server:
```bash
npm run dev
```

3. Open your browser and navigate to http://localhost:5173

The frontend allows you to:
- Ask questions about cryptocurrencies
- View real-time price data from CoinGecko
- Access historical information stored in the vector database
- View related cryptocurrency information

Make sure the backend API is running on port 8000 before starting the frontend.