"""데이터베이스 설정 및 구성 모듈.

이 모듈은 PostgreSQL 데이터베이스 연결을 위한 URL을 생성하는 기능을 제공합니다.
환경변수로부터 데이터베이스 설정을 읽어와 SQLAlchemy 연결 문자열을 생성합니다.
"""

import os
from pathlib import Path
from typing import Optional
from dotenv import load_dotenv


def get_database_url() -> str:
  """환경변수로부터 PostgreSQL 데이터베이스 연결 URL을 생성합니다.

  kapp-config/kapp-scraping/.env 파일에서 데이터베이스 설정을 읽어옵니다.
  필요한 환경변수가 없는 경우 기본값을 사용합니다.

  환경변수:
    DB_HOST: 데이터베이스 호스트 주소 (기본값: localhost)
    DB_PORT: 데이터베이스 포트 번호 (기본값: 5432)
    DB_NAME: 데이터베이스 이름 (기본값: kapp)
    DB_USERNAME: 데이터베이스 사용자명 (기본값: postgres)
    DB_PASSWORD: 데이터베이스 비밀번호 (기본값: 빈 문자열)
    DB_SSLMODE: SSL 연결 모드 (기본값: prefer)

  Returns:
    str: SQLAlchemy 호환 PostgreSQL 연결 URL
         형식: postgresql://username:password@host:port/database?sslmode=mode

  Example:
    >>> url = get_database_url()
    >>> print(url)
    postgresql://postgres:mypass@localhost:5432/kapp?sslmode=prefer
  """
  # 환경변수 파일을 다시 로드하여 최신 값 확보
  env_path: Path = Path(__file__).parent.parent.parent / 'kapp-config' / 'kapp-scraping' / '.env'
  load_dotenv(dotenv_path=env_path)

  # 환경변수 읽기 (기본값 제공)
  host: str = os.getenv('DB_HOST') or 'localhost'
  port: str = os.getenv('DB_PORT') or '5432'
  database: str = os.getenv('DB_NAME') or 'kapp'
  username: str = os.getenv('DB_USERNAME') or 'postgres'
  password: str = os.getenv('DB_PASSWORD') or ''
  sslmode: str = os.getenv('DB_SSLMODE') or 'prefer'

  return f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
