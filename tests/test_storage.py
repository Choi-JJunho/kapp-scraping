"""storage.py 모듈 테스트."""

import json
import csv
from pathlib import Path
from unittest.mock import Mock, MagicMock, patch

import pytest

from src.kmeal.storage import MealStorage
from src.kmeal.models import MenuEntity, MealDB, MealMenuItem


class TestMealStorage:
    """MealStorage 클래스 테스트."""

    def test_meal_storage_initialization(self):
        """MealStorage 초기화 테스트."""
        storage = MealStorage()

        assert storage.engine is None
        assert storage.session is None

    def test_save_to_database_empty_list(self):
        """빈 리스트 저장 시 0 반환 테스트."""
        storage = MealStorage()

        result = storage.save_to_database([])

        assert result == 0

    def test_save_to_csv_empty_list(self, tmp_path):
        """빈 리스트를 CSV로 저장 테스트."""
        storage = MealStorage()
        csv_file = tmp_path / "test.csv"

        storage.save_to_csv([], str(csv_file))

        # 파일이 생성되지 않거나 빈 파일이어야 함
        assert not csv_file.exists() or csv_file.stat().st_size == 0

    def test_save_to_csv_with_data(self, tmp_path):
        """데이터를 CSV로 저장 테스트."""
        storage = MealStorage()
        csv_file = tmp_path / "test.csv"

        menus = [
            MenuEntity(
                date="2025-01-15",
                dining_time="lunch",
                place="Korean Food (한식)",
                price=5000,
                kcal=650,
                menu=["김치찌개", "밥", "김치"]
            )
        ]

        storage.save_to_csv(menus, str(csv_file))

        assert csv_file.exists()

        # CSV 내용 확인
        with open(csv_file, 'r', encoding='utf-8-sig') as f:
            reader = csv.DictReader(f)
            rows = list(reader)

            assert len(rows) == 1
            assert rows[0]['date'] == '2025-01-15'
            assert rows[0]['dining_time'] == 'lunch'
            assert rows[0]['place'] == 'Korean Food (한식)'
            assert rows[0]['price'] == '5000'
            assert rows[0]['kcal'] == '650'
            assert '김치찌개' in rows[0]['menu_items']

    def test_save_to_json_empty_list(self, tmp_path):
        """빈 리스트를 JSON으로 저장 테스트."""
        storage = MealStorage()
        json_file = tmp_path / "test.json"

        storage.save_to_json([], str(json_file))

        # 파일이 생성되지 않거나 빈 파일이어야 함
        assert not json_file.exists() or json_file.stat().st_size == 0

    def test_save_to_json_with_data(self, tmp_path):
        """데이터를 JSON으로 저장 테스트."""
        storage = MealStorage()
        json_file = tmp_path / "test.json"

        menus = [
            MenuEntity(
                date="2025-01-15",
                dining_time="lunch",
                place="Korean Food (한식)",
                price=5000,
                kcal=650,
                menu=["김치찌개", "밥", "김치"]
            )
        ]

        storage.save_to_json(menus, str(json_file))

        assert json_file.exists()

        # JSON 내용 확인
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)

            assert len(data) == 1
            assert data[0]['date'] == '2025-01-15'
            assert data[0]['dining_time'] == 'lunch'
            assert data[0]['place'] == 'Korean Food (한식)'
            assert data[0]['price'] == 5000
            assert data[0]['kcal'] == 650
            assert data[0]['menu'] == ["김치찌개", "밥", "김치"]

    def test_save_all_formats_empty_list(self):
        """빈 리스트를 모든 형식으로 저장 테스트."""
        storage = MealStorage()

        result = storage.save_all_formats([])

        assert result == 0

    @patch('src.kmeal.storage.MealStorage.save_to_csv')
    @patch('src.kmeal.storage.MealStorage.save_to_json')
    @patch('src.kmeal.storage.MealStorage.save_to_database')
    def test_save_all_formats_calls_all_methods(
        self,
        mock_db,
        mock_json,
        mock_csv
    ):
        """save_all_formats가 모든 저장 메서드를 호출하는지 테스트."""
        storage = MealStorage()
        mock_db.return_value = 5

        menus = [
            MenuEntity(
                date="2025-01-15",
                dining_time="lunch",
                place="Korean Food (한식)",
                price=5000,
                kcal=650,
                menu=["김치찌개"]
            )
        ]

        result = storage.save_all_formats(menus)

        mock_csv.assert_called_once()
        mock_json.assert_called_once()
        mock_db.assert_called_once_with(menus)
        assert result == 5

    def test_close_without_session(self):
        """세션이 없을 때 close 호출 테스트."""
        storage = MealStorage()

        # 에러 없이 실행되어야 함
        storage.close()

    def test_close_with_session(self):
        """세션이 있을 때 close 호출 테스트."""
        storage = MealStorage()
        storage.session = Mock()

        storage.close()

        storage.session.close.assert_called_once()

    def test_csv_encoding_utf8_bom(self, tmp_path):
        """CSV 파일이 UTF-8 with BOM으로 저장되는지 테스트."""
        storage = MealStorage()
        csv_file = tmp_path / "test.csv"

        menus = [
            MenuEntity(
                date="2025-01-15",
                dining_time="lunch",
                place="한식",
                price=5000,
                kcal=650,
                menu=["김치"]
            )
        ]

        storage.save_to_csv(menus, str(csv_file))

        # BOM 확인
        with open(csv_file, 'rb') as f:
            first_bytes = f.read(3)
            # UTF-8 BOM: EF BB BF
            assert first_bytes == b'\xef\xbb\xbf'

    def test_json_encoding_utf8(self, tmp_path):
        """JSON 파일이 UTF-8로 저장되고 한글이 포함되는지 테스트."""
        storage = MealStorage()
        json_file = tmp_path / "test.json"

        menus = [
            MenuEntity(
                date="2025-01-15",
                dining_time="lunch",
                place="한식",
                price=5000,
                kcal=650,
                menu=["김치"]
            )
        ]

        storage.save_to_json(menus, str(json_file))

        # 파일 내용에 한글이 그대로 있는지 확인 (ensure_ascii=False)
        with open(json_file, 'r', encoding='utf-8') as f:
            content = f.read()
            assert '한식' in content
            assert '김치' in content
            assert '\\u' not in content  # 유니코드 이스케이프가 없어야 함
