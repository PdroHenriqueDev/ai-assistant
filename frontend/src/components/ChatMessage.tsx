import React from 'react';
import './ChatMessage.css';
import { ChatMessageProps } from '../types';

const ChatMessage: React.FC<ChatMessageProps> = ({ message }) => {
  const { text, sender, timestamp, type, source, execution_time, metadata, routing_info } = message;
  
  const formatTime = (timestamp: string): string => {
    const date = new Date(timestamp);
    return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
  };

  const getMessageTypeIcon = (type: string): string => {
    switch (type) {
      case 'math':
        return '🧮';
      case 'knowledge':
        return '📚';
      case 'error':
        return '⚠️';
      default:
        return '💬';
    }
  };

  const renderMetadata = (): JSX.Element | null => {
    if (sender === 'user' || !routing_info) return null;
    
    return (
      <div className="message-metadata">
        <div className="metadata-item">
          <span className="metadata-label">Agent:</span>
          <span className="metadata-value">{routing_info.agent_used}</span>
        </div>
        {source && (
          <div className="metadata-item">
            <span className="metadata-label">Source:</span>
            <span className="metadata-value">{source}</span>
          </div>
        )}
        {execution_time && (
          <div className="metadata-item">
            <span className="metadata-label">Response time:</span>
            <span className="metadata-value">{execution_time.toFixed(2)}s</span>
          </div>
        )}
        {metadata && metadata.num_sources && (
          <div className="metadata-item">
            <span className="metadata-label">Sources found:</span>
            <span className="metadata-value">{metadata.num_sources}</span>
          </div>
        )}
      </div>
    );
  };

  return (
    <div className={`chat-message ${sender === 'user' ? 'user-message' : 'agent-message'} ${type ? `message-${type}` : ''}`}>
      <div className="message-content">
        <div className="message-header">
          {sender !== 'user' && (
            <span className="message-type-icon">{getMessageTypeIcon(type)}</span>
          )}
          <div className="message-text">{text}</div>
        </div>
        {renderMetadata()}
        <div className="message-info">
          <span className="message-time">{formatTime(timestamp)}</span>
          <span className="message-sender">{sender === 'user' ? 'You' : 'Assistant'}</span>
        </div>
      </div>
    </div>
  );
};

export default ChatMessage;