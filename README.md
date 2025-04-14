![Cryptocurrency Research Agent](https://github.com/chromindscan/vector-db-agent/blob/main/public/landing.png)

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


## Web Application

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
