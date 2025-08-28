import React, { useState, useEffect, FormEvent, ChangeEvent } from 'react';
import axios, { AxiosResponse } from 'axios';
import './RAGInterface.css';
import { RAGMessage, PipelineStatus, AskResponse, EvaluationResponse } from '../types';

const RAGInterface: React.FC = () => {
  const [messages, setMessages] = useState<RAGMessage[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [isLoading, setIsLoading] = useState<boolean>(false);
  const [pipelineStatus, setPipelineStatus] = useState<PipelineStatus | null>(null);
  const [isSetupMode, setIsSetupMode] = useState<boolean>(false);
  const [setupProgress, setSetupProgress] = useState<string>('');

  const RAG_API_BASE = 'http://localhost:8001';

  useEffect(() => {
    checkPipelineStatus();
  }, []);

  const checkPipelineStatus = async (): Promise<void> => {
    try {
      const response: AxiosResponse<PipelineStatus> = await axios.get(`${RAG_API_BASE}/status`);
      setPipelineStatus(response.data);
    } catch (error) {
      console.error('Error checking pipeline status:', error);
      setPipelineStatus({ ready: false, error: 'API not available' });
    }
  };

  const setupPipeline = async (): Promise<void> => {
    setIsSetupMode(true);
    setSetupProgress('Initializing pipeline setup...');
    
    try {
      await axios.post(`${RAG_API_BASE}/setup`, {
        max_articles: 20
      });
      
      setSetupProgress('Pipeline setup completed successfully!');
      setPipelineStatus({ ready: true, message: 'Pipeline is ready' });
      
      setTimeout(() => {
        setIsSetupMode(false);
        setSetupProgress('');
      }, 2000);
    } catch (error: any) {
      console.error('Error setting up pipeline:', error);
      setSetupProgress(`Setup failed: ${error.response?.data?.detail || error.message}`);
      
      setTimeout(() => {
        setIsSetupMode(false);
        setSetupProgress('');
      }, 3000);
    }
  };

  const handleSubmit = async (e: FormEvent<HTMLFormElement>): Promise<void> => {
    e.preventDefault();
    if (!inputMessage.trim() || isLoading) return;

    const userMessage: RAGMessage = {
      type: 'user',
      content: inputMessage,
      timestamp: new Date().toLocaleTimeString()
    };

    setMessages(prev => [...prev, userMessage]);
    setInputMessage('');
    setIsLoading(true);

    try {
      const response: AxiosResponse<AskResponse> = await axios.post(`${RAG_API_BASE}/ask`, {
        question: inputMessage
      });

      const botMessage: RAGMessage = {
        type: 'bot',
        content: response.data.answer,
        sources: response.data.sources,
        timestamp: new Date().toLocaleTimeString()
      };

      setMessages(prev => [...prev, botMessage]);
    } catch (error: any) {
      console.error('Error asking question:', error);
      const errorMessage: RAGMessage = {
        type: 'error',
        content: `Erro: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const clearChat = (): void => {
    setMessages([]);
  };

  const runEvaluation = async (): Promise<void> => {
    setIsLoading(true);
    try {
      const response: AxiosResponse<EvaluationResponse> = await axios.post(`${RAG_API_BASE}/evaluate`);
      
      const evalMessage: RAGMessage = {
        type: 'system',
        content: `Avaliação concluída:\n- Questões processadas: ${response.data.total_questions}\n- Taxa de erro: ${response.data.error_rate}%\n- Fontes médias por resposta: ${response.data.avg_sources}`,
        timestamp: new Date().toLocaleTimeString()
      };
      
      setMessages(prev => [...prev, evalMessage]);
    } catch (error: any) {
      console.error('Error running evaluation:', error);
      const errorMessage: RAGMessage = {
        type: 'error',
        content: `Erro na avaliação: ${error.response?.data?.detail || error.message}`,
        timestamp: new Date().toLocaleTimeString()
      };
      setMessages(prev => [...prev, errorMessage]);
    } finally {
      setIsLoading(false);
    }
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setInputMessage(e.target.value);
  };

  return (
    <div className="rag-interface">
      <div className="rag-header">
        <h2>🤖 InfinitePay RAG Assistant</h2>
        <div className="rag-controls">
          <div className={`status-indicator ${pipelineStatus?.ready ? 'ready' : 'not-ready'}`}>
            {pipelineStatus?.ready ? '✅ Pronto' : '❌ Não configurado'}
          </div>
          <button 
            onClick={setupPipeline} 
            disabled={isSetupMode}
            className="setup-button"
          >
            {isSetupMode ? 'Configurando...' : '⚙️ Configurar Pipeline'}
          </button>
          <button onClick={clearChat} className="clear-button">
            🗑️ Limpar
          </button>
          <button 
            onClick={runEvaluation} 
            disabled={!pipelineStatus?.ready || isLoading}
            className="eval-button"
          >
            📊 Avaliar
          </button>
        </div>
      </div>

      {isSetupMode && (
        <div className="setup-progress">
          <div className="progress-bar">
            <div className="progress-fill"></div>
          </div>
          <p>{setupProgress}</p>
        </div>
      )}

      <div className="rag-messages">
        {messages.length === 0 ? (
          <div className="welcome-message">
            <h3>Bem-vindo ao Assistente RAG da InfinitePay!</h3>
            <p>Faça perguntas sobre os serviços e produtos da InfinitePay.</p>
            <div className="example-questions">
              <h4>Exemplos de perguntas:</h4>
              <ul>
                <li>"Como entrar em contato com o suporte?"</li>
                <li>"Quais são as taxas das maquininhas?"</li>
                <li>"Como criar uma conta na InfinitePay?"</li>
                <li>"Como funciona o sistema de pagamentos?"</li>
              </ul>
            </div>
            {!pipelineStatus?.ready && (
              <div className="setup-notice">
                <p>⚠️ O pipeline RAG precisa ser configurado antes do uso. Clique em "Configurar Pipeline" acima.</p>
              </div>
            )}
          </div>
        ) : (
          messages.map((msg, index) => (
            <div key={index} className={`message ${msg.type}`}>
              <div className="message-header">
                <span className="message-type">
                  {msg.type === 'user' ? '👤 Você' : 
                   msg.type === 'bot' ? '🤖 RAG Assistant' :
                   msg.type === 'system' ? '📊 Sistema' : '❌ Erro'}
                </span>
                <span className="message-time">{msg.timestamp}</span>
              </div>
              <div className="message-content">
                {msg.content.split('\n').map((line, i) => (
                  <p key={i}>{line}</p>
                ))}
              </div>
              {msg.sources && msg.sources.length > 0 && (
                <div className="message-sources">
                  <h4>📚 Fontes:</h4>
                  <ul>
                    {msg.sources.map((source, i) => (
                      <li key={i}>
                        <a href={source} target="_blank" rel="noopener noreferrer">
                          {source}
                        </a>
                      </li>
                    ))}
                  </ul>
                </div>
              )}
            </div>
          ))
        )}
        
        {isLoading && (
          <div className="loading-indicator">
            <div className="typing-dots">
              <span></span>
              <span></span>
              <span></span>
            </div>
            <p>Processando sua pergunta...</p>
          </div>
        )}
      </div>

      <form className="rag-input-form" onSubmit={handleSubmit}>
        <input
          type="text"
          value={inputMessage}
          onChange={handleInputChange}
          placeholder="Faça uma pergunta sobre a InfinitePay..."
          disabled={!pipelineStatus?.ready || isLoading}
        />
        <button 
          type="submit" 
          disabled={!pipelineStatus?.ready || !inputMessage.trim() || isLoading}
        >
          {isLoading ? '⏳' : '📤'} Enviar
        </button>
      </form>
    </div>
  );
};

export default RAGInterface;