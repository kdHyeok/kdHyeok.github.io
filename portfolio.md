---
layout: page
title: Portfolio
permalink: /portfolio/
---

<style>
  .project-grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 20px; }
  .project-card { border: 1px solid #ddd; padding: 15px; border-radius: 8px; transition: transform 0.2s; }
  .project-card:hover { transform: translateY(-5px); box-shadow: 0 4px 15px rgba(0,0,0,0.1); }
  .btn { display: inline-block; padding: 5px 10px; background: #0366d6; color: white !important; border-radius: 5px; text-decoration: none; font-size: 0.8em; }
  .btn-demo { background: #28a745; }
</style>

<div class="project-grid">
  {% for item in site.data.github_data.portfolios %}
    <div class="project-card">
      <h3>{{ item.name }}</h3>
      <p>{{ item.description }}</p>
      <div class="tags">
        <span class="language">#{{ item.language }}</span>
      </div>
      <div class="links" style="margin-top: 15px;">
        <a href="{{ item.repo_url }}" class="btn">GitHub</a>
        {% if item.pages_url %}
          <a href="{{ item.pages_url }}" class="btn btn-demo">Live Demo</a>
        {% endif %}
      </div>
    </div>
  {% endfor %}
</div>