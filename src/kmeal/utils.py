"""유틸리티 함수들"""

import logging
from datetime import datetime
from pathlib import Path


def setup_logging():
  """파일과 콘솔 출력을 위한 로깅 설정"""
  # logs 디렉토리가 없으면 생성
  logs_dir = Path("logs")
  logs_dir.mkdir(exist_ok=True)

  # 타임스탬프가 포함된 로그 파일명 생성
  log_filename = f"kmeal_scraping_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"
  log_filepath = logs_dir / log_filename

  # 로깅 설정
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(levelname)s - %(message)s',
      handlers=[
        logging.FileHandler(log_filepath, encoding='utf-8'),
        logging.StreamHandler()  # 콘솔 출력
      ]
  )

  logger = logging.getLogger(__name__)
  logger.info(f"로깅 시스템 초기화 완료. 로그 파일: {log_filepath}")
  return logger
