# tests/test_housekeeping.py
import os
import time
import pytest
from unittest.mock import patch, MagicMock
from scripts.housekeeping import prune_database, prune_logs, check_mosquitto_health

def test_prune_database_dry_run():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.fetchone.return_value = [42]

    with patch("scripts.housekeeping.get_db_connection", return_value=mock_conn):
        count = prune_database(days=7, dry_run=True)
        assert count == 42
        mock_cur.execute.assert_called_once()
        assert "SELECT COUNT(*)" in mock_cur.execute.call_args[0][0]

def test_prune_database_execution():
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value.__enter__.return_value = mock_cur
    mock_cur.rowcount = 15

    with patch("scripts.housekeeping.get_db_connection", return_value=mock_conn):
        count = prune_database(days=7, dry_run=False)
        assert count == 15
        mock_cur.execute.assert_called_once()
        assert "DELETE FROM light_events" in mock_cur.execute.call_args[0][0]
        mock_conn.commit.assert_called_once()

def test_prune_logs(tmp_path):
    logs_dir = tmp_path / "logs"
    logs_dir.mkdir()
    
    old_log = logs_dir / "test.log.1"
    old_log.write_text("old content")
    # Altera mtime para 10 dias atrás
    ten_days_ago = time.time() - (10 * 86400)
    os.utime(old_log, (ten_days_ago, ten_days_ago))

    new_log = logs_dir / "test.log.2"
    new_log.write_text("new content")

    with patch("scripts.housekeeping.PROJECT_ROOT", str(tmp_path)):
        deleted = prune_logs(days=7, dry_run=False)
        assert deleted >= 1
        assert not old_log.exists()
        assert new_log.exists()

def test_check_mosquitto_health():
    with patch("os.path.exists", return_value=True), patch("os.stat") as mock_stat, patch("os.path.getsize", return_value=2048):
        mock_stat.return_value.st_mode = 0o755
        # Não deve lançar exceções
        check_mosquitto_health(dry_run=True)
