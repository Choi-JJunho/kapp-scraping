#!/usr/bin/env python3
"""코리아텍 식단 크롤링 메인 실행 스크립트.

코리아텍 포털에서 식단 정보를 크롤링하여 데이터베이스와 파일로 저장합니다.

실행 모드:
  - 일반 모드: 오늘 기준 2주 전 ~ 2주 후 (총 29일)
  - 초기화 모드 (--init): 올해 1월 1일 ~ 한 달 후
  - 테스트 모드 (--test): 오늘 하루만

사용 예시:
  python src/main.py              # 일반 모드
  python src/main.py --init       # 초기화 모드
  python src/main.py --test       # 테스트 모드
"""

import argparse
import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

from dotenv import load_dotenv

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.kmeal.crawler import KoreatechMealCrawler
from src.kmeal.storage import MealStorage
from src.kmeal.utils import setup_logging


def main() -> None:
  """메인 실행 함수.

  명령행 인자를 파싱하고, 환경변수를 확인한 후,
  크롤링 → 저장의 전체 프로세스를 실행합니다.

  프로세스:
    1. 명령행 인자 파싱 (--init, --test)
    2. 로깅 시스템 초기화
    3. 환경변수 확인 (PORTAL_ID, PORTAL_PW, YOUR_IP_ADDRESS)
    4. 포털 로그인
    5. 날짜 범위 설정
    6. 식단 데이터 크롤링
    7. 데이터 저장 (CSV, JSON, Database)
    8. 결과 출력

  Raises:
    KeyboardInterrupt: 사용자가 Ctrl+C로 중단한 경우
    Exception: 실행 중 발생한 기타 예외
  """
  # 명령행 인자 파싱
  parser = argparse.ArgumentParser(
      description='코리아텍 식단 크롤링',
      epilog='예시: python src/main.py --test'
  )
  parser.add_argument(
      '--init',
      action='store_true',
      help='초기 데이터 수집 모드 (올해 1월 1일부터 한 달 후까지)'
  )
  parser.add_argument(
      '--test',
      action='store_true',
      help='테스트 모드 (오늘 하루치만 스크래핑)'
  )
  args = parser.parse_args()

  # 로깅 설정
  logger = setup_logging()

  # 환경변수 로드
  PORTAL_ID = os.getenv('PORTAL_ID')
  PORTAL_PW = os.getenv('PORTAL_PW')
  YOUR_IP_ADDRESS = os.getenv('YOUR_IP_ADDRESS')

  if not all([PORTAL_ID, PORTAL_PW, YOUR_IP_ADDRESS]):
    print("❌ 환경변수가 설정되지 않았습니다!")
    print(f"PORTAL_ID: {PORTAL_ID}")
    print(f"PORTAL_PW: {'*' * len(PORTAL_PW) if PORTAL_PW else None}")
    print(f"YOUR_IP_ADDRESS: {YOUR_IP_ADDRESS}")
    print("\n.env 파일을 확인하세요.")
    return

  try:
    # 1. 크롤러 초기화 및 로그인
    print("🔐 인증을 시작합니다...")
    crawler = KoreatechMealCrawler(PORTAL_ID, PORTAL_PW, YOUR_IP_ADDRESS)
    crawler.portal_login()

    # 2. 날짜 범위 설정
    today = datetime.now()

    if args.init:
      # 초기 데이터 수집: 올해 1월 1일부터 오늘로부터 한 달 후까지
      start_date = datetime(today.year, 1, 1)
      end_date = today + timedelta(days=30)
      print("📅 초기 데이터 수집 모드")
    elif args.test:
      # 테스트 모드: 오늘 하루치만
      start_date = today
      end_date = today
      print("📅 테스트 모드 (오늘 하루치만)")
    else:
      # 일반 모드: 오늘 기준 2주 전부터 2주 후까지
      start_date = today - timedelta(weeks=2)
      end_date = today + timedelta(weeks=2)
      print("📅 일반 데이터 수집 모드")

    print(
        f"\n📅 {start_date.strftime('%Y-%m-%d')}부터 {end_date.strftime('%Y-%m-%d')}까지 식단 데이터를 수집합니다")
    print(f"📊 처리할 총 일수: {(end_date - start_date).days + 1}일")

    # 3. 사용자 확인
    if args.test:
      print("\n🧪 테스트 모드: 자동으로 진행합니다.")
    else:
      user_input = input(
          "\n시간이 오래 걸릴 수 있습니다. 계속하시겠습니까? (y/N): ").strip().lower()
      if user_input not in ['y', 'yes']:
        print("작업이 취소되었습니다.")
        return

    # 4. 식단 정보 크롤링
    print("\n🍽️ 식단 데이터 수집을 시작합니다...")
    all_meals = crawler.get_meals_for_date_range(start_date, end_date)

    # 5. 결과 저장
    if not all_meals:
      print("\n❌ 2025년 식단 데이터를 찾을 수 없습니다.")
    else:
      print(f"\n✅ 총 {len(all_meals)}개의 식단 정보를 성공적으로 수집했습니다!")

      # 저장소 초기화 및 저장
      storage = MealStorage()
      storage.save_all_formats(all_meals)
      storage.close()

      # 샘플 결과 출력
      print("\n📋 샘플 결과 (처음 5개 항목):")
      for menu in all_meals[:5]:
        print(f"  {menu}")
        print(f"    - 가격: {menu.price} (타입: {type(menu.price)})")
        print(f"    - 칼로리: {menu.kcal} (타입: {type(menu.kcal)})")

      if len(all_meals) > 5:
        print(f"  ... 그리고 {len(all_meals) - 5}개 더")

  except KeyboardInterrupt:
    print("\n\n⏹️ 사용자에 의해 작업이 중단되었습니다.")
  except Exception as e:
    logger.error(f"실행 중 오류 발생: {e}")
    print(f"\n❌ 오류가 발생했습니다: {e}")


if __name__ == "__main__":
  # .env 파일 경로를 kapp-config/kapp-scraping/.env로 설정
  env_path = Path(__file__).parent.parent / 'kapp-config' / 'kapp-scraping' / '.env'
  load_dotenv(dotenv_path=env_path)
  main()
