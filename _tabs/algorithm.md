---
title: Algorithm
icon: fas fa-code
order: 3
---

{% assign bj = site.data.github_data.baekjoon %}

<div style="display: flex; align-items: center; gap: 20px; background: var(--card-bg, #f8f9fa); padding: 20px; border-radius: 10px; margin-bottom: 2rem;">
  <img src="{{ bj.tier_image }}" width="80">
  <div>
    <p><strong>Rank:</strong> #{{ bj.rank }}</p>
    <p><strong>Solved:</strong> {{ bj.solved_count }} Problems</p>
    <p><strong>Max Streak:</strong> {{ bj.streak }} Days</p>
  </div>
</div>

## 📂 Problem Solving Repositories

{% for item in site.data.github_data.algorithms %}
### [{{ item.name }}]({{ item.repo_url }})
> {{ item.description }}
* **주요 언어:** {{ item.language }}
* **풀이 보러가기:** [GitHub Repository]({{ item.repo_url }})
{% endfor %}

---

## 🗂️ 풀이 포스트

{% assign algo_posts = site.posts | where_exp: "post", "post.categories contains 'algorithm'" %}
{% if algo_posts.size == 0 %}
<p style="color: #888;">아직 작성된 풀이 포스트가 없습니다.</p>
{% else %}
<div class="algo-card-grid">
  {% for post in algo_posts %}
  <a href="{{ post.url }}" class="algo-card">
    <div class="algo-card-header">
      {% for tag in post.tags %}
        {% unless tag == "baekjoon" %}
        <span class="algo-tier-badge">{{ tag }}</span>
        {% endunless %}
      {% endfor %}
      <span class="algo-date">{{ post.date | date: "%Y.%m.%d" }}</span>
    </div>
    <h3 class="algo-card-title">{{ post.title }}</h3>
    <p class="algo-card-excerpt">{{ post.excerpt | strip_html | truncate: 80 }}</p>
  </a>
  {% endfor %}
</div>
{% endif %}
