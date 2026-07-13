// ---------- Auth guard ----------
// Every dashboard page includes this before its own page-specific script.
// It checks a token exists and matches the expected role for this page.
const SPPS_TOKEN = localStorage.getItem("spps_token");
const SPPS_ROLE = localStorage.getItem("spps_role");
const REQUIRED_ROLE = document.body.dataset.requiredRole;

if (!SPPS_TOKEN || SPPS_ROLE !== REQUIRED_ROLE) {
  window.location.href = "/login";
}

// ---------- Authenticated fetch helper ----------
async function apiFetch(url, options = {}) {
  const headers = {
    ...(options.headers || {}),
    Authorization: `Bearer ${SPPS_TOKEN}`,
  };
  if (options.body && !headers["Content-Type"]) {
    headers["Content-Type"] = "application/json";
  }
  const response = await fetch(url, { ...options, headers });

  if (response.status === 401) {
    localStorage.removeItem("spps_token");
    localStorage.removeItem("spps_role");
    window.location.href = "/login";
    return null;
  }
  return response;
}

// ---------- Logout ----------
document.addEventListener("DOMContentLoaded", () => {
  const logoutBtn = document.getElementById("logoutBtn");
  if (logoutBtn) {
    logoutBtn.addEventListener("click", () => {
      localStorage.removeItem("spps_token");
      localStorage.removeItem("spps_role");
      window.location.href = "/login";
    });
  }

  // Sidebar nav tab switching
  const navLinks = document.querySelectorAll(".sidebar-link[data-section]");
  const sections = document.querySelectorAll(".dashboard-section");
  navLinks.forEach((link) => {
    link.addEventListener("click", () => {
      navLinks.forEach((l) => l.classList.remove("active"));
      link.classList.add("active");
      const target = link.dataset.section;
      sections.forEach((sec) => {
        sec.classList.toggle("active", sec.id === target);
      });
      const titleEl = document.getElementById("pageTitle");
      const subtitleEl = document.getElementById("pageSubtitle");
      if (titleEl) titleEl.textContent = link.dataset.title || link.textContent.trim();
      if (subtitleEl) subtitleEl.textContent = link.dataset.subtitle || "";
    });
  });

  // Mobile sidebar toggle
  const menuToggle = document.getElementById("menuToggle");
  const sidebar = document.querySelector(".sidebar");
  if (menuToggle && sidebar) {
    menuToggle.addEventListener("click", () => sidebar.classList.toggle("open"));
  }
});

// ---------- Toast ----------
function showToast(message, type = "success") {
  let toast = document.getElementById("sppsToast");
  if (!toast) {
    toast = document.createElement("div");
    toast.id = "sppsToast";
    toast.className = "toast";
    document.body.appendChild(toast);
  }
  toast.textContent = message;
  toast.className = `toast show ${type}`;
  setTimeout(() => toast.classList.remove("show"), 3000);
}
// ---------- CSV download helper ----------
async function downloadCSV(url, fallbackFilename) {
  const res = await apiFetch(url);
  if (!res || !res.ok) {
    showToast("Could not generate the report.", "error");
    return;
  }

  const blob = await res.blob();
  const disposition = res.headers.get("Content-Disposition") || "";
  const match = disposition.match(/filename="(.+)"/);
  const filename = match ? match[1] : fallbackFilename;

  const downloadUrl = window.URL.createObjectURL(blob);
  const link = document.createElement("a");
  link.href = downloadUrl;
  link.download = filename;
  document.body.appendChild(link);
  link.click();
  link.remove();
  window.URL.revokeObjectURL(downloadUrl);

  showToast("Report downloaded.");
}