import React, { useState, useEffect, useRef, FormEvent, ChangeEvent } from 'react';
import { io, Socket } from 'socket.io-client';
import axios from 'axios';
import './App.css';
import ChatMessage from './components/ChatMessage';
import { Message, ChatError } from './types';

function App(): JSX.Element {
  const [messages, setMessages] = useState<Message[]>([]);
  const [inputMessage, setInputMessage] = useState<string>('');
  const [socket, setSocket] = useState<Socket | null>(null);
  const [isConnected, setIsConnected] = useState<boolean>(false);
  const [isTyping, setIsTyping] = useState<boolean>(false);

  const messagesEndRef = useRef<HTMLDivElement>(null);


  useEffect(() => {
    const apiUrl = process.env.REACT_APP_API_URL || 'http://localhost:8000';
    const newSocket = io(apiUrl, {
      transports: ['polling'],
      reconnection: true,
    });

    newSocket.on('connect', () => {
      console.log('Connected to server');
      setIsConnected(true);
    });

    newSocket.on('disconnect', () => {
      console.log('Disconnected from server');
      setIsConnected(false);
    });

    newSocket.on('chat_response', (response: Message) => {
      setMessages(prevMessages => [...prevMessages, response]);
      setIsTyping(false);
    });

    newSocket.on('chat_error', (error: ChatError) => {
      console.error('Chat error:', error);
      setMessages(prevMessages => [
        ...prevMessages, 
        { 
          text: error.text || 'Sorry, an error occurred', 
          type: 'error',
          timestamp: new Date().toISOString(),
          sender: 'agent'
        }
      ]);
      setIsTyping(false);
    });

    setSocket(newSocket);


    loadChatHistory();

    return () => {
      newSocket.disconnect();
    };
  }, []);


  useEffect(() => {
    scrollToBottom();
  }, [messages]);

  const scrollToBottom = (): void => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  };

  const loadChatHistory = async (): Promise<void> => {
    try {
      const response = await axios.get<{ messages: Message[] }>('/api/messages', {
        params: {
          session_id: 'default',
          limit: 50
        }
      });
      setMessages(response.data.messages || []);
    } catch (error) {
      console.error('Failed to load chat history:', error);
      setMessages([]);
    }
  };

  const handleSubmit = (e: FormEvent<HTMLFormElement>): void => {
    e.preventDefault();
    if (!inputMessage.trim() || !socket) return;

    const message: Message = {
      text: inputMessage,
      type: 'text',
      timestamp: new Date().toISOString(),
      sender: 'user'
    };

    setMessages(prevMessages => [...prevMessages, message]);
    socket.emit('chat_message', message);
    setInputMessage('');
    setIsTyping(true);
  };

  const handleInputChange = (e: ChangeEvent<HTMLInputElement>): void => {
    setInputMessage(e.target.value);
  };



  return (
    <div className="app">
      <header className="app-header">
        <h1>AI Assistant Platform</h1>

        <div className={`connection-status ${isConnected ? 'connected' : 'disconnected'}`}>
          {isConnected ? 'Connected' : 'Disconnected'}
        </div>
      </header>

      <main className="app-main">
        <div className="chat-container">
            <div className="messages-container">
              {messages.length === 0 ? (
                <div className="welcome-message">
                  <h2>Welcome to Knowledge & Math Assistant!</h2>
                  <p>Ask me questions about InfinitePay or solve mathematical expressions.</p>
                  <p>Examples:</p>
                  <ul>
                    <li>"How do I create an account on InfinitePay?"</li>
                    <li>"What is 65 x 3.11?"</li>
                    <li>"Calculate (42 * 2) / 6"</li>
                  </ul>
                </div>
              ) : (
                messages.map((msg, index) => (
                  <ChatMessage key={index} message={msg} />
                ))
              )}
              {isTyping && (
                <div className="typing-indicator">
                  <span></span>
                  <span></span>
                  <span></span>
                </div>
              )}
              <div ref={messagesEndRef} />
            </div>

            <form className="message-form" onSubmit={handleSubmit}>
              <input
                type="text"
                value={inputMessage}
                onChange={handleInputChange}
                placeholder="Ask a question or enter a math expression..."
                disabled={!isConnected}
              />
              <button type="submit" disabled={!isConnected || !inputMessage.trim()}>
                Send
              </button>
            </form>
        </div>

        <div className="info-panel">
          <h2>Query Information</h2>
          {messages.some(msg => (msg.type === 'knowledge' || msg.type === 'math') && msg.routing_info) ? (
            <div className="query-stats">
              {messages
                .filter(msg => (msg.type === 'knowledge' || msg.type === 'math') && msg.routing_info)
                .slice(-5)
                .map((msg, index) => (
                  <div key={index} className="query-stat-item">
                    <div className="stat-header">
                      <span className={`stat-type ${msg.type}`}>
                        {msg.type === 'math' ? '🧮' : '📚'} {msg.type.charAt(0).toUpperCase() + msg.type.slice(1)}
                      </span>
                      <span className="stat-time">{msg.execution_time?.toFixed(2)}s</span>
                    </div>
                    <div className="stat-details">
                      {msg.source && <span>Source: {msg.source}</span>}
                      {msg.metadata?.num_sources && <span>Sources: {msg.metadata.num_sources}</span>}
                    </div>
                  </div>
                ))
              }
            </div>
          ) : (
            <div className="no-query-data">
              <p>No query information to display yet.</p>
              <p>Try asking a question or solving a math problem!</p>
            </div>
          )}
        </div>
      </main>
    </div>
  );
}

export default App;