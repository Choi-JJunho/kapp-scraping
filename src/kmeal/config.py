"""데이터베이스 설정 및 구성"""
import os
from pathlib import Path
from dotenv import load_dotenv


def get_database_url():
  """데이터베이스 URL 생성"""
  # 환경변수 파일을 다시 로드하여 최신 값 확보
  env_path = Path(__file__).parent.parent.parent / 'kapp-config' / 'kapp-scraping' / '.env'
  load_dotenv(dotenv_path=env_path)

  # 환경변수 읽기
  host = os.getenv('DB_HOST') or 'localhost'
  port = os.getenv('DB_PORT') or '5432'
  database = os.getenv('DB_NAME') or 'kapp'
  username = os.getenv('DB_USERNAME') or 'postgres'
  password = os.getenv('DB_PASSWORD') or ''
  sslmode = os.getenv('DB_SSLMODE') or 'prefer'

  return f"postgresql://{username}:{password}@{host}:{port}/{database}?sslmode={sslmode}"
