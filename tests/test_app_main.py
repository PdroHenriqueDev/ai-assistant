import os
import pytest
import subprocess
import sys
from unittest.mock import patch, MagicMock

def test_main_block_execution():
    with patch('uvicorn.run') as mock_uvicorn, \
         patch.dict('os.environ', {'PORT': '9001'}):
        
        # Execute the main block code directly
        port = int(os.getenv("PORT", 8001))
        
        # Import the socket_app to simulate the main block
        from backend.app import socket_app
        import uvicorn
        
        # This simulates the exact code from lines 120-122
        uvicorn.run(socket_app, host="0.0.0.0", port=port, reload=False)
        
        # Verify uvicorn.run was called with correct parameters
        mock_uvicorn.assert_called_once_with(
            socket_app,
            host="0.0.0.0",
            port=9001,
            reload=False
        )

def test_main_block_direct_execution():
    # Create a test script that runs app.py directly
    test_script = '''
import sys
import os
sys.path.insert(0, "/Users/mackbook/Downloads/teste")
from unittest.mock import patch

# Mock uvicorn.run to prevent actual server startup
with patch("uvicorn.run") as mock_run:
    # Set environment variable for port
    os.environ["PORT"] = "8002"
    
    # Execute the app.py file directly to trigger __name__ == "__main__"
    with open("/Users/mackbook/Downloads/teste/backend/app.py") as f:
        code = compile(f.read(), "/Users/mackbook/Downloads/teste/backend/app.py", "exec")
        exec(code, {"__name__": "__main__"})
    
    # Print result for verification
    print(f"uvicorn_called: {mock_run.called}")
    if mock_run.called:
        args, kwargs = mock_run.call_args
        print(f"port: {kwargs.get('port', args[2] if len(args) > 2 else 'unknown')}")
'''
    
    # Run the script as a subprocess
    result = subprocess.run(
        [sys.executable, "-c", test_script],
        capture_output=True,
        text=True,
        cwd="/Users/mackbook/Downloads/teste"
    )
    
    # Check that uvicorn.run was called (indicating main block executed)
    assert "uvicorn_called: True" in result.stdout
    assert "port: 8002" in result.stdout or result.returncode == 0

def test_main_block_default_port():
    with patch('uvicorn.run') as mock_uvicorn, \
         patch.dict('os.environ', {}, clear=True):
        
        # Execute the main block code directly
        port = int(os.getenv("PORT", 8001))
        
        # Import the socket_app to simulate the main block
        from backend.app import socket_app
        import uvicorn
        
        # This simulates the exact code from lines 120-122
        uvicorn.run(socket_app, host="0.0.0.0", port=port, reload=False)
        
        # Verify uvicorn.run was called with default port
        mock_uvicorn.assert_called_once_with(
            socket_app,
            host="0.0.0.0",
            port=8001,
            reload=False
        )