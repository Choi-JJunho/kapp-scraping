"""코리아텍 식단 크롤링 모듈.

이 모듈은 코리아텍(한국기술교육대학교) 포털에 로그인하여
식단 정보를 크롤링하는 기능을 제공합니다.

주요 기능:
  - 포털 4단계 SSO 인증
  - Nexacro Platform XML API를 통한 식단 데이터 조회
  - XML 응답 파싱 및 MenuEntity 객체 생성
  - 날짜 범위 크롤링
  - 서버 부하 방지를 위한 요청 지연 처리
"""

import logging
import re
import time
from datetime import datetime, timedelta
from typing import List, Optional

import requests
from bs4 import BeautifulSoup

from .models import MenuEntity

logger = logging.getLogger(__name__)


class KoreatechMealCrawler:
  """코리아텍 포털 식단 정보 크롤러 클래스.

  코리아텍 포털에 SSO 인증을 수행하고, Nexacro Platform API를 통해
  식단 정보를 크롤링합니다. 모든 캠퍼스, 식당, 식사 시간 조합에 대해
  식단 데이터를 수집할 수 있습니다.

  Attributes:
    portal_id (str): 포털 로그인 ID
    portal_pw (str): 포털 로그인 비밀번호
    ip_address (str): 요청 헤더에 사용할 IP 주소
    session (Optional[requests.Session]): 인증된 세션 객체
    eat_types (List[str]): 식사 시간 목록 (breakfast, lunch, dinner)
    campus1_restaurants (List[str]): 1캠퍼스 식당 목록
    campus2_restaurants (List[str]): 2캠퍼스 식당 목록
    campuses (List[str]): 캠퍼스 목록

  Example:
    >>> crawler = KoreatechMealCrawler("user_id", "password", "127.0.0.1")
    >>> crawler.portal_login()
    >>> menus = crawler.get_all_menus_for_day(datetime(2025, 1, 15))
    >>> print(f"수집된 식단: {len(menus)}개")
  """

  def __init__(self, portal_id: str, portal_pw: str, ip_address: str) -> None:
    """KoreatechMealCrawler 인스턴스를 생성합니다.

    Args:
      portal_id: 코리아텍 포털 로그인 ID
      portal_pw: 코리아텍 포털 로그인 비밀번호
      ip_address: X-Forwarded-For 헤더에 사용할 IP 주소
    """
    self.portal_id: str = portal_id
    self.portal_pw: str = portal_pw
    self.ip_address: str = ip_address
    self.session: Optional[requests.Session] = None

    # 식당 정보
    self.eat_types: List[str] = ["breakfast", "lunch", "dinner"]
    self.campus1_restaurants: List[str] = [
        "Korean Food (한식)",
        "Onedish Food (일품)",
        "Special Food ",
        "Faculty (능수관)"
    ]
    self.campus2_restaurants: List[str] = ["코너1"]
    self.campuses: List[str] = ["Campus1", "Campus2"]

  def portal_login(self) -> requests.Session:
    """코리아텍 포털에 4단계 SSO 인증을 수행합니다.

    포털 로그인 → 2차 인증 → SSO 어서션 → 최종 SSO 로그인의
    4단계 인증 프로세스를 거쳐 JSESSIONID 쿠키를 획득합니다.

    Returns:
      requests.Session: JSESSIONID 쿠키가 포함된 인증된 세션 객체

    Raises:
      requests.exceptions.HTTPError: HTTP 요청 실패 시
      ConnectionError: JSESSIONID 쿠키 획득 실패 시

    Example:
      >>> crawler = KoreatechMealCrawler("id", "pw", "127.0.0.1")
      >>> session = crawler.portal_login()
      >>> print("로그인 성공!")
    """
    logger.info("🚀 포털 로그인 프로세스 시작...")
    logger.info(f"로그인 ID: {self.portal_id}")
    logger.info(f"IP 주소: {self.ip_address}")
    print("🚀 포털에 로그인 중...")

    self.session = requests.session()

    custom_headers = {
      "X-Forwarded-For": self.ip_address,
      "X-Real-IP": self.ip_address,
      'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/139.0.0.0 Safari/537.36'
    }
    # Use these headers for subsequent requests
    self.session.headers.update(custom_headers)

    # 인증 및 SSO 단계
    logger.info("단계 1: 로그인 자격증명 확인 중...")
    self.session.post(
        "https://portal.koreatech.ac.kr/ktp/login/checkLoginId.do",
        headers=custom_headers,
        data={'login_id': self.portal_id, 'login_pwd': self.portal_pw}
    ).raise_for_status()
    logger.info("✅ 로그인 자격증명 확인 완료")

    self.session.cookies.set('kut_login_type', 'id')
    logger.info("단계 2: 2차 로그인 인증 시도 중...")
    try:
      self.session.post(
          "https://portal.koreatech.ac.kr/ktp/login/checkSecondLoginCert.do",
          headers=custom_headers, data={'login_id': self.portal_id}
      ).raise_for_status()
      logger.info("✅ 2차 로그인 인증 완료")
    except requests.exceptions.HTTPError as e:
      if e.response.status_code == 404:
        logger.warning("2차 로그인 엔드포인트를 찾을 수 없음 (404) - 건너뜀")
      else:
        logger.error(f"2차 로그인 실패: {e}")
        raise e

    logger.info("단계 3: SSO 어서션...")
    self.session.post(
        "https://portal.koreatech.ac.kr/exsignon/sso/sso_assert.jsp",
        headers=custom_headers
    ).raise_for_status()
    logger.info("✅ SSO 어서션 완료")

    logger.info("단계 4: 최종 SSO 로그인...")
    self.session.get(
        "https://kut90.koreatech.ac.kr/ssoLogin_ext.jsp?&PGM_ID=CO::CO0998W&locale=ko",
        headers=custom_headers
    ).raise_for_status()
    logger.info("✅ 최종 SSO 로그인 완료")

    # Safely check and report JSESSIONID cookies without causing conflicts
    jsids = [
      (c.value, c.domain, c.path) for c in self.session.cookies if
      c.name == 'JSESSIONID'
    ]
    if not jsids:
      logger.error("포털 로그인 실패 - 쿠키에서 JSESSIONID를 찾을 수 없음")
      raise ConnectionError("Portal login failed. Could not obtain JSESSIONID.")

    logger.info(f"✅ 로그인 성공! JSESSIONID cookies: {jsids}")
    print("✅ 로그인 성공. 인증된 세션이 준비되었습니다.")
    return self.session

  def send_meal_request(
      self,
      eat_date: str,
      eat_type: str,
      restaurant: str,
      campus: str
  ) -> requests.Response:
    """Nexacro Platform XML API에 식단 데이터를 요청합니다.

    JSESSIONID 쿠키를 XML 파라미터에 포함하여 인증된 요청을 전송합니다.

    Args:
      eat_date: 식단 날짜 (YYYY-MM-DD 형식)
      eat_type: 식사 시간 (breakfast, lunch, dinner)
      restaurant: 식당 이름
      campus: 캠퍼스 (Campus1, Campus2)

    Returns:
      requests.Response: 식단 데이터가 포함된 XML 응답

    Raises:
      RuntimeError: portal_login()이 먼저 호출되지 않은 경우
      ConnectionError: API 요청 실패 또는 ErrorCode가 0이 아닌 경우
      requests.RequestException: HTTP 요청 중 예외 발생

    Example:
      >>> response = crawler.send_meal_request(
      ...     "2025-01-15", "lunch", "Korean Food (한식)", "Campus1"
      ... )
      >>> print(response.status_code)
      200
    """
    if not self.session:
      raise RuntimeError("포털 로그인이 필요합니다. portal_login()을 먼저 호출하세요.")

    logger.info(
        f"📋 식단 데이터 요청: {eat_date} | {eat_type} | {restaurant} | {campus}")
    headers = {"Content-Type": "text/xml; charset=utf-8",
               'User-Agent': self.session.headers['User-Agent']}

    # 관련 쿠키 값을 포함한 <Parameters> 섹션 생성
    cookies_dict = self.session.cookies.get_dict(domain="koreatech.ac.kr")
    parameters_xml = ""
    for key, value in cookies_dict.items():
      parameters_xml += f'<Parameter id="{key}">{value}</Parameter>\n'

    body = f"""<?xml version="1.0" encoding="UTF-8"?>
    <Root xmlns="http://www.nexacroplatform.com/platform/dataset">
        <Parameters>
            {parameters_xml}
            <Parameter id="method">getList_sp</Parameter>
            <Parameter id="sqlid">NK_COT_MEAL_PLAN.NP_SELECT_11</Parameter>
        </Parameters>
        <Dataset id="input1">
            <ColumnInfo>
                <Column id="EAT_DATE" type="string" size="4000" />
                <Column id="EAT_TYPE" type="string" size="4000" />
                <Column id="RESTURANT" type="string" size="4000" />
                <Column id="CAMPUS" type="string" size="4000" />
            </ColumnInfo>
            <Rows>
                <Row>
                    <Col id="EAT_DATE">{eat_date}</Col>
                    <Col id="EAT_TYPE">{eat_type}</Col>
                    <Col id="RESTURANT">{restaurant}</Col>
                    <Col id="CAMPUS">{campus}</Col>
                </Row>
            </Rows>
        </Dataset>
    </Root>""".encode("utf-8")

    try:
      response = self.session.post(
          "https://kut90.koreatech.ac.kr/nexacroController.do",
          headers=headers,
          data=body
      )
      response.raise_for_status()
      logger.info(f"✅ API 요청 성공: {response.status_code}")

      soup = BeautifulSoup(response.text, 'lxml-xml')
      error_code = soup.find("Parameter", {"id": "ErrorCode"})
      if error_code and error_code.text == '0':
        logger.info("✅ 식단 데이터 조회 성공")
        return response

      error_msg = soup.find('Parameter', {'id': 'ErrorMsg'})
      error_text = error_msg.text if error_msg else "알 수 없는 오류"
      logger.error(f"❌ 식단 데이터 요청 실패: {error_text}")
      raise ConnectionError(f"Meal data request failed: {error_text}")

    except requests.RequestException as e:
      logger.error(f"❌ HTTP 요청 실패: {e}")
      raise
    except Exception as e:
      logger.error(f"❌ 식단 요청 중 예상치 못한 오류: {e}")
      raise

  def parse_meal_response(self, response: requests.Response) -> Optional[MenuEntity]:
    """Nexacro XML 응답을 파싱하여 MenuEntity 객체로 변환합니다.

    XML 응답에서 식단 정보를 추출하고, 칼로리와 가격 정보를 정리한 후
    MenuEntity 인스턴스를 생성합니다.

    Args:
      response: Nexacro API의 XML 응답

    Returns:
      Optional[MenuEntity]: 파싱된 식단 엔티티, 데이터가 없으면 None

    Example:
      >>> response = crawler.send_meal_request(...)
      >>> entity = crawler.parse_meal_response(response)
      >>> if entity:
      ...     print(f"메뉴: {', '.join(entity.menu)}")
    """
    soup = BeautifulSoup(response.text, 'lxml-xml')
    row = soup.find('Row')
    if not row:
      logger.warning("⚠️ 응답에서 데이터 행을 찾을 수 없음")
      return None

    try:
      def clean_text(text):
        return re.sub(r'\s+', ' ', text).strip() if text else ""

      def safe_get_text(element, column_id):
        """안전하게 텍스트를 추출하는 함수"""
        col = element.find("Col", {"id": column_id})
        if col is not None and col.text is not None:
          return clean_text(col.text)
        return ""

      def parse_dish_list(dish_text):
        if not dish_text: return []
        # Remove the trailing kcal and price lines
        dish_text = re.sub(r'(\d+)\s*kcal.*', '', dish_text,
                           flags=re.IGNORECASE).strip()
        dish_text = re.sub(r'(\d+,)*\d+\s*원.*', '', dish_text).strip()
        return [d.strip() for d in dish_text.split('\n') if d.strip()]

      # Use the correct column IDs from the ground truth response
      menu_entity = MenuEntity(
          date=safe_get_text(row, "EAT_DATE"),
          dining_time=safe_get_text(row, "EAT_TYPE"),
          place=safe_get_text(row, "RESTURANT"),
          price=safe_get_text(row, "PRICE"),
          kcal=safe_get_text(row, "KCAL"),
          menu=parse_dish_list(safe_get_text(row, "DISH"))
      )

      logger.info(
          f"✅ 식단 파싱 완료: {menu_entity.date} | {menu_entity.dining_time} | {menu_entity.place} | {len(menu_entity.menu)}개 항목")
      return menu_entity

    except Exception as e:
      logger.error(f"❌ 식단 응답 파싱 실패: {e}")
      print(f"경고: 데이터 행 파싱 실패 - {e}")
      return None

  def get_all_menus_for_day(self, target_date: datetime) -> List[MenuEntity]:
    """특정 날짜의 모든 캠퍼스, 식당, 식사 시간 조합에 대한 식단을 크롤링합니다.

    모든 가능한 조합 (캠퍼스 × 식당 × 식사시간)에 대해 API를 호출하여
    해당 날짜의 전체 식단 정보를 수집합니다.
    개별 요청 실패는 경고를 출력하고 건너뜁니다.

    Args:
      target_date: 크롤링할 날짜

    Returns:
      List[MenuEntity]: 수집된 식단 엔티티 리스트

    Raises:
      RuntimeError: portal_login()이 먼저 호출되지 않은 경우

    Example:
      >>> from datetime import datetime
      >>> menus = crawler.get_all_menus_for_day(datetime(2025, 1, 15))
      >>> print(f"{len(menus)}개 식단 수집 완료")
      24개 식단 수집 완료
    """
    if not self.session:
      raise RuntimeError("포털 로그인이 필요합니다. portal_login()을 먼저 호출하세요.")

    date_str = target_date.strftime("%Y-%m-%d")
    menus = []

    logger.info(f"📅 날짜 처리 중: {date_str}")
    print(f"{date_str}의 식단 데이터를 가져오는 중...")

    # 캠퍼스별 식당 선택
    restaurants_by_campus = {
      "Campus1": self.campus1_restaurants,
      "Campus2": self.campus2_restaurants
    }

    total_requests = sum(
        len(restaurants_by_campus[campus]) for campus in self.campuses) * len(
        self.eat_types)
    request_count = 0

    for campus in self.campuses:
      restaurants = restaurants_by_campus[campus]
      for restaurant in restaurants:
        for eat_type in self.eat_types:
          request_count += 1
          logger.info(
              f"🔄 요청 {request_count}/{total_requests}: {restaurant}의 {eat_type}")

          try:
            # 과거 데이터용 실제 날짜 사용
            response = self.send_meal_request(date_str, eat_type, restaurant,
                                              campus)
            menu_data = self.parse_meal_response(response)
            if menu_data:
              menus.append(menu_data)
              logger.info(f"✅ {restaurant}의 {eat_type} 식단 데이터 추가 성공")
            else:
              logger.warning(f"⚠️ {restaurant}의 {eat_type} 식단 데이터 없음")
            # 서버 과부하 방지를 위한 짧은 지연
            time.sleep(0.1)
          except ConnectionError as e:
            logger.warning(f"⚠️ {restaurant}의 {eat_type} 연결 실패: {e}")
            print(f"  경고: {restaurant}의 {eat_type} 가져오기 실패 - {e}")
          except Exception as e:
            logger.error(f"❌ {restaurant}의 {eat_type} 예상치 못한 오류: {e}")
            print(f"  오류: {e}")

    logger.info(
        f"📊 {date_str} 일일 요약: 총 {total_requests}개 요청 중 {len(menus)}개 식단 수집")
    return menus

  def get_meals_for_date_range(
      self,
      start_date: datetime,
      end_date: datetime
  ) -> List[MenuEntity]:
    """날짜 범위에 해당하는 모든 식단 정보를 크롤링합니다.

    시작 날짜부터 종료 날짜까지의 모든 날짜에 대해
    get_all_menus_for_day()를 호출하여 식단 데이터를 수집합니다.
    날짜 간 0.5초 지연을 두어 서버 부하를 방지합니다.

    Args:
      start_date: 시작 날짜 (포함)
      end_date: 종료 날짜 (포함)

    Returns:
      List[MenuEntity]: 전체 기간의 식단 엔티티 리스트

    Raises:
      RuntimeError: portal_login()이 먼저 호출되지 않은 경우

    Example:
      >>> from datetime import datetime, timedelta
      >>> start = datetime(2025, 1, 1)
      >>> end = start + timedelta(days=7)
      >>> menus = crawler.get_meals_for_date_range(start, end)
      >>> print(f"총 {len(menus)}개 식단 수집")
    """
    if not self.session:
      raise RuntimeError("포털 로그인이 필요합니다. portal_login()을 먼저 호출하세요.")

    all_menus = []
    current_date = start_date

    total_days = (end_date - start_date).days + 1
    day_count = 0

    while current_date <= end_date:
      day_count += 1
      print(
          f"\n[{day_count}/{total_days}] Processing {current_date.strftime('%Y-%m-%d')}...")

      daily_menus = self.get_all_menus_for_day(current_date)
      all_menus.extend(daily_menus)

      # Progress report
      if daily_menus:
        print(f"  ✅ Found {len(daily_menus)} meals")
      else:
        print(f"  ❌ No meals found")

      current_date += timedelta(days=1)

      # Add delay between days to be respectful to the server
      time.sleep(0.5)

    return all_menus
