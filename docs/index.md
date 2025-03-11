---
template: home.html
hide:
  - toc
  - navigation
---

<section class="home">
  <h1>Features</h1>

<div class="bento">
  <article>
    <i>⏰</i>
    <h2>Task scheduling</h2>
    <p>Based on <a href="https://github.com/agronholm/apscheduler">APScheduler</a>, it supports Interval, Cron and Date triggers</p>
  </article>

  <article class="large">
    <div>
      <i>👩‍💻🐍</i>
      <h2>Python pipelines</h2>
      <p>Define pipelines and tasks in pure Python: if you can write a function, you can write a pipeline</p>
    </div>
    <img src="assets/images/minimal-code.png" />
  </article>

  <article class="large" style="grid-column: span 2 / span 1;">
    <div>
      <i>🎛️</i>
      <h2>Parametrized pipelines</h2>
      <p>Use <a href="https://docs.pydantic.dev/">Pydantic</a> to define parameters,
       and get a nice web form to run your pipelines</p>
    </div>
    <img src="assets/images/recipes/ssl_check_manual.png" />
  </article>

  <article>
    <i>👉</i>
    <h2>Manual runs</h2>
    <p>Run pipelines manually from the web UI, just click the button</p>
  </article>

  <article>
    <i>💻</i>
    <h2>Built-in Web interface</h2>
    <p>No HTML/JS/CSS coding required</p>
  </article>

  <article class="large" style="grid-row: span 2;">
    <div>
      <i>🔍</i>
      <h2>Debugging</h2>
      <p>Explore logs and output data</p>
    </div>
    <img src="assets/images/recipes/ssl_check_run.png" />
  </article>

  <article>
    <i>🔐</i>
    <h2>Secured</h2>
    <p>Optional OAuth2 authentication</p>
  </article>

  <article class="large">
    <div>
      <i>💣</i>
      <h2>REST API</h2>
      <p>For advanced integrations use the REST API</p>
    </div>
    <div class="api-endpoint">
      <span>POST</span>
      <span>https://plombery.com/api/pipelines/run</span>
    </div>
  </article>

  <article>
    <i>📩</i>
    <h2>Monitoring</h2>
    <p>Get alerted if something goes wrong</p>
  </article>
</div>
</section>
