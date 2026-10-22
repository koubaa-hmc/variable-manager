# import pytest
import json
from variable_manager.lsp import VariableManagerLSP

class MockStream:
    def __init__(self, input_data: str):
        self.input_data = input_data
        self.output = []

    def readline(self):
        if not self.input_data:
            return ""
        lines = self.input_data.splitlines(keepends=True)
        self.input_data = "".join(lines[1:])
        return lines[0]

    def read(self, n):
        res = self.input_data[:n]
        self.input_data = self.input_data[n:]
        return res

    def write(self, s):
        self.output.append(s)

    def flush(self):
        pass

def test_lsp_initialize_and_commands():
    # Construct JSON-RPC messages
    init_msg = {
        "jsonrpc": "2.0",
        "id": 1,
        "method": "initialize",
        "params": {}
    }

    cmd_msg = {
        "jsonrpc": "2.0",
        "id": 2,
        "method": "workspace/executeCommand",
        "params": {
            "command": "variableManager.setVariable",
            "arguments": ["local", "test_lsp_var", 99, "integer", "Target Location", "Test LSP variable"]
        }
    }

    recommend_msg = {
        "jsonrpc": "2.0",
        "id": 3,
        "method": "workspace/executeCommand",
        "params": {
            "command": "variableManager.recommendVariables",
            "arguments": ["move", 2]
        }
    }

    completion_msg = {
        "jsonrpc": "2.0",
        "id": 4,
        "method": "textDocument/completion",
        "params": {
            "textDocument": {"uri": "file:///test.py"},
            "position": {"line": 0, "character": 0}
        }
    }

    exit_msg = {
        "jsonrpc": "2.0",
        "method": "exit",
        "params": {}
    }

    # Format with Content-Length
    def format_rpc(msg):
        content = json.dumps(msg)
        return f"Content-Length: {len(content)}\r\n\r\n{content}"

    input_stream = format_rpc(init_msg) + format_rpc(cmd_msg) + format_rpc(recommend_msg) + format_rpc(completion_msg) + format_rpc(exit_msg)

    import sys
    mock_io = MockStream(input_stream)

    server = VariableManagerLSP()

    # Temporarily monkeypatch sys.stdin and sys.stdout
    old_stdin = sys.stdin
    old_stdout = sys.stdout
    sys.stdin = mock_io
    sys.stdout = mock_io

    try:
        server.run()
    finally:
        sys.stdin = old_stdin
        sys.stdout = old_stdout

    # Verify responses
    assert len(mock_io.output) > 0
    # Combine outputs and parse JSON-RPC responses
    # full_output = "".join(mock_io.output)

    # Check that variable was successfully set in manager
    var = server.vm.get_variable("local", "test_lsp_var")
    assert var is not None
    assert var["value"] == 99
    assert var["type"] == "integer"
