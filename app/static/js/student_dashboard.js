let myRecords = [];
let myScores = [];
let trendChartInstance = null;

function badgeClassFor(category) {
  if (category === "Top Performer") return "badge-green";
  if (category === "Average Performer") return "badge-amber";
  if (category === "At-Risk") return "badge-coral";
  return "";
}

function statusClassFor(category) {
  if (category === "Top Performer") return "status-green";
  if (category === "Average Performer") return "status-amber";
  if (category === "At-Risk") return "status-coral";
  return "status-neutral";
}

async function loadMyData() {
  const [recordsRes, scoresRes] = await Promise.all([
    apiFetch("/records/me"),
    apiFetch("/scores/me"),
  ]);

  myRecords = recordsRes && recordsRes.ok ? await recordsRes.json() : [];
  myScores = scoresRes && scoresRes.ok ? await scoresRes.json() : [];

  renderStatusCard();
  renderTrendChart();
  renderHistoryTable();
}

function findScoreForRecord(recordId) {
  return myScores.find((s) => s.record_id === recordId);
}

function renderStatusCard() {
  if (myRecords.length === 0) {
    document.getElementById("latestScore").textContent = "—";
    document.getElementById("latestCategory").textContent = "No data yet";
    document.getElementById("latestCategory").className = "status-category status-neutral";
    return;
  }

  const sorted = myRecords.slice().sort((a, b) => new Date(b.date_recorded) - new Date(a.date_recorded));
  const latestRecord = sorted[0];
  const latestScore = findScoreForRecord(latestRecord.id);

  document.getElementById("latestScore").textContent = latestScore ? latestScore.weighted_score : "—";
  const categoryEl = document.getElementById("latestCategory");
  categoryEl.textContent = latestScore ? latestScore.category : "Pending calculation";
  categoryEl.className = `status-category ${latestScore ? statusClassFor(latestScore.category) : "status-neutral"}`;

  document.getElementById("breakdownAttendance").textContent = `${latestRecord.attendance_percent}%`;
  document.getElementById("breakdownAssignment").textContent = latestRecord.assignment_score;
  document.getElementById("breakdownExam").textContent = latestRecord.exam_score;
  document.getElementById("breakdownSemester").textContent = latestRecord.semester;
}

function renderTrendChart() {
  if (typeof Chart === "undefined") return;

  const sorted = myRecords.slice().sort((a, b) => new Date(a.date_recorded) - new Date(b.date_recorded));
  const labels = sorted.map((r) => r.semester);
  const dataPoints = sorted.map((r) => {
    const score = findScoreForRecord(r.id);
    return score ? score.weighted_score : null;
  });

  const ctx = document.getElementById("trendChart");
  if (trendChartInstance) trendChartInstance.destroy();
  trendChartInstance = new Chart(ctx, {
    type: "line",
    data: {
      labels,
      datasets: [{
        label: "Weighted score",
        data: dataPoints,
        borderColor: "#2E5FF0",
        backgroundColor: "rgba(46, 95, 240, 0.1)",
        tension: 0.35,
        fill: true,
        pointRadius: 5,
        pointBackgroundColor: "#2E5FF0",
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, max: 100 } },
    },
  });
}

function renderHistoryTable() {
  const tbody = document.getElementById("historyTableBody");

  if (myRecords.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No records yet.</td></tr>`;
    return;
  }

  const sorted = myRecords.slice().sort((a, b) => new Date(b.date_recorded) - new Date(a.date_recorded));

  tbody.innerHTML = sorted.map((r) => {
    const score = findScoreForRecord(r.id);
    const scoreText = score ? score.weighted_score : "—";
    const badge = score
      ? `<span class="badge ${badgeClassFor(score.category)}">${score.category}</span>`
      : `<span class="badge">Pending</span>`;
    const date = new Date(r.date_recorded).toLocaleDateString();

    return `
      <tr>
        <td>${r.semester}</td>
        <td>${r.attendance_percent}% / ${r.assignment_score} / ${r.exam_score}</td>
        <td>${scoreText}</td>
        <td>${badge}</td>
        <td>${date}</td>
      </tr>
    `;
  }).join("");
}

loadMyData();
// ---------- Attendance History ----------
async function loadAttendanceHistory() {
  const meRes = await apiFetch("/auth/me");
  const me = meRes && meRes.ok ? await meRes.json() : null;
  if (!me) return;

  const [logsRes, percentRes] = await Promise.all([
    apiFetch("/attendance/me"),
    apiFetch(`/attendance/percentage/${me.user_id}`),
  ]);

  const logs = logsRes && logsRes.ok ? await logsRes.json() : [];
  const percentData = percentRes && percentRes.ok ? await percentRes.json() : null;

  if (percentData) {
    document.getElementById("attTotalDays").textContent = percentData.total_days_marked;
    document.getElementById("attDaysPresent").textContent = percentData.days_present;
    document.getElementById("attPercent").textContent = `${percentData.attendance_percent}%`;
  }

  const tbody = document.getElementById("attendanceLogBody");
  if (logs.length === 0) {
    tbody.innerHTML = `<tr><td colspan="2" class="empty-state">No attendance marked yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = logs.map((log) => {
    const badgeClass = log.status === "present" ? "badge-green" : "badge-coral";
    const label = log.status === "present" ? "Present" : "Absent";
    return `
      <tr>
        <td>${log.date}</td>
        <td><span class="badge ${badgeClass}">${label}</span></td>
      </tr>
    `;
  }).join("");
}

loadAttendanceHistory();
// ---------- My Profile ----------
let currentProfile = null;

function renderProfileDisplay() {
  if (!currentProfile) return;
  document.getElementById("profileAvatarInitial").textContent = currentProfile.name.charAt(0).toUpperCase();
  document.getElementById("profileDisplayName").textContent = currentProfile.name;
  document.getElementById("profileDisplayEmail").textContent = currentProfile.email;
  document.getElementById("profileDisplayCourse").textContent = currentProfile.course_name || "—";
  document.getElementById("profileDisplaySemester").textContent = currentProfile.semester;
  document.getElementById("profileDisplayTeacher").textContent = currentProfile.teacher_name || "—";

  const phoneEl = document.getElementById("profileDisplayPhone");
  if (currentProfile.phone_number) {
    phoneEl.textContent = currentProfile.phone_number;
    phoneEl.classList.remove("empty");
  } else {
    phoneEl.textContent = "Not provided";
    phoneEl.classList.add("empty");
  }
}

async function loadMyProfile() {
  const res = await apiFetch("/students/me/profile");
  if (!res || !res.ok) return;
  currentProfile = await res.json();
  renderProfileDisplay();
}

document.getElementById("editProfileBtn").addEventListener("click", () => {
  document.getElementById("profileName").value = currentProfile.name;
  document.getElementById("profileEmail").value = currentProfile.email;
  document.getElementById("profilePhone").value = currentProfile.phone_number || "";
  document.getElementById("profileDisplayCard").style.display = "none";
  document.getElementById("profileEditPanel").style.display = "block";
});

document.getElementById("cancelEditBtn").addEventListener("click", () => {
  document.getElementById("profileEditPanel").style.display = "none";
  document.getElementById("profileDisplayCard").style.display = "block";
});

document.getElementById("profileForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    name: document.getElementById("profileName").value.trim(),
    email: document.getElementById("profileEmail").value.trim(),
    phone_number: document.getElementById("profilePhone").value.trim() || null,
  };
  const res = await apiFetch("/students/me/profile", { method: "PUT", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Could not update profile.", "error");
    return;
  }
  await loadMyProfile();
  showToast("Profile updated.");
  document.getElementById("profileEditPanel").style.display = "none";
  document.getElementById("profileDisplayCard").style.display = "block";
});

document.getElementById("passwordForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    current_password: document.getElementById("currentPassword").value,
    new_password: document.getElementById("newPassword").value,
  };
  const res = await apiFetch("/students/change-password", { method: "POST", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Could not update password.", "error");
    return;
  }
  showToast("Password updated.");
  e.target.reset();
});

loadMyProfile();