import requests
import yaml
import os

# 1. 설정 정보
USERNAME = "kdHyeok"
BOJ_ID = "kimdh219"
ALGO_REPO = "Algorithms"

def get_headers():
    token = os.environ.get("GITHUB_TOKEN")
    return {"Authorization": f"token {token}"} if token else {}

def get_github_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
    response = requests.get(url, headers=get_headers())
    return response.json()

def get_readme_description(repo_name):
    """README.md 첫 문단을 가져와 설명으로 사용"""
    url = f"https://api.github.com/repos/{USERNAME}/{repo_name}/readme"
    resp = requests.get(url, headers=get_headers())
    if resp.status_code != 200:
        return None
    import base64, re
    content = base64.b64decode(resp.json()["content"]).decode("utf-8")
    lines = []
    heading_fallback = []
    for line in content.splitlines():
        stripped = line.strip()
        if not stripped:
            if lines:
                break
            continue
        if stripped.startswith("![") or stripped.startswith("[!["):
            continue
        if stripped.startswith("#"):
            # 헤딩 텍스트는 폴백용으로 보관
            heading_text = re.sub(r"^#+\s*", "", stripped)
            if heading_text:
                heading_fallback.append(heading_text)
            continue
        lines.append(stripped)
    text = " ".join(lines) if lines else " | ".join(heading_fallback[1:])  # h1 제외
    # 마크다운 링크/강조 제거
    text = re.sub(r"!?\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"[*_`]", "", text)
    return text.strip()[:200] if text.strip() else None

def get_solved_ac_stats():
    url = f"https://solved.ac/api/v3/user/show?handle={BOJ_ID}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None
    
def get_recent_problems():
    url = f"https://api.github.com/repos/{USERNAME}/{ALGO_REPO}/contents/백준"
    response = requests.get(url)
    if response.status_code != 200: return []

    problems = []
    tiers = response.json()
    
    for tier in tiers:
        if tier['type'] == 'dir':
            t_url = tier['url']
            t_res = requests.get(t_url).json()
            for p in t_res:
                if p['type'] == 'dir':
                    problems.append({
                        'name': p['name'],
                        'tier': tier['name'],
                        'url': p['html_url']
                    })
    return problems

def main():
    repos = get_github_repos()
    stats = get_solved_ac_stats()
    recent_problems = get_recent_problems()

    # 결과 데이터를 담을 최종 구조 (portfolios 추가)
    data = {
        "portfolios": [],    # 'portfolio' 태그 (핵심 작업물)
        "projects": [],      # 'project' 태그 (일반 개발 활동)
        "algorithms": [],    # 'algorithm' 태그
        "baekjoon": {},
        "recent_solved": recent_problems[-5:]
    }

    # 2. 깃허브 레포지토리 분류 로직
    for repo in repos:
        if repo.get('fork'): continue
        
        topics = repo.get('topics', [])
        repo_name = repo['name']
        
        if repo_name.lower() == f"{USERNAME.lower()}.github.io":
            generated_pages_url = f"https://{USERNAME}.github.io/"
        else:
            generated_pages_url = f"https://{USERNAME}.github.io/{repo_name}/"

        # portfolio/project 태그가 있는 레포만 README 조회
        is_content_repo = 'portfolio' in topics or 'project' in topics
        if is_content_repo:
            readme_desc = get_readme_description(repo_name)
        else:
            readme_desc = None

        repo_info = {
            'name': repo_name,
            'repo_url': repo['html_url'],
            'pages_url': generated_pages_url,
            'description': readme_desc or repo['description'] or "설명이 없습니다.",
            'language': repo['language']
        }

        # 우선순위에 따른 분류 (하나의 레포가 여러 태그를 가질 경우 대비)
        if 'portfolio' in topics:
            data['portfolios'].append(repo_info)
        elif 'project' in topics:
            data['projects'].append(repo_info)
        elif 'algorithm' in topics:
            # 언어 비율 조회
            lang_resp = requests.get(
                f"https://api.github.com/repos/{USERNAME}/{repo_name}/languages",
                headers=get_headers()
            )
            languages = lang_resp.json() if lang_resp.status_code == 200 else {}
            total = sum(languages.values()) or 1
            lang_ratio = {k: round(v / total * 100, 1) for k, v in
                          sorted(languages.items(), key=lambda x: -x[1])}
            repo_info['languages'] = lang_ratio
            data['algorithms'].append(repo_info)

    # 3. 백준 통계 추가
    if stats:
        data['baekjoon'] = {
            "tier": stats.get('tier'),
            "rank": stats.get('rank'),
            "solved_count": stats.get('solvedCount'),
            "streak": stats.get('maxStreak'),
            "tier_image": f"https://static.solved.ac/tier_small/{stats.get('tier')}.svg"
        }

    # 4. 파일 저장
    os.makedirs('_data', exist_ok=True)
    with open('_data/github_data.yml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

    # 5. contact.yml 갱신 (포트폴리오 페이지 링크)
    contact = [{'type': 'github', 'icon': 'fab fa-github'}]
    for portfolio in data['portfolios']:
        contact.append({
            'type': 'portfolio',
            'icon': 'fas fa-globe',
            'url': portfolio['pages_url'],
            'noblank': False
        })
    with open('_data/contact.yml', 'w', encoding='utf-8') as f:
        yaml.dump(contact, f, allow_unicode=True, sort_keys=False)

    print("성공적으로 github_data.yml, contact.yml이 갱신되었습니다.")

if __name__ == "__main__":
    main()