"""데이터베이스 모델 정의"""

import hashlib
from datetime import datetime

from sqlalchemy import Column, BigInteger, Date, String, Integer, \
  DateTime, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

Base = declarative_base()


class User(Base):
  """사용자 테이블 모델"""
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
  """식단 테이블 모델"""
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

  # 관계 설정
  menu_items = relationship("MealMenuItem", back_populates="meal",
                            cascade="all, delete-orphan")


class MealMenuItem(Base):
  """식단 메뉴 아이템 테이블 모델"""
  __tablename__ = 'meal_menu_items'

  meal_id = Column(BigInteger, ForeignKey('meals.id', ondelete='CASCADE'),
                   nullable=False, primary_key=True)
  menu_item = Column(String(200), nullable=False, primary_key=True)

  # 관계 설정
  meal = relationship("MealDB", back_populates="menu_items")


class MenuEntity:
  """Holds the information for a single meal menu."""

  def __init__(self, date, dining_time, place, price, kcal, menu):
    self.date = date
    self.dining_time = dining_time
    self.place = place
    self.price = price or 0
    self.kcal = kcal or 0
    self.menu = menu
    self.id = self._generate_id()

  def _generate_id(self):
    """고유 ID 생성 (date + dining_time + place의 해시 기반)"""
    unique_string = f"{self.date}_{self.dining_time}_{self.place}"
    return int(hashlib.md5(unique_string.encode()).hexdigest()[:15], 16)

  def __repr__(self):
    """Provides a clean string representation of the menu."""
    menu_str = ", ".join(self.menu)
    return (f"[{self.dining_time}/{self.place}] {menu_str} "
            f"({self.kcal} kcal, {self.price} won)")

  def to_db_model(self):
    """데이터베이스 모델로 변환"""
    # 문자열 날짜를 datetime.date로 변환
    if isinstance(self.date, str):
      date_obj = datetime.strptime(self.date, '%Y-%m-%d').date()
    else:
      date_obj = self.date

    # 안전한 정수 변환 함수
    def safe_int_convert(value, default=0):
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
