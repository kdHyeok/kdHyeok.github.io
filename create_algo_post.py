"""
Notion 알고리즘 DB에서 '포스팅 상태' = '완료'인 항목을 읽어
_posts/boj/, _posts/swea/ 에 Jekyll 포스트로 동기화합니다.
- '최종 편집 일시' 기준으로 변경 감지
- 문제 설명 섹션은 알고리즘 레포 README 원문(HTML) 우선 사용
- README 없으면 Notion 블록 변환 내용 사용
"""
import requests
import os
import re
import base64
from datetime import datetime
from urllib.parse import quote as urlquote

NOTION_TOKEN = os.environ.get("NOTION_TOKEN", "")
NOTION_ALGO_DB_ID = os.environ.get("NOTION_ALGO_DB_ID", "")
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

GITHUB_USERNAME = "kdHyeok"
ALGO_REPO = "Algorithms"

PLATFORMS = {
    "백준": {
        "oj": "baekjoon", "post_prefix": "boj",
        "permalink": "/algorithm/boj/{num}/", "label": "Baekjoon",
        "repo_base": "백준",
    },
    "SWEA": {
        "oj": "swea", "post_prefix": "swea",
        "permalink": "/algorithm/swea/{num}/", "label": "SWEA",
        "repo_base": "SWEA",
    },
}


def get_platform_info(site: str) -> dict:
    """알려진 플랫폼은 PLATFORMS에서, 없으면 site 이름으로 자동 생성"""
    if site in PLATFORMS:
        return PLATFORMS[site]
    slug = re.sub(r"[^\w가-힣]", "", site).lower() or "etc"
    return {
        "oj": slug,
        "post_prefix": slug,
        "permalink": f"/algorithm/{slug}/{{num}}/",
        "label": site,
        "repo_base": site,
    }

LANG_CODE_MAP = {
    "C++": "cpp", "Java": "java", "Python": "python",
    "Kotlin": "kotlin", "JavaScript": "javascript", "TypeScript": "typescript",
}

NOTION_LANG_MAP = {
    "c++": "cpp", "java": "java", "python": "python",
    "kotlin": "kotlin", "javascript": "javascript", "typescript": "typescript",
    "plain text": "", "text": "",
}


# ─── Notion API ──────────────────────────────────────────────────────────────

def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_algo_db():
    url = f"{NOTION_API}/databases/{NOTION_ALGO_DB_ID}/query"
    payload = {"filter": {"property": "포스팅 상태", "status": {"equals": "완료"}}}
    pages = []
    while True:
        resp = requests.post(url, headers=notion_headers(), json=payload)
        if resp.status_code != 200:
            print(f"Notion DB 조회 실패: {resp.status_code} {resp.text[:200]}")
            return []
        data = resp.json()
        pages.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        payload["start_cursor"] = data["next_cursor"]
    return pages


def get_block_children(block_id):
    url = f"{NOTION_API}/blocks/{block_id}/children?page_size=100"
    blocks = []
    while True:
        resp = requests.get(url, headers=notion_headers())
        if resp.status_code != 200:
            break
        data = resp.json()
        blocks.extend(data.get("results", []))
        if not data.get("has_more"):
            break
        url = (f"{NOTION_API}/blocks/{block_id}/children"
               f"?page_size=100&start_cursor={data['next_cursor']}")
    return blocks


# ─── GitHub API ──────────────────────────────────────────────────────────────

def github_headers():
    token = os.environ.get("GITHUB_TOKEN", "")
    return {"Authorization": f"token {token}"} if token else {}


def fetch_readme_from_repo(platform_info, num, title, level):
    """
    알고리즘 레포에서 README.md 원문을 가져온다.
    폴더 구조: {base}/{lang_tier}/{num}. {title} ({level})/README.md
    lang_tier를 모르므로 base 하위 디렉토리를 먼저 조회해서 찾는다.
    """
    base = platform_info["repo_base"]
    encoded_base = urlquote(base, safe="")
    url = f"https://api.github.com/repos/{GITHUB_USERNAME}/{ALGO_REPO}/contents/{encoded_base}"
    resp = requests.get(url, headers=github_headers())
    if resp.status_code != 200 or not isinstance(resp.json(), list):
        return None

    # lang_tier 후보 목록 (C++17, C++, Java 등)
    lang_tiers = [item["name"] for item in resp.json() if item["type"] == "dir"]

    folder_name = f"{num}. {title} ({level})"
    for tier in lang_tiers:
        path = f"{base}/{tier}/{folder_name}/README.md"
        encoded = "/".join(urlquote(seg, safe="") for seg in path.split("/"))
        r = requests.get(
            f"https://api.github.com/repos/{GITHUB_USERNAME}/{ALGO_REPO}/contents/{encoded}",
            headers=github_headers(),
        )
        if r.status_code == 200:
            content = base64.b64decode(r.json()["content"]).decode("utf-8")
            return content

    return None


def extract_problem_section_from_readme(readme_text, problem_url=""):
    """README에서 문제 설명·입력·출력 섹션을 원문(HTML) 그대로 추출"""
    parts = []

    if problem_url:
        parts.append(f"[문제 링크]({problem_url})\n")

    for section_name, heading in [("문제 설명", "문제"), ("입력", "입력"), ("출력", "출력")]:
        # ### 문제 설명 또는 ### 입력  / ### 출력 (공백 포함)
        pattern = rf"### {section_name}\s*\n([\s\S]+?)(?=\n###|\Z)"
        m = re.search(pattern, readme_text)
        if not m:
            continue
        content = m.group(1).strip()
        if section_name == "문제 설명":
            parts.append(content)
        else:
            parts.append(f"### {heading}\n\n{content}")

    return "\n\n".join(parts)


# ─── Notion 블록 → 마크다운 ──────────────────────────────────────────────────

def rich_text_to_md(rich_texts):
    result = ""
    for rt in rich_texts:
        text = rt.get("plain_text", "")
        ann = rt.get("annotations", {})
        href = rt.get("href")

        # 앞뒤 공백을 마커 바깥으로 분리 (CommonMark: 마커 안쪽 끝에 공백 불가)
        leading  = len(text) - len(text.lstrip())
        trailing = len(text) - len(text.rstrip())
        inner    = text.strip()

        if inner:
            if ann.get("code"):
                inner = f"`{inner}`"
            if ann.get("bold"):
                inner = f"**{inner}**"
            if ann.get("italic"):
                inner = f"*{inner}*"
            if ann.get("strikethrough"):
                inner = f"~~{inner}~~"
            if href:
                inner = f"[{inner}]({href})"
            text = text[:leading] + inner + text[len(text) - trailing:] if trailing else text[:leading] + inner
        result += text
    return result


def block_to_md_lines(block, depth=0):
    btype = block.get("type")
    content = block.get(btype, {})
    has_children = block.get("has_children", False)
    indent = "  " * depth
    lines = []

    if btype == "paragraph":
        text = rich_text_to_md(content.get("rich_text", []))
        lines.append(f"{indent}{text}" if text else "")

    elif btype in ("heading_1", "heading_2", "heading_3"):
        level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[btype]
        text = rich_text_to_md(content.get("rich_text", []))
        lines.append(f"{level} {text}")

    elif btype == "bulleted_list_item":
        text = rich_text_to_md(content.get("rich_text", []))
        lines.append(f"{indent}- {text}")
        if has_children:
            for child in get_block_children(block["id"]):
                lines.extend(block_to_md_lines(child, depth + 1))

    elif btype == "numbered_list_item":
        text = rich_text_to_md(content.get("rich_text", []))
        lines.append(f"{indent}1. {text}")
        if has_children:
            for child in get_block_children(block["id"]):
                lines.extend(block_to_md_lines(child, depth + 1))

    elif btype == "code":
        text = rich_text_to_md(content.get("rich_text", []))
        notion_lang = content.get("language", "").lower()
        lang = NOTION_LANG_MAP.get(notion_lang, notion_lang)
        caption = rich_text_to_md(content.get("caption", []))
        lines.append(f"```{lang}\n{text}\n```")
        if caption:
            lines.append(f"*{caption}*")

    elif btype == "quote":
        text = rich_text_to_md(content.get("rich_text", []))
        lines.append(f"> {text}")

    elif btype == "callout":
        text = rich_text_to_md(content.get("rich_text", []))
        icon = content.get("icon") or {}
        emoji = icon.get("emoji", "") if icon.get("type") == "emoji" else ""
        lines.append(f"> {(emoji + ' ' + text).strip()}")

    elif btype == "divider":
        lines.append("---")

    elif btype == "toggle":
        text = rich_text_to_md(content.get("rich_text", []))
        lines.append(f"**{text}**")
        if has_children:
            for child in get_block_children(block["id"]):
                lines.extend(block_to_md_lines(child, depth + 1))

    elif btype == "image":
        file_obj = content.get("file") or content.get("external") or {}
        url = file_obj.get("url", "")
        caption = rich_text_to_md(content.get("caption", []))
        lines.append(f"![{caption}]({url})")

    elif btype == "table":
        rows = get_block_children(block["id"]) if has_children else []
        has_col_header = content.get("has_column_header", False)
        tr_lines = []
        for i, row in enumerate(rows):
            cells = row.get("table_row", {}).get("cells", [])
            tag = "th" if (i == 0 and has_col_header) else "td"
            tds = "".join(
                f"<{tag} style='text-align:center;padding:4px 8px;'>"
                f"{rich_text_to_md(cell)}</{tag}>"
                for cell in cells
            )
            tr_lines.append(f"  <tr>{tds}</tr>")
        if tr_lines:
            lines.append(
                '<table style="border-collapse:collapse;width:auto;">\n'
                + "\n".join(tr_lines) + "\n</table>"
            )

    elif btype == "column_list":
        columns = get_block_children(block["id"]) if has_children else []
        media_cells, caption_cells = [], []
        for col in columns:
            col_children = get_block_children(col["id"]) if col.get("has_children") else []
            media_html = ""
            caption_texts = []
            for child in col_children:
                ctype = child.get("type")
                ccontent = child.get(ctype, {})
                if ctype == "image":
                    file_obj = ccontent.get("file") or ccontent.get("external") or {}
                    url = file_obj.get("url", "")
                    media_html = f'<img src="{url}" style="max-width:100%;">'
                elif ctype == "code":
                    text = rich_text_to_md(ccontent.get("rich_text", []))
                    media_html = f"<pre>{text}</pre>"
                elif ctype == "paragraph":
                    text = rich_text_to_md(ccontent.get("rich_text", []))
                    if text.strip():
                        caption_texts.append(text.strip())
            media_cells.append(
                f"<td style='text-align:center;vertical-align:middle;'>{media_html}</td>"
            )
            caption_cells.append(
                f"<td style='text-align:center;'>{' '.join(caption_texts)}</td>"
            )
        if media_cells:
            lines.append(
                '<table style="width:100%;border-collapse:collapse;">\n'
                f"  <tr>{''.join(media_cells)}</tr>\n"
                f"  <tr>{''.join(caption_cells)}</tr>\n"
                "</table>"
            )

    elif btype == "equation":
        expr = content.get("expression", "")
        lines.append(f"$${expr}$$")

    return lines


def blocks_to_markdown(blocks, depth=0):
    all_lines = []
    for block in blocks:
        all_lines.extend(block_to_md_lines(block, depth))
    return "\n\n".join(line for line in all_lines if line is not None)


def split_notion_blocks(blocks):
    """
    Notion 블록을 '문제' 섹션 블록과 '문제 조건 이후' 블록으로 분리.
    - 문제 섹션: ## 문제 다음 ~ ## 풀이 또는 ### 문제 조건 전까지
    - 이후 섹션: ### 문제 조건 포함 ~ 끝
    """
    problem_blocks = []
    rest_blocks = []
    state = "before"  # before → problem → rest

    for block in blocks:
        btype = block.get("type")
        content = block.get(btype, {})
        text = rich_text_to_md(content.get("rich_text", [])) if "rich_text" in content else ""

        if state == "before":
            if btype == "heading_2" and text == "문제":
                state = "problem"
            # heading_2 "문제" 자체는 포함하지 않음
            continue

        if state == "problem":
            if (btype == "heading_3" and text == "문제 조건") or \
               (btype == "heading_2" and text == "풀이"):
                state = "rest"
                rest_blocks.append(block)
            else:
                problem_blocks.append(block)
            continue

        if state == "rest":
            rest_blocks.append(block)

    return problem_blocks, rest_blocks


# ─── Jekyll 포스트 생성 ───────────────────────────────────────────────────────

def slugify(t):
    return re.sub(r"[\s/]+", "-", t.strip())


def find_existing_post(prefix, num):
    folder = f"_posts/{prefix}"
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            if f"{prefix}-{num}" in f:
                return os.path.join(folder, f)
    return None


def read_notion_edited(post_file):
    try:
        with open(post_file, encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"^notion_edited:\s*(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else None
    except FileNotFoundError:
        return None


def create_or_update_post(num, title, platform_info, level, tags, lang_disp,
                           problem_url, notion_blocks, readme_text, notion_edited, date_str):
    prefix = platform_info["post_prefix"]
    existing = find_existing_post(prefix, num)

    if existing and read_notion_edited(existing) == notion_edited:
        return "skip"

    tags_yaml = ", ".join(tags) if tags else ""
    tag_links = " ".join(
        f'<a href="/tags/{slugify(t)}/" class="post-tag">{t}</a>' for t in tags
    )
    tag_block = f'<div class="post-tags-top">{tag_links}</div>\n\n' if tags else ""

    level_disp = f" ({level})" if level else ""
    post_title = f"[{platform_info['label']}] {num}번: {title}{level_disp} - {lang_disp} 풀이"
    permalink = platform_info["permalink"].format(num=num)

    # 문제 섹션: README 원문 우선, 없으면 Notion 블록
    _, rest_blocks = split_notion_blocks(notion_blocks)

    if readme_text:
        problem_section = extract_problem_section_from_readme(readme_text, problem_url)
        source_note = ""
    else:
        problem_blocks, _ = split_notion_blocks(notion_blocks)
        problem_section = f"[문제 링크]({problem_url})\n\n" if problem_url else ""
        problem_section += blocks_to_markdown(problem_blocks)
        source_note = ""

    rest_section = blocks_to_markdown(rest_blocks)

    body = (
        f"{tag_block}"
        f"## 문제\n\n{problem_section}\n\n"
        + (f"{rest_section}" if rest_section else "")
    )

    folder = f"_posts/{prefix}"
    filepath = existing if existing else f"{folder}/{date_str}-{prefix}-{num}.md"

    content = f"""---
layout: post
title: "{post_title}"
date: {date_str} 00:00:00 +0900
categories: algorithm
tags: [{tags_yaml}]
toc: true
permalink: {permalink}
platform: {platform_info["oj"]}
lang: {lang_disp}
notion_edited: {notion_edited}
---

{body}
"""

    os.makedirs(folder, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)

    return "updated" if existing else "created"


# ─── 메인 ────────────────────────────────────────────────────────────────────

def main():
    if not NOTION_TOKEN or not NOTION_ALGO_DB_ID:
        print("NOTION_TOKEN 또는 NOTION_ALGO_DB_ID 환경변수가 없습니다.")
        return

    print("Notion 알고리즘 DB 조회 중...")
    pages = query_algo_db()
    print(f"완료 상태 포스트: {len(pages)}개")

    created = updated = skipped = 0

    for page in pages:
        props = page.get("properties", {})
        notion_edited = page.get("last_edited_time", "")

        title_str = "".join(
            rt.get("plain_text", "")
            for rt in props.get("제목", {}).get("title", [])
        )
        m = re.match(r"\[(\d+)\]\s*(.+)", title_str.strip())
        if m:
            num, title = m.group(1), m.group(2).strip()
        else:
            # 번호 없는 경우: 제목 slug를 번호 대신 사용
            num = re.sub(r"[^\w가-힣]", "-", title_str.strip()).strip("-")[:40]
            title = title_str.strip()
            if not num:
                print(f"  제목 파싱 실패 (빈 제목): {title_str}")
                continue

        site = (props.get("문제 사이트", {}).get("select") or {}).get("name", "")
        if not site:
            print(f"  문제 사이트 없음: {title_str}")
            continue
        platform_info = get_platform_info(site)

        level = (props.get("문제 레벨", {}).get("select") or {}).get("name", "")
        tags = [t["name"] for t in props.get("태그", {}).get("multi_select", [])]
        lang_disp = (props.get("사용 언어", {}).get("select") or {}).get("name", "C++")
        problem_url = props.get("문제 주소", {}).get("url") or ""

        created_time = page.get("created_time", "")
        date_str = created_time[:10] if created_time else datetime.now().strftime("%Y-%m-%d")

        # 변경 없으면 스킵 (API 호출 최소화)
        prefix = platform_info["post_prefix"]
        existing = find_existing_post(prefix, num)
        if existing and read_notion_edited(existing) == notion_edited:
            skipped += 1
            continue

        print(f"  처리 중: {num}번 {title}")
        notion_blocks = get_block_children(page["id"])

        readme_text = fetch_readme_from_repo(platform_info, num, title, level)
        if readme_text:
            print(f"    ✓ README 원문 사용")
        else:
            print(f"    ✗ README 없음 → Notion 블록 사용")

        result = create_or_update_post(
            num, title, platform_info, level, tags, lang_disp,
            problem_url, notion_blocks, readme_text, notion_edited, date_str
        )

        if result == "created":
            print(f"  [{platform_info['label']}] 생성됨: {num}번 {title}")
            created += 1
        elif result == "updated":
            print(f"  [{platform_info['label']}] 업데이트됨: {num}번 {title}")
            updated += 1
        else:
            skipped += 1

    print(f"\n생성: {created}개 | 업데이트: {updated}개 | 변경 없음: {skipped}개")


if __name__ == "__main__":
    main()
