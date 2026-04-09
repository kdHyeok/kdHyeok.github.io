"""
Notion DB의 게시글을 _posts/ 에 Jekyll 포스트로 동기화합니다.
- 상태가 '발행'인 글만 처리
- 없는 글은 새로 생성
- '최근 편집'이 저장된 시각보다 늦으면 업데이트
"""
import requests
import os
import re
import hashlib
import io
from datetime import datetime, timezone
from PIL import Image

NOTION_TOKEN = os.environ.get("NOTION_TOKEN")
NOTION_DB_ID = os.environ.get("NOTION_DB_ID")
NOTION_API = "https://api.notion.com/v1"
NOTION_VERSION = "2022-06-28"

POST_PREFIX = "daily"
SYNC_FILE = "_data/daily_last_sync.txt"


def notion_headers():
    return {
        "Authorization": f"Bearer {NOTION_TOKEN}",
        "Notion-Version": NOTION_VERSION,
        "Content-Type": "application/json",
    }


def query_db():
    """상태가 '발행'인 페이지만 조회"""
    url = f"{NOTION_API}/databases/{NOTION_DB_ID}/query"
    payload = {
        "filter": {
            "property": "상태",
            "status": {"equals": "완료"}
        }
    }
    resp = requests.post(url, headers=notion_headers(), json=payload)
    if resp.status_code != 200:
        print(f"Notion DB 조회 실패: {resp.status_code} {resp.text}")
        return []
    data = resp.json()
    return data.get("results", [])


def get_page_content(page_id):
    """페이지 블록을 마크다운으로 변환"""
    url = f"{NOTION_API}/blocks/{page_id}/children?page_size=100"
    resp = requests.get(url, headers=notion_headers())
    if resp.status_code != 200:
        return ""
    blocks = resp.json().get("results", [])
    return blocks_to_markdown(blocks)


IMG_DIR = "assets/img/daily"

def download_image(notion_url):
    """노션 이미지 URL을 다운받아 WebP로 변환 후 assets/img/daily/에 저장"""
    if not notion_url:
        return ""
    try:
        url_hash = hashlib.md5(notion_url.split("?")[0].encode()).hexdigest()[:12]
        orig_ext = notion_url.split("?")[0].rsplit(".", 1)[-1].lower()
        filename = f"{url_hash}.webp"
        local_path = os.path.join(IMG_DIR, filename)
        if not os.path.exists(local_path):
            os.makedirs(IMG_DIR, exist_ok=True)
            resp = requests.get(notion_url, timeout=15)
            if resp.status_code != 200:
                return notion_url
            if orig_ext == "svg":
                fallback = f"{url_hash}.svg"
                fallback_path = os.path.join(IMG_DIR, fallback)
                with open(fallback_path, "wb") as f:
                    f.write(resp.content)
                print(f"  이미지 저장(svg): {fallback}")
                return f"/{fallback_path}"
            img = Image.open(io.BytesIO(resp.content)).convert("RGBA")
            img.save(local_path, "WEBP", quality=85)
            print(f"  이미지 저장(webp): {filename}")
        return f"/{local_path}"
    except Exception as e:
        print(f"  이미지 다운로드 실패: {e}")
        return notion_url


def rich_text_to_str(rich_texts):
    return "".join(rt.get("plain_text", "") for rt in rich_texts)


def blocks_to_markdown(blocks):
    lines = []
    for block in blocks:
        btype = block.get("type")
        content = block.get(btype, {})

        if btype == "paragraph":
            text = rich_text_to_str(content.get("rich_text", []))
            lines.append(text if text else "")

        elif btype in ("heading_1", "heading_2", "heading_3"):
            level = {"heading_1": "#", "heading_2": "##", "heading_3": "###"}[btype]
            text = rich_text_to_str(content.get("rich_text", []))
            lines.append(f"{level} {text}")

        elif btype == "bulleted_list_item":
            text = rich_text_to_str(content.get("rich_text", []))
            lines.append(f"- {text}")

        elif btype == "numbered_list_item":
            text = rich_text_to_str(content.get("rich_text", []))
            lines.append(f"1. {text}")

        elif btype == "code":
            text = rich_text_to_str(content.get("rich_text", []))
            lang = content.get("language", "")
            lines.append(f"```{lang}\n{text}\n```")

        elif btype == "quote":
            text = rich_text_to_str(content.get("rich_text", []))
            lines.append(f"> {text}")

        elif btype == "divider":
            lines.append("---")

        elif btype == "image":
            file_info = content.get("file") or content.get("external", {})
            notion_url = file_info.get("url", "")
            caption = rich_text_to_str(content.get("caption", []))
            local_path = download_image(notion_url)
            lines.append(f"![{caption}]({local_path})")

    return "\n\n".join(lines)


def prop_text(page, prop_name):
    prop = page.get("properties", {}).get(prop_name, {})
    ptype = prop.get("type")
    if ptype == "title":
        return rich_text_to_str(prop.get("title", []))
    if ptype == "rich_text":
        return rich_text_to_str(prop.get("rich_text", []))
    return ""


def prop_tags(page, prop_name):
    prop = page.get("properties", {}).get(prop_name, {})
    ptype = prop.get("type")
    if ptype == "multi_select":
        return [opt["name"] for opt in prop.get("multi_select", [])]
    if ptype == "select" and prop.get("select"):
        return [prop["select"]["name"]]
    return []


def prop_date(page, prop_name):
    prop = page.get("properties", {}).get(prop_name, {})
    d = prop.get("date") or {}
    return d.get("start", "")


def slugify(text):
    text = re.sub(r"[^\w\s가-힣-]", "", text)
    text = re.sub(r"[\s]+", "-", text.strip())
    return text.lower()


def find_existing_post(page_id):
    folder = "_posts/daily"
    if os.path.isdir(folder):
        for f in os.listdir(folder):
            if f"daily-{page_id}" in f:
                return os.path.join(folder, f)
    return None


def read_stored_edited(post_file):
    try:
        with open(post_file, encoding="utf-8") as f:
            content = f.read()
        m = re.search(r"^notion_edited:\s*(.+)$", content, re.MULTILINE)
        return m.group(1).strip() if m else None
    except FileNotFoundError:
        return None


def create_or_update_post(page):
    page_id = page["id"].replace("-", "")
    title = prop_text(page, "제목")
    tags = prop_tags(page, "태그")
    created = prop_date(page, "생성일") or page.get("created_time", "")[:10]
    last_edited = page.get("last_edited_time", "")

    if not title:
        return "skip"

    date_str = created[:10] if created else datetime.now(timezone.utc).strftime("%Y-%m-%d")
    existing = find_existing_post(page_id)

    if existing:
        stored = read_stored_edited(existing)
        if stored and stored >= last_edited:
            return "skip"

    content_md = get_page_content(page["id"])

    tags_yaml = ", ".join(tags) if tags else ""
    permalink = f"/chatter/{slugify(title) or page_id[:8]}/"

    post_content = f"""---
layout: post
title: "{title}"
date: {date_str} 00:00:00 +0900
categories: daily
tags: [{tags_yaml}]
toc: true
permalink: {permalink}
notion_edited: {last_edited}
---

{content_md}
"""

    folder = "_posts/daily"
    filepath = existing if existing else f"{folder}/{date_str}-{POST_PREFIX}-{page_id}.md"
    os.makedirs(folder, exist_ok=True)
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(post_content)

    return "updated" if existing else "created"


def main():
    if not NOTION_TOKEN or not NOTION_DB_ID:
        print("NOTION_TOKEN 또는 NOTION_DB_ID 환경변수가 없습니다.")
        return

    print("Notion DB 조회 중...")
    pages = query_db()
    print(f"발행 상태 게시글: {len(pages)}개")

    created = updated = skipped = 0
    for page in pages:
        title = prop_text(page, "제목")
        result = create_or_update_post(page)
        if result == "created":
            print(f"생성됨: {title}")
            created += 1
        elif result == "updated":
            print(f"업데이트됨: {title}")
            updated += 1
        else:
            skipped += 1

    print(f"\n생성: {created}개 | 업데이트: {updated}개 | 변경 없음: {skipped}개")


if __name__ == "__main__":
    main()
