---
layout: home
---

## 🚀 Featured Projects
실제 개발하고 구현한 프로젝트들입니다.
<ul>
  {% for item in site.data.github_data.projects %}
    <li>
      <strong><a href="{{ item.url }}">{{ item.name }}</a></strong> ({{ item.language }})
      <p>{{ item.description }}</p>
    </li>
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