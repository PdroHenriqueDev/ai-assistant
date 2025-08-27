# Knowledge & Math Assistant

A real-time chatbot application that combines knowledge retrieval and mathematical computation capabilities using a sophisticated agent-based architecture.

## Features

### 🧠 Knowledge Agent
- **RAG (Retrieval-Augmented Generation)** system using LangChain
- Knowledge base sourced from InfinitePay help documentation
- Vector-based document retrieval with ChromaDB
- Contextual answers with source attribution

### 🧮 Math Agent
- Mathematical expression interpretation using OpenAI GPT
- Support for basic arithmetic, algebra, and mathematical functions
- Step-by-step solution explanations
- Natural language math problem solving

### 🎯 Router Agent
- Intelligent message routing between specialized agents
- Pattern-based mathematical expression detection
- Structured logging with decision details and execution times
- Real-time performance metrics

## Architecture

### Backend (Python + FastAPI)
- **FastAPI** web framework with WebSocket support
- **Agent-based architecture** with specialized components:
  - `RouterAgent`: Routes messages to appropriate agents
  - `KnowledgeAgent`: Handles knowledge queries using RAG
  - `MathAgent`: Processes mathematical expressions
- **MongoDB** integration for message persistence
- **Socket.IO** for real-time communication
- **Structured logging** for monitoring and debugging

### Frontend (React)
- **React** application with Socket.IO client
- **Real-time chat interface** with typing indicators
- **Message type visualization** with icons and metadata
- **Query statistics panel** showing agent usage and performance
- **Responsive design** for desktop and mobile

## Installation

### Prerequisites
- Python 3.8+
- Node.js 16+
- MongoDB
- OpenAI API key

### Backend Setup

1. **Navigate to backend directory:**
   ```bash
   cd backend
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment:**
   ```bash
   cp ../.env.example .env
   # Edit .env file with your OpenAI API key and MongoDB settings
   ```

5. **Start the backend server:**
   ```bash
   python app.py
   ```

### Frontend Setup

1. **Navigate to frontend directory:**
   ```bash
   cd frontend
   ```

2. **Install dependencies:**
   ```bash
   npm install
   ```

3. **Start the development server:**
   ```bash
   npm start
   ```

## Usage Examples

### Knowledge Queries
- "How do I create an account on InfinitePay?"
- "What are the payment methods available?"
- "How can I contact customer support?"

### Mathematical Expressions
- "What is 65 x 3.11?"
- "Calculate (42 * 2) / 6"
- "Solve 2x + 5 = 15"
- "What's the square root of 144?"

## API Endpoints

### REST API
- `GET /health` - Health check endpoint
- `GET /api/messages` - Retrieve message history
- `POST /api/messages` - Send a new message

### WebSocket Events
- `chat_message` - Send message to chatbot
- `chat_response` - Receive response from chatbot
- `chat_error` - Error handling

## Configuration

### Environment Variables

| Variable | Description | Required |
|----------|-------------|-----------|
| `OPENAI_API_KEY` | OpenAI API key for LLM operations | Yes |
| `MONGODB_URL` | MongoDB connection string | Yes |
| `PORT` | Backend server port | No (default: 8000) |
| `CORS_ORIGINS` | Allowed CORS origins | No |
| `LOG_LEVEL` | Logging level | No (default: INFO) |

### RAG System Configuration
- **Vector Store**: ChromaDB with persistent storage
- **Embeddings**: OpenAI text-embedding-3-large
- **Chunk Size**: 1000 characters with 200 character overlap
- **Retrieval**: Top 3 most relevant documents

## Development

### Project Structure
```
├── backend/
│   ├── agents/
│   │   ├── knowledge_agent.py
│   │   └── math_agent.py
│   ├── brokers/
│   │   └── broker_system.py
│   ├── database/
│   │   └── mongodb.py
│   ├── app.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── components/
│   │   │   ├── ChatMessage.js
│   │   │   └── ChatMessage.css
│   │   ├── App.js
│   │   └── App.css
│   └── package.json
└── README.md
```

### Adding New Agents

1. Create agent class in `backend/agents/`
2. Implement `process_query()` method
3. Update `RouterAgent` routing logic
4. Add message type handling in frontend

### Monitoring and Logging

The system provides structured logging with:
- **Routing decisions** with reasoning
- **Execution times** for performance monitoring
- **Source attribution** for knowledge queries
- **Error tracking** with detailed context

## Technologies Used

### Backend
- **FastAPI** - Modern Python web framework
- **LangChain** - LLM application framework
- **ChromaDB** - Vector database for embeddings
- **OpenAI** - Language model and embeddings
- **MongoDB** - Document database
- **Socket.IO** - Real-time communication

### Frontend
- **React** - UI library
- **Socket.IO Client** - Real-time communication
- **CSS3** - Styling and animations

## License

This project is licensed under the MIT License.