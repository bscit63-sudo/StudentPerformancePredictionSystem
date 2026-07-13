let allTeachers = [];
let allStudents = [];
let distributionChartInstance = null;

async function loadOverview() {
  const scoresRes = await apiFetch("/scores/");
  const scores = scoresRes && scoresRes.ok ? await scoresRes.json() : [];

  const counts = { "Top Performer": 0, "Average Performer": 0, "At-Risk": 0 };
  scores.forEach((s) => { if (counts[s.category] !== undefined) counts[s.category]++; });

  document.getElementById("statTop").textContent = counts["Top Performer"];
  document.getElementById("statAtRisk").textContent = counts["At-Risk"];

  const ctx = document.getElementById("distributionChart");
  if (typeof Chart === "undefined") return;
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

async function loadWeightConfigSummary() {
  const res = await apiFetch("/weight-configs/latest");
  const summaryEl = document.getElementById("currentWeightsSummary");
  if (!res || !res.ok) {
    summaryEl.textContent = "No weight configuration has been set yet.";
    return;
  }
  const config = await res.json();
  summaryEl.innerHTML = `
    Attendance <strong>${Math.round(config.attendance_weight * 100)}%</strong> ·
    Assignment <strong>${Math.round(config.assignment_weight * 100)}%</strong> ·
    Exam <strong>${Math.round(config.exam_weight * 100)}%</strong>
  `;
  summaryEl.classList.remove("empty-state");

  document.getElementById("weightAttendance").value = config.attendance_weight;
  document.getElementById("weightAssignment").value = config.assignment_weight;
  document.getElementById("weightExam").value = config.exam_weight;
}

async function loadTeachers() {
  const res = await apiFetch("/teachers/");
  allTeachers = res && res.ok ? await res.json() : [];

  document.getElementById("statTeachers").textContent = allTeachers.length;

  const tbody = document.getElementById("teachersTableBody");
  if (allTeachers.length === 0) {
    tbody.innerHTML = `<tr><td colspan="4" class="empty-state">No teachers yet. Add one above.</td></tr>`;
  } else {
    tbody.innerHTML = allTeachers.map((t) => `
      <tr>
        <td>${t.name}</td>
        <td>${t.email}</td>
        <td>${t.department}</td>
        <td>
          <button class="action-link" data-edit-teacher='${JSON.stringify(t)}'>Edit</button>
          <button class="action-link danger" data-delete-teacher="${t.id}">Delete</button>
        </td>
      </tr>
    `).join("");
  }

  document.querySelectorAll(".action-link[data-edit-teacher]").forEach((btn) => {
    btn.addEventListener("click", () => openEditTeacherModal(JSON.parse(btn.dataset.editTeacher)));
  });
  document.querySelectorAll(".action-link[data-delete-teacher]").forEach((btn) => {
    btn.addEventListener("click", () => deleteTeacher(btn.dataset.deleteTeacher));
  });

  const select = document.getElementById("studentTeacher");
  select.innerHTML = allTeachers.map((t) => `<option value="${t.id}">${t.name}</option>`).join("");

  const editSelect = document.getElementById("editStudentTeacher");
  editSelect.innerHTML = allTeachers.map((t) => `<option value="${t.id}">${t.name}</option>`).join("");
}

async function loadStudents() {
  const res = await apiFetch("/students/");
  allStudents = res && res.ok ? await res.json() : [];

  document.getElementById("statStudents").textContent = allStudents.length;

  const tbody = document.getElementById("studentsTableBody");
  if (allStudents.length === 0) {
    tbody.innerHTML = `<tr><td colspan="5" class="empty-state">No students yet. Add one above.</td></tr>`;
  } else {
    tbody.innerHTML = allStudents.map((s) => `
      <tr>
        <td>${s.name}</td>
        <td>${s.program}</td>
        <td>${s.semester}</td>
        <td>${s.email}</td>
        <td>
          <button class="action-link" data-edit-student='${JSON.stringify(s)}'>Edit</button>
          <button class="action-link danger" data-delete-student="${s.id}">Delete</button>
        </td>
      </tr>
    `).join("");
  }

  document.querySelectorAll(".action-link[data-edit-student]").forEach((btn) => {
    btn.addEventListener("click", () => openEditStudentModal(JSON.parse(btn.dataset.editStudent)));
  });
  document.querySelectorAll(".action-link[data-delete-student]").forEach((btn) => {
    btn.addEventListener("click", () => deleteStudent(btn.dataset.deleteStudent));
  });
}

document.getElementById("addTeacherForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    name: document.getElementById("teacherName").value.trim(),
    email: document.getElementById("teacherEmail").value.trim(),
    department: document.getElementById("teacherDept").value.trim(),
    password: document.getElementById("teacherPassword").value,
  };
  const res = await apiFetch("/teachers/", { method: "POST", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Could not add teacher.", "error");
    return;
  }
  showToast(`Teacher "${data.name}" added.`);
  e.target.reset();
  await loadTeachers();
});

const editTeacherModalOverlay = document.getElementById("editTeacherModalOverlay");
const editTeacherForm = document.getElementById("editTeacherForm");

function openEditTeacherModal(teacher) {
  document.getElementById("editTeacherId").value = teacher.id;
  document.getElementById("editTeacherName").value = teacher.name;
  document.getElementById("editTeacherEmail").value = teacher.email;
  document.getElementById("editTeacherDept").value = teacher.department;
  editTeacherModalOverlay.classList.add("open");
}

function closeEditTeacherModal() {
  editTeacherModalOverlay.classList.remove("open");
}

document.getElementById("editTeacherModalClose").addEventListener("click", closeEditTeacherModal);
editTeacherModalOverlay.addEventListener("click", (e) => {
  if (e.target === editTeacherModalOverlay) closeEditTeacherModal();
});

editTeacherForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const teacherId = document.getElementById("editTeacherId").value;
  const body = {
    name: document.getElementById("editTeacherName").value.trim(),
    email: document.getElementById("editTeacherEmail").value.trim(),
    department: document.getElementById("editTeacherDept").value.trim(),
  };
  const res = await apiFetch(`/teachers/${teacherId}`, { method: "PUT", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Could not update teacher.", "error");
    return;
  }
  showToast("Teacher updated.");
  closeEditTeacherModal();
  await loadTeachers();
});

async function deleteTeacher(teacherId) {
  if (!confirm("Delete this teacher? This is blocked if any students are still assigned to them.")) return;

  const res = await apiFetch(`/teachers/${teacherId}`, { method: "DELETE" });
  if (!res.ok) {
    const data = await res.json();
    showToast(data.detail || "Could not delete teacher.", "error");
    return;
  }
  showToast("Teacher deleted.");
  await loadTeachers();
}

document.getElementById("addStudentForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const body = {
    name: document.getElementById("studentName").value.trim(),
    email: document.getElementById("studentEmail").value.trim(),
    program: document.getElementById("studentProgram").value.trim(),
    semester: Number(document.getElementById("studentSemester").value),
    teacher_id: document.getElementById("studentTeacher").value,
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
  await loadStudents();
});

const editStudentModalOverlay = document.getElementById("editStudentModalOverlay");
const editStudentForm = document.getElementById("editStudentForm");

function openEditStudentModal(student) {
  document.getElementById("editStudentId").value = student.id;
  document.getElementById("editStudentName").value = student.name;
  document.getElementById("editStudentEmail").value = student.email;
  document.getElementById("editStudentProgram").value = student.program;
  document.getElementById("editStudentSemester").value = student.semester;
  document.getElementById("editStudentTeacher").value = student.teacher_id;
  editStudentModalOverlay.classList.add("open");
}

function closeEditStudentModal() {
  editStudentModalOverlay.classList.remove("open");
}

document.getElementById("editStudentModalClose").addEventListener("click", closeEditStudentModal);
editStudentModalOverlay.addEventListener("click", (e) => {
  if (e.target === editStudentModalOverlay) closeEditStudentModal();
});

editStudentForm.addEventListener("submit", async (e) => {
  e.preventDefault();
  const studentId = document.getElementById("editStudentId").value;
  const body = {
    name: document.getElementById("editStudentName").value.trim(),
    email: document.getElementById("editStudentEmail").value.trim(),
    program: document.getElementById("editStudentProgram").value.trim(),
    semester: Number(document.getElementById("editStudentSemester").value),
    teacher_id: document.getElementById("editStudentTeacher").value,
  };
  const res = await apiFetch(`/students/${studentId}`, { method: "PUT", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Could not update student.", "error");
    return;
  }
  showToast("Student updated.");
  closeEditStudentModal();
  await loadStudents();
});

async function deleteStudent(studentId) {
  if (!confirm("Delete this student? This cannot be undone.")) return;

  const res = await apiFetch(`/students/${studentId}`, { method: "DELETE" });
  if (!res.ok) {
    const data = await res.json();
    showToast(data.detail || "Could not delete student.", "error");
    return;
  }
  showToast("Student deleted.");
  await loadStudents();
}

document.getElementById("weightConfigForm").addEventListener("submit", async (e) => {
  e.preventDefault();
  const meRes = await apiFetch("/auth/me");
  const me = meRes && meRes.ok ? await meRes.json() : { user_id: "unknown" };

  const body = {
    attendance_weight: Number(document.getElementById("weightAttendance").value),
    assignment_weight: Number(document.getElementById("weightAssignment").value),
    exam_weight: Number(document.getElementById("weightExam").value),
    admin_id: me.user_id,
  };

  const res = await apiFetch("/weight-configs/", { method: "POST", body: JSON.stringify(body) });
  const data = await res.json();
  if (!res.ok) {
    showToast(data.detail || "Weights must add up to 1.0.", "error");
    return;
  }
  showToast("Weight configuration updated.");
  await loadWeightConfigSummary();
});
document.getElementById("exportSummaryBtn").addEventListener("click", () => {
  downloadCSV("/reports/summary.csv", "summary_report.csv");
});

document.getElementById("exportFullBtn").addEventListener("click", () => {
  downloadCSV("/reports/full.csv", "full_report.csv");
});
(async function init() {
  await Promise.all([loadTeachers(), loadStudents(), loadWeightConfigSummary(), loadOverview()]);
})();