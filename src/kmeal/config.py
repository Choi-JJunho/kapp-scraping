"""데이터베이스 설정 및 구성"""
import os

# Database Configuration
DATABASE_CONFIG = {
  'driver': 'postgresql',
  'host': os.getenv('DB_HOST'),
  'port': os.getenv('DB_PORT'),
  'database': os.getenv('DB_NAME'),
  'username': os.getenv('DB_USERNAME'),
  'password': os.getenv('DB_PASSWORD'),
  'sslmode': os.getenv('DB_SSLMODE')
}


def get_database_url():
  """데이터베이스 URL 생성"""
  config = DATABASE_CONFIG
  return f"postgresql://{config['username']}:{config['password']}@{config['host']}:{config['port']}/{config['database']}?sslmode={config['sslmode']}"
