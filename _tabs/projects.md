---
title: Projects
icon: fas fa-folder-open
order: 2
---

<div class="project-grid">
  {% for item in site.data.github_data.portfolios %}
    <div class="project-card">
      <h3>{{ item.name }}</h3>
      <p>{{ item.description }}</p>
      <div class="tags">
        <span class="lang-badge">{{ item.language }}</span>
      </div>
      <div class="links" style="margin-top: 15px;">
        <a href="{{ item.repo_url }}" class="btn-github">GitHub</a>
        {% if item.pages_url %}
          <a href="{{ item.pages_url }}" class="btn-demo">Live Demo</a>
        {% endif %}
      </div>
    </div>
  {% endfor %}
</div>

---

<h3 style="margin-top:2rem;">🛠️ Other Projects</h3>
<ul class="project-list">
  {% for item in site.data.github_data.projects %}
  <li>
    <a href="{{ item.repo_url }}" target="_blank"><strong>{{ item.name }}</strong></a>
    <span class="project-lang">[{{ item.language }}]</span>
    <p class="project-desc">{{ item.description }}</p>
  </li>
  {% endfor %}
</ul>
