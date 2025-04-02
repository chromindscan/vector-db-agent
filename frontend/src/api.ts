import axios from 'axios';
import { CryptoResponse, SearchResponse, EmbeddingResponse } from './types';

const API_URL = '/v1';

export const askQuestion = async (question: string, topK: number = 3): Promise<CryptoResponse> => {
  try {
    const response = await axios.post(`${API_URL}/text_conversation`, {
      question,
      top_k: topK
    });
    return response.data;
  } catch (error) {
    console.error('Error asking question:', error);
    throw error;
  }
};

export const searchText = async (text: string, maxResults: number = 5): Promise<SearchResponse> => {
  try {
    const response = await axios.post(`${API_URL}/text_search`, {
      text,
      max_results: maxResults
    });
    return response.data;
  } catch (error) {
    console.error('Error searching text:', error);
    throw error;
  }
};

export const addText = async (text: string): Promise<EmbeddingResponse> => {
  try {
    const response = await axios.post(`${API_URL}/text_embedding`, {
      text
    });
    return response.data;
  } catch (error) {
    console.error('Error adding text:', error);
    throw error;
  }
}; 