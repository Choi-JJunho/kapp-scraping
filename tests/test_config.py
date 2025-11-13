"""config.py 모듈 테스트."""

import os
from unittest.mock import patch

import pytest

from src.kmeal.config import get_database_url


class TestGetDatabaseUrl:
    """get_database_url 함수 테스트."""

    def test_get_database_url_with_all_env_vars(self, monkeypatch):
        """모든 환경변수가 설정된 경우 테스트."""
        # 환경변수 설정
        monkeypatch.setenv('DB_HOST', 'test-host')
        monkeypatch.setenv('DB_PORT', '5433')
        monkeypatch.setenv('DB_NAME', 'test-db')
        monkeypatch.setenv('DB_USERNAME', 'test-user')
        monkeypatch.setenv('DB_PASSWORD', 'test-password')
        monkeypatch.setenv('DB_SSLMODE', 'require')

        url = get_database_url()

        assert url == 'postgresql://test-user:test-password@test-host:5433/test-db?sslmode=require'

    def test_get_database_url_with_default_values(self, monkeypatch):
        """환경변수가 없을 때 기본값 사용 테스트."""
        # 모든 환경변수 제거
        monkeypatch.delenv('DB_HOST', raising=False)
        monkeypatch.delenv('DB_PORT', raising=False)
        monkeypatch.delenv('DB_NAME', raising=False)
        monkeypatch.delenv('DB_USERNAME', raising=False)
        monkeypatch.delenv('DB_PASSWORD', raising=False)
        monkeypatch.delenv('DB_SSLMODE', raising=False)

        url = get_database_url()

        assert url == 'postgresql://postgres:@localhost:5432/kapp?sslmode=prefer'

    def test_get_database_url_with_partial_env_vars(self, monkeypatch):
        """일부 환경변수만 설정된 경우 테스트."""
        monkeypatch.setenv('DB_HOST', 'custom-host')
        monkeypatch.setenv('DB_NAME', 'custom-db')
        monkeypatch.delenv('DB_PORT', raising=False)
        monkeypatch.delenv('DB_USERNAME', raising=False)
        monkeypatch.delenv('DB_PASSWORD', raising=False)
        monkeypatch.delenv('DB_SSLMODE', raising=False)

        url = get_database_url()

        assert url == 'postgresql://postgres:@custom-host:5432/custom-db?sslmode=prefer'

    def test_get_database_url_return_type(self, monkeypatch):
        """반환 타입이 문자열인지 테스트."""
        url = get_database_url()

        assert isinstance(url, str)
        assert url.startswith('postgresql://')
