<h2 class="section-title">⭐ Featured Portfolios</h2>
<p class="section-desc">가장 핵심적인 프로젝트들입니다. 이미지와 배포 링크가 포함되어 있습니다.</p>

<div class="portfolio-grid">
  {% for item in site.data.github_data.portfolios %}
  <div class="portfolio-card">
    <div class="card-content">
      <span class="lang-badge">{{ item.language }}</span>
      <h3>{{ item.name }}</h3>
      <p>{{ item.description }}</p>
      <div class="card-links">
        <a href="{{ item.pages_url }}" target="_blank" class="btn-demo">Live Demo</a>
        <a href="{{ item.repo_url }}" target="_blank" class="btn-github">GitHub</a>
      </div>
    </div>
  </div>
  {% endfor %}
</div>

<hr class="divider">

<h2 class="section-title">🛠️ Other Projects</h2>
<p class="section-desc">학습 및 기술 스택 연습을 위해 진행한 프로젝트들입니다.</p>

<ul class="project-list">
  {% for item in site.data.github_data.projects %}
  <li>
    <span class="project-date">{{ item.updated }}</span>
    <a href="{{ item.repo_url }}" target="_blank"><strong>{{ item.name }}</strong></a>
    <span class="project-lang">[{{ item.language }}]</span>
    <p class="project-desc">{{ item.description }}</p>
  </li>
  {% endfor %}
</ul>