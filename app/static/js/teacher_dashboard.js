let myStudents = [];
let latestScoreByStudent = {};
let distributionChartInstance = null;
let myTeacherId = null;
let currentHistoryStudent = { id: null, name: null };
let myCourses = [];

async function loadCourses() {
  const res = await apiFetch("/courses/");
  myCourses = res && res.ok ? await res.json() : [];
  const options = `<option value="">Select a course</option>` +
    myCourses.map((c) => `<option value="${c.id}">${c.course_name}</option>`).join("");
  document.getElementById("studentCourse").innerHTML = options;
}

async function getMyTeacherId() {
  if (myTeacherId) return myTeacherId;
  const res = await apiFetch("/auth/me");
  const me = res && res.ok ? await res.json() : null;
  myTeacherId = me ? me.user_id : null;
  return myTeacherId;
}

function badgeClassFor(category) {
  if (category === "Top Performer") return "badge-green";
  if (category === "Average Performer") return "badge-amber";
  if (category === "At-Risk") return "badge-coral";
  return "";
}

async function loadStudentsAndScores() {
  const [studentsRes, scoresRes] = await Promise.all([
    apiFetch("/students/"),
    apiFetch("/scores/"),
  ]);

  myStudents = studentsRes && studentsRes.ok ? await studentsRes.json() : [];
  const scores = scoresRes && scoresRes.ok ? await scoresRes.json() : [];

  latestScoreByStudent = {};
  scores.forEach((s) => {
    const existing = latestScoreByStudent[s.student_id];
    if (!existing || new Date(s.calculated_date) > new Date(existing.calculated_date)) {
      latestScoreByStudent[s.student_id] = s;
    }
  });

  renderTable();
  renderStats();
  renderChart();
}
document.getElementById("exportSummaryBtn").addEventListener("click", () => {
  downloadCSV("/reports/summary.csv", "my_students_summary.csv");
});

document.getElementById("exportFullBtn").addEventListener("click", () => {
  downloadCSV("/reports/full.csv", "my_students_full.csv");
});

function renderStats() {
  document.getElementById("statStudents").textContent = myStudents.length;

  const counts = { "Top Performer": 0, "Average Performer": 0, "At-Risk": 0 };
  Object.values(latestScoreByStudent).forEach((s) => {
    if (counts[s.category] !== undefined) counts[s.category]++;
  });

  document.getElementById("statTop").textContent = counts["Top Performer"];
  document.getElementById("statAverage").textContent = counts["Average Performer"];
  document.getElementById("statAtRisk").textContent = counts["At-Risk"];
}

function renderChart() {
  if (typeof Chart === "undefined") return;

  const counts = { "Top Performer": 0, "Average Performer": 0, "At-Risk": 0 };
  Object.values(latestScoreByStudent).forEach((s) => {
    if (counts[s.category] !== undefined) counts[s.category]++;
  });

  const ctx = document.getElementById("distributionChart");
  if (distributionChartInstance) distributionChartInstance.destroy();
  distributionChartInstance = new Chart(ctx, {
    type: "bar",
    data: {
      labels: ["Top Performer", "Average Performer", "At-Risk"],
      datasets: [{
        data: [counts["Top Performer"], counts["Average Performer"], counts["At-Risk"]],
        backgroundColor: ["#12B886", "#F5A524", "#F0475B"],
        borderRadius: 8,
        maxBarThickness: 60,
      }],
    },
    options: {
      responsive: true,
      plugins: { legend: { display: false } },
      scales: { y: { beginAtZero: true, ticks: { precision: 0 } } },
    },
  });
}

function renderTable() {
  const tbody = document.getElementById("studentsTableBody");

  if (myStudents.length === 0) {
    tbody.innerHTML = `<tr><td colspan="6" class="empty-state">No students assigned to you yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = myStudents.map((student) => {
    const score = latestScoreByStudent[student.id];
    const scoreText = score ? score.weighted_score : "—";
    const categoryBadge = score
      ? `<span class="badge ${badgeClassFor(score.category)}">${score.category}</span>`
      : `<span class="badge">No data</span>`;

    return `
      <tr>
        <td>${student.name}</td>
        <td>${student.course_name || "_"}</td>
        <td>${student.semester}</td>
        <td>${scoreText}</td>
        <td>${categoryBadge}</td>
        <td>
          <button class="action-link" data-student-id="${student.id}" data-student-name="${student.name}">
            Add Record
          </button>
          <button class="action-link" data-history-id="${student.id}" data-history-name="${student.name}">
            History
          </button>
        </td>
      </tr>
    `;
  }).join("");

  document.querySelectorAll(".action-link[data-student-id]").forEach((btn) => {
    btn.addEventListener("click", () => openRecordModal(btn.dataset.studentId, btn.dataset.studentName));
  });

  document.querySelectorAll(".action-link[data-history-id]").forEach((btn) => {
    btn.addEventListener("click", () => openHistoryModal(btn.dataset.historyId, btn.dataset.historyName));
  });
}

// ---------- Add / Edit Record Modal ----------
const modalOverlay = document.getElementById("recordModalOverlay");
const modalClose = document.getElementById("modalClose");
const recordForm = document.getElementById("recordForm");
const recordModalTitle = document.getElementById("recordModalTitle");
const recordSubmitBtn = document.getElementById("recordSubmitBtn");

function openRecordModal(studentId, studentName) {
  recordForm.reset();
  document.getElementById("recordStudentId").value = studentId;
  document.getElementById("editingRecordId").value = "";
  document.getElementById("modalStudentName").textContent = `For: ${studentName}`;
  recordModalTitle.textContent = "Add performance record";
  recordSubmitBtn.textContent = "Save record";
  modalOverlay.classList.add("open");
}

function openEditRecordModal(record, studentName) {
  document.getElementById("recordStudentId").value = record.student_id;
  document.getElementById("editingRecordId").value = record.id;
  document.getElementById("recordAttendance").value = record.attendance_percent;
  document.getElementById("recordAssignment").value = record.assignment_score;
  document.getElementById("recordExam").value = record.exam_score;
  document.getElementById("recordSemester").value = record.semester;
  document.getElementById("modalStudentName").textContent = `For: ${studentName}`;
  recordModalTitle.textContent = "Edit performance record";
  recordSubmitBtn.textContent = "Update record";
  modalOverlay.classList.add("open");
}

function closeRecordModal() {
  modalOverlay.classList.remove("open");
}

modalClose.addEventListener("click", closeRecordModal);
modalOverlay.addEventListener("click", (e) => {
  if (e.target === modalOverlay) closeRecordModal();
});

recordForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const editingId = document.getElementById("editingRecordId").value;

  const body = {
    student_id: document.getElementById("recordStudentId").value,
    attendance_percent: Number(document.getElementById("recordAttendance").value),
    assignment_score: Number(document.getElementById("recordAssignment").value),
    exam_score: Number(document.getElementById("recordExam").value),
    semester: document.getElementById("recordSemester").value.trim(),
  };

  const url = editingId ? `/records/${editingId}` : "/records/";
  const method = editingId ? "PUT" : "POST";

  const res = await apiFetch(url, { method, body: JSON.stringify(body) });
  const data = await res.json();

  if (!res.ok) {
    showToast(data.detail || "Could not save record.", "error");
    return;
  }

  showToast(editingId ? "Record updated." : "Record saved and score calculated.");
  closeRecordModal();
  await loadStudentsAndScores();

  if (currentHistoryStudent.id === body.student_id) {
    await openHistoryModal(currentHistoryStudent.id, currentHistoryStudent.name);
  }
});

// ---------- History Modal ----------
const historyModalOverlay = document.getElementById("historyModalOverlay");
const historyModalClose = document.getElementById("historyModalClose");

async function openHistoryModal(studentId, studentName) {
  currentHistoryStudent = { id: studentId, name: studentName };
  document.getElementById("historyStudentName").textContent = `For: ${studentName}`;
  const tbody = document.getElementById("historyTableBody");
  tbody.innerHTML = `<tr><td colspan="6" class="empty-state">Loading...</td></tr>`;
  historyModalOverlay.classList.add("open");

  const [recordsRes, scoresRes] = await Promise.all([
    apiFetch(`/records/student/${studentId}`),
    apiFetch(`/scores/student/${studentId}`),
  ]);

  const records = recordsRes && recordsRes.ok ? await recordsRes.json() : [];
  const scores = scoresRes && scoresRes.ok ? await scoresRes.json() : [];

  const scoreByRecordId = {};
  scores.forEach((s) => { scoreByRecordId[s.record_id] = s; });

  const sortedRecords = records.slice().sort((a, b) => new Date(b.date_recorded) - new Date(a.date_recorded));

  const rows = sortedRecords.map((r) => {
    const score = scoreByRecordId[r.id];
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
        <td>
          <button class="action-link" data-edit-record='${JSON.stringify(r)}'>Edit</button>
          <button class="action-link danger" data-delete-record="${r.id}">Delete</button>
        </td>
      </tr>
    `;
  });

  tbody.innerHTML = rows.length
    ? rows.join("")
    : `<tr><td colspan="6" class="empty-state">No records yet for this student.</td></tr>`;

  document.querySelectorAll(".action-link[data-edit-record]").forEach((btn) => {
    btn.addEventListener("click", () => {
      const record = JSON.parse(btn.dataset.editRecord);
      closeHistoryModal();
      openEditRecordModal(record, currentHistoryStudent.name);
    });
  });

  document.querySelectorAll(".action-link[data-delete-record]").forEach((btn) => {
    btn.addEventListener("click", () => deleteRecord(btn.dataset.deleteRecord));
  });
}

async function deleteRecord(recordId) {
  if (!confirm("Delete this record? This also removes its calculated score. This cannot be undone.")) {
    return;
  }

  const res = await apiFetch(`/records/${recordId}`, { method: "DELETE" });

  if (!res.ok) {
    const data = await res.json();
    showToast(data.detail || "Could not delete record.", "error");
    return;
  }

  showToast("Record deleted.");
  await loadStudentsAndScores();
  await openHistoryModal(currentHistoryStudent.id, currentHistoryStudent.name);
}

function closeHistoryModal() {
  historyModalOverlay.classList.remove("open");
}

historyModalClose.addEventListener("click", closeHistoryModal);
historyModalOverlay.addEventListener("click", (e) => {
  if (e.target === historyModalOverlay) closeHistoryModal();
});

// ---------- Add Student ----------
document.getElementById("addStudentForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const teacherId = await getMyTeacherId();

  const body = {
    name: document.getElementById("studentName").value.trim(),
    email: document.getElementById("studentEmail").value.trim(),
    course_id: document.getElementById("studentCourse").value,
    semester: Number(document.getElementById("studentSemester").value),
    teacher_id: teacherId,
    password: document.getElementById("studentPassword").value,
  };

  const res = await apiFetch("/students/", { method: "POST", body: JSON.stringify(body) });
  const data = await res.json();

  if (!res.ok) {
    showToast(data.detail || "Could not add student.", "error");
    return;
  }

  showToast(`Student "${data.name}" added.`);
  e.target.reset();
  await loadStudentsAndScores();
});

loadCourses();
loadStudentsAndScores();
// ---------- Take Attendance ----------
let attendanceState = {};

function todayISO() {
  return new Date().toISOString().split("T")[0];
}

function renderAttendanceTable() {
  const tbody = document.getElementById("attendanceTableBody");

  if (myStudents.length === 0) {
    tbody.innerHTML = `<tr><td colspan="3" class="empty-state">No students assigned to you yet.</td></tr>`;
    return;
  }

  tbody.innerHTML = myStudents.map((student) => {
    const status = attendanceState[student.id] || "present";
    return `
      <tr>
        <td>${student.name}</td>
        <td>${student.course_name || "—"}</td>
        <td>
          <div class="attendance-toggle" data-student-id="${student.id}">
            <button type="button" class="attendance-btn present ${status === "present" ? "active" : ""}" data-status="present">Present</button>
            <button type="button" class="attendance-btn absent ${status === "absent" ? "active" : ""}" data-status="absent">Absent</button>
          </div>
        </td>
      </tr>
    `;
  }).join("");

  document.querySelectorAll(".attendance-toggle").forEach((toggle) => {
    const studentId = toggle.dataset.studentId;
    toggle.querySelectorAll(".attendance-btn").forEach((btn) => {
      btn.addEventListener("click", () => {
        attendanceState[studentId] = btn.dataset.status;
        renderAttendanceTable();
      });
    });
  });
}

document.getElementById("attendanceDate").value = todayISO();

document.querySelector("[data-section='section-attendance']").addEventListener("click", () => {
  myStudents.forEach((s) => {
    if (!attendanceState[s.id]) attendanceState[s.id] = "present";
  });
  renderAttendanceTable();
});

document.getElementById("saveAttendanceBtn").addEventListener("click", async () => {
  const date = document.getElementById("attendanceDate").value;
  if (!date) {
    showToast("Pick a date first.", "error");
    return;
  }

  const entries = myStudents.map((s) => ({
    student_id: s.id,
    status: attendanceState[s.id] || "present",
  }));

  const res = await apiFetch("/attendance/mark", {
    method: "POST",
    body: JSON.stringify({ date, entries }),
  });
  const data = await res.json();

  if (!res.ok) {
    showToast(data.detail || "Could not save attendance.", "error");
    return;
  }

  showToast(`Attendance saved for ${data.students_marked} student(s).`);
});
// ---------- My Profile ----------
let currentProfile = null;

function renderProfileDisplay() {
  if (!currentProfile) return;
  document.getElementById("profileAvatarInitial").textContent = currentProfile.name.charAt(0).toUpperCase();
  document.getElementById("profileDisplayName").textContent = currentProfile.name;
  document.getElementById("profileDisplayEmail").textContent = currentProfile.email;
  document.getElementById("profileDisplayDept").textContent = currentProfile.department || "—";

  const phoneEl = document.getElementById("profileDisplayPhone");
  if (currentProfile.phone_number) {
    phoneEl.textContent = currentProfile.phone_number;
    phoneEl.classList.remove("empty");
  } else {
    phoneEl.textContent = "Not provided";
    phoneEl.classList.add("empty");
  }

  const coursesEl = document.getElementById("profileDisplayCourses");
  if (currentProfile.courses && currentProfile.courses.length > 0) {
    coursesEl.textContent = currentProfile.courses.join(", ");
    coursesEl.classList.remove("empty");
  } else {
    coursesEl.textContent = "No courses assigned";
    coursesEl.classList.add("empty");
  }
}

async function loadMyProfile() {
  const res = await apiFetch("/teachers/me/profile");
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
  const res = await apiFetch("/teachers/me/profile", { method: "PUT", body: JSON.stringify(body) });
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
  const res = await apiFetch("/teachers/change-password", { method: "POST", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Could not update password.", "error");
    return;
  }
  showToast("Password updated.");
  e.target.reset();
});

loadMyProfile();