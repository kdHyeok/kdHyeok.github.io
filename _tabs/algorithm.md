---
title: Algorithm
icon: fas fa-code
order: 3
---

{% assign algo_posts = site.posts | where_exp: "post", "post.categories contains 'algorithm'" %}

<div class="algo-stats-row">
  {% for item in site.data.github_data.algorithms %}
  <div class="algo-stats-repo">
    <a href="{{ item.repo_url }}" target="_blank" class="algo-repo-title">
      <i class="fab fa-github"></i> {{ item.name }}
    </a>
    <div class="algo-lang-bars">
      {% for lang in item.languages %}
      <div class="algo-lang-bar-row">
        <span class="algo-lang-name">{{ lang[0] }}</span>
        <div class="algo-lang-bar-bg">
          <div class="algo-lang-bar-fill" style="width: {{ lang[1] }}%"></div>
        </div>
        <span class="algo-lang-pct">{{ lang[1] }}%</span>
      </div>
      {% endfor %}
    </div>
  </div>
  {% endfor %}
</div>

---

## 🗂️ 풀이 포스트

{% assign platforms = algo_posts | map: "platform" | uniq | sort %}
{% assign langs     = algo_posts | map: "lang"     | uniq | sort %}

<!-- 필터 버튼 -->
<div class="algo-filter-bar">
  <div class="algo-filter-group">
    <span class="algo-filter-label">플랫폼</span>
    <button class="algo-filter-btn active" data-filter="platform" data-value="">전체</button>
    {% for p in platforms %}
    <button class="algo-filter-btn" data-filter="platform" data-value="{{ p }}">{{ p | upcase }}</button>
    {% endfor %}
  </div>
  <div class="algo-filter-group">
    <span class="algo-filter-label">언어</span>
    <button class="algo-filter-btn active" data-filter="lang" data-value="">전체</button>
    {% for l in langs %}
    <button class="algo-filter-btn" data-filter="lang" data-value="{{ l }}">{{ l }}</button>
    {% endfor %}
  </div>
</div>

{% if algo_posts.size == 0 %}
<p style="color:#888;">아직 작성된 풀이 포스트가 없습니다.</p>
{% else %}
<div class="algo-card-grid" id="algo-card-grid">
  {% for post in algo_posts %}
  <a href="{{ post.url }}" class="algo-card"
     data-platform="{{ post.platform }}"
     data-lang="{{ post.lang }}">
    <div class="algo-card-header">
      <span class="algo-platform-badge algo-platform-{{ post.platform }}">{{ post.platform | upcase }}</span>
      <span class="algo-lang-badge-sm">{{ post.lang }}</span>
      <span class="algo-date">{{ post.date | date: "%Y.%m.%d" }}</span>
    </div>
    <h3 class="algo-card-title">{{ post.title }}</h3>
    <p class="algo-card-excerpt">{{ post.excerpt | strip_html | truncate: 80 }}</p>
  </a>
  {% endfor %}
</div>
{% endif %}

<script>
document.addEventListener('DOMContentLoaded', function () {
  const active = { platform: "", lang: "" };
  document.querySelectorAll(".algo-filter-btn").forEach(function(btn) {
    btn.addEventListener("click", function() {
      const filter = btn.dataset.filter;
      const value = btn.dataset.value;
      active[filter] = value;
      btn.closest(".algo-filter-group").querySelectorAll(".algo-filter-btn").forEach(function(b) {
        b.classList.toggle("active", b === btn);
      });
      document.querySelectorAll("#algo-card-grid .algo-card").forEach(function(card) {
        const matchPlatform = !active.platform || card.dataset.platform === active.platform;
        const matchLang = !active.lang || card.dataset.lang === active.lang;
        card.style.display = (matchPlatform && matchLang) ? "" : "none";
      });
    });
  });
});
</script>
