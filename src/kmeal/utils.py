"""유틸리티 함수 모듈.

애플리케이션 전반에서 사용되는 공통 유틸리티 함수들을 제공합니다.
현재는 로깅 시스템 설정 기능을 포함하고 있습니다.
"""

import logging
from datetime import datetime
from pathlib import Path


def setup_logging() -> logging.Logger:
  """파일과 콘솔에 동시 출력하는 로깅 시스템을 설정합니다.

  logs/ 디렉토리에 타임스탬프가 포함된 로그 파일을 생성하고,
  INFO 레벨 이상의 로그를 파일과 콘솔에 동시에 출력하도록 설정합니다.

  로그 파일명 형식: kmeal_scraping_YYYYMMDD_HHMMSS.log
  로그 메시지 형식: %(asctime)s - %(levelname)s - %(message)s

  Returns:
    logging.Logger: 설정된 로거 인스턴스

  Side Effects:
    - logs/ 디렉토리를 생성합니다 (존재하지 않는 경우)
    - 로그 파일을 생성합니다
    - 전역 로깅 설정을 변경합니다

  Example:
    >>> logger = setup_logging()
    >>> logger.info("애플리케이션이 시작되었습니다")
    2025-01-15 10:30:00 - INFO - 애플리케이션이 시작되었습니다
  """
  # logs 디렉토리가 없으면 생성
  logs_dir: Path = Path("logs")
  logs_dir.mkdir(exist_ok=True)

  # 타임스탬프가 포함된 로그 파일명 생성
  timestamp: str = datetime.now().strftime('%Y%m%d_%H%M%S')
  log_filename: str = f"kmeal_scraping_{timestamp}.log"
  log_filepath: Path = logs_dir / log_filename

  # 로깅 설정
  logging.basicConfig(
      level=logging.INFO,
      format='%(asctime)s - %(levelname)s - %(message)s',
      handlers=[
        logging.FileHandler(log_filepath, encoding='utf-8'),
        logging.StreamHandler()  # 콘솔 출력
      ]
  )

  logger: logging.Logger = logging.getLogger(__name__)
  logger.info(f"로깅 시스템 초기화 완료. 로그 파일: {log_filepath}")

  return logger
