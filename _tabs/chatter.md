---
title: Chatter
icon: fas fa-comments
order: 4
---

일상 잡담을 기록하는 공간입니다.

{% assign chatter_posts = site.posts | where_exp: "post", "post.categories contains 'chatter'" %}
{% if chatter_posts.size == 0 %}
<p style="color: #888;">아직 작성된 글이 없습니다.</p>
{% else %}
{% for post in chatter_posts %}
- [{{ post.title }}]({{ post.url }}) — {{ post.date | date: "%Y.%m.%d" }}
{% endfor %}
{% endif %}
