import requests
import yaml
import os

# 1. 설정 정보
USERNAME = "kdHyeok"  # GitHub 아이디
BOJ_ID = "kimdh219"   # 백준(Solved.ac) 아이디
ALGO_REPO = "Algorithms"

def get_github_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
    response = requests.get(url)
    return response.json()

def get_solved_ac_stats():
    # USERNAME이 아니라 BOJ_ID를 사용해야 정확합니다.
    url = f"https://solved.ac/api/v3/user/show?handle={BOJ_ID}"
    try:
        response = requests.get(url)
        if response.status_code == 200:
            return response.json()
        return None
    except:
        return None
    
def get_recent_problems():
    # '백준' 폴더 내부의 티어 폴더들을 가져옵니다.
    url = f"https://api.github.com/repos/{USERNAME}/{ALGO_REPO}/contents/백준"
    response = requests.get(url)
    if response.status_code != 200: return []

    problems = []
    tiers = response.json() # [Bronze, Silver, Gold, Platinum...]
    
    for tier in tiers:
        if tier['type'] == 'dir':
            # 각 티어 폴더 내부의 문제 폴더를 가져옵니다.
            t_url = tier['url']
            t_res = requests.get(t_url).json()
            for p in t_res:
                if p['type'] == 'dir':
                    problems.append({
                        'name': p['name'], # "11438. LCA 2"
                        'tier': tier['name'], # "Platinum"
                        'url': p['html_url']
                    })
    
    # 최근에 추가된 순서대로 정렬하고 싶지만, API 특성상 이름순일 확률이 높습니다.
    # 일단은 전체 리스트를 반환합니다.
    return problems

def main():
    repos = get_github_repos()
    stats = get_solved_ac_stats()
    recent_problems = get_recent_problems()

    # 결과 데이터를 담을 최종 구조
    data = {
        "projects": [],
        "algorithms": [],
        "baekjoon": {},
        "recent_solved": recent_problems[-5:] # 최신 5개 (순서는 로컬 테스트 필요)
    }

    # 2. 깃허브 레포지토리 분류
    for repo in repos:
        if repo.get('fork'): continue
        
        topics = repo.get('topics', [])
        repo_name = repo['name']
        
        # URL 생성 로직
        if repo_name.lower() == f"{USERNAME.lower()}.github.io":
            generated_pages_url = f"https://{USERNAME}.github.io/"
        else:
            generated_pages_url = f"https://{USERNAME}.github.io/{repo_name}/"

        repo_info = {
            'name': repo_name,
            'repo_url': repo['html_url'],
            'pages_url': generated_pages_url,
            'description': repo['description'] or "설명이 없습니다.",
            'language': repo['language']
        }

        if 'portfolio' in topics:
            data['projects'].append(repo_info)
        elif 'algorithm' in topics:
            data['algorithms'].append(repo_info)

    # 3. 백준 통계 추가 (루프 밖에서 한 번만 수행)
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
    
    print("성공적으로 github_data.yml이 갱신되었습니다.")

if __name__ == "__main__":
    main()