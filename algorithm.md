---
layout: page
title: Algorithm Study
permalink: /algorithm/
---

{% assign bj = site.data.github_data.baekjoon %}

## 🏆 My Solved.ac Status
<div style="display: flex; align-items: center; gap: 20px; background: #f8f9fa; padding: 20px; border-radius: 10px;">
  <img src="{{ bj.tier_image }}" width="80">
  <div>
    <p><strong>Rank:</strong> #{{ bj.rank }}</p>
    <p><strong>Solved:</strong> {{ bj.solved_count }} Problems</p>
    <p><strong>Max Streak:</strong> {{ bj.streak }} Days</p>
  </div>
</div>

---

## 📂 Problem Solving Repositories
{% for item in site.data.github_data.algorithms %}
### [{{ item.name }}]({{ item.repo_url }})
> {{ item.description }}
* **주요 언어:** {{ item.language }}
* **풀이 보러가기:** [GitHub Repository]({{ item.repo_url }})
{% endfor %}

---

## 🕐 Recently Solved Problems
<ul>
{% for problem in site.data.github_data.recent_solved %}
  <li>
    <a href="{{ problem.url }}" target="_blank"><strong>{{ problem.name }}</strong></a>
    <span style="margin-left: 8px; font-size: 0.85em; color: #888;">{{ problem.tier }}</span>
  </li>
{% endfor %}
</ul>