import requests
import os
import re

USERNAME = "kdHyeok"
ALGO_REPO = "Algorithms"


def get_headers():
    headers = {}
    token = os.environ.get("GITHUB_TOKEN")
    if token:
        headers["Authorization"] = f"token {token}"
    return headers


def get_recent_commits():
    url = f"https://api.github.com/repos/{USERNAME}/{ALGO_REPO}/commits?per_page=50"
    resp = requests.get(url, headers=get_headers())
    return resp.json() if resp.status_code == 200 else []


def get_commit_files(sha):
    url = f"https://api.github.com/repos/{USERNAME}/{ALGO_REPO}/commits/{sha}"
    resp = requests.get(url, headers=get_headers())
    return resp.json().get("files", []) if resp.status_code == 200 else []


def get_raw(raw_url):
    resp = requests.get(raw_url, headers=get_headers())
    return resp.text if resp.status_code == 200 else ""


def parse_path(filepath):
    """백준/{Tier}/{num}. {title}/{title}.{ext}"""
    pattern = r"백준/([^/]+)/(\d+)\.\s*(.+?)/[^/]+\.(cpp|cc|java|py|kt|js|ts)$"
    m = re.match(pattern, filepath)
    if m:
        return m.group(1), m.group(2), m.group(3).strip(), m.group(4)
    return None, None, None, None


def parse_readme(readme_text):
    """BaekjoonHub README에서 필요한 섹션 추출"""
    result = {"performance": "", "categories": "", "description": "", "input": "", "output": ""}

    perf = re.search(r"메모리:\s*(.+?),\s*시간:\s*(.+)", readme_text)
    if perf:
        result["performance"] = f"메모리: {perf.group(1).strip()}, 시간: {perf.group(2).strip()}"

    cat = re.search(r"### 분류\s*\n+([\s\S]+?)(?=\n###|\Z)", readme_text)
    if cat:
        result["categories"] = cat.group(1).strip()

    desc = re.search(r"### 문제 설명\s*\n+([\s\S]+?)(?=\n###|\Z)", readme_text)
    if desc:
        # HTML 태그 제거
        text = re.sub(r"<[^>]+>", "", desc.group(1)).strip()
        result["description"] = text

    inp = re.search(r"### 입력\s*\n+([\s\S]+?)(?=\n###|\Z)", readme_text)
    if inp:
        text = re.sub(r"<[^>]+>", "", inp.group(1)).strip()
        result["input"] = text

    out = re.search(r"### 출력\s*\n+([\s\S]+?)(?=\n###|\Z)", readme_text)
    if out:
        text = re.sub(r"<[^>]+>", "", out.group(1)).strip()
        result["output"] = text

    return result


def post_exists(num):
    posts_dir = "_posts"
    if not os.path.isdir(posts_dir):
        return False
    return any(f"baekjoon-{num}" in f for f in os.listdir(posts_dir))


def create_post(tier, num, title, code, readme_text, date_str, ext):
    lang_map = {"cpp": "cpp", "cc": "cpp", "java": "java", "py": "python",
                "kt": "kotlin", "js": "javascript", "ts": "typescript"}
    lang_display_map = {"cpp": "C++", "cc": "C++", "java": "Java", "py": "Python",
                        "kt": "Kotlin", "js": "JavaScript", "ts": "TypeScript"}
    lang = lang_map.get(ext, ext)
    lang_display = lang_display_map.get(ext, ext)

    info = parse_readme(readme_text)
    boj_url = f"https://www.acmicpc.net/problem/{num}"
    filename = f"_posts/{date_str}-baekjoon-{num}.md"

    desc_block = ""
    if info["description"]:
        desc_block = info["description"]
    if info["input"]:
        desc_block += f"\n\n**입력**\n\n{info['input']}"
    if info["output"]:
        desc_block += f"\n\n**출력**\n\n{info['output']}"

    perf_line = f"\n> {info['performance']}" if info["performance"] else ""

    # 분류를 tags 배열로 변환
    algo_tags = ["baekjoon", tier.lower()]
    if info["categories"]:
        algo_tags += [t.strip() for t in info["categories"].split(",")]
    tags_yaml = ", ".join(algo_tags)

    content = f"""---
layout: post
title: "[Baekjoon] {num}번: {title} - {lang_display} 풀이"
date: {date_str} 00:00:00 +0900
categories: algorithm
tags: [{tags_yaml}]
toc: true
excerpt: "백준 {num}번 {title} 풀이입니다."
---

## 문제 링크

[{num}번: {title}]({boj_url}){perf_line}

## 문제 설명

{desc_block if desc_block else "<!-- 문제 설명 -->"}

## 풀이 전략 (Approach)

<!-- ✏️ TODO: 풀이 전략을 직접 작성해주세요 -->

## 코드 ({lang_display})

```{lang}
{code.strip()}
```
"""

    os.makedirs("_posts", exist_ok=True)
    with open(filename, "w", encoding="utf-8") as f:
        f.write(content)
    print(f"생성됨: {filename}")


def main():
    commits = get_recent_commits()
    created = 0

    for commit in commits:
        sha = commit["sha"]
        date_str = commit["commit"]["author"]["date"][:10]
        files = get_commit_files(sha)

        # 같은 커밋의 코드파일과 README를 함께 처리
        code_files = {}
        readme_files = {}

        for f in files:
            filepath = f.get("filename", "")
            tier, num, title, ext = parse_path(filepath)
            if num:
                code_files[num] = {"tier": tier, "title": title, "ext": ext,
                                   "raw_url": f.get("raw_url", ""), "date": date_str}
            elif re.match(r"백준/[^/]+/(\d+)\..+/README\.md$", filepath):
                m = re.match(r"백준/[^/]+/(\d+)\.", filepath)
                if m:
                    readme_files[m.group(1)] = f.get("raw_url", "")

        for num, info in code_files.items():
            if post_exists(num):
                continue
            code = get_raw(info["raw_url"])
            readme_text = get_raw(readme_files[num]) if num in readme_files else ""
            create_post(info["tier"], num, info["title"], code, readme_text,
                        info["date"], info["ext"])
            created += 1

    print(f"총 {created}개의 포스트가 새로 생성되었습니다.")


if __name__ == "__main__":
    main()
