const API_BASE_URL = '/api';

export interface ChatMessage {
  role: 'user' | 'assistant';
  content: string;
}

export interface ChatRequest {
  message: string;
  conversation_id?: string;
}

export interface ChatResponse {
  response: string;
  conversation_id: string;
  sources?: Array<{
    content: string;
    metadata: {
      source: string;
      page?: number;
    };
  }>;
}

export interface STTRequest {
  audio: Blob;
}

export interface STTResponse {
  text: string;
  confidence?: number;
}

export interface TTSRequest {
  text: string;
  language?: string;
}

export interface TTSResponse {
  audio_url: string;
}

class ChatApiService {
  private async makeRequest<T>(
    endpoint: string,
    options: RequestInit = {}
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
      ...options,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  private async makeFormRequest<T>(
    endpoint: string,
    formData: FormData
  ): Promise<T> {
    const url = `${API_BASE_URL}${endpoint}`;
    
    const response = await fetch(url, {
      method: 'POST',
      body: formData,
    });

    if (!response.ok) {
      throw new Error(`API request failed: ${response.status} ${response.statusText}`);
    }

    return response.json();
  }

  // Chat API
  async sendMessage(request: ChatRequest): Promise<ChatResponse> {
    return this.makeRequest<ChatResponse>('/api/chat', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Speech-to-Text API
  async transcribeAudio(audioBlob: Blob): Promise<STTResponse> {
    const formData = new FormData();
    formData.append('audio', audioBlob, 'audio.wav');

    return this.makeFormRequest<STTResponse>('/api/speech/stt', formData);
  }

  // Text-to-Speech API
  async synthesizeSpeech(request: TTSRequest): Promise<TTSResponse> {
    return this.makeRequest<TTSResponse>('/api/speech/tts', {
      method: 'POST',
      body: JSON.stringify(request),
    });
  }

  // Get audio file as blob for playback
  async getAudioBlob(audioUrl: string): Promise<Blob> {
    const response = await fetch(`${API_BASE_URL}${audioUrl}`);
    if (!response.ok) {
      throw new Error(`Failed to fetch audio: ${response.status}`);
    }
    return response.blob();
  }

  // Health check
  async healthCheck(): Promise<{ status: string }> {
    return this.makeRequest<{ status: string }>('/health');
  }
}

export const chatApi = new ChatApiService();
