---
title: Projects
icon: fas fa-folder-open
order: 2
---

<div class="project-grid">
  {% for item in site.data.github_data.projects %}
    <div class="project-card">
      <div class="project-card__body">
        <span class="lang-badge">{{ item.language }}</span>
        <h3>{{ item.name }}</h3>
        <p class="project-desc">{{ item.description }}</p>
      </div>
      <div class="project-card__footer">
        <a href="{{ item.repo_url }}" target="_blank" class="btn-github">
          <i class="fab fa-github"></i> GitHub
        </a>
      </div>
    </div>
  {% endfor %}
</div>
