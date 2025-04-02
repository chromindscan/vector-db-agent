export interface RelatedAnswer {
  answer: string;
  distance: number;
}

export interface MarketData {
  symbol: string | null;
  current_price: number | null;
}

export interface CryptoResponse {
  question: string;
  answer: string;
  related_answers: RelatedAnswer[];
  market_data: MarketData;
}

export interface SearchResponse {
  results: {
    text: string;
    distance: number;
  }[];
}

export interface EmbeddingResponse {
  success: boolean;
  error?: string;
} 