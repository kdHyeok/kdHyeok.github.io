"""
풀이 전략(TODO)이 아직 작성되지 않은 알고리즘 포스트 목록을 보여줍니다.
사용법: python find_todos.py
"""
import os
import re

POSTS_DIR = "_posts"
TODO_MARKER = "<!-- ✏️ TODO: 풀이 전략을 직접 작성해주세요 -->"


def main():
    todos = []
    for filename in sorted(os.listdir(POSTS_DIR)):
        if "baekjoon" not in filename or not filename.endswith(".md"):
            continue
        filepath = os.path.join(POSTS_DIR, filename)
        with open(filepath, encoding="utf-8") as f:
            content = f.read()
        if TODO_MARKER in content:
            # 제목 추출
            title_m = re.search(r'^title:\s*"(.+)"', content, re.MULTILINE)
            title = title_m.group(1) if title_m else filename
            todos.append((filename, title, filepath))

    if not todos:
        print("✅ 풀이 전략이 모두 작성되어 있습니다!")
        return

    print(f"✏️  풀이 전략 작성이 필요한 포스트 ({len(todos)}개):\n")
    for i, (fname, title, fpath) in enumerate(todos, 1):
        print(f"  {i}. {title}")
        print(f"     파일: {fpath}\n")


if __name__ == "__main__":
    main()
