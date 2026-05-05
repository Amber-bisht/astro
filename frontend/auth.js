// Shared auth module — renders navbar + handles Google Sign-In via JWT cookies.

const GITHUB_URL = "https://github.com/Amber-bisht/astro";

const AUTH = {
  user: null,

  async init() {
    await this._checkSession();
    this._renderNavbar();
    this._initGoogle();
  },

  async _checkSession() {
    try {
      const res = await fetch("/auth/me");
      const data = await res.json();
      this.user = data.logged_in ? { email: data.email, name: data.name, picture: data.picture } : null;
    } catch {
      this.user = null;
    }
  },

  async _initGoogle() {
    try {
      const res = await fetch("/auth/config");
      const cfg = await res.json();
      if (!cfg.google_client_id) return;
      this._waitForGoogle(() => {
        google.accounts.id.initialize({
          client_id: cfg.google_client_id,
          callback: (r) => this._handleCredential(r),
        });
        const btn = document.getElementById("g-login-btn");
        if (btn) {
          google.accounts.id.renderButton(btn, {
            type: "standard", theme: "outline", size: "medium",
            text: "signin_with", shape: "pill", width: 200,
          });
        }
      });
    } catch (e) { console.error("Auth init:", e); }
  },

  _waitForGoogle(cb, n = 0) {
    if (typeof google !== "undefined" && google.accounts) cb();
    else if (n < 50) setTimeout(() => this._waitForGoogle(cb, n + 1), 100);
  },

  async _handleCredential(response) {
    try {
      const res = await fetch("/auth/google", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ credential: response.credential }),
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.detail || "Login failed");
      this.user = { email: data.email, name: data.name, picture: data.picture };
      this._renderNavbar();
      this._initGoogle();
      if (typeof refreshProfiles === "function") refreshProfiles();
    } catch (e) {
      console.error("Login error:", e);
      alert("Login failed: " + e.message);
    }
  },

  async logout() {
    try { await fetch("/auth/logout", { method: "POST" }); } catch {}
    this.user = null;
    this._renderNavbar();
    this._initGoogle();
    if (typeof refreshProfiles === "function") refreshProfiles();
  },

  isLoggedIn() { return !!this.user; },

  _renderNavbar() {
    const el = document.getElementById("app-navbar");
    if (!el) return;

    const ghIcon = `<svg width="18" height="18" viewBox="0 0 24 24" fill="currentColor"><path d="M12 2C6.477 2 2 6.484 2 12.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0112 6.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.202 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.943.359.309.678.92.678 1.855 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0022 12.017C22 6.484 17.522 2 12 2z"/></svg>`;

    let rightHtml;
    if (this.user) {
      const firstName = (this.user.name || this.user.email).split(" ")[0];
      const pic = this.user.picture
        ? `<img src="${this.user.picture}" alt="" class="nav-user-avatar" referrerpolicy="no-referrer" />`
        : `<div class="nav-user-initial">${firstName.charAt(0)}</div>`;
      rightHtml = `
        <a href="${GITHUB_URL}" target="_blank" rel="noopener" class="nav-link">${ghIcon}<span>GitHub</span></a>
        <div class="nav-user">
          ${pic}
          <span class="nav-user-name">${this._esc(firstName)}</span>
          <button class="nav-logout" id="nav-logout-btn">Logout</button>
        </div>
      `;
    } else {
      rightHtml = `
        <a href="${GITHUB_URL}" target="_blank" rel="noopener" class="nav-link">${ghIcon}<span>GitHub</span></a>
        <div id="g-login-btn"></div>
      `;
    }

    el.innerHTML = `
      <a href="/" class="nav-brand">
        <span class="nav-brand-icon"><svg width="22" height="22" viewBox="0 0 24 24" fill="none" stroke="var(--primary)" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round"><circle cx="12" cy="12" r="5"/><ellipse cx="12" cy="12" rx="11" ry="4" transform="rotate(-30 12 12)"/></svg></span>
        <span class="nav-brand-name">astro.amberbisht.me</span>
      </a>
      <div class="nav-right">${rightHtml}</div>
    `;

    document.getElementById("nav-logout-btn")?.addEventListener("click", () => this.logout());
  },

  _esc(s) { const d = document.createElement("div"); d.textContent = s; return d.innerHTML; },
};

if (document.readyState === "loading") {
  document.addEventListener("DOMContentLoaded", () => AUTH.init());
} else {
  AUTH.init();
}
