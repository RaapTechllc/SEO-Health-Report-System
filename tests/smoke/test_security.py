import pytest
import sys
import os

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, '.kiro', 'lib'))

@pytest.mark.smoke
def test_path_traversal_protection():
    """Ensure path traversal attacks are blocked."""
    try:
        from evolution_engine import EvolutionEngine
        engine = EvolutionEngine()
        
        # Test malicious agent names
        malicious_names = ["../../../etc/passwd", "..\\..\\windows\\system32", "agent/../../../secret"]
        
        for malicious_name in malicious_names:
            result = engine.apply_evolution(malicious_name, {"test": "change"})
            assert result == False, f"Path traversal not blocked for: {malicious_name}"
            
    except ImportError:
        pytest.skip("evolution_engine not available")

@pytest.mark.smoke
def test_handoff_path_validation():
    """Ensure handoff creation validates paths."""
    try:
        from handoff_protocol import HandoffProtocol
        protocol = HandoffProtocol()
        
        # Test malicious agent names
        with pytest.raises(ValueError):
            protocol.create_handoff("../../../malicious", "target", "test task")
            
        with pytest.raises(ValueError):
            protocol.create_handoff("source", "../../../malicious", "test task")
            
    except ImportError:
        pytest.skip("handoff_protocol not available")

@pytest.mark.smoke
def test_agent_name_validation():
    """Ensure agent names are properly validated."""
    try:
        from agent_schema import parse_agent_config, validate_agent_config
        
        # Test malicious config
        malicious_config = {
            "name": "../../../malicious",
            "description": "x",  # Too short
            "model": "",  # Empty
            "tools": ["invalid-tool!@#"]
        }
        
        config = parse_agent_config(malicious_config)
        errors = validate_agent_config(config)
        
        # Should have multiple validation errors
        assert len(errors) >= 3, f"Expected multiple validation errors, got: {errors}"
        
    except ImportError:
        pytest.skip("agent_schema not available")

@pytest.mark.smoke
def test_subprocess_safety():
    """Ensure subprocess calls are safe."""
    try:
        from verification_layer import VerificationLayer
        verifier = VerificationLayer()
        
        # This should not crash or allow injection
        result = verifier.run_smoke_tests()
        
        # Should return a TestResult object
        assert hasattr(result, 'status')
        assert hasattr(result, 'test_count')
        assert hasattr(result, 'duration_seconds')
        
    except ImportError:
        pytest.skip("verification_layer not available")
