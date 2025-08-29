# Testing Infrastructure

This directory contains comprehensive tests for the chat application, covering unit tests for individual components and end-to-end tests for API endpoints.

## Test Structure

### Unit Tests
- **`test_router_agent.py`** - Tests for the RouterAgent decision logic that determines whether to route messages to math or knowledge agents
- **`test_math_agent.py`** - Tests for the MathAgent's simple expression evaluation capabilities

### End-to-End Tests
- **`test_chat_api_e2e.py`** - Comprehensive tests for the `/chat` API endpoints, including REST API and Socket.IO functionality

## Running Tests

### Prerequisites

1. **Create a virtual environment:**
   ```bash
   python3 -m venv test_env
   source test_env/bin/activate
   ```

2. **Install test dependencies:**
   ```bash
   pip install pytest pytest-asyncio fastapi httpx openai aiohttp python-socketio redis uvicorn python-dotenv motor
   ```

### Running All Tests

```bash
# Activate virtual environment
source test_env/bin/activate

# Run all tests with verbose output
python -m pytest tests/ -v

# Run tests with short traceback format
python -m pytest tests/ -v --tb=short

# Run specific test file
python -m pytest tests/test_router_agent.py -v
```

### Running Individual Test Categories

```bash
# Run only unit tests
python -m pytest tests/test_router_agent.py tests/test_math_agent.py -v

# Run only E2E tests
python -m pytest tests/test_chat_api_e2e.py -v
```

## Test Coverage

### RouterAgent Tests (`test_router_agent.py`)
- ✅ Basic arithmetic detection (addition, subtraction, multiplication, division)
- ✅ Mathematical keyword recognition ("calculate", "compute", "solve")
- ✅ Advanced function detection (trigonometric, logarithmic, exponential)
- ✅ Special operator handling (factorial, power, modulo)
- ✅ Non-mathematical query routing to knowledge agent
- ✅ Edge cases (empty strings, special characters)
- ✅ Case insensitivity testing
- ✅ Decision details structure validation

### MathAgent Tests (`test_math_agent.py`)
- ✅ Math query detection logic
- ✅ Simple arithmetic calculations (integers and decimals)
- ✅ Expression parsing with parentheses
- ✅ Keyword-based math detection
- ✅ Invalid expression handling
- ✅ Process query workflow (simple math vs OpenAI fallback)
- ✅ Error handling and edge cases
- ✅ Whitespace and punctuation handling

### Chat API E2E Tests (`test_chat_api_e2e.py`)
- ✅ Health endpoint functionality
- ✅ GET `/api/messages` endpoint
- ✅ POST `/api/messages` with math queries
- ✅ POST `/api/messages` with knowledge queries
- ✅ Cached response handling
- ✅ Error handling and validation
- ✅ Socket.IO test endpoint
- ✅ Concurrent request handling
- ✅ Session ID management
- ✅ Response structure validation
- ✅ Example messages from requirements

## Test Configuration

### Environment Variables
Some tests may require environment variables to be set:

```bash
# Optional: Set OpenAI API key for full MathAgent testing
export OPENAI_API_KEY="your-api-key-here"

# Optional: Set Redis connection details
export REDIS_HOST="localhost"
export REDIS_PORT="6379"
```

### Mock Configuration
The tests use extensive mocking to avoid external dependencies:
- **Redis**: Mocked to avoid requiring a running Redis instance
- **OpenAI API**: Mocked to avoid API calls and costs
- **MongoDB**: Mocked to avoid database dependencies
- **Socket.IO**: Mocked for isolated testing

## Test Examples

### Example Messages Tested
The tests validate the system's handling of the specific example messages from the requirements:

1. **"What are the card machine fees?"** → Routes to knowledge agent
2. **"Can I use my phone as a card machine?"** → Routes to knowledge agent  
3. **"How much is 65 x 3.11?"** → Routes to math agent

### Mathematical Expressions Tested
- Basic arithmetic: `2 + 3`, `10 - 5`, `4 * 6`, `8 / 2`
- Decimal operations: `3.14 * 2`, `10.5 / 2.1`
- Complex expressions: `(2 + 3) * 4`, `sqrt(16) + log(10)`
- Edge cases: `2++3` (invalid), `calculate 5+5` (keyword-based)

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all dependencies are installed in the virtual environment
2. **OpenAI API Errors**: Set `OPENAI_API_KEY` environment variable or expect some tests to be skipped
3. **Redis Connection Errors**: Tests use mocks, so Redis doesn't need to be running
4. **Path Issues**: Run tests from the project root directory

### Test Failures
Some tests may fail if:
- Environment variables are not set correctly
- Dependencies are missing or outdated
- The application code has been modified without updating tests

### Debugging

```bash
# Run tests with more detailed output
python -m pytest tests/ -v -s

# Run a specific test method
python -m pytest tests/test_router_agent.py::TestRouterAgent::test_basic_arithmetic -v

# Show local variables in tracebacks
python -m pytest tests/ -v -l
```

## Continuous Integration

To integrate these tests into a CI/CD pipeline:

```yaml
# Example GitHub Actions workflow
name: Run Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v2
      - name: Set up Python
        uses: actions/setup-python@v2
        with:
          python-version: '3.9'
      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install pytest pytest-asyncio fastapi httpx openai aiohttp python-socketio redis uvicorn python-dotenv motor
      - name: Run tests
        run: pytest tests/ -v
```

## Contributing

When adding new tests:

1. **Follow naming conventions**: `test_*.py` for files, `test_*` for methods
2. **Use descriptive names**: Test names should clearly indicate what is being tested
3. **Include docstrings**: Document what each test validates
4. **Mock external dependencies**: Avoid requiring external services
5. **Test edge cases**: Include both positive and negative test cases
6. **Update this README**: Document new test categories or requirements

## Test Metrics

- **Total Tests**: 38 tests across 3 test files
- **Unit Tests**: 26 tests (RouterAgent: 12, MathAgent: 14)
- **E2E Tests**: 12 tests covering API endpoints
- **Coverage Areas**: Agent routing, math evaluation, API endpoints, error handling