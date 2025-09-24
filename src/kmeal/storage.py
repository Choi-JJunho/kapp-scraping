"""데이터 저장 모듈"""

import csv
import json
import logging
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from .config import get_database_url
from .models import Base, MealDB, MealMenuItem

logger = logging.getLogger(__name__)


class MealStorage:
  """식단 데이터 저장 클래스"""

  def __init__(self):
    self.engine = None
    self.session = None

  def initialize_database(self):
    """데이터베이스 연결 초기화"""
    database_url = get_database_url()
    self.engine = create_engine(database_url, echo=False)

    # 테이블 생성 (존재하지 않는 경우)
    Base.metadata.create_all(self.engine)

    # 세션 생성
    Session = sessionmaker(bind=self.engine)
    self.session = Session()

  def save_to_database(self, menus):
    """Save menu data to PostgreSQL database."""
    if not menus:
      print("No menu data to save.")
      return 0

    if not self.session:
      self.initialize_database()

    saved_count = 0
    skipped_count = 0

    logger.info(f"📥 데이터베이스 저장 시작: {len(menus)}개 항목")

    for menu in menus:
      try:
        # MenuEntity를 데이터베이스 모델로 변환
        meal_db, menu_items = menu.to_db_model()

        # 중복 체크
        existing = self.session.query(MealDB).filter_by(id=meal_db.id).first()
        if existing:
          skipped_count += 1
          continue

        # 식단 정보 저장
        self.session.add(meal_db)
        self.session.flush()  # meal_db.id 생성을 위해 flush

        # 메뉴 아이템들 저장
        for menu_item in menu_items:
          menu_item_db = MealMenuItem(
              meal_id=meal_db.id,
              menu_item=menu_item
          )
          self.session.add(menu_item_db)

        saved_count += 1

      except Exception as e:
        logger.warning(f"개별 메뉴 저장 실패: {e}")
        self.session.rollback()
        continue

    # 변경사항 커밋
    self.session.commit()

    logger.info(f"💾 데이터베이스 저장 완료: {saved_count}개 저장, {skipped_count}개 건너뜀")
    print(
        f"💾 Database: Saved {saved_count} new entries ({skipped_count} duplicates skipped)")

    return saved_count

  def save_to_csv(self, menus, filename="koreatech_meals_2025.csv"):
    """Save menu data to CSV file."""
    if not menus:
      print("No menu data to save.")
      return

    filepath = Path(filename)

    with open(filepath, 'w', newline='', encoding='utf-8-sig') as csvfile:
      fieldnames = ['date', 'dining_time', 'place', 'price', 'kcal',
                    'menu_items']
      writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

      writer.writeheader()
      for menu in menus:
        writer.writerow({
          'date': menu.date,
          'dining_time': menu.dining_time,
          'place': menu.place,
          'price': menu.price,
          'kcal': menu.kcal,
          'menu_items': '; '.join(menu.menu)
        })

    print(f"\n💾 Saved {len(menus)} menu entries to {filepath}")

  def save_to_json(self, menus, filename="koreatech_meals_2025.json"):
    """Save menu data to JSON file."""
    if not menus:
      print("No menu data to save.")
      return

    filepath = Path(filename)

    menu_data = []
    for menu in menus:
      menu_data.append({
        'date': menu.date,
        'dining_time': menu.dining_time,
        'place': menu.place,
        'price': menu.price,
        'kcal': menu.kcal,
        'menu': menu.menu
      })

    with open(filepath, 'w', encoding='utf-8') as jsonfile:
      json.dump(menu_data, jsonfile, ensure_ascii=False, indent=2)

    print(f"💾 Saved {len(menus)} menu entries to {filepath}")

  def save_all_formats(self, menus):
    """Save menu data to all formats: database, CSV, and JSON."""
    if not menus:
      print("No menu data to save.")
      return 0

    print(f"\n💾 Saving {len(menus)} menu entries to all formats...")

    # Save to database
    saved_count = self.save_to_database(menus)

    # Save to files
    self.save_to_csv(menus, "koreatech_meals_2025.csv")
    self.save_to_json(menus, "koreatech_meals_2025.json")

    return saved_count

  def close(self):
    """데이터베이스 연결 종료"""
    if self.session:
      self.session.close()
