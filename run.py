import subprocess
import sys
import os

def run_update_script():
    print("--- 1. GitHub 데이터 업데이트 시작 ---")
    try:
        # 현재 디렉토리에 있는 update_projects.py 실행
        result = subprocess.run([sys.executable, "update_projects.py"], check=True)
        print("--- 데이터 업데이트 완료 ---\n")
    except subprocess.CalledProcessError as e:
        print(f"에러 발생: 데이터 업데이트 중 문제가 발생했습니다. ({e})")
        sys.exit(1)

def start_jekyll_server():
    print("--- 2. Jekyll 서버 기동 ---")
    # 실행할 명령어 리스트
    command = ["bundle", "exec", "jekyll", "serve", "--host", "0.0.0.0"]
    
    try:
        # 서버는 계속 떠 있어야 하므로 run()을 사용 (프로세스가 종료될 때까지 대기)
        subprocess.run(command, check=True)
    except KeyboardInterrupt:
        print("\n--- 서버를 종료합니다. ---")
    except Exception as e:
        print(f"서버 실행 중 에러 발생: {e}")

if __name__ == "__main__":
    run_update_script()
    start_jekyll_server()