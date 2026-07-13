const roleTabs = document.querySelectorAll(".role-tab");
const submitLabel = document.getElementById("submitLabel");
const loginForm = document.getElementById("loginForm");
const formError = document.getElementById("formError");
const submitBtn = document.getElementById("submitBtn");

let activeRole = "admin";

const ROLE_CONFIG = {
  admin:   { endpoint: "/auth/admin/login", label: "Log in as Admin",   redirect: "/admin/dashboard" },
  teacher: { endpoint: "/teachers/login",   label: "Log in as Teacher", redirect: "/teacher/dashboard" },
  student: { endpoint: "/students/login",   label: "Log in as Student", redirect: "/student/dashboard" },
};

roleTabs.forEach((tab) => {
  tab.addEventListener("click", () => {
    roleTabs.forEach((t) => {
      t.classList.remove("active");
      t.setAttribute("aria-selected", "false");
    });
    tab.classList.add("active");
    tab.setAttribute("aria-selected", "true");
    activeRole = tab.dataset.role;
    submitLabel.textContent = ROLE_CONFIG[activeRole].label;
    hideError();
  });
});

function showError(message) {
  formError.textContent = message;
  formError.hidden = false;
}

function hideError() {
  formError.hidden = true;
  formError.textContent = "";
}

loginForm.addEventListener("submit", async (event) => {
  event.preventDefault();
  hideError();

  const email = document.getElementById("email").value.trim();
  const password = document.getElementById("password").value;
  const config = ROLE_CONFIG[activeRole];

  submitBtn.disabled = true;
  const originalLabel = submitLabel.textContent;
  submitLabel.textContent = "Logging in...";

  try {
    const response = await fetch(config.endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    const data = await response.json();

    if (!response.ok) {
      showError(data.detail || "Incorrect email or password.");
      return;
    }

    localStorage.setItem("spps_token", data.access_token);
    localStorage.setItem("spps_role", activeRole);

    window.location.href = config.redirect;
  } catch (err) {
    showError("Could not reach the server. Is it running?");
  } finally {
    submitBtn.disabled = false;
    submitLabel.textContent = originalLabel;
  }
});