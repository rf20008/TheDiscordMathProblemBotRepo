from unittest.mock import patch, MagicMock
import pytest

from helpful_modules import actual_restarter

def test_start_raises_not_implemented():
    """Verify that calling start() raises NotImplementedError."""
    with pytest.raises(NotImplementedError) as exc_info:
        actual_restarter.start()
    assert "os.execv()" in str(exc_info.value)

@patch("helpful_modules.actual_restarter.os._exit")
@patch("helpful_modules.actual_restarter.multiprocessing.Process")
@patch("helpful_modules.actual_restarter.subprocess.Popen")
def test_main_block_execution(mock_popen, mock_process, mock_exit):
    """Test that main() correctly sets up subprocesses and processes without real execution."""
    mock_q = MagicMock()
    mock_q.pid = 999
    mock_popen.return_value = mock_q

    mock_sp = MagicMock()
    mock_process.return_value = mock_sp

    # Run the main function safely mocked
    actual_restarter.main()

    # Assert subprocess and multiprocessing were called correctly
    mock_popen.assert_called_once()
    mock_process.assert_called_once_with(target=actual_restarter.start)
    mock_sp.start.assert_called_once()
    mock_sp.join.assert_called_once_with(timeout=1.0)
    mock_sp.kill.assert_called_once()
    mock_exit.assert_called_once()  # Prevented accidental test runner exit