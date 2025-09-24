"""코리아텍 식단 크롤링 모듈"""

import logging
import re
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup

from .models import MenuEntity

logger = logging.getLogger(__name__)


class KoreatechMealCrawler:
  """코리아텍 식단 정보 크롤러"""

  def __init__(self, portal_id, portal_pw, ip_address):
    self.portal_id = portal_id
    self.portal_pw = portal_pw
    self.ip_address = ip_address
    self.session = None

    # 식당 정보
    self.eat_types = ["breakfast", "lunch", "dinner"]
    self.campus1_restaurants = ["Korean Food (한식)", "Onedish Food (일품)",
                                "Special Food ", "Faculty (능수관)"]
    self.campus2_restaurants = ["코너1"]
    self.campuses = ["Campus1", "Campus2"]

  def portal_login(self):
    """코리아텍 포털에 로그인하고 인증된 requests.Session 객체를 반환"""
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

  def send_meal_request(self, eat_date, eat_type, restaurant, campus):
    """Nexacro API에 식단 데이터 요청을 정확한 형식으로 전송"""
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

  def parse_meal_response(self, response):
    """XML 응답을 파싱하여 MenuEntity 객체로 변환"""
    soup = BeautifulSoup(response.text, 'lxml-xml')
    row = soup.find('Row')
    if not row:
      logger.warning("⚠️ 응답에서 데이터 행을 찾을 수 없음")
      return None

    try:
      def clean_text(text):
        return re.sub(r'\s+', ' ', text).strip() if text else ""

      def parse_dish_list(dish_text):
        if not dish_text: return []
        # Remove the trailing kcal and price lines
        dish_text = re.sub(r'(\d+)\s*kcal.*', '', dish_text,
                           flags=re.IGNORECASE).strip()
        dish_text = re.sub(r'(\d+,)*\d+\s*원.*', '', dish_text).strip()
        return [d.strip() for d in dish_text.split('\n') if d.strip()]

      # Use the correct column IDs from the ground truth response
      menu_entity = MenuEntity(
          date=clean_text(row.find("Col", {"id": "EAT_DATE"}).text),
          dining_time=clean_text(row.find("Col", {"id": "EAT_TYPE"}).text),
          place=clean_text(row.find("Col", {"id": "RESTURANT"}).text),
          price=clean_text(row.find("Col", {"id": "PRICE"}).text),
          kcal=clean_text(row.find("Col", {"id": "KCAL"}).text),
          menu=parse_dish_list(row.find("Col", {"id": "DISH"}).text)
      )

      logger.info(
          f"✅ 식단 파싱 완료: {menu_entity.date} | {menu_entity.dining_time} | {menu_entity.place} | {len(menu_entity.menu)}개 항목")
      return menu_entity

    except Exception as e:
      logger.error(f"❌ 식단 응답 파싱 실패: {e}")
      print(f"경고: 데이터 행 파싱 실패 - {e}")
      return None

  def get_all_menus_for_day(self, target_date: datetime):
    """특정 날짜의 모든 식단 정보 크롤링"""
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

  def get_meals_for_date_range(self, start_date: datetime, end_date: datetime):
    """Crawls meal information for a date range."""
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
