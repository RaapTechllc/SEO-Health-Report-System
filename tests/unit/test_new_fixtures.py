"""
Quick test to verify all new fixtures work correctly.
"""



def test_mock_config_fixture(mock_config):
    """Test mock_config fixture works."""
    assert mock_config is not None
    assert hasattr(mock_config, "api_timeout")


def test_sample_audit_results_fixture(sample_audit_results):
    """Test sample_audit_results fixture works."""
    assert sample_audit_results is not None
    assert "audits" in sample_audit_results
    assert "technical" in sample_audit_results["audits"]


def test_sample_issues_fixture(sample_issues):
    """Test sample_issues fixture works."""
    assert sample_issues is not None
    assert len(sample_issues) == 2
    assert sample_issues[0]["type"] == "technical"


def test_sample_recommendations_fixture(sample_recommendations):
    """Test sample_recommendations fixture works."""
    assert sample_recommendations is not None
    assert len(sample_recommendations) == 2
    assert sample_recommendations[0]["action"] == "Fix meta tags"


def test_sample_brand_colors_fixture(sample_brand_colors):
    """Test sample_brand_colors fixture works."""
    assert sample_brand_colors is not None
    assert "primary" in sample_brand_colors
    assert sample_brand_colors["primary"] == "#1a73e8"


def test_temp_dir_fixture(temp_dir):
    """Test temp_dir fixture works."""
    assert temp_dir is not None
    import os

    assert os.path.exists(temp_dir)
    assert "test_output" in temp_dir


def test_mock_scheduled_job_fixture(mock_scheduled_job):
    """Test mock_scheduled_job fixture works."""
    assert mock_scheduled_job is not None
    assert mock_scheduled_job.id == "test-job-id"


def test_mock_async_client_fixture(mock_async_client):
    """Test mock_async_client fixture works."""
    assert mock_async_client is not None
    assert callable(mock_async_client.get)
    assert callable(mock_async_client.post)


def test_mock_smtp_server_fixture(mock_smtp_server):
    """Test mock_smtp_server fixture works."""
    assert mock_smtp_server is not None
    assert callable(mock_smtp_server.send_message)
