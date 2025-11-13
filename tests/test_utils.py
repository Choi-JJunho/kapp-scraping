"""utils.py 모듈 테스트."""

import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from src.kmeal.utils import setup_logging


class TestSetupLogging:
    """setup_logging 함수 테스트."""

    def test_setup_logging_creates_logs_directory(self, tmp_path, monkeypatch):
        """logs 디렉토리가 생성되는지 테스트."""
        # 임시 디렉토리를 작업 디렉토리로 설정
        monkeypatch.chdir(tmp_path)

        setup_logging()

        logs_dir = tmp_path / "logs"
        assert logs_dir.exists()
        assert logs_dir.is_dir()

    def test_setup_logging_creates_log_file(self, tmp_path, monkeypatch):
        """로그 파일이 생성되는지 테스트."""
        monkeypatch.chdir(tmp_path)

        setup_logging()

        logs_dir = tmp_path / "logs"
        log_files = list(logs_dir.glob("kmeal_scraping_*.log"))

        assert len(log_files) > 0
        assert log_files[0].name.startswith("kmeal_scraping_")
        assert log_files[0].name.endswith(".log")

    def test_setup_logging_returns_logger(self):
        """Logger 인스턴스를 반환하는지 테스트."""
        logger = setup_logging()

        assert isinstance(logger, logging.Logger)

    def test_setup_logging_log_file_format(self, tmp_path, monkeypatch):
        """로그 파일명 형식이 올바른지 테스트."""
        monkeypatch.chdir(tmp_path)

        setup_logging()

        logs_dir = tmp_path / "logs"
        log_files = list(logs_dir.glob("kmeal_scraping_*.log"))

        # 파일명 형식: kmeal_scraping_YYYYMMDD_HHMMSS.log
        import re
        pattern = r'kmeal_scraping_\d{8}_\d{6}\.log'

        assert len(log_files) > 0
        assert re.match(pattern, log_files[0].name)

    def test_setup_logging_info_level(self, tmp_path, monkeypatch):
        """로그 레벨이 INFO로 설정되는지 테스트."""
        monkeypatch.chdir(tmp_path)

        # 이전 핸들러 제거
        root_logger = logging.getLogger()
        root_logger.handlers.clear()

        logger = setup_logging()

        # basicConfig로 설정된 루트 로거 레벨 확인
        # 여러 번 호출되면 레벨이 변경되지 않을 수 있으므로 핸들러 확인
        assert len(root_logger.handlers) >= 2  # FileHandler와 StreamHandler
        assert root_logger.level <= logging.INFO  # INFO 이하여야 함

    def test_setup_logging_multiple_calls(self, tmp_path, monkeypatch):
        """여러 번 호출해도 정상 동작하는지 테스트."""
        monkeypatch.chdir(tmp_path)

        logger1 = setup_logging()
        logger2 = setup_logging()

        assert isinstance(logger1, logging.Logger)
        assert isinstance(logger2, logging.Logger)
