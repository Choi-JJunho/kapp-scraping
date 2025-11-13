"""crawler.py 모듈 테스트."""

from datetime import datetime
from unittest.mock import Mock, MagicMock, patch

import pytest
import requests
import responses

from src.kmeal.crawler import KoreatechMealCrawler
from src.kmeal.models import MenuEntity


class TestKoreatechMealCrawler:
    """KoreatechMealCrawler 클래스 테스트."""

    def test_crawler_initialization(self):
        """크롤러 초기화 테스트."""
        crawler = KoreatechMealCrawler(
            portal_id="test_id",
            portal_pw="test_pw",
            ip_address="127.0.0.1"
        )

        assert crawler.portal_id == "test_id"
        assert crawler.portal_pw == "test_pw"
        assert crawler.ip_address == "127.0.0.1"
        assert crawler.session is None
        assert crawler.eat_types == ["breakfast", "lunch", "dinner"]
        assert len(crawler.campus1_restaurants) == 4
        assert len(crawler.campus2_restaurants) == 1

    def test_portal_login_no_jsessionid(self):
        """JSESSIONID가 없을 때 에러 발생 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        with responses.RequestsMock() as rsps:
            # 모든 로그인 단계 모킹
            rsps.add(responses.POST,
                     "https://portal.koreatech.ac.kr/ktp/login/checkLoginId.do",
                     status=200)
            rsps.add(responses.POST,
                     "https://portal.koreatech.ac.kr/ktp/login/checkSecondLoginCert.do",
                     status=404)
            rsps.add(responses.POST,
                     "https://portal.koreatech.ac.kr/exsignon/sso/sso_assert.jsp",
                     status=200)
            rsps.add(responses.GET,
                     "https://kut90.koreatech.ac.kr/ssoLogin_ext.jsp",
                     status=200)

            with pytest.raises(ConnectionError, match="Could not obtain JSESSIONID"):
                crawler.portal_login()

    def test_send_meal_request_without_login(self):
        """로그인 없이 요청 시 에러 발생 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        with pytest.raises(RuntimeError, match="포털 로그인이 필요합니다"):
            crawler.send_meal_request(
                "2025-01-15",
                "lunch",
                "Korean Food (한식)",
                "Campus1"
            )

    def test_parse_meal_response_no_data(self):
        """데이터가 없는 응답 파싱 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        # 빈 XML 응답 생성
        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <Root>
            <Dataset id="output">
            </Dataset>
        </Root>"""

        result = crawler.parse_meal_response(mock_response)

        assert result is None

    def test_parse_meal_response_valid_data(self):
        """정상 데이터 파싱 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        mock_response = Mock()
        mock_response.text = """<?xml version="1.0" encoding="UTF-8"?>
        <Root>
            <Dataset id="output">
                <Row>
                    <Col id="EAT_DATE">2025-01-15</Col>
                    <Col id="EAT_TYPE">lunch</Col>
                    <Col id="RESTURANT">Korean Food (한식)</Col>
                    <Col id="PRICE">5000</Col>
                    <Col id="KCAL">650</Col>
                    <Col id="DISH">김치찌개
계란말이
밥
650 kcal
5,000 원</Col>
                </Row>
            </Dataset>
        </Root>"""

        result = crawler.parse_meal_response(mock_response)

        assert isinstance(result, MenuEntity)
        assert result.date == "2025-01-15"
        assert result.dining_time == "lunch"
        assert result.place == "Korean Food (한식)"
        assert result.price == "5000"
        assert result.kcal == "650"
        # 메뉴 리스트가 비어있지 않은지 확인
        assert len(result.menu) > 0
        # 첫 번째 메뉴 항목에 기대하는 텍스트가 포함되어 있는지 확인
        menu_text = ' '.join(result.menu)
        assert "김치찌개" in menu_text

    def test_get_all_menus_for_day_without_login(self):
        """로그인 없이 get_all_menus_for_day 호출 시 에러 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        with pytest.raises(RuntimeError, match="포털 로그인이 필요합니다"):
            crawler.get_all_menus_for_day(datetime(2025, 1, 15))

    def test_get_meals_for_date_range_without_login(self):
        """로그인 없이 get_meals_for_date_range 호출 시 에러 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        with pytest.raises(RuntimeError, match="포털 로그인이 필요합니다"):
            crawler.get_meals_for_date_range(
                datetime(2025, 1, 15),
                datetime(2025, 1, 16)
            )

    def test_campus_restaurants_configuration(self):
        """캠퍼스별 식당 설정이 올바른지 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        # Campus1 식당
        assert "Korean Food (한식)" in crawler.campus1_restaurants
        assert "Onedish Food (일품)" in crawler.campus1_restaurants
        assert "Special Food " in crawler.campus1_restaurants
        assert "Faculty (능수관)" in crawler.campus1_restaurants

        # Campus2 식당
        assert "코너1" in crawler.campus2_restaurants

    def test_eat_types_configuration(self):
        """식사 시간 설정이 올바른지 테스트."""
        crawler = KoreatechMealCrawler("test_id", "test_pw", "127.0.0.1")

        assert "breakfast" in crawler.eat_types
        assert "lunch" in crawler.eat_types
        assert "dinner" in crawler.eat_types
        assert len(crawler.eat_types) == 3
