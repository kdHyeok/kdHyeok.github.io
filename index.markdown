---
layout: home
---

## 🚀 Featured Projects
실제 개발하고 구현한 프로젝트들입니다.
<ul>
  {% for item in site.data.github_data.projects %}
   <a href="{{ item.pages_url }}" target="_blank">View Page</a>
{% endfor %}
</ul>

---

## 📝 Algorithm & Study
매일 해결한 알고리즘 문제와 학습 기록입니다.
<ul>
  {% for item in site.data.github_data.algorithms %}
    <li>
      <a href="{{ item.url }}">{{ item.name }}</a> - {{ item.description }}
    </li>
  {% endfor %}
</ul>

### 🚩 최근 해결한 문제 (Latest Solved)
<ul>
  {% for prob in site.data.github_data.recent_solved reversed %}
    <li>
      <span class="label">{{ prob.tier }}</span> 
      <a href="{{ prob.url }}" target="_blank">{{ prob.name }}</a>
    </li>
  {% endfor %}
</ul>

<style>
  .label {
    display: inline-block;
    padding: 2px 8px;
    font-size: 12px;
    background: #000;
    color: #fff;
    border-radius: 4px;
    margin-right: 5px;
  }
</style>