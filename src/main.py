#!/usr/bin/env python3
"""코리아텍 식단 크롤링 메인 실행 스크립트"""
import os
import sys
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

# 프로젝트 루트 경로 설정
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from src.kmeal.crawler import KoreatechMealCrawler
from src.kmeal.storage import MealStorage
from src.kmeal.utils import setup_logging

def main():
  """메인 실행 함수"""
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
    print("🔐 Starting authentication...")
    crawler = KoreatechMealCrawler(PORTAL_ID, PORTAL_PW, YOUR_IP_ADDRESS)
    crawler.portal_login()

    # 2. 날짜 범위 설정
    start_date = datetime(2025, 1, 1)  # January 1, 2025
    end_date = datetime(2025, 10, 1)  # October 1, 2025

    print(
        f"\n📅 Fetching meal data from {start_date.strftime('%Y-%m-%d')} to {end_date.strftime('%Y-%m-%d')}")
    print(f"📊 Total days to process: {(end_date - start_date).days + 1}")

    # 3. 사용자 확인
    user_input = input(
        "\nThis will take a long time. Continue? (y/N): ").strip().lower()
    if user_input not in ['y', 'yes']:
      print("Operation cancelled.")
      return

    # 4. 식단 정보 크롤링
    print("\n🍽️ Starting meal data collection...")
    all_meals = crawler.get_meals_for_date_range(start_date, end_date)

    # 5. 결과 저장
    if not all_meals:
      print("\n❌ No meal data found for 2025.")
    else:
      print(f"\n✅ Successfully collected {len(all_meals)} meal entries!")

      # 저장소 초기화 및 저장
      storage = MealStorage()
      saved_count = storage.save_all_formats(all_meals)
      storage.close()

      # 샘플 결과 출력
      print(f"\n📋 Sample results (first 5 entries):")
      for menu in all_meals[:5]:
        print(f"  {menu}")

      if len(all_meals) > 5:
        print(f"  ... and {len(all_meals) - 5} more entries")

  except KeyboardInterrupt:
    print("\n\n⏹️ Operation interrupted by user.")
  except Exception as e:
    logger.error(f"실행 중 오류 발생: {e}")
    print(f"\n❌ An error occurred: {e}")


if __name__ == "__main__":
  # .env 파일 경로를 kapp-config/kapp-scraping/.env로 설정
  env_path = Path(__file__).parent.parent / 'kapp-config' / 'kapp-scraping' / '.env'
  load_dotenv(dotenv_path=env_path)
  main()
