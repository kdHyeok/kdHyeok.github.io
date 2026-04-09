import subprocess
import sys
import os

def load_env():
    env_file = os.path.join(os.path.dirname(__file__), ".env")
    if not os.path.exists(env_file):
        return
    with open(env_file, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line or line.startswith("#") or "=" not in line:
                continue
            key, _, value = line.partition("=")
            os.environ.setdefault(key.strip(), value.strip())

load_env()

def run_update_script():
    print("--- 1. GitHub 데이터 업데이트 시작 ---")
    try:
        subprocess.run([sys.executable, "update_projects.py"], check=True)
        print("--- 데이터 업데이트 완료 ---\n")
    except subprocess.CalledProcessError as e:
        print(f"에러 발생: 데이터 업데이트 중 문제가 발생했습니다. ({e})")
        sys.exit(1)

def run_algo_post_script():
    print("--- 2. 알고리즘 포스트 생성 시작 ---")
    try:
        subprocess.run([sys.executable, "create_algo_post.py"], check=True)
        print("--- 알고리즘 포스트 생성 완료 ---\n")
    except subprocess.CalledProcessError as e:
        print(f"에러 발생: 알고리즘 포스트 생성 중 문제가 발생했습니다. ({e})")
        sys.exit(1)

def run_chatter_post_script():
    print("--- 3. 잡담 포스트 동기화 시작 ---")
    try:
        subprocess.run([sys.executable, "create_chatter_post.py"], check=True)
        print("--- 잡담 포스트 동기화 완료 ---\n")
    except subprocess.CalledProcessError as e:
        print(f"에러 발생: 잡담 포스트 동기화 중 문제가 발생했습니다. ({e})")
        sys.exit(1)

def start_jekyll_server():
    print("--- 4. Jekyll 서버 기동 ---")
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
    run_algo_post_script()
    run_chatter_post_script()
    start_jekyll_server()