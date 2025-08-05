#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
로또 자동구매 프로그램 통합 테스트
인증정보 암호화 + Discord 알림 기능 테스트
"""
import os
import sys
import asyncio
import subprocess

def test_dependencies():
    """의존성 확인"""
    print("🔍 의존성 확인 중...")
    
    required_packages = [
        ('cryptography', '인증정보 암호화'),
        ('aiohttp', 'Discord 알림'),
        ('selenium', '웹 자동화'),
    ]
    
    missing_packages = []
    
    for package, description in required_packages:
        try:
            __import__(package)
            print(f"✅ {package} - {description}")
        except ImportError:
            print(f"❌ {package} - {description}")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n❌ 누락된 패키지: {', '.join(missing_packages)}")
        print("💡 설치 명령어:")
        print(f"   pip install {' '.join(missing_packages)}")
        return False
    
    print("✅ 모든 의존성이 설치되어 있습니다.")
    return True

def test_credential_encryption():
    """인증정보 암호화 테스트"""
    print("\n🔐 인증정보 암호화 기능 테스트")
    print("-" * 30)
    
    try:
        from credential_manager import CredentialManager, UserCredentials
        
        # 테스트용 인증정보
        test_credentials = UserCredentials(
            user_id="test_user_integration",
            password="test_pass_integration",
            recharge_password="123456"
        )
        
        # 테스트 파일
        test_file = "test_integration_credentials.enc"
        manager = CredentialManager(test_file)
        
        # 저장 테스트
        print("💾 암호화 저장 테스트...")
        success = manager.save_credentials(test_credentials, "test_master_pass_123")
        if not success:
            print("❌ 인증정보 저장 실패")
            return False
        print("✅ 인증정보 저장 성공")
        
        # 로드 테스트
        print("📂 암호화 로드 테스트...")
        loaded = manager.load_credentials("test_master_pass_123")
        if not loaded:
            print("❌ 인증정보 로드 실패")
            return False
        
        # 데이터 일치 확인
        if (loaded.user_id == test_credentials.user_id and
            loaded.password == test_credentials.password and
            loaded.recharge_password == test_credentials.recharge_password):
            print("✅ 인증정보 로드 및 일치 확인 성공")
        else:
            print("❌ 로드된 데이터 불일치")
            return False
        
        # 정리
        if os.path.exists(test_file):
            os.remove(test_file)
            print("✅ 테스트 파일 정리 완료")
        
        return True
        
    except Exception as e:
        print(f"❌ 인증정보 암호화 테스트 실패: {e}")
        return False

async def test_discord_notification():
    """Discord 알림 테스트"""
    print("\n🔔 Discord 알림 기능 테스트")
    print("-" * 30)
    
    try:
        from discord_notifier import NotificationManager
        
        # 테스트용 설정
        test_config = {
            "notifications": {
                "discord": {
                    "enabled": False,  # 테스트용으로 비활성화
                    "webhook_url": "",
                    "notify_login": True,
                    "notify_balance": True,
                    "notify_recharge": True,
                    "notify_purchase": True,
                    "notify_errors": True
                }
            }
        }
        
        # NotificationManager 생성
        manager = NotificationManager(test_config)
        
        if manager.discord_notifier:
            print("❌ Discord가 비활성화되어야 하는데 활성화됨")
            return False
        
        print("✅ Discord 비활성화 상태 정상 확인")
        
        # 활성화 테스트 (웹훅 URL 없음)
        test_config["notifications"]["discord"]["enabled"] = True
        manager = NotificationManager(test_config)
        
        if manager.discord_notifier and manager.discord_notifier.is_enabled():
            print("❌ 웹훅 URL 없이도 활성화됨")
            return False
        
        print("✅ 웹훅 URL 없을 때 비활성화 확인")
        
        # 모듈 로드 테스트
        print("✅ Discord 알림 모듈 로드 성공")
        return True
        
    except Exception as e:
        print(f"❌ Discord 알림 테스트 실패: {e}")
        return False

def test_integrated_configuration():
    """통합 설정 테스트"""
    print("\n⚙️ 통합 설정 테스트")
    print("-" * 30)
    
    try:
        from lotto_auto_buyer_integrated import ConfigurationManager
        
        # ConfigurationManager 생성
        config_manager = ConfigurationManager()
        config = config_manager.load_configuration()
        
        if not config:
            print("❌ 설정 로드 실패")
            return False
        
        print("✅ 설정 파일 로드 성공")
        
        # Discord 설정 확인
        discord_config = config.get('notifications', {}).get('discord', {})
        if 'enabled' not in discord_config:
            print("❌ Discord 설정 구조 누락")
            return False
        
        print("✅ Discord 설정 구조 확인")
        
        # 인증정보 관리자 확인
        if config_manager.credential_manager:
            print("✅ 인증정보 관리자 초기화 성공")
        else:
            print("⚠️ 인증정보 관리자 비활성화 (정상)")
        
        return True
        
    except Exception as e:
        print(f"❌ 통합 설정 테스트 실패: {e}")
        return False

def test_command_line_options():
    """명령줄 옵션 테스트"""
    print("\n🖥️ 명령줄 옵션 테스트")
    print("-" * 30)
    
    try:
        # --help 옵션 테스트
        result = subprocess.run([
            sys.executable, 'lotto_auto_buyer_integrated.py', '--help'
        ], capture_output=True, text=True, timeout=10)
        
        if result.returncode != 0:
            print("❌ --help 옵션 실패")
            return False
        
        help_text = result.stdout
        required_options = ['--credentials', '--test-credentials', '--now', '--config']
        
        missing_options = []
        for option in required_options:
            if option not in help_text:
                missing_options.append(option)
        
        if missing_options:
            print(f"❌ 누락된 옵션: {', '.join(missing_options)}")
            return False
        
        print("✅ 모든 명령줄 옵션 확인")
        return True
        
    except Exception as e:
        print(f"❌ 명령줄 옵션 테스트 실패: {e}")
        return False

def main():
    """메인 테스트 함수"""
    print("🧪 로또 자동구매 프로그램 통합 테스트")
    print("=" * 50)
    
    # 현재 디렉토리 확인
    if not os.path.exists('lotto_config.json'):
        print("❌ lotto_config.json 파일을 찾을 수 없습니다.")
        print("💡 올바른 디렉토리에서 실행하세요.")
        return False
    
    tests = [
        ("의존성 확인", test_dependencies),
        ("인증정보 암호화", test_credential_encryption),
        ("Discord 알림", lambda: asyncio.run(test_discord_notification())),
        ("통합 설정", test_integrated_configuration),
        ("명령줄 옵션", test_command_line_options),
    ]
    
    passed_tests = 0
    total_tests = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n🔍 {test_name} 테스트 중...")
        try:
            if test_func():
                passed_tests += 1
                print(f"✅ {test_name} 테스트 통과")
            else:
                print(f"❌ {test_name} 테스트 실패")
        except Exception as e:
            print(f"❌ {test_name} 테스트 오류: {e}")
    
    print("\n" + "=" * 50)
    print(f"📊 테스트 결과: {passed_tests}/{total_tests} 통과")
    
    if passed_tests == total_tests:
        print("🎉 모든 테스트 통과! 시스템이 정상 작동합니다.")
        print("\n📋 다음 단계:")
        print("1. Discord 알림 설정:")
        print("   python setup_discord.py")
        print()
        print("2. 인증정보 설정:")
        print("   python lotto_auto_buyer_integrated.py --credentials")
        print()
        print("3. 로또 자동구매 실행:")
        print("   python lotto_auto_buyer_integrated.py --now")
        return True
    else:
        print("❌ 일부 테스트 실패. 문제를 해결한 후 다시 시도하세요.")
        return False

if __name__ == "__main__":
    try:
        success = main()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        print("\n❌ 테스트가 사용자에 의해 중단되었습니다.")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ 테스트 실행 오류: {e}")
        sys.exit(1)
