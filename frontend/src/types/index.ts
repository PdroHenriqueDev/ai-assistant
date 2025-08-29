export interface Message {
  text: string;
  type: 'text' | 'knowledge' | 'math' | 'error';
  timestamp: string;
  sender: 'user' | 'agent';
  source?: string;
  execution_time?: number;
  routing_info?: {
    agent_used: string;
  };
  metadata?: {
    num_sources?: number;
  };
}

export interface ChatError {
  text?: string;
}



export interface SocketData {
  message: string;
  sender: string;
  timestamp: string;
  type?: string;
  agent?: string;
  source?: string;
  executionTime?: number;
}

export interface ChatMessageProps {
  message: Message;
}

export interface RAGMessage {
  type: 'user' | 'bot' | 'system' | 'error';
  content: string;
  timestamp: string;
  sources?: string[];
}

export interface PipelineStatus {
  ready: boolean;
  message?: string;
  error?: string;
}

export interface SetupResponse {
  message: string;
}

export interface AskResponse {
  answer: string;
  sources: string[];
}

export interface EvaluationResponse {
  total_questions: number;
  error_rate: number;
  avg_sources: number;
}

export type ReportHandler = (metric: any) => void;