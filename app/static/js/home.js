const WEIGHTS = { attendance: 0.2, assignment: 0.3, exam: 0.5 };

const attendanceRange = document.getElementById("attendanceRange");
const assignmentRange = document.getElementById("assignmentRange");
const examRange = document.getElementById("examRange");

const attendanceVal = document.getElementById("attendanceVal");
const assignmentVal = document.getElementById("assignmentVal");
const examVal = document.getElementById("examVal");

const gaugeFill = document.getElementById("gaugeFill");
const gaugeScore = document.getElementById("gaugeScore");
const gaugeLabel = document.getElementById("gaugeLabel");

function classify(score) {
  if (score >= 75) return { label: "Top Performer", color: "#12B886" };
  if (score >= 50) return { label: "Average Performer", color: "#F5A524" };
  return { label: "At-Risk", color: "#F0475B" };
}

function updateGauge() {
  const attendance = Number(attendanceRange.value);
  const assignment = Number(assignmentRange.value);
  const exam = Number(examRange.value);

  attendanceVal.textContent = attendance;
  assignmentVal.textContent = assignment;
  examVal.textContent = exam;

  const score = Math.round(
    attendance * WEIGHTS.attendance +
    assignment * WEIGHTS.assignment +
    exam * WEIGHTS.exam
  );

  const { label, color } = classify(score);

  gaugeFill.style.strokeDasharray = `${score} 100`;
  gaugeFill.style.stroke = color;
  gaugeScore.textContent = score;
  gaugeLabel.textContent = label;
  gaugeLabel.style.color = color;
}

if (attendanceRange && assignmentRange && examRange) {
  [attendanceRange, assignmentRange, examRange].forEach((el) =>
    el.addEventListener("input", updateGauge)
  );
  updateGauge();
}