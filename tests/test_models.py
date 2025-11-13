"""models.py 모듈 테스트."""

from datetime import datetime, date

import pytest

from src.kmeal.models import MenuEntity, MealDB, MealMenuItem, User


class TestMenuEntity:
    """MenuEntity 클래스 테스트."""

    def test_menu_entity_initialization(self):
        """MenuEntity 초기화 테스트."""
        entity = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price=5000,
            kcal=650,
            menu=["김치찌개", "밥", "김치"]
        )

        assert entity.date == "2025-01-15"
        assert entity.dining_time == "lunch"
        assert entity.place == "Korean Food (한식)"
        assert entity.price == 5000
        assert entity.kcal == 650
        assert entity.menu == ["김치찌개", "밥", "김치"]
        assert isinstance(entity.id, int)

    def test_menu_entity_id_generation(self):
        """ID가 자동으로 생성되는지 테스트."""
        entity1 = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price=5000,
            kcal=650,
            menu=["김치찌개"]
        )

        entity2 = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price=6000,  # 다른 가격
            kcal=700,    # 다른 칼로리
            menu=["돈까스"]  # 다른 메뉴
        )

        # 날짜, 시간, 장소가 같으면 같은 ID
        assert entity1.id == entity2.id

    def test_menu_entity_different_ids(self):
        """날짜/시간/장소가 다르면 다른 ID가 생성되는지 테스트."""
        entity1 = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price=5000,
            kcal=650,
            menu=["김치찌개"]
        )

        entity2 = MenuEntity(
            date="2025-01-15",
            dining_time="dinner",  # 다른 시간
            place="Korean Food (한식)",
            price=5000,
            kcal=650,
            menu=["김치찌개"]
        )

        assert entity1.id != entity2.id

    def test_menu_entity_repr(self):
        """__repr__ 메서드 테스트."""
        entity = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price=5000,
            kcal=650,
            menu=["김치찌개", "밥"]
        )

        repr_str = repr(entity)

        assert "lunch" in repr_str
        assert "Korean Food (한식)" in repr_str
        assert "김치찌개" in repr_str
        assert "밥" in repr_str
        assert "650 kcal" in repr_str
        assert "5000 won" in repr_str

    def test_menu_entity_null_price_kcal(self):
        """가격과 칼로리가 None일 때 0으로 설정되는지 테스트."""
        entity = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price=None,
            kcal=None,
            menu=["김치찌개"]
        )

        assert entity.price == 0
        assert entity.kcal == 0

    def test_to_db_model(self):
        """to_db_model 메서드 테스트."""
        entity = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price="5,000",  # 콤마 포함 문자열
            kcal="650",
            menu=["김치찌개", "밥", "김치"]
        )

        meal_db, menu_items = entity.to_db_model()

        assert isinstance(meal_db, MealDB)
        assert meal_db.id == entity.id
        assert isinstance(meal_db.date, date)
        assert meal_db.date == date(2025, 1, 15)
        assert meal_db.dining_time == "lunch"
        assert meal_db.place == "Korean Food (한식)"
        assert meal_db.price == 5000  # 콤마 제거됨
        assert meal_db.kcal == 650
        assert menu_items == ["김치찌개", "밥", "김치"]

    def test_to_db_model_null_values(self):
        """NULL 값들이 0으로 변환되는지 테스트."""
        entity = MenuEntity(
            date="2025-01-15",
            dining_time="lunch",
            place="Korean Food (한식)",
            price="NULL",
            kcal="-",
            menu=["김치찌개"]
        )

        meal_db, menu_items = entity.to_db_model()

        assert meal_db.price == 0
        assert meal_db.kcal == 0


class TestMealDB:
    """MealDB 클래스 테스트."""

    def test_meal_db_initialization(self):
        """MealDB 초기화 테스트."""
        meal = MealDB(
            id=123456789,
            date=date(2025, 1, 15),
            dining_time="lunch",
            place="Korean Food (한식)",
            price=5000,
            kcal=650
        )

        assert meal.id == 123456789
        assert meal.date == date(2025, 1, 15)
        assert meal.dining_time == "lunch"
        assert meal.place == "Korean Food (한식)"
        assert meal.price == 5000
        assert meal.kcal == 650

    def test_meal_db_tablename(self):
        """테이블명이 올바른지 테스트."""
        assert MealDB.__tablename__ == 'meals'


class TestMealMenuItem:
    """MealMenuItem 클래스 테스트."""

    def test_meal_menu_item_initialization(self):
        """MealMenuItem 초기화 테스트."""
        item = MealMenuItem(
            meal_id=123456789,
            menu_item="김치찌개"
        )

        assert item.meal_id == 123456789
        assert item.menu_item == "김치찌개"

    def test_meal_menu_item_tablename(self):
        """테이블명이 올바른지 테스트."""
        assert MealMenuItem.__tablename__ == 'meal_menu_items'


class TestUser:
    """User 클래스 테스트."""

    def test_user_tablename(self):
        """테이블명이 올바른지 테스트."""
        assert User.__tablename__ == 'users'
