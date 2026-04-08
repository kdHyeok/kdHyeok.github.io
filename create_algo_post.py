"""
Algorithms 레포의 README를 읽어 _posts/ 에 Jekyll 포스트로 동기화합니다.
- 포스트가 없으면 새로 생성
- README가 변경됐으면 기존 포스트를 덮어씀
- 사용자가 README에 추가한 섹션(풀이 전략 등)도 그대로 반영
"""
import requests
import os
import re
import hashlib

USERNAME = "kdHyeok"
ALGO_REPO = "Algorithms"


def get_headers():
    token = os.environ.get("GITHUB_TOKEN")
    return {"Authorization": f"token {token}"} if token else {}


def get_recent_commits():
    url = f"https://api.github.com/repos/{USERNAME}/{ALGO_REPO}/commits?per_page=100"
    resp = requests.get(url, headers=get_headers())
    return resp.json() if resp.status_code == 200 else []


def get_commit_files(sha):
    url = f"https://api.github.com/repos/{USERNAME}/{ALGO_REPO}/commits/{sha}"
    resp = requests.get(url, headers=get_headers())
    return resp.json().get("files", []) if resp.status_code == 200 else []


def get_raw(raw_url):
    resp = requests.get(raw_url, headers=get_headers())
    return resp.text if resp.status_code == 200 else ""


def parse_code_path(filepath):
    """백준/{Tier}/{num}. {title}/{title}.{ext}"""
    pattern = r"백준/([^/]+)/(\d+)\.\s*(.+?)/[^/]+\.(cpp|cc|java|py|kt|js|ts)$"
    m = re.match(pattern, filepath)
    if m:
        return m.group(1), m.group(2), m.group(3).strip(), m.group(4)
    return None, None, None, None


def parse_readme_path(filepath):
    """백준/{Tier}/{num}. {title}/README.md"""
    m = re.match(r"백준/([^/]+)/(\d+)\.\s*(.+?)/README\.md$", filepath)
    if m:
        return m.group(1), m.group(2), m.group(3).strip()
    return None, None, None


def extract_section(text, heading):
    """### heading 섹션 내용을 추출하고 원문에서 제거한 텍스트도 반환"""
    pattern = rf"### {heading}\s*\n([\s\S]+?)(?=\n###|\Z)"
    m = re.search(pattern, text)
    value = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    cleaned = re.sub(pattern, "", text).strip()
    return value, cleaned


def readme_to_post_body(readme_text, tags):
    """
    BaekjoonHub README를 Jekyll 포스트 본문으로 변환.
    - 첫 번째 h1 제거
    - ### 분류 / 성능 요약 / 제출 일자 섹션 제거
    - 최상단에 태그 링크 + 정보 박스 삽입
    """
    lines = readme_text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start = i + 1
            break
    body = "\n".join(lines[start:]).strip()

    # 섹션 추출 및 제거
    performance, body = extract_section(body, "성능 요약")
    submitted,   body = extract_section(body, "제출 일자")
    _,           body = extract_section(body, "분류")

    # 정보 박스 (성능 요약 + 제출 일자)
    info_items = []
    if performance:
        info_items.append(f'<span>💾 {performance}</span>')
    if submitted:
        info_items.append(f'<span>📅 {submitted}</span>')
    info_box = ""
    if info_items:
        info_box = (
            '<div class="post-info-box">'
            + "".join(info_items)
            + "</div>\n\n"
        )

    # 태그 링크 블록
    tag_block = ""
    if tags:
        def slugify(t):
            return re.sub(r"[\s/]+", "-", t.strip())
        tag_links = " ".join(
            f'<a href="/tags/{slugify(t)}/" class="post-tag">{t}</a>'
            for t in tags
        )
        tag_block = f'<div class="post-tags-top">{tag_links}</div>\n\n'

    return tag_block + info_box + body


def extract_meta(readme_text):
    """README에서 태그, 성능 정보 추출"""
    result = {"tags": [], "performance": ""}

    perf = re.search(r"메모리:\s*(.+?),\s*시간:\s*(.+)", readme_text)
    if perf:
        result["performance"] = f"메모리: {perf.group(1).strip()}, 시간: {perf.group(2).strip()}"

    cat = re.search(r"### 분류\s*\n+([\s\S]+?)(?=\n###|\Z)", readme_text)
    if cat:
        raw = re.sub(r"<[^>]+>", "", cat.group(1)).strip()
        result["tags"] = [t.strip() for t in raw.split(",") if t.strip()]

    return result


def post_path(num, date_str):
    return f"_posts/{date_str}-baekjoon-{num}.md"


def find_existing_post(num):
    """이미 만들어진 포스트 파일 경로 반환 (날짜 무관)"""
    if not os.path.isdir("_posts"):
        return None
    for f in os.listdir("_posts"):
        if f"baekjoon-{num}" in f:
            return os.path.join("_posts", f)
    return None


def readme_hash(readme_text):
    return hashlib.md5(readme_text.encode()).hexdigest()


def read_stored_hash(post_file):
    """포스트 front matter에서 저장된 README 해시 읽기"""
    try:
        with open(post_file, encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"^readme_hash:\s*(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else None
    except FileNotFoundError:
        return None


def create_or_update_post(tier, num, title, readme_text, code_text, date_str, ext):
    lang_map = {"cpp": "cpp", "cc": "cpp", "java": "java", "py": "python",
                "kt": "kotlin", "js": "javascript", "ts": "typescript"}
    lang_display_map = {"cpp": "C++", "cc": "C++", "java": "Java", "py": "Python",
                        "kt": "Kotlin", "js": "JavaScript", "ts": "TypeScript"}
    lang = lang_map.get(ext, ext)
    lang_display = lang_display_map.get(ext, ext)

    current_hash = readme_hash(readme_text)
    existing = find_existing_post(num)

    if existing and read_stored_hash(existing) == current_hash:
        return "skip"

    meta = extract_meta(readme_text)
    tags_yaml = ", ".join(meta["tags"]) if meta["tags"] else ""
    body = readme_to_post_body(readme_text, meta["tags"])

    # 코드 블록이 README에 없으면 자동 삽입
    if code_text and "```" not in body:
        body += f"\n\n### 코드 ({lang_display})\n\n```{lang}\n{code_text.strip()}\n```"

    filepath = existing if existing else post_path(num, date_str)

    content = f"""---
layout: post
title: "[Baekjoon] {num}번: {title} - {lang_display} 풀이"
date: {date_str} 00:00:00 +0900
categories: algorithm
tags: [{tags_yaml}]
toc: true
permalink: /algorithm/boj/{num}/
readme_hash: {current_hash}
---

{body}
"""

    os.makedirs("_posts", exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return "updated" if existing else "created"


def main():
    commits = get_recent_commits()
    created = updated = skipped = 0

    # 커밋별로 코드 파일과 README 파일을 매핑
    seen_nums = set()

    for commit in commits:
        sha = commit["sha"]
        date_str = commit["commit"]["author"]["date"][:10]
        files = get_commit_files(sha)

        code_files = {}
        readme_files = {}

        for f in files:
            filepath = f.get("filename", "")
            tier, num, title, ext = parse_code_path(filepath)
            if num:
                code_files[num] = {"tier": tier, "title": title, "ext": ext,
                                   "raw_url": f.get("raw_url", ""), "date": date_str}
            else:
                r_tier, r_num, r_title = parse_readme_path(filepath)
                if r_num:
                    readme_files[r_num] = {"raw_url": f.get("raw_url", ""),
                                           "tier": r_tier, "title": r_title, "date": date_str}

        # 코드 또는 README가 있는 문제 처리
        all_nums = set(code_files.keys()) | set(readme_files.keys())
        for num in all_nums:
            if num in seen_nums:
                continue
            seen_nums.add(num)

            code_info = code_files.get(num, {})
            readme_info = readme_files.get(num, code_info)

            tier = code_info.get("tier") or readme_info.get("tier", "")
            title = code_info.get("title") or readme_info.get("title", num)
            ext = code_info.get("ext", "cpp")
            date = code_info.get("date") or readme_info.get("date", date_str)

            readme_url = readme_info.get("raw_url", "")
            code_url = code_info.get("raw_url", "")

            readme_text = get_raw(readme_url) if readme_url else ""
            code_text = get_raw(code_url) if code_url else ""

            if not readme_text:
                continue

            result = create_or_update_post(tier, num, title, readme_text, code_text, date, ext)
            if result == "created":
                print(f"생성됨: {num}번 {title}")
                created += 1
            elif result == "updated":
                print(f"업데이트됨: {num}번 {title}")
                updated += 1
            else:
                skipped += 1

    print(f"\n생성: {created}개 | 업데이트: {updated}개 | 변경 없음: {skipped}개")


if __name__ == "__main__":
    main()
