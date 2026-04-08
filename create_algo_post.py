"""
Algorithms 레포의 README를 읽어 _posts/ 에 Jekyll 포스트로 동기화합니다.
- 백준(BaekjoonHub), SWEA 지원
- 포스트가 없으면 새로 생성
- README가 변경됐으면 기존 포스트를 덮어씀
"""
import requests
import os
import re
import hashlib

USERNAME = "kdHyeok"
ALGO_REPO = "Algorithms"

# 지원 플랫폼 파서 정의
# (prefix, code_pattern, readme_pattern, oj_name, permalink_prefix)
PLATFORMS = [
    {
        "oj": "baekjoon",
        "label": "Baekjoon",
        "code_re": r"백준/([^/]+)/(\d+)\.\s*(.+?)/[^/]+\.(cpp|cc|java|py|kt|js|ts)$",
        "readme_re": r"백준/([^/]+)/(\d+)\.\s*(.+?)/README\.md$",
        "permalink": "/algorithm/boj/{num}/",
        "post_prefix": "boj",
        "title_fmt": "[Baekjoon] {num}번: {title} - {lang} 풀이",
    },
    {
        "oj": "swea",
        "label": "SWEA",
        "code_re": r"SWEA/([^/]+)/(\d+)\.\s*(.+?)/[^/]+\.(cpp|cc|java|py|kt|js|ts)$",
        "readme_re": r"SWEA/([^/]+)/(\d+)\.\s*(.+?)/README\.md$",
        "permalink": "/algorithm/swea/{num}/",
        "post_prefix": "swea",
        "title_fmt": "[SWEA] {num}번: {title} - {lang} 풀이",
    },
]

LANG_MAP = {"cpp": "cpp", "cc": "cpp", "java": "java", "py": "python",
            "kt": "kotlin", "js": "javascript", "ts": "typescript"}
LANG_DISPLAY = {"cpp": "C++", "cc": "C++", "java": "Java", "py": "Python",
                "kt": "Kotlin", "js": "JavaScript", "ts": "TypeScript"}


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


def match_platform(filepath):
    """파일 경로에서 플랫폼, tier, num, title, ext 반환"""
    for p in PLATFORMS:
        m = re.match(p["code_re"], filepath)
        if m:
            return p, m.group(1), m.group(2), m.group(3).strip(), m.group(4)
        m = re.match(p["readme_re"], filepath)
        if m:
            return p, m.group(1), m.group(2), m.group(3).strip(), None
    return None, None, None, None, None


def extract_section(text, heading):
    pattern = rf"### {heading}\s*\n([\s\S]+?)(?=\n###|\Z)"
    m = re.search(pattern, text)
    value = re.sub(r"<[^>]+>", "", m.group(1)).strip() if m else ""
    cleaned = re.sub(pattern, "", text).strip()
    return value, cleaned


def slugify(t):
    return re.sub(r"[\s/]+", "-", t.strip())


def readme_to_post_body(readme_text, tags):
    lines = readme_text.splitlines()
    start = 0
    for i, line in enumerate(lines):
        if line.startswith("# "):
            start = i + 1
            break
    body = "\n".join(lines[start:]).strip()

    performance, body = extract_section(body, "성능 요약")
    submitted,   body = extract_section(body, "제출 일자")
    _,           body = extract_section(body, "분류")

    info_items = []
    if performance:
        info_items.append(f'<span>💾 {performance}</span>')
    if submitted:
        info_items.append(f'<span>📅 {submitted}</span>')
    info_box = (
        '<div class="post-info-box">' + "".join(info_items) + "</div>\n\n"
        if info_items else ""
    )

    tag_block = ""
    if tags:
        tag_links = " ".join(
            f'<a href="/tags/{slugify(t)}/" class="post-tag">{t}</a>'
            for t in tags
        )
        tag_block = f'<div class="post-tags-top">{tag_links}</div>\n\n'

    return tag_block + info_box + body


EXCLUDE_TAGS = {"자료 구조"}

def extract_meta(readme_text):
    result = {"tags": []}
    cat = re.search(r"### 분류\s*\n+([\s\S]+?)(?=\n###|\Z)", readme_text)
    if cat:
        raw = re.sub(r"<[^>]+>", "", cat.group(1)).strip()
        result["tags"] = [t.strip() for t in raw.split(",")
                          if t.strip() and t.strip() not in EXCLUDE_TAGS]
    return result


def readme_hash(text):
    return hashlib.md5(text.encode()).hexdigest()


def find_existing_post(prefix, num):
    if not os.path.isdir("_posts"):
        return None
    for f in os.listdir("_posts"):
        if f"{prefix}-{num}" in f:
            return os.path.join("_posts", f)
    return None


def read_stored_hash(post_file):
    try:
        with open(post_file, encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"^readme_hash:\s*(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else None
    except FileNotFoundError:
        return None


def create_or_update_post(platform, tier, num, title, readme_text, code_text, date_str, ext):
    lang = LANG_MAP.get(ext, ext or "cpp")
    lang_disp = LANG_DISPLAY.get(ext, ext or "C++")

    current_hash = readme_hash(readme_text)
    prefix = platform["post_prefix"]
    existing = find_existing_post(prefix, num)

    if existing and read_stored_hash(existing) == current_hash:
        return "skip"

    meta = extract_meta(readme_text)
    tags_yaml = ", ".join(meta["tags"]) if meta["tags"] else ""
    body = readme_to_post_body(readme_text, meta["tags"])

    if code_text and "```" not in body:
        body += f"\n\n### 코드 ({lang_disp})\n\n```{lang}\n{code_text.strip()}\n```"

    filepath = existing if existing else f"_posts/{date_str}-{prefix}-{num}.md"
    permalink = platform["permalink"].format(num=num)
    post_title = platform["title_fmt"].format(num=num, title=title, lang=lang_disp)

    content = f"""---
layout: post
title: "{post_title}"
date: {date_str} 00:00:00 +0900
categories: algorithm
tags: [{tags_yaml}]
toc: true
permalink: {permalink}
platform: {platform["oj"]}
lang: {lang_disp}
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
    seen = set()  # (prefix, num)

    for commit in commits:
        sha = commit["sha"]
        date_str = commit["commit"]["author"]["date"][:10]
        files = get_commit_files(sha)

        code_files   = {}
        readme_files = {}

        for f in files:
            filepath = f.get("filename", "")
            platform, tier, num, title, ext = match_platform(filepath)
            if not platform:
                continue
            key = (platform["post_prefix"], num)
            if ext:
                code_files[key] = {"platform": platform, "tier": tier,
                                   "title": title, "ext": ext,
                                   "raw_url": f.get("raw_url", ""), "date": date_str}
            else:
                readme_files[key] = {"platform": platform, "tier": tier,
                                     "title": title,
                                     "raw_url": f.get("raw_url", ""), "date": date_str}

        for key in set(code_files) | set(readme_files):
            if key in seen:
                continue
            seen.add(key)

            code_info   = code_files.get(key, {})
            readme_info = readme_files.get(key, code_info)

            platform = code_info.get("platform") or readme_info.get("platform")
            tier  = code_info.get("tier")  or readme_info.get("tier", "")
            title = code_info.get("title") or readme_info.get("title", key[1])
            ext   = code_info.get("ext", "cpp")
            date  = code_info.get("date")  or readme_info.get("date", date_str)

            readme_text = get_raw(readme_info["raw_url"]) if readme_info.get("raw_url") else ""
            code_text   = get_raw(code_info["raw_url"])   if code_info.get("raw_url")   else ""

            if not readme_text:
                continue

            result = create_or_update_post(platform, tier, key[1], title,
                                           readme_text, code_text, date, ext)
            label = platform["label"]
            if result == "created":
                print(f"[{label}] 생성됨: {key[1]}번 {title}")
                created += 1
            elif result == "updated":
                print(f"[{label}] 업데이트됨: {key[1]}번 {title}")
                updated += 1
            else:
                skipped += 1

    print(f"\n생성: {created}개 | 업데이트: {updated}개 | 변경 없음: {skipped}개")


if __name__ == "__main__":
    main()
