# Crypto Research Agent Frontend

A minimalist React + TypeScript frontend for the Crypto Research Agent.

## Features

- Query cryptocurrency information using natural language questions
- Get real-time price data from CoinGecko API
- Access historical data stored in the vector database
- View related cryptocurrency information

## Prerequisites

- Node.js (v14 or higher)
- npm or yarn
- Backend API running (default: http://localhost:8000)

## Getting Started

1. Install dependencies
```bash
npm install
# or
yarn
```

2. Start the development server
```bash
npm run dev
# or
yarn dev
```

3. Open your browser and navigate to http://localhost:5173

## Building for Production

```bash
npm run build
# or
yarn build
```

The build artifacts will be stored in the `dist/` directory.

## Technologies Used

- React
- TypeScript
- Vite
- Axios for API requests

## API Integration

The frontend communicates with the backend through the following endpoints:

- `/v1/text_conversation` - Ask cryptocurrency questions
- `/v1/text_search` - Search for related crypto information
- `/v1/text_embedding` - Add new information to the vector database

## License

This project is licensed under the MIT License.