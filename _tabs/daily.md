---
title: Daily
icon: fas fa-comments
order: 4
---

{% assign daily_posts = site.posts | where_exp: "post", "post.categories contains 'daily'" %}
{% assign all_tags = daily_posts | map: "tags" | join: "," | split: "," | uniq | sort %}

<div class="daily-filter-bar">
  <div class="daily-filter-group">
    <span class="algo-filter-label">태그</span>
    <button class="algo-filter-btn active" data-filter="tag" data-value="">전체</button>
    {% for tag in all_tags %}
    {% assign t = tag | strip %}
    {% if t != "" %}
    <button class="algo-filter-btn" data-filter="tag" data-value="{{ t }}">{{ t }}</button>
    {% endif %}
    {% endfor %}
  </div>
</div>

{% if daily_posts.size == 0 %}
<p style="color: #888;">아직 작성된 글이 없습니다.</p>
{% else %}
<div class="daily-card-grid" id="daily-card-grid">
  {% for post in daily_posts %}
  {% assign first_img = post.content | strip_html | strip %}
  {% assign img_match = post.content | split: '<img ' | last %}
  <a href="{{ post.url }}" class="daily-card"
     data-tags="{{ post.tags | join: ',' }}">
    {% if post.image %}
    <div class="daily-card-img" style="background-image: url('{{ post.image }}')"></div>
    {% elsif post.content contains '<img' %}
    {% assign img_src = post.content | split: 'src="' | last | split: '"' | first %}
    <div class="daily-card-img" style="background-image: url('{{ img_src }}')"></div>
    {% endif %}
    <div class="daily-card-body">
      <div class="algo-card-header">
        <span class="algo-date">{{ post.date | date: "%Y.%m.%d" }}</span>
      </div>
      <h3 class="algo-card-title">{{ post.title }}</h3>
      <p class="algo-card-excerpt">{{ post.excerpt | strip_html | truncate: 80 }}</p>
      {% if post.tags.size > 0 %}
      <div class="daily-card-tags">
        {% for tag in post.tags %}
        <span class="daily-tag">{{ tag }}</span>
        {% endfor %}
      </div>
      {% endif %}
    </div>
  </a>
  {% endfor %}
</div>
{% endif %}

<script>
document.addEventListener('DOMContentLoaded', function () {
  var activeTag = "";
  document.querySelectorAll(".algo-filter-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      activeTag = btn.dataset.value;
      btn.closest(".daily-filter-group").querySelectorAll(".algo-filter-btn").forEach(function(b) {
        b.classList.toggle("active", b === btn);
      });
      document.querySelectorAll("#daily-card-grid .daily-card").forEach(function(card) {
        var tags = card.dataset.tags ? card.dataset.tags.split(",") : [];
        var match = !activeTag || tags.some(function(t) { return t.trim() === activeTag; });
        card.style.display = match ? "" : "none";
      });
    });
  });
});
</script>
