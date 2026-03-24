import pytest
from unittest.mock import patch, MagicMock
from eth_permissions.graph import build_graph
from hexbytes import HexBytes

@patch("eth_permissions.graph.AccessControlEventStream")
def test_build_graph(mock_stream_cls):
    # Setup mock stream and snapshot
    mock_stream = mock_stream_cls.return_value
    role_mock = MagicMock()
    role_mock.hash = HexBytes("0x" + "1" * 64)
    role_mock.__str__.return_value = "ROLE_1"
    
    mock_stream.snapshot = [
        {
            "role": role_mock,
            "members": ["0x1111111111111111111111111111111111111111"]
        }
    ]
    
    dot = build_graph("0x2222222222222222222222222222222222222222")
    
    # Verify graph contains nodes/edges
    source = dot.source
    assert "CONTRACT" in source
    assert "ROLE_1" in source
    assert "0x1111...1111" in source
