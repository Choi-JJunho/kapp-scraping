"""데이터베이스 모델 및 엔티티 정의 모듈.

이 모듈은 식단 데이터를 저장하기 위한 SQLAlchemy 모델과
크롤링 데이터를 처리하기 위한 비즈니스 엔티티를 정의합니다.

주요 클래스:
  - User: 사용자 정보 테이블 모델
  - MealDB: 식단 정보 테이블 모델
  - MealMenuItem: 식단 메뉴 아이템 테이블 모델
  - MenuEntity: 크롤링된 식단 데이터를 표현하는 비즈니스 엔티티
"""

import hashlib
from datetime import datetime, date
from typing import List, Tuple, Union, Optional, Any

from sqlalchemy import Column, BigInteger, Date, String, Integer, \
  DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
  """사용자 정보를 저장하는 데이터베이스 테이블 모델.

  코리아텍 포털 사용자 정보를 관리합니다.
  현재는 식단 크롤링에 직접 사용되지 않지만, 향후 사용자별
  식단 관리 기능 구현을 위해 정의되어 있습니다.

  Attributes:
    id: 사용자 고유 식별자 (기본키)
    email: 사용자 이메일 주소 (고유값)
    password: 암호화된 비밀번호
    name: 사용자 이름
    student_employee_id: 학번 또는 교직원 번호
    created_at: 계정 생성 일시 (자동 생성)
    updated_at: 최근 수정 일시 (자동 갱신)
  """
  __tablename__ = 'users'

  id = Column(BigInteger, primary_key=True)
  email = Column(String(255), nullable=False, unique=True)
  password = Column(String(255), nullable=False)
  name = Column(String(100), nullable=False)
  student_employee_id = Column(String(50), nullable=False)
  created_at = Column(DateTime, nullable=False, server_default=func.now())
  updated_at = Column(DateTime, nullable=False, server_default=func.now(),
                      onupdate=func.now())


class MealDB(Base):
  """식단 기본 정보를 저장하는 데이터베이스 테이블 모델.

  각 식사(아침/점심/저녁)의 기본 정보를 저장합니다.
  메뉴 아이템은 별도의 MealMenuItem 테이블에 정규화되어 저장됩니다.

  고유 ID는 날짜, 식사시간, 장소의 조합으로 생성된 MD5 해시값을 사용하여
  동일한 식단의 중복 저장을 방지합니다.

  Attributes:
    id: 식단 고유 식별자 (MD5 해시 기반, 기본키)
    date: 식단 제공 날짜
    dining_time: 식사 시간 (breakfast, lunch, dinner)
    place: 식당 이름
    price: 가격 (원)
    kcal: 열량 (kcal)
    created_at: 레코드 생성 일시 (자동 생성)
    updated_at: 최근 수정 일시 (자동 갱신)
    menu_items: 연결된 메뉴 아이템 목록 (One-to-Many 관계)
  """
  __tablename__ = 'meals'

  id = Column(BigInteger, primary_key=True)
  date = Column(Date, nullable=False)
  dining_time = Column(String(20), nullable=False)
  place = Column(String(100), nullable=False)
  price = Column(Integer, nullable=False)
  kcal = Column(Integer, nullable=False)
  created_at = Column(DateTime, nullable=False, server_default=func.now())
  updated_at = Column(DateTime, nullable=False, server_default=func.now(),
                      onupdate=func.now())

  # 관계 설정: 식단 삭제 시 연결된 메뉴 아이템도 함께 삭제 (CASCADE)
  menu_items = relationship("MealMenuItem", back_populates="meal",
                            cascade="all, delete-orphan")


class MealMenuItem(Base):
  """식단의 개별 메뉴 아이템을 저장하는 데이터베이스 테이블 모델.

  각 식단에 포함된 메뉴 항목들을 정규화하여 저장합니다.
  복합 기본키(meal_id, menu_item)를 사용하여 동일 식단에서
  같은 메뉴 아이템이 중복 저장되는 것을 방지합니다.

  Attributes:
    meal_id: 식단 외래키 (MealDB.id 참조, CASCADE 삭제)
    menu_item: 메뉴 아이템 이름 (예: "김치찌개", "밥", "김치")
    meal: 연결된 식단 정보 (Many-to-One 관계)

  Note:
    복합 기본키: (meal_id, menu_item)
    예: (12345, "김치찌개"), (12345, "밥")
  """
  __tablename__ = 'meal_menu_items'

  meal_id = Column(BigInteger, ForeignKey('meals.id', ondelete='CASCADE'),
                   nullable=False, primary_key=True)
  menu_item = Column(String(200), nullable=False, primary_key=True)

  # 관계 설정
  meal = relationship("MealDB", back_populates="menu_items")


class MenuEntity:
  """크롤링된 식단 데이터를 표현하는 비즈니스 엔티티 클래스.

  코리아텍 포털에서 크롤링한 식단 정보를 메모리에 보관하는 데이터 객체입니다.
  데이터베이스 모델과는 별도로, 크롤링부터 저장까지의 중간 처리 과정에서
  사용됩니다.

  Attributes:
    date (str): 식단 제공 날짜 (형식: YYYY-MM-DD)
    dining_time (str): 식사 시간 (breakfast, lunch, dinner)
    place (str): 식당 이름
    price (int): 가격 (원)
    kcal (int): 열량 (kcal)
    menu (List[str]): 메뉴 아이템 리스트
    id (int): 자동 생성된 고유 식별자 (MD5 해시 기반)

  Example:
    >>> entity = MenuEntity(
    ...     date="2025-01-15",
    ...     dining_time="lunch",
    ...     place="Korean Food (한식)",
    ...     price="5000",
    ...     kcal="650",
    ...     menu=["김치찌개", "계란말이", "밥", "김치"]
    ... )
    >>> print(entity)
    [lunch/Korean Food (한식)] 김치찌개, 계란말이, 밥, 김치 (650 kcal, 5000 won)
  """

  def __init__(
      self,
      date: str,
      dining_time: str,
      place: str,
      price: Union[str, int],
      kcal: Union[str, int],
      menu: List[str]
  ) -> None:
    """MenuEntity 인스턴스를 생성합니다.

    Args:
      date: 식단 제공 날짜 (YYYY-MM-DD 형식)
      dining_time: 식사 시간 (breakfast, lunch, dinner)
      place: 식당 이름
      price: 가격 (원, 문자열 또는 정수)
      kcal: 열량 (kcal, 문자열 또는 정수)
      menu: 메뉴 아이템 리스트
    """
    self.date: str = date
    self.dining_time: str = dining_time
    self.place: str = place
    self.price: int = price or 0
    self.kcal: int = kcal or 0
    self.menu: List[str] = menu
    self.id: int = self._generate_id()

  def _generate_id(self) -> int:
    """날짜, 식사시간, 장소의 조합으로 고유 ID를 생성합니다.

    MD5 해시의 첫 15자리를 16진수 정수로 변환하여 사용합니다.
    이를 통해 동일한 식단(날짜+시간+장소)에 대한 중복 저장을 방지할 수 있습니다.

    Returns:
      int: 고유 식별자 (15자리 16진수의 정수 변환값)

    Example:
      >>> entity = MenuEntity("2025-01-15", "lunch", "한식", 5000, 650, ["김치"])
      >>> entity.id  # 예시값
      123456789012345
    """
    unique_string: str = f"{self.date}_{self.dining_time}_{self.place}"
    hash_hex: str = hashlib.md5(unique_string.encode()).hexdigest()[:15]
    return int(hash_hex, 16)

  def __repr__(self) -> str:
    """사람이 읽기 쉬운 문자열 표현을 반환합니다.

    Returns:
      str: 식단 정보의 요약 문자열

    Example:
      >>> entity = MenuEntity("2025-01-15", "lunch", "한식", 5000, 650, ["김치", "밥"])
      >>> repr(entity)
      '[lunch/한식] 김치, 밥 (650 kcal, 5000 won)'
    """
    menu_str: str = ", ".join(self.menu)
    return (f"[{self.dining_time}/{self.place}] {menu_str} "
            f"({self.kcal} kcal, {self.price} won)")

  def to_db_model(self) -> Tuple[MealDB, List[str]]:
    """MenuEntity를 SQLAlchemy 데이터베이스 모델로 변환합니다.

    문자열 형태의 날짜를 datetime.date 객체로 변환하고,
    가격과 칼로리 값을 안전하게 정수로 변환합니다.
    NULL, 빈 문자열, 하이픈 등은 0으로 변환됩니다.

    Returns:
      Tuple[MealDB, List[str]]: (MealDB 인스턴스, 메뉴 아이템 리스트) 튜플

    Example:
      >>> entity = MenuEntity("2025-01-15", "lunch", "한식", "5,000", "650", ["김치"])
      >>> meal_db, menu_items = entity.to_db_model()
      >>> meal_db.price
      5000
      >>> menu_items
      ['김치']
    """
    # 문자열 날짜를 datetime.date로 변환
    date_obj: date
    if isinstance(self.date, str):
      date_obj = datetime.strptime(self.date, '%Y-%m-%d').date()
    else:
      date_obj = self.date

    # 안전한 정수 변환 함수
    def safe_int_convert(value: Any, default: int = 0) -> int:
      """문자열을 정수로 안전하게 변환합니다.

      NULL, 빈 문자열, 하이픈 등의 특수값을 처리하고,
      숫자 형식의 문자열에서 콤마를 제거한 후 정수로 변환합니다.

      Args:
        value: 변환할 값 (문자열, 정수, None 등)
        default: 변환 실패 시 반환할 기본값

      Returns:
        int: 변환된 정수값 또는 기본값

      Example:
        >>> safe_int_convert("1,000")
        1000
        >>> safe_int_convert("NULL")
        0
        >>> safe_int_convert("-")
        0
      """
      if value in ['NULL', 'null', '', '-', None, 'None']:
        return default
      try:
        # 콤마 제거 (예: "1,000" -> "1000")
        if isinstance(value, str):
          value = value.replace(',', '').strip()
        return int(value)
      except (ValueError, TypeError):
        return default

    meal = MealDB(
        id=self.id,
        date=date_obj,
        dining_time=self.dining_time,
        place=self.place,
        price=safe_int_convert(self.price),
        kcal=safe_int_convert(self.kcal)
    )

    return meal, self.menu
