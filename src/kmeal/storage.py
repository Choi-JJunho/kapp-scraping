"""데이터 저장 모듈.

식단 데이터를 다양한 형식(PostgreSQL, CSV, JSON)으로 저장하는 기능을 제공합니다.
중복 데이터 방지 및 트랜잭션 관리 기능을 포함합니다.

주요 기능:
  - PostgreSQL 데이터베이스 저장 (중복 체크 포함)
  - CSV 파일 저장 (Excel 호환)
  - JSON 파일 저장 (UTF-8, 한글 지원)
  - 일괄 저장 (모든 형식 동시 저장)
"""

import csv
import json
import logging
from pathlib import Path
from typing import List, Optional

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.engine import Engine

from .config import get_database_url
from .models import Base, MealDB, MealMenuItem, MenuEntity

logger = logging.getLogger(__name__)


class MealStorage:
  """식단 데이터를 다양한 형식으로 저장하는 클래스.

  PostgreSQL 데이터베이스, CSV, JSON 형식으로 식단 데이터를 저장할 수 있습니다.
  데이터베이스 저장 시 자동으로 중복을 체크하여 동일한 식단이 여러 번
  저장되는 것을 방지합니다.

  Attributes:
    engine (Optional[Engine]): SQLAlchemy 데이터베이스 엔진
    session (Optional[Session]): SQLAlchemy 데이터베이스 세션

  Example:
    >>> storage = MealStorage()
    >>> storage.initialize_database()
    >>> storage.save_to_database(menu_entities)
    >>> storage.close()
  """

  def __init__(self) -> None:
    """MealStorage 인스턴스를 생성합니다.

    데이터베이스 연결은 지연 초기화되므로,
    initialize_database()를 호출하여 초기화해야 합니다.
    """
    self.engine: Optional[Engine] = None
    self.session: Optional[Session] = None

  def initialize_database(self) -> None:
    """PostgreSQL 데이터베이스 연결을 초기화하고 테이블을 생성합니다.

    환경변수로부터 데이터베이스 설정을 읽어와 SQLAlchemy 엔진과 세션을 생성합니다.
    필요한 테이블이 존재하지 않는 경우 자동으로 생성합니다.

    Side Effects:
      - self.engine과 self.session이 초기화됩니다
      - 데이터베이스에 테이블이 생성될 수 있습니다

    Example:
      >>> storage = MealStorage()
      >>> storage.initialize_database()
      🔗 Attempting to connect to database: postgresql://...
    """
    database_url: str = get_database_url()
    print(f"🔗 Attempting to connect to database: {database_url}")
    self.engine = create_engine(database_url, echo=False)

    # 테이블 생성 (존재하지 않는 경우)
    Base.metadata.create_all(self.engine)

    # 세션 생성
    SessionLocal = sessionmaker(bind=self.engine)
    self.session = SessionLocal()

  def save_to_database(self, menus: List[MenuEntity]) -> int:
    """식단 데이터를 PostgreSQL 데이터베이스에 저장합니다.

    MenuEntity 리스트를 MealDB와 MealMenuItem 모델로 변환하여 저장합니다.
    ID 기반 중복 체크를 수행하여 이미 존재하는 식단은 건너뜁니다.
    개별 저장 실패는 롤백되며 전체 프로세스를 중단하지 않습니다.

    Args:
      menus: 저장할 MenuEntity 리스트

    Returns:
      int: 실제로 저장된 식단 개수

    Example:
      >>> storage = MealStorage()
      >>> saved = storage.save_to_database(menu_list)
      💾 Database: Saved 15 new entries (3 duplicates skipped)
      >>> print(f"저장 완료: {saved}개")
      저장 완료: 15개
    """
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

  def save_to_csv(
      self,
      menus: List[MenuEntity],
      filename: str = "koreatech_meals_2025.csv"
  ) -> None:
    """식단 데이터를 CSV 파일로 저장합니다.

    UTF-8 with BOM 인코딩을 사용하여 Excel에서도 한글이 정상적으로
    표시되도록 합니다. 메뉴 아이템은 세미콜론(;)으로 구분하여 하나의 필드에 저장합니다.

    Args:
      menus: 저장할 MenuEntity 리스트
      filename: 저장할 CSV 파일 경로 (기본값: koreatech_meals_2025.csv)

    CSV 형식:
      date, dining_time, place, price, kcal, menu_items
      2025-01-15, lunch, Korean Food (한식), 5000, 650, 김치찌개; 밥; 김치

    Example:
      >>> storage = MealStorage()
      >>> storage.save_to_csv(menu_list, "meals.csv")
      💾 Saved 20 menu entries to meals.csv
    """
    if not menus:
      print("No menu data to save.")
      return

    filepath: Path = Path(filename)

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

  def save_to_json(
      self,
      menus: List[MenuEntity],
      filename: str = "koreatech_meals_2025.json"
  ) -> None:
    """식단 데이터를 JSON 파일로 저장합니다.

    UTF-8 인코딩으로 한글을 그대로 저장하며, 들여쓰기를 사용하여
    사람이 읽기 쉬운 형식으로 저장합니다.

    Args:
      menus: 저장할 MenuEntity 리스트
      filename: 저장할 JSON 파일 경로 (기본값: koreatech_meals_2025.json)

    JSON 구조:
      [
        {
          "date": "2025-01-15",
          "dining_time": "lunch",
          "place": "Korean Food (한식)",
          "price": 5000,
          "kcal": 650,
          "menu": ["김치찌개", "밥", "김치"]
        }
      ]

    Example:
      >>> storage = MealStorage()
      >>> storage.save_to_json(menu_list, "meals.json")
      💾 Saved 20 menu entries to meals.json
    """
    if not menus:
      print("No menu data to save.")
      return

    filepath: Path = Path(filename)

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

  def save_all_formats(self, menus: List[MenuEntity]) -> int:
    """식단 데이터를 모든 형식(CSV, JSON, Database)으로 동시에 저장합니다.

    CSV와 JSON 파일을 먼저 저장한 후 데이터베이스에 저장합니다.
    파일 저장은 항상 성공하지만, 데이터베이스는 중복 체크가 수행됩니다.

    Args:
      menus: 저장할 MenuEntity 리스트

    Returns:
      int: 데이터베이스에 실제로 저장된 식단 개수

    Example:
      >>> storage = MealStorage()
      >>> saved = storage.save_all_formats(menu_list)
      💾 Saving 20 menu entries to all formats...
      💾 Saved 20 menu entries to koreatech_meals_2025.csv
      💾 Saved 20 menu entries to koreatech_meals_2025.json
      💾 Database: Saved 15 new entries (5 duplicates skipped)
      >>> print(f"DB 저장: {saved}개")
      DB 저장: 15개
    """
    if not menus:
      print("No menu data to save.")
      return 0

    print(f"\n💾 Saving {len(menus)} menu entries to all formats...")

    # Save to files
    self.save_to_csv(menus, "koreatech_meals_2025.csv")
    self.save_to_json(menus, "koreatech_meals_2025.json")

    # Save to database
    saved_count: int = self.save_to_database(menus)

    return saved_count

  def close(self) -> None:
    """데이터베이스 세션을 종료하고 리소스를 정리합니다.

    데이터베이스 작업이 완료되면 반드시 호출하여
    연결을 정리해야 합니다.

    Example:
      >>> storage = MealStorage()
      >>> storage.initialize_database()
      >>> # ... 작업 수행 ...
      >>> storage.close()
    """
    if self.session:
      self.session.close()
