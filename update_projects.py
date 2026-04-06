import requests
import yaml
import os

USERNAME = "kdHyeok"  # 본인의 GitHub 아이디

def get_github_repos():
    url = f"https://api.github.com/users/{USERNAME}/repos?per_page=100&sort=updated"
    response = requests.get(url)
    return response.json()

def main():
    repos = get_github_repos()
    data = {"projects": [], "algorithms": []}

    for repo in repos:
        if repo.get('fork'): continue
        
        topics = repo.get('topics', [])
        repo_name = repo['name']
        
        # 깃허브 페이지 URL 규칙 적용
        # 메인 블로그(username.github.io)인 경우와 일반 레포인 경우를 구분
        if repo_name.lower() == f"{USERNAME.lower()}.github.io":
            generated_pages_url = f"https://{USERNAME}.github.io/"
        else:
            generated_pages_url = f"https://{USERNAME}.github.io/{repo_name}/"

        repo_info = {
            'name': repo_name,
            'repo_url': repo['html_url'],         # 소스 코드 주소
            'pages_url': generated_pages_url,     # 실제 배포된 페이지 주소
            'description': repo['description'] or "설명이 없습니다.",
            'language': repo['language']
        }

        if 'portfolio' in topics:
            data['projects'].append(repo_info)
        elif 'algorithm' in topics:
            data['algorithms'].append(repo_info)

    os.makedirs('_data', exist_ok=True)
    with open('_data/github_data.yml', 'w', encoding='utf-8') as f:
        yaml.dump(data, f, allow_unicode=True, sort_keys=False)

if __name__ == "__main__":
    main()