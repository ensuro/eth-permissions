import json
import pytest
from io import StringIO
from unittest.mock import patch
from eth_permissions.main import main

@patch("eth_permissions.main.AccessManagerEventStream")
@patch("eth_permissions.main.am.AccessManager")
def test_cli_access_manager_snapshot(mock_am_cls, mock_stream_cls):
    # Setup mock stream
    mock_stream = mock_stream_cls.return_value
    mock_stream.snapshot_dict = {"roles": {}, "targets": {}}
    
    # Capture stdout
    stdout = StringIO()
    with patch("sys.stdout", stdout), patch("sys.argv", ["eth-permissions", "0x1234567890123456789012345678901234567890"]):
        main()
    
    output = json.loads(stdout.getvalue())
    assert output == {"roles": {}, "targets": {}}
    mock_stream_cls.assert_called_once_with("0x1234567890123456789012345678901234567890")

@patch("eth_permissions.main.AccessManagerEventStream")
@patch("eth_permissions.main.am.AccessManager")
def test_cli_access_manager_compare(mock_am_cls, mock_stream_cls, tmp_path):
    # Setup reference snapshot file
    ref_file = tmp_path / "ref.json"
    ref_data = {"roles": {}, "targets": {}}
    ref_file.write_text(json.dumps(ref_data))
    
    # Setup mock stream and comparison
    mock_stream = mock_stream_cls.return_value
    mock_stream.compare.return_value = []
    
    # Capture stdout
    stdout = StringIO()
    args = [
        "eth-permissions", 
        "--compare-snapshot", str(ref_file),
        "0x1234567890123456789012345678901234567890"
    ]
    with patch("sys.stdout", stdout), patch("sys.argv", args):
        main()
    
    output = json.loads(stdout.getvalue())
    assert output == []
    mock_stream.compare.assert_called_once()

@patch("eth_permissions.main.build_graph")
@patch("eth_permissions.main.load_registry")
def test_cli_access_control_graph(mock_load, mock_build, tmp_path):
    # Setup mock graph
    mock_graph = mock_build.return_value
    output_file = tmp_path / "graph.png"
    
    args = [
        "eth-permissions",
        "--type", "AccessControl",
        "--output", str(output_file),
        "0x1234567890123456789012345678901234567890"
    ]
    
    with patch("sys.argv", args):
        main()
    
    mock_build.assert_called_once_with("0x1234567890123456789012345678901234567890")
    mock_graph.render.assert_called_once()

def test_cli_missing_output_error():
    args = [
        "eth-permissions",
        "--type", "AccessControl",
        "0x1234567890123456789012345678901234567890"
    ]
    with patch("sys.argv", args), pytest.raises(ValueError, match="Output file must be specified"):
        main()

@patch("eth_permissions.main.get_registry")
def test_load_registry(mock_get_registry):
    from eth_permissions.main import load_registry, KNOWN_ROLES
    mock_reg = mock_get_registry.return_value
    
    with patch("eth_permissions.main.KNOWN_COMPONENTS", ["0x1111111111111111111111111111111111111111"]), \
         patch("eth_permissions.main.KNOWN_COMPONENT_NAMES", ["Comp1"]):
        load_registry()
        
    mock_reg.add_roles.assert_called_once()
    mock_reg.add_components.assert_called_once()

@patch("eth_permissions.main.build_graph")
def test_cli_access_control_graph_with_format(mock_build, tmp_path):
    mock_graph = mock_build.return_value
    output_file = tmp_path / "graph.png"
    
    args = [
        "eth-permissions",
        "--type", "AccessControl",
        "--output", str(output_file),
        "--format", "pdf",
        "0x1234567890123456789012345678901234567890"
    ]
    
    with patch("sys.argv", args):
        main()
    
    mock_graph.render.assert_called_once()
    # Check if 'format' was passed in kwargs
    args, kwargs = mock_graph.render.call_args
    assert kwargs["format"] == "pdf"
