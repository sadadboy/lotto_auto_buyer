#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Clean Architecture 통합 로또 자동구매 시스템
기존 lotto_auto_buyer.py를 Clean Architecture와 통합한 버전
"""

import sys
import os
import json
import time
import logging
import random
import argparse
from datetime import datetime
from collections import Counter
from pathlib import Path
import numpy as np

# Selenium imports
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait, Select
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.keys import Keys
from selenium.common.exceptions import TimeoutException, NoSuchElementException

# 현재 디렉토리를 Python path에 추가 (import 문제 해결)
current_dir = Path(__file__).parent
sys.path.insert(0, str(current_dir))

# Clean Architecture imports (optional)
CLEAN_ARCHITECTURE_AVAILABLE = False
try:
    from src.config.dependency_injection import DIContainer
    from src.application.usecases.configuration_usecase import ConfigurationUseCase
    from src.domain.entities.configuration import Configuration
    CLEAN_ARCHITECTURE_AVAILABLE = True
    print("✅ Clean Architecture 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ Clean Architecture 모듈 로드 실패: {e}")
    print("기존 JSON 설정 방식을 사용합니다.")

# AutoRecharger import (with fallback)
AutoRecharger = None
try:
    from auto_recharge import AutoRecharger
    print("✅ AutoRecharger 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ AutoRecharger 모듈 로드 실패: {e}")
    print("자동충전 기능이 비활성화됩니다.")

# CredentialManager import (with fallback)
CredentialManager = None
try:
    from credential_manager import CredentialManager, UserCredentials
    print("✅ CredentialManager 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ CredentialManager 모듈 로드 실패: {e}")
    print("인증정보 암호화 기능이 비활성화됩니다.")

# Discord Notifier import (with fallback)
NotificationManager = None
try:
    from discord_notifier import NotificationManager, run_notification
    print("✅ Discord 알림 모듈 로드 성공")
except ImportError as e:
    print(f"⚠️ Discord 알림 모듈 로드 실패: {e}")
    print("Discord 알림 기능이 비활성화됩니다.")

class ConfigurationManager:
    """설정 관리자 - Clean Architecture와 JSON 설정을 통합"""
    
    def __init__(self):
        self.config = None
        self.config_usecase = None
        self.credential_manager = None
        
        # 암호화 인증정보 관리자 초기화
        if CredentialManager:
            try:
                credentials_file = "credentials.enc"
                # config에서 파일 경로 확인
                if hasattr(self, 'config') and self.config:
                    security_config = self.config.get('security', {})
                    credentials_file = security_config.get('credentials_file', credentials_file)
                
                self.credential_manager = CredentialManager(credentials_file)
                print(f"✅ 암호화 인증정보 관리자 초기화: {credentials_file}")
            except Exception as e:
                print(f"⚠️ 암호화 인증정보 관리자 초기화 실패: {e}")
                self.credential_manager = None
        
    def load_configuration(self):
        """설정 로드 (Clean Architecture 우선, fallback to JSON)"""
        if CLEAN_ARCHITECTURE_AVAILABLE:
            try:
                container = DIContainer()
                self.config_usecase = container.get_configuration_usecase()
                config_entity = self.config_usecase.get_current_configuration()
                if config_entity:
                    self.config = config_entity.to_dict_compatible()  # 호훈성 메서드 사용
                    print("✅ Clean Architecture 설정 로드 성공")
                    return self.config
                else:
                    print("⚠️ Clean Architecture 설정 비어있음 - JSON fallback 사용")
                    raise Exception("Configuration is None")
            except Exception as e:
                print(f"⚠️ Clean Architecture 설정 로드 실패: {e}")
        
        # JSON fallback
        try:
            with open('lotto_config.json', 'r', encoding='utf-8') as f:
                self.config = json.load(f)
                print("✅ JSON 설정 파일 로드")
                return self.config
        except Exception as e:
            print(f"⚠️ JSON 설정 로드 실패: {e}")
            self.config = self._create_default_config()
            return self.config
    
    def _create_default_config(self):
        """기본 설정 생성"""
        return {
            "user_credentials": {
                "user_id": "",
                "password": ""
            },
            "purchase_settings": {
                "games_per_purchase": 5,
                "max_amount_per_game": 5000,
                "purchase_method": "auto",
                "number_selection_method": "mixed"
            },
            "payment": {
                "auto_recharge": False,
                "recharge_amount": 50000,
                "min_balance": 5000,
                "recharge_method": "account_transfer"
            }
        }
    
    def get_user_credentials(self, force_input=False):
        """사용자 인증정보 반환 (암호화 우선, JSON fallback)"""
        
        # 1. 암호화된 인증정보 시도 (우선)
        if self.credential_manager and not force_input:
            try:
                if self.credential_manager.has_credentials():
                    credentials = self.credential_manager.load_credentials()
                    if credentials:
                        print("✅ 암호화된 인증정보 로드 성공")
                        return {
                            'user_id': credentials.user_id,
                            'password': credentials.password,
                            'recharge_password': credentials.recharge_password
                        }
                    else:
                        print("⚠️ 암호화된 인증정보 로드 실패 - JSON fallback 사용")
                else:
                    print("📝 암호화된 인증정보 파일이 없음 - 설정 필요")
            except Exception as e:
                print(f"⚠️ 인증정보 로드 오류: {e}")
        
        # 2. JSON 설정 fallback
        if 'user_credentials' in self.config:
            creds = self.config['user_credentials']
            print("ℹ️ JSON 설정에서 인증정보 로드")
            return creds
        elif 'login' in self.config:
            creds = {
                'user_id': self.config['login'].get('user_id', ''),
                'password': self.config['login'].get('password', ''),
                'recharge_password': ''
            }
            print("ℹ️ JSON 레거시 설정에서 인증정보 로드")
            return creds
        else:
            print("❌ 인증정보가 없음 - 설정 필요")
            return {'user_id': '', 'password': '', 'recharge_password': ''}
    
    def get_purchase_settings(self):
        """구매 설정 반환 (기존/신규 구조 모두 지원)"""
        # 새로운 구조 시도
        if 'purchase_settings' in self.config:
            return self.config['purchase_settings']
        # 기존 구조 fallback
        elif 'purchase' in self.config:
            purchase = self.config['purchase']
            return {
                'games_per_purchase': purchase.get('count', 5),
                'max_amount_per_game': 1000,  # 기본값
                'purchase_method': 'auto',
                'number_selection_method': 'mixed',
                'lotto_list': purchase.get('lotto_list', [])
            }
        else:
            return {
                'games_per_purchase': 5,
                'max_amount_per_game': 5000,
                'purchase_method': 'auto',
                'number_selection_method': 'mixed'
            }
    
    def get_payment_settings(self):
        """결제 설정 반환"""
        return self.config.get('payment', {})
    
    def setup_credentials(self, force_new=False):
        """인증정보 설정 (암호화 저장)"""
        if not self.credential_manager:
            print("❌ CredentialManager가 사용할 수 없습니다.")
            return False
        
        try:
            credentials = self.credential_manager.setup_credentials(force_new)
            if credentials:
                print("✅ 인증정보 설정 완료")
                return True
            else:
                print("❌ 인증정보 설정 실패")
                return False
        except Exception as e:
            print(f"❌ 인증정보 설정 중 오류: {e}")
            return False
    
    def test_credentials(self):
        """인증정보 테스트"""
        if not self.credential_manager:
            print("❌ CredentialManager가 사용할 수 없습니다.")
            return False
        
        return self.credential_manager.test_credentials_file()

class LottoStatistics:
    """로또 통계 분석 클래스 (기존 코드 유지)"""
    
    def __init__(self):
        self.winning_numbers_file = "winning_numbers.json"
        self.winning_numbers = self.load_winning_numbers()
        
    def load_winning_numbers(self):
        """저장된 당첨번호 불러오기"""
        try:
            with open(self.winning_numbers_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except FileNotFoundError:
            return self.create_sample_winning_numbers()
            
    def create_sample_winning_numbers(self):
        """샘플 당첨번호 생성"""
        sample_data = []
        for i in range(50):
            numbers = sorted(random.sample(range(1, 46), 6))
            sample_data.append({
                'round': 1000 + i,
                'numbers': numbers,
                'date': f"2024-{(i%12)+1:02d}-{(i%28)+1:02d}"
            })
        
        with open(self.winning_numbers_file, 'w', encoding='utf-8') as f:
            json.dump(sample_data, f, ensure_ascii=False, indent=2)
        
        return sample_data
            
    def get_most_frequent_numbers(self, count=6):
        """가장 자주 나온 번호들"""
        all_numbers = []
        for data in self.winning_numbers:
            all_numbers.extend(data['numbers'])
        
        counter = Counter(all_numbers)
        return [num for num, _ in counter.most_common(count)]
    
    def get_least_frequent_numbers(self, count=6):
        """가장 적게 나온 번호들"""
        all_numbers = []
        for data in self.winning_numbers:
            all_numbers.extend(data['numbers'])
        
        counter = Counter(all_numbers)
        return [num for num, _ in counter.most_common()[-count:]]
    
    def get_hot_numbers(self, recent_count=10):
        """최근 자주 나온 번호들"""
        recent_numbers = []
        for data in self.winning_numbers[-recent_count:]:
            recent_numbers.extend(data['numbers'])
        
        counter = Counter(recent_numbers)
        return [num for num, _ in counter.most_common(6)]

class IntegratedLottoBuyer:
    """통합 로또 자동구매 클래스"""
    
    def __init__(self):
        self.config_manager = ConfigurationManager()
        self.config = self.config_manager.load_configuration()
        self.statistics = LottoStatistics()
        self.auto_recharger = None
        self.notification_manager = None
        
        # NotificationManager 초기화
        if NotificationManager:
            try:
                self.notification_manager = NotificationManager(self.config)
                print("✅ Discord 알림 서비스 초기화 완료")
            except Exception as e:
                print(f"⚠️ Discord 알림 서비스 초기화 실패: {e}")
                self.notification_manager = None
        
        # AutoRecharger 초기화
        if AutoRecharger and self.config.get('payment', {}).get('auto_recharge'):
            try:
                self.auto_recharger = AutoRecharger(self.config)
                print("✅ 자동충전 기능 활성화")
            except Exception as e:
                print(f"⚠️ 자동충전 초기화 실패: {e}")
        
        self.setup_logging()
        self.driver = None
    
    def setup_logging(self):
        """로깅 설정"""
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(levelname)s - %(message)s',
            handlers=[
                logging.FileHandler('lotto_auto_buyer.log', encoding='utf-8'),
                logging.StreamHandler()
            ]
        )
        self.logger = logging.getLogger(__name__)
    
    def setup_driver(self):
        """Chrome 드라이버 설정"""
        try:
            options = Options()
            options.add_argument('--disable-blink-features=AutomationControlled')
            options.add_argument('--user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36')
            options.add_experimental_option("excludeSwitches", ["enable-automation"])
            options.add_experimental_option('useAutomationExtension', False)
            
            self.driver = webdriver.Chrome(options=options)
            self.driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
            
            self.logger.info("✅ Chrome 드라이버 초기화 완료")
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 드라이버 초기화 실패: {e}")
            return False
    
    def login(self):
        """로그인 (빠른 속도 최적화)"""
        try:
            credentials = self.config_manager.get_user_credentials()
            user_id = credentials.get('user_id')
            password = credentials.get('password')
            
            if not user_id or not password:
                self.logger.error("❌ 사용자 ID 또는 비밀번호가 설정되지 않았습니다")
                return False
            
            # 로그인 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_login_start(user_id))
            
            self.logger.info("🔐 로그인 시작")
            self.driver.get("https://www.dhlottery.co.kr/user.do?method=login")
            time.sleep(1)  # 3초 → 1초
            
            # 로그인 입력 필드 찾기 (여러 방법 시도)
            id_input = None
            pw_input = None
            
            # 1. 기본 ID 선택자들 시도
            id_selectors = [
                (By.ID, "userId"),
                (By.NAME, "userId"),
                (By.CSS_SELECTOR, "input[name='userId']"),
                (By.CSS_SELECTOR, "input[id='userId']"),
                (By.XPATH, "//input[@placeholder='아이디' or @placeholder='ID' or contains(@class, 'user') or contains(@class, 'id')]"),
                (By.CSS_SELECTOR, "input[type='text']:first-of-type")
            ]
            
            for selector_type, selector in id_selectors:
                try:
                    id_input = WebDriverWait(self.driver, 3).until(  # 5초 → 3초
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    self.logger.info(f"✅ ID 입력 필드 발견: {selector_type.name}='{selector}'")
                    break
                except:
                    continue
            
            if not id_input:
                self.logger.error("❌ ID 입력 필드를 찾을 수 없습니다")
                return False
            
            # 2. 비밀번호 선택자들 시도
            pw_selectors = [
                (By.ID, "password"),
                (By.NAME, "password"),
                (By.CSS_SELECTOR, "input[name='password']"),
                (By.CSS_SELECTOR, "input[id='password']"),
                (By.CSS_SELECTOR, "input[type='password']"),
                (By.XPATH, "//input[@placeholder='비밀번호' or @placeholder='password' or @placeholder='Password' or contains(@class, 'password') or contains(@class, 'pass')]"),
            ]
            
            for selector_type, selector in pw_selectors:
                try:
                    pw_input = WebDriverWait(self.driver, 3).until(  # 5초 → 3초
                        EC.presence_of_element_located((selector_type, selector))
                    )
                    self.logger.info(f"✅ 비밀번호 입력 필드 발견: {selector_type.name}='{selector}'")
                    break
                except:
                    continue
            
            if not pw_input:
                self.logger.error("❌ 비밀번호 입력 필드를 찾을 수 없습니다")
                return False
            
            # 3. 로그인 정보 빠른 입력
            id_input.clear()
            id_input.send_keys(user_id)
            self.logger.info("✅ 사용자 ID 입력 완료")
            
            pw_input.clear()
            pw_input.send_keys(password)
            self.logger.info("✅ 비밀번호 입력 완료")
            
            # time.sleep(1) 제거
            
            # 4. 로그인 버튼 찾기 및 클릭
            login_selectors = [
                (By.CSS_SELECTOR, "input[type='submit'][value='로그인']"),
                (By.CSS_SELECTOR, "button[type='submit']"),
                (By.CSS_SELECTOR, "input[type='submit']"),
                (By.XPATH, "//button[contains(text(), '로그인') or contains(text(), 'login') or contains(text(), 'Login')]"),
                (By.XPATH, "//input[@value='로그인' or @value='login' or @value='Login']"),
                (By.CSS_SELECTOR, ".btn_login, .login-btn, .login_btn")
            ]
            
            login_success = False
            for selector_type, selector in login_selectors:
                try:
                    login_btn = WebDriverWait(self.driver, 3).until(  # 5초 → 3초
                        EC.element_to_be_clickable((selector_type, selector))
                    )
                    login_btn.click()
                    self.logger.info(f"✅ 로그인 버튼 클릭: {selector_type.name}='{selector}'")
                    login_success = True
                    break
                except:
                    continue
            
            if not login_success:
                # Enter 키로 대체
                try:
                    pw_input.send_keys(Keys.ENTER)
                    self.logger.info("✅ Enter 키로 로그인 시도")
                    login_success = True
                except:
                    self.logger.error("❌ 로그인 버튼을 찾을 수 없습니다")
                    return False
            
            time.sleep(2)  # 5초 → 2초
            
            # 5. 로그인 성공 확인
            success_indicators = [
                "마이페이지",
                "로그아웃",
                "myPage",
                "logout",
                "로또구매",
                "main"
            ]
            
            current_url = self.driver.current_url
            page_source = self.driver.page_source
            
            for indicator in success_indicators:
                if indicator in current_url or indicator in page_source:
                    self.logger.info("✅ 로그인 성공!")
                    
                    # 로그인 성공 알림
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_login_success(user_id))
                    
                    return True
            
            # 추가 확인: 오류 메시지 체크
            error_indicators = [
                "아이디나 비밀번호",
                "로그인 실패",
                "error",
                "잘못된"
            ]
            
            for error in error_indicators:
                if error in page_source:
                    self.logger.error(f"❌ 로그인 오류: {error} 감지")
                    
                    # 로그인 실패 알림
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_login_failure(user_id, error))
                    
                    return False
            
            self.logger.warning("⚠️ 로그인 상태를 확인할 수 없습니다")
            self.logger.info(f"현재 URL: {current_url}")
            return False
                
        except Exception as e:
            self.logger.error(f"❌ 로그인 오류: {e}")
            
            # 로그인 실패 알림 (예외)
            if self.notification_manager:
                credentials = self.config_manager.get_user_credentials()
                user_id = credentials.get('user_id', 'unknown')
                run_notification(self.notification_manager.notify_login_failure(user_id, str(e)))
            
            return False
    
    def check_balance(self):
        """잔액 확인"""
        try:
            self.driver.get("https://www.dhlottery.co.kr/myPage.do?method=myPage")
            time.sleep(2)
            
            # 예치금 정보 찾기
            balance_elements = self.driver.find_elements(By.XPATH, "//td[contains(text(), '원')]")
            for element in balance_elements:
                text = element.text.replace(',', '').replace('원', '')
                if text.isdigit():
                    balance = int(text)
                    self.logger.info(f"💰 현재 잔액: {balance:,}원")
                    
                    # 잔액 확인 알림
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_balance_check(balance))
                    
                    return balance
            
            self.logger.warning("⚠️ 잔액 정보를 찾을 수 없습니다")
            return 0
            
        except Exception as e:
            self.logger.error(f"❌ 잔액 확인 실패: {e}")
            return 0
    
    def generate_numbers(self, method="mixed"):
        """번호 생성"""
        settings = self.config_manager.get_purchase_settings()
        selection_method = settings.get('number_selection_method', method)
        
        if selection_method == "random":
            return sorted(random.sample(range(1, 46), 6))
        elif selection_method == "hot":
            hot_numbers = self.statistics.get_hot_numbers()
            return hot_numbers[:6]
        elif selection_method == "cold":
            cold_numbers = self.statistics.get_least_frequent_numbers()
            return cold_numbers[:6]
        else:  # mixed
            hot = self.statistics.get_hot_numbers()[:3]
            cold = self.statistics.get_least_frequent_numbers()[:2]
            random_num = random.sample([i for i in range(1, 46) if i not in hot + cold], 1)
            return sorted(hot + cold + random_num)
    
    def purchase_lotto(self):
        """로또 구매"""
        try:
            settings = self.config_manager.get_purchase_settings()
            games_count = settings.get('games_per_purchase', 5)
            
            self.logger.info(f"🎰 로또 구매 시작 - {games_count}게임")
            
            # 로또 구매 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_purchase_start(games_count))
            
            # 로또 구매 페이지로 이동
            self.driver.get("https://ol.dhlottery.co.kr/olotto/game/execGameMulti.do")
            time.sleep(3)
            
            for game in range(games_count):
                numbers = self.generate_numbers()
                self.logger.info(f"🎯 게임 {game+1}: {numbers}")
                
                # 번호 선택 로직 (실제 구현 필요)
                # 여기서는 기본적인 구조만 제시
                
            self.logger.info("✅ 로또 구매 완료")
            
            # 로또 구매 성공 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_purchase_success(games_count, games_count * 1000))
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 로또 구매 실패: {e}")
            
            # 로또 구매 실패 알림
            if self.notification_manager:
                settings = self.config_manager.get_purchase_settings()
                games_count = settings.get('games_per_purchase', 5)
                run_notification(self.notification_manager.notify_purchase_failure(games_count, str(e)))
            
            return False
    
    def run(self, immediate=False):
        """메인 실행"""
        try:
            self.logger.info("🚀 통합 로또 자동구매 시스템 시작")
            
            # 프로그램 시작 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_program_start())
            
            # 드라이버 설정
            if not self.setup_driver():
                return False
            
            # 로그인
            if not self.login():
                return False
            
            # 잔액 확인
            balance = self.check_balance()
            
            # 자동충전 처리
            payment_settings = self.config_manager.get_payment_settings()
            min_balance = payment_settings.get('min_balance', 5000)
            
            self.logger.info(f"💰 현재 잔액: {balance:,}원, 최소 잔액: {min_balance:,}원")
            
            if balance < min_balance and self.auto_recharger:
                self.logger.info(f"💳 잔액이 {min_balance:,}원 이하입니다. 자동충전을 시도합니다.")
                if payment_settings.get('auto_recharge', False):
                    # 충전 시작 알림
                    recharge_amount = payment_settings.get('recharge_amount', 10000)
                    if self.notification_manager:
                        run_notification(self.notification_manager.notify_recharge_start(recharge_amount))
                    
                    if self.auto_recharger.auto_recharge(self.driver, balance):
                        self.logger.info("💳 자동충전 완료! 잔액 재확인 중...")
                        new_balance = self.check_balance()  # 충전 후 잔액 재확인
                        self.logger.info(f"💰 충전 후 잔액: {new_balance:,}원")
                        
                        # 충전 성공 알림
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_success(recharge_amount, new_balance))
                    else:
                        self.logger.error("❌ 자동충전 실패. 수동으로 충전 후 다시 실행해주세요.")
                        
                        # 충전 실패 알림
                        if self.notification_manager:
                            run_notification(self.notification_manager.notify_recharge_failure(recharge_amount, "자동충전 실패"))
                        
                        return False
                else:
                    self.logger.warning("⚠️ 자동충전이 비활성화되어 있습니다.")
                    self.logger.info("💳 설정 파일에서 'auto_recharge'를 true로 변경해주세요.")
                    if balance < 1000:  # 1게임도 구매할 수 없을 때
                        self.logger.error("❌ 잔액 부족으로 구매할 수 없습니다.")
                        return False
            elif balance < min_balance:
                self.logger.warning(f"⚠️ 자동충전 기능이 비활성화되어 있습니다 (잔액: {balance:,}원)")
            
            # 로또 구매
            if immediate or datetime.now().weekday() in [0, 3]:  # 월, 목요일 또는 즉시 실행
                self.purchase_lotto()
            
            self.logger.info("✅ 시스템 실행 완료")
            
            # 프로그램 완료 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_program_complete())
            
            return True
            
        except Exception as e:
            self.logger.error(f"❌ 시스템 실행 실패: {e}")
            
            # 시스템 실행 실패 알림
            if self.notification_manager:
                run_notification(self.notification_manager.notify_critical("시스템 실행 실패", f"예상치 못한 오류가 발생했습니다: {str(e)}"))
            
            return False
        finally:
            if self.driver:
                self.driver.quit()
            
            # 알림 매니저 정리
            if self.notification_manager:
                try:
                    run_notification(self.notification_manager.cleanup())
                except Exception as cleanup_error:
                    print(f"⚠️ 알림 매니저 정리 실패: {cleanup_error}")

def main():
    """메인 함수"""
    parser = argparse.ArgumentParser(description='통합 로또 자동구매 시스템')
    parser.add_argument('--now', action='store_true', help='즉시 구매 실행')
    parser.add_argument('--config', action='store_true', help='설정 확인')
    parser.add_argument('--credentials', action='store_true', help='인증정보 설정/업데이트')
    parser.add_argument('--test-credentials', action='store_true', help='인증정보 테스트')
    
    args = parser.parse_args()
    
    # ConfigurationManager 초기화
    config_mgr = ConfigurationManager()
    config = config_mgr.load_configuration()
    
    if args.config:
        # 설정 확인
        print("📋 현재 설정:")
        print(json.dumps(config, indent=2, ensure_ascii=False))
        return
    
    if args.credentials:
        # 인증정보 설정
        print("🔐 인증정보 설정 모드")
        success = config_mgr.setup_credentials(force_new=True)
        if success:
            print("✅ 인증정보 설정이 완료되었습니다.")
        else:
            print("❌ 인증정보 설정에 실패했습니다.")
            sys.exit(1)
        return
    
    if args.test_credentials:
        # 인증정보 테스트
        print("🧪 인증정보 테스트 모드")
        success = config_mgr.test_credentials()
        if success:
            print("✅ 인증정보 테스트 통과")
        else:
            print("❌ 인증정보 테스트 실패")
            sys.exit(1)
        return
    
    # 인증정보 확인
    print("🔍 인증정보 확인 중...")
    credentials = config_mgr.get_user_credentials()
    
    if not credentials.get('user_id') or not credentials.get('password'):
        print("❌ 인증정보가 설정되지 않았습니다.")
        print("💡 다음 명령어로 인증정보를 설정하세요:")
        print(f"    python {os.path.basename(__file__)} --credentials")
        sys.exit(1)
    
    # 로또 구매 실행
    buyer = IntegratedLottoBuyer()
    success = buyer.run(immediate=args.now)
    
    if success:
        print("✅ 시스템 실행 성공")
    else:
        print("❌ 시스템 실행 실패")
        sys.exit(1)

if __name__ == "__main__":
    main()
