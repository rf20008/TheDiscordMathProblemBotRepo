import pathlib
import datetime
from unittest.mock import patch
import pytest

from helpful_modules._error_logging import log_error, log_error_to_file

# Assuming your code is imported or defined above, e.g.:
# from your_module import log_error_to_file, log_error
@pytest.fixture(autouse=True)
def setup_error_logs_dir(fs):
    """Automatically create the error_logs directory in the fake filesystem for every test."""
    fs.create_dir("error_logs")
def test_log_error_to_file_custom_path(fs):
    """Test that errors are correctly logged to a specified custom file path."""
    fs.create_dir("custom_logs")
    test_file = pathlib.Path("custom_logs/custom_log.txt")
    err = ValueError("Custom path test exception")

    log_error_to_file(err, file_path=str(test_file))

    assert test_file.exists()
    content = test_file.read_text()
    assert "ValueError: Custom path test exception" in content


def test_invalid_file_path_type():
    """Test that passing a non-string file_path raises a TypeError."""
    err = ValueError("Test exception")
    with pytest.raises(TypeError):
        log_error_to_file(err, file_path=123)


def test_invalid_error_type():
    """Test that passing a non-exception object as the error raises a TypeError."""
    with pytest.raises(TypeError):
        log_error_to_file("not an error object", file_path="test.txt")


@patch('helpful_modules._error_logging.datetime')
def test_default_file_path_generation_with_fakefs(mock_datetime, fs):

    """Test that default file path generation works seamlessly using the pyfakefs (fs) fixture."""
    mock_now = datetime.datetime(2026, 8, 15, 12, 0, 0)
    mock_datetime.datetime.now.return_value = mock_now

    err = RuntimeError("Default path test exception")
    expected_path = "error_logs/2026 August 15.txt"

    # Call the function (it hardcodes writing to "error_logs/", intercepted by pyfakefs)
    log_error_to_file(err, file_path="")

    # Assertions on the fake filesystem
    assert fs.exists(expected_path)

    with open(expected_path, "r") as f:
        content = f.read()
        assert "RuntimeError: Default path test exception" in content


@pytest.mark.asyncio
async def test_log_error_webhook_not_implemented():
    """Test that the async wrapper raises NotImplementedError when send_to_webhook is True."""
    err = RuntimeError("Webhook test")

    with pytest.raises(NotImplementedError):
        await log_error(err, send_to_webhook=True)