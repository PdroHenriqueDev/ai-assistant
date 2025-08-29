# AI Assistant

A real-time chatbot application that combines knowledge retrieval and mathematical computation capabilities using a sophisticated agent-based architecture.

## Project Information

- **Project Name**: AI Assistant
- **Repository**: https://github.com/PdroHenriqueDev/ai-assistant
- **Project Folder**: `ai-assistant` (or your chosen directory name)
- **Main Components**: Backend (Python/FastAPI), Frontend (React/TypeScript), RAG Pipeline, Tests

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
- Docker and Docker Compose (recommended)
- OR Python 3.8+ and Node.js 16+ for local development
- OpenAI API key

## Running with Docker (Recommended)

### Quick Start

1. **Clone the repository and navigate to the project directory:**
   ```bash
   git clone https://github.com/PdroHenriqueDev/ai-assistant.git
   cd ai-assistant
   ```

2. **Configure environment variables:**
   ```bash
   cp .env.example .env
   # Edit .env file with your OpenAI API key
   ```

3. **Build and run all services:**
   ```bash
   docker-compose up --build
   ```

4. **Access the application:**
   - Frontend: http://localhost:3000 (development mode)
   - Backend API: http://localhost:8000
   - RAG API: http://localhost:8001
   - MongoDB: localhost:27017
   - Redis: localhost:6379

### Docker Services

The application consists of the following Docker services:

- **app**: Main FastAPI backend with Socket.IO support
- **rag-api**: Separate RAG (Retrieval-Augmented Generation) service
- **redis**: Redis server for caching and session management
- **mongo**: MongoDB database for message persistence
- **frontend-dev**: React development server (optional, for development)

### Docker Commands

```bash
# Start all services
docker-compose up

# Start with rebuild
docker-compose up --build

# Start in background
docker-compose up -d

# Start with development frontend
docker-compose --profile dev up

# View logs
docker-compose logs -f

# Stop all services
docker-compose down

# Stop and remove volumes
docker-compose down -v
```

## Kubernetes Deployment

### Prerequisites
- Kubernetes cluster (local or cloud)
- kubectl configured to access your cluster
- Docker images built and pushed to a registry

### Deploy to Kubernetes

1. **Build and push Docker images:**
   ```bash
   # Build the application image
   docker build -t your-registry/ai-assistant:latest .
   
   # Push to your container registry
   docker push your-registry/ai-assistant:latest
   ```

2. **Create secrets for sensitive data:**
   ```bash
   kubectl create secret generic app-secrets \
     --from-literal=OPENAI_API_KEY=your_openai_api_key \
     -n ai-assistant
   ```

3. **Deploy all Kubernetes resources:**
   ```bash
   # Apply all configurations in order
   kubectl apply -f k8s/namespace.yaml
   kubectl apply -f k8s/storage.yaml
   kubectl apply -f k8s/configmap.yaml
   kubectl apply -f k8s/redis-pvc.yaml
   kubectl apply -f k8s/redis-deployment.yaml
   kubectl apply -f k8s/redis-service.yaml
   kubectl apply -f k8s/backend-deployment.yaml
   kubectl apply -f k8s/backend-service.yaml
   kubectl apply -f k8s/frontend-deployment.yaml
   kubectl apply -f k8s/frontend-service.yaml
   kubectl apply -f k8s/ingress.yaml
   ```

   Or apply all at once:
   ```bash
   kubectl apply -f k8s/
   ```

4. **Verify deployment:**
   ```bash
   # Check all pods are running
   kubectl get pods -n ai-assistant
   
   # Check services
   kubectl get services -n ai-assistant
   
   # Check ingress
   kubectl get ingress -n ai-assistant
   ```

5. **Access the application:**
   ```bash
   # Port forward for local access
   kubectl port-forward service/frontend 3000:80 -n ai-assistant
   kubectl port-forward service/backend 8000:8000 -n ai-assistant
   ```

### Kubernetes Resources

The deployment includes:
- **Namespace**: `ai-assistant` for resource isolation
- **Backend**: FastAPI application with 2 replicas
- **Frontend**: React application served via nginx
- **Redis**: Caching and session storage
- **Persistent Volumes**: For data persistence (ChromaDB, logs)
- **ConfigMap**: Environment configuration
- **Secrets**: Sensitive data (API keys)
- **Ingress**: External access with CORS configuration

### Scaling

```bash
# Scale backend replicas
kubectl scale deployment backend --replicas=3 -n ai-assistant

# Scale frontend replicas
kubectl scale deployment frontend --replicas=2 -n ai-assistant
```

## Local Development Setup

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
| `HOST` | Server host configuration | No (default: 0.0.0.0) |
| `CORS_ORIGINS` | Allowed CORS origins | No |
| `LOG_LEVEL` | Logging level | No (default: INFO) |
| `RAG_API_URL` | RAG API service URL | Yes |
| `RAG_VECTOR_STORE_PATH` | ChromaDB storage path | No (default: ./chroma_db) |

### RAG System Configuration
- **Vector Store**: ChromaDB with persistent storage
- **Embeddings**: OpenAI text-embedding-3-large
- **Chunk Size**: 1000 characters with 200 character overlap
- **Retrieval**: Top 3 most relevant documents

## Development

### Project Structure
```
ai-assistant/
├── .env.example                 # Environment variables template
├── .gitignore                   # Git ignore rules
├── Dockerfile                   # Docker configuration for backend
├── README.md                    # Project documentation
├── docker-compose.yml           # Docker Compose configuration
├── requirements.txt             # Python dependencies
├── backend/                     # Backend application (Python/FastAPI)
│   ├── __init__.py
│   ├── agents/                  # AI agents implementation
│   │   ├── __init__.py
│   │   ├── knowledge_agent.py   # RAG-based knowledge agent
│   │   └── math_agent.py        # Mathematical computation agent
│   ├── app.py                   # Main FastAPI application
│   ├── brokers/                 # Message routing system
│   │   ├── __init__.py
│   │   └── broker_system.py     # Router agent implementation
│   ├── database/                # Database clients
│   │   ├── __init__.py
│   │   ├── mongodb.py           # MongoDB client
│   │   └── redis_client.py      # Redis client
│   └── rag_api.py              # RAG API service
├── frontend/                    # Frontend application (React/TypeScript)
│   ├── Dockerfile.dev           # Docker configuration for frontend
│   ├── package.json             # Node.js dependencies
│   ├── package-lock.json        # Locked dependencies
│   ├── tsconfig.json           # TypeScript configuration
│   └── src/                     # Source code
│       ├── App.css
│       ├── App.tsx              # Main React component
│       ├── components/          # React components
│       ├── index.css
│       ├── index.tsx            # Application entry point
│       ├── reportWebVitals.ts
│       └── types/               # TypeScript type definitions
├── k8s/                         # Kubernetes deployment files
│   ├── backend-deployment.yaml
│   ├── backend-service.yaml
│   ├── configmap.yaml
│   ├── frontend-deployment.yaml
│   ├── frontend-service.yaml
│   ├── ingress.yaml
│   ├── namespace.yaml
│   ├── redis-deployment.yaml
│   ├── redis-pvc.yaml
│   ├── redis-service.yaml
│   └── storage.yaml
├── rag_pipeline/                # RAG pipeline components
│   ├── .env.example
│   ├── README.md
│   ├── document_processor.py    # Document processing
│   ├── main_pipeline.py         # Main RAG pipeline
│   ├── rag_chain.py            # RAG chain implementation
│   ├── requirements.txt         # RAG-specific dependencies
│   ├── scraper.py              # Web scraping utilities
│   └── vector_store.py         # Vector database management
├── test_env/                    # Test environment files
└── tests/                       # Test suite
    ├── README.md                # Testing documentation
    ├── __init__.py
    ├── test_app_additional.py   # Additional app tests
    ├── test_app_main.py         # Main app tests
    ├── test_broker_system_full.py # Broker system tests
    ├── test_chat_api_e2e.py     # End-to-end API tests
    ├── test_knowledge_agent.py  # Knowledge agent tests
    ├── test_math_agent.py       # Math agent tests
    ├── test_mongodb_client.py   # MongoDB client tests
    ├── test_rag_api.py          # RAG API tests
    ├── test_rag_api_import_coverage.py # Import coverage tests
    ├── test_redis_client.py     # Redis client tests
    └── test_router_agent.py     # Router agent tests
```

### Adding New Agents

1. Create agent class in `backend/agents/`
2. Implement `process_query()` method
3. Update `RouterAgent` routing logic
4. Add message type handling in frontend

### Example Logs (JSON Format)

The system produces structured JSON logs for monitoring and debugging:

#### Router Decision Log
```json
{
  "session_id": "user_session_123",
  "message": "What is 25 * 4?",
  "agent_selected": "math",
  "decision_details": {
    "patterns_checked": 7,
    "matches_found": ["\\d+\\s*[+\\-*/×÷]\\s*\\d+"],
    "reasoning": "Mathematical patterns detected"
  },
  "execution_time_seconds": 0.245,
  "response_type": "math"
}
```

#### Knowledge Query Log
```json
{
  "session_id": "user_session_456",
  "message": "How do I create an account on InfinitePay?",
  "agent_selected": "knowledge",
  "decision_details": {
    "patterns_checked": 7,
    "matches_found": [],
    "reasoning": "No mathematical patterns, routing to knowledge agent"
  },
  "execution_time_seconds": 1.832,
  "response_type": "knowledge"
}
```

#### Error Processing Log
```json
{
  "session_id": "user_session_789",
  "message": "Calculate the impossible",
  "error": "OpenAI API rate limit exceeded",
  "execution_time_seconds": 0.156
}
```

#### Redis Structured Event Log
```json
{
  "timestamp": "2024-01-15T10:30:45.123456",
  "event_type": "message_processed",
  "session_id": "user_session_123",
  "message": "What is 25 * 4?",
  "agent_selected": "math",
  "execution_time_seconds": 0.245,
  "response_type": "math"
}
```

#### Agent Response with Routing Info
```json
{
  "text": "The answer is 100",
  "type": "math",
  "timestamp": "2024-01-15T10:30:45.368912",
  "sender": "agent",
  "routing_info": {
    "agent_used": "math",
    "execution_time": 0.245,
    "decision_details": {
      "patterns_checked": 7,
      "matches_found": ["\\d+\\s*[+\\-*/×÷]\\s*\\d+"],
      "reasoning": "Mathematical patterns detected"
    }
  }
}
```

### Monitoring and Logging

The system provides structured logging with:
- **Routing decisions** with reasoning and pattern matching details
- **Execution times** for performance monitoring
- **Source attribution** for knowledge queries
- **Error tracking** with detailed context
- **Redis streams** for real-time log aggregation
- **Session tracking** for conversation flow analysis

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

## Security and Input Validation

The system implements multiple layers of security to protect against malicious input and prompt injection attacks:

### Input Sanitization

#### Math Agent Protection
The Math Agent implements strict input validation for mathematical expressions:

```python
# Expression cleaning and validation
cleaned = re.sub(r'[^0-9+\-*/().\s]', '', expression)  # Remove non-math characters
if re.match(r'^[0-9+\-*/().\s]+$', cleaned):           # Validate safe pattern
    result = eval(cleaned)  # Only evaluate if pattern matches
```

**Security Features:**
- **Character filtering**: Removes all non-mathematical characters
- **Pattern validation**: Only allows numbers, operators, parentheses, and whitespace
- **Safe evaluation**: Uses `eval()` only after strict validation
- **Error handling**: Gracefully handles malformed expressions

#### Knowledge Agent Protection
The Knowledge Agent processes queries through the RAG pipeline with built-in safeguards:

- **Input validation**: Checks for empty or malformed queries
- **Content filtering**: RAG system processes only legitimate knowledge queries
- **Response sanitization**: Structured responses prevent injection in outputs

### Prompt Injection Prevention

#### System-Level Protections
1. **Agent Isolation**: Math and Knowledge agents operate independently
2. **Input Routing**: Router agent classifies queries before processing
3. **Structured Responses**: All agent responses follow predefined schemas
4. **Error Boundaries**: Exceptions are caught and sanitized before user display

#### RAG Pipeline Security
- **Document Processing**: Input documents are cleaned and normalized
- **Query Isolation**: User queries are processed in isolated contexts
- **Response Validation**: Generated responses are validated before return

### API Security

#### Input Validation
```python
# FastAPI request validation
class QuestionRequest(BaseModel):
    question: str
    max_sources: int = 5

# Empty query protection
if not request.question.strip():
    raise HTTPException(status_code=400, detail="Question cannot be empty")
```

#### CORS Configuration
- Configured for development with appropriate restrictions
- Headers and methods are controlled
- Credentials handling is managed

### Session Security

- **Session Isolation**: Each conversation session is isolated
- **Redis Security**: Structured logging prevents injection in log streams
- **Error Sanitization**: Error messages are cleaned before storage/display

### Best Practices Implemented

1. **Input Validation**: All user inputs are validated before processing
2. **Output Encoding**: Responses are properly structured and encoded
3. **Error Handling**: Comprehensive error handling prevents information leakage
4. **Logging Security**: Structured logging prevents log injection
5. **Agent Boundaries**: Clear separation between different processing agents

### Security Testing

The system includes comprehensive security tests:

```bash
# Run security-focused tests
python -m pytest tests/test_math_agent.py::TestMathAgent::test_unsafe_expression_pattern -v
python -m pytest tests/test_broker_system_full.py -v
```

**Test Coverage:**
- ✅ Malicious expression detection
- ✅ Input sanitization validation
- ✅ Error boundary testing
- ✅ Agent isolation verification
- ✅ Response structure validation

## How to Run Tests

### Test Environment Setup

**Prerequisites:**
```bash
# Create and activate virtual environment
python3 -m venv test_env
source test_env/bin/activate  # On Windows: test_env\Scripts\activate

# Install all dependencies
pip install -r requirements.txt

# Or install test-specific dependencies
pip install pytest pytest-asyncio fastapi httpx openai aiohttp python-socketio redis uvicorn python-dotenv motor
```

### Backend Tests

#### Basic Test Commands
```bash
# Run all tests
pytest

# Run with verbose output
pytest -v

# Run with short traceback format
pytest -v --tb=short

# Run specific test file
pytest tests/test_math_agent.py

# Run specific test method
pytest tests/test_math_agent.py::TestMathAgent::test_is_math_query_detection -v
```

#### Test Coverage
```bash
# Run with coverage report
pytest --cov=backend --cov-report=html

# Run with coverage and show missing lines
pytest --cov=backend --cov-report=term-missing

# Generate coverage report in multiple formats
pytest --cov=backend --cov-report=html --cov-report=xml --cov-report=term

# View coverage report
open htmlcov/index.html  # On macOS
# Or navigate to htmlcov/index.html in your browser
```

#### Test Categories
```bash
# Run unit tests only
pytest tests/test_math_agent.py tests/test_router_agent.py -v

# Run integration tests
pytest tests/test_broker_system_full.py -v

# Run end-to-end tests
pytest tests/test_chat_api_e2e.py -v

# Run Redis-related tests
pytest tests/test_redis_client.py -v

# Run database tests
pytest tests/test_mongodb_client.py -v

# Run RAG API tests
pytest tests/test_rag_api.py -v
```

#### Test Filtering
```bash
# Run tests matching a pattern
pytest -k "math" -v
pytest -k "session" -v
pytest -k "redis" -v

# Run tests with specific markers
pytest -m "asyncio" -v

# Exclude specific tests
pytest -k "not slow" -v
```

#### Debugging Tests
```bash
# Run with detailed output and local variables
pytest -v -s -l

# Stop on first failure
pytest -x

# Drop into debugger on failures
pytest --pdb

# Show print statements
pytest -s

# Run with maximum verbosity
pytest -vv
```

#### Parallel Testing
```bash
# Install pytest-xdist for parallel execution
pip install pytest-xdist

# Run tests in parallel
pytest -n auto  # Auto-detect CPU cores
pytest -n 4     # Use 4 processes
```

### Test Structure Overview

**Total Test Coverage: 38+ tests across multiple categories**

#### Unit Tests (26 tests)
- **RouterAgent Tests** (`test_router_agent.py`): 12 tests
  - Basic arithmetic detection
  - Mathematical keyword recognition
  - Advanced function detection
  - Edge cases and error handling

- **MathAgent Tests** (`test_math_agent.py`): 14 tests
  - Math query detection logic
  - Simple arithmetic calculations
  - Expression parsing and validation
  - Security testing (unsafe expressions)

#### Integration Tests (12+ tests)
- **BrokerSystem Tests** (`test_broker_system_full.py`)
  - Message processing workflow
  - Agent routing decisions
  - Redis integration
  - Caching mechanisms
  - Error handling

#### End-to-End Tests (12+ tests)
- **Chat API Tests** (`test_chat_api_e2e.py`)
  - REST API endpoints
  - WebSocket functionality
  - Session management
  - Concurrent request handling
  - Response validation

#### Database Tests
- **Redis Client Tests** (`test_redis_client.py`)
  - Connection management
  - Conversation storage
  - Caching operations
  - Structured logging

- **MongoDB Tests** (`test_mongodb_client.py`)
  - Database operations
  - Message persistence
  - Query functionality

#### RAG API Tests
- **RAG API Tests** (`test_rag_api.py`)
  - Pipeline initialization
  - Question processing
  - CORS configuration
  - Error handling

### Environment Variables for Testing

```bash
# Set test environment variables
export OPENAI_API_KEY="test-key-for-testing"
export MONGODB_URL="mongodb://localhost:27017/test_db"
export REDIS_URL="redis://localhost:6379"
export RAG_API_URL="http://localhost:8002"

# Or create a .env.test file
echo "OPENAI_API_KEY=test-key" > .env.test
echo "MONGODB_URL=mongodb://localhost:27017/test_db" >> .env.test
```

### Continuous Integration Setup

**GitHub Actions Example:**
```yaml
# .github/workflows/test.yml
name: Run Tests
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    
    services:
      redis:
        image: redis:7-alpine
        ports:
          - 6379:6379
      mongodb:
        image: mongo:7
        ports:
          - 27017:27017
    
    steps:
      - uses: actions/checkout@v4
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'
      
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt
      
      - name: Run tests with coverage
        run: |
          pytest --cov=backend --cov-report=xml --cov-report=term
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          MONGODB_URL: mongodb://localhost:27017/test_db
          REDIS_URL: redis://localhost:6379
      
      - name: Upload coverage to Codecov
        uses: codecov/codecov-action@v3
        with:
          file: ./coverage.xml
```

### Frontend Tests
```bash
cd frontend

# Install dependencies
npm install

# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Run tests in watch mode
npm run test:watch

# Run tests in CI mode
npm run test:ci
```

### Performance Testing

```bash
# Install performance testing tools
pip install pytest-benchmark locust

# Run benchmark tests
pytest --benchmark-only

# Load testing with Locust
locust -f tests/load_test.py --host=http://localhost:8001
```

### Test Maintenance

**Adding New Tests:**
1. Follow naming convention: `test_*.py` for files, `test_*` for methods
2. Use descriptive test names that explain what is being tested
3. Include docstrings for complex test scenarios
4. Mock external dependencies (OpenAI, databases)
5. Test both positive and negative cases
6. Update test documentation when adding new test categories

**Test Quality Checklist:**
- ✅ Tests are isolated and don't depend on each other
- ✅ External services are properly mocked
- ✅ Test data is cleaned up after each test
- ✅ Edge cases and error conditions are covered
- ✅ Tests run quickly (< 1 second per test ideally)
- ✅ Test names clearly describe the scenario being tested

## Testing Multiple Conversations Simultaneously

The system supports concurrent conversations through session isolation. Each conversation is identified by a unique `session_id` and maintains separate conversation history, caching, and state.

### Session Management Architecture

- **Session Isolation**: Each session has its own conversation history stored in Redis with key pattern `conversation:{session_id}`
- **Concurrent Processing**: The system handles multiple simultaneous requests without blocking
- **Session Persistence**: Conversations are stored for 7 days (604800 seconds) with automatic expiration
- **Message Limits**: Each session maintains up to 100 messages (automatically trimmed)

### Testing Multiple Sessions

#### 1. REST API Testing

**Test concurrent sessions via HTTP API:**
```bash
# Terminal 1 - Session A
curl -X POST http://localhost:8001/api/messages \
  -H "Content-Type: application/json" \
  -d '{"text": "What is 2+2?", "session_id": "session_a"}'

# Terminal 2 - Session B  
curl -X POST http://localhost:8001/api/messages \
  -H "Content-Type: application/json" \
  -d '{"text": "Tell me about Python", "session_id": "session_b"}'

# Terminal 3 - Session C
curl -X POST http://localhost:8001/api/messages \
  -H "Content-Type: application/json" \
  -d '{"text": "Calculate 10*5", "session_id": "session_c"}'
```

**Retrieve conversation history for each session:**
```bash
# Get messages for session A
curl "http://localhost:8001/api/messages?session_id=session_a&limit=10"

# Get messages for session B
curl "http://localhost:8001/api/messages?session_id=session_b&limit=10"

# Get messages for session C
curl "http://localhost:8001/api/messages?session_id=session_c&limit=10"
```

#### 2. WebSocket Testing

**Test multiple WebSocket connections:**

```typescript
// Client 1
const socket1 = io('http://localhost:8001');
socket1.emit('chat_message', {
  text: 'What is 5+5?',
  session_id: 'websocket_session_1'
});

// Client 2
const socket2 = io('http://localhost:8001');
socket2.emit('chat_message', {
  text: 'Explain machine learning',
  session_id: 'websocket_session_2'
});

// Client 3 (using socket ID as session)
const socket3 = io('http://localhost:8001');
socket3.emit('chat_message', {
  text: 'Calculate square root of 16'
  // No session_id - will use socket.id
});
```

#### 3. Load Testing with Python

**Create a load test script:**
```python
# load_test.py
import asyncio
import aiohttp
import json
from datetime import datetime

async def send_message(session, session_id, message):
    url = 'http://localhost:8001/api/messages'
    data = {
        'text': message,
        'session_id': session_id
    }
    
    async with session.post(url, json=data) as response:
        result = await response.json()
        print(f"Session {session_id}: {result.get('text', 'No response')}")
        return result

async def test_concurrent_sessions():
    async with aiohttp.ClientSession() as session:
        tasks = []
        
        # Create 10 concurrent sessions
        for i in range(10):
            session_id = f"load_test_session_{i}"
            message = f"What is {i} + {i}?"
            task = send_message(session, session_id, message)
            tasks.append(task)
        
        # Execute all requests concurrently
        results = await asyncio.gather(*tasks)
        print(f"Completed {len(results)} concurrent requests")

if __name__ == "__main__":
    asyncio.run(test_concurrent_sessions())
```

**Run the load test:**
```bash
python load_test.py
```

#### 4. Frontend Multi-Tab Testing

1. **Open multiple browser tabs** to `http://localhost:3000`
2. **Each tab automatically gets a unique session ID**
3. **Send different messages** in each tab:
   - Tab 1: "What is 2+2?"
   - Tab 2: "Tell me about AI"
   - Tab 3: "Calculate 15*3"
4. **Verify session isolation** - each tab maintains its own conversation history

#### 5. Automated Testing

**The test suite includes concurrent session tests:**
```bash
# Run concurrent session tests
pytest tests/test_chat_api_e2e.py::TestChatAPIE2E::test_concurrent_requests -v

# Run session handling tests
pytest tests/test_chat_api_e2e.py::TestChatAPIE2E::test_session_id_handling -v

# Run all session-related tests
pytest -k "session" -v
```

### Monitoring Concurrent Sessions

#### Redis Session Monitoring
```bash
# Connect to Redis container
docker exec -it teste-redis-1 redis-cli

# List all conversation keys
KEYS conversation:*

# Get conversation history for a specific session
LRANGE conversation:session_a 0 -1

# Monitor real-time Redis operations
MONITOR
```

#### System Logs
```bash
# Monitor broker system logs
docker-compose logs broker-system --follow

# Monitor all services
docker-compose logs --follow

# Filter for session-related logs
docker-compose logs | grep "session_id"
```

### Expected Behavior

✅ **Correct Session Isolation:**
- Each session maintains separate conversation history
- Messages from different sessions don't interfere
- Caching works independently per session
- Agent routing works correctly for all sessions

✅ **Performance Characteristics:**
- Multiple sessions can be processed simultaneously
- No blocking between different session requests
- Redis handles concurrent read/write operations
- WebSocket connections scale independently

✅ **Error Handling:**
- Errors in one session don't affect others
- Failed sessions can be retried independently
- System remains stable under concurrent load