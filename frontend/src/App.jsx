
import { useEffect, useState } from "react";
import {
  ResponsiveContainer,
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  PieChart,
  Pie,
  Cell,
  Legend
} from "recharts";
import "./App.css";

const API = "http://127.0.0.1:8000";

function App() {
  const [students, setStudents] = useState([]);
  const [selectedId, setSelectedId] = useState("");
  const [predictions, setPredictions] = useState([]);
  const [performanceData, setPerformanceData] = useState([]);
  const [attendanceData, setAttendanceData] = useState([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    async function loadDashboard() {
      try {
        setLoading(true);
        setError("");

        const studentRes = await fetch(`${API}/students`);
        if (!studentRes.ok) throw new Error("Unable to load students");

        const studentList = await studentRes.json();
        setStudents(studentList);

        if (studentList.length > 0) {
          setSelectedId(String(studentList[0].student_id));
        }

        const [attendanceRes, ...studentResults] = await Promise.all([
          fetch(`${API}/attendance/summary`),
          ...studentList.map(async (student) => {
            const [performance, prediction] = await Promise.all([
              fetch(`${API}/students/${student.student_id}/performance`)
                .then((r) => r.ok ? r.json() : null)
                .catch(() => null),
              fetch(`${API}/predict/${student.student_id}`)
                .then((r) => r.ok ? r.json() : null)
                .catch(() => null)
            ]);

            return { student, performance, prediction };
          })
        ]);

        if (!attendanceRes.ok) {
          throw new Error("Unable to load attendance");
        }

        const attendance = await attendanceRes.json();

        setPerformanceData(
          studentResults
            .filter((item) => item.performance)
            .map((item) => ({
              name: item.student.name,
              marks: Number(item.performance.average_percentage)
            }))
        );

        setAttendanceData(
          attendance.map((item) => {
            const total = Number(item.total_classes);
            const present = Number(item.present_classes);

            return {
              name: item.name,
              attendance: total > 0
                ? Number(((present / total) * 100).toFixed(2))
                : 0
            };
          })
        );

        setPredictions(
          studentResults
            .filter((item) => item.prediction)
            .map((item) => item.prediction)
        );
      } catch (err) {
        setError(err.message || "Failed to fetch dashboard data");
      } finally {
        setLoading(false);
      }
    }

    loadDashboard();
  }, []);

  const selectedStudent = predictions.find(
    (item) => String(item.student_id) === selectedId
  );

  const riskData = [
    {
      name: "Low Risk",
      value: predictions.filter((p) => p.predicted_risk === "Low Risk").length
    },
    {
      name: "Medium Risk",
      value: predictions.filter((p) => p.predicted_risk === "Medium Risk").length
    },
    {
      name: "High Risk",
      value: predictions.filter((p) => p.predicted_risk === "High Risk").length
    }
  ].filter((item) => item.value > 0);

  const riskColors = ["#20a779", "#e9a23b", "#df5b5b"];

  if (loading) {
    return <div className="loading">Loading EduTwin analytics...</div>;
  }

  return (
    <div className="app">
      <aside className="sidebar">
        <h2>✦ EduTwin</h2>
        <p className="tagline">Student Intelligence Platform</p>

        <nav>
          <div className="active">▦ Dashboard</div>
          <div>♙ Students</div>
          <div>◷ Performance</div>
          <div>⌁ AI Predictions</div>
        </nav>

        <p className="sidebar-footer">Powered by AI & PostgreSQL</p>
      </aside>

      <main className="main">
        <header>
          <div>
            <p className="eyebrow">OVERVIEW</p>
            <h1>Student Dashboard</h1>
            <p className="subheading">
              Academic analytics and AI-powered student intelligence.
            </p>
          </div>
          <span className="status">● System Connected</span>
        </header>

        {error && <p className="error">{error}</p>}

        <section className="selector">
          <label htmlFor="student">Select Student</label>
          <select
            id="student"
            value={selectedId}
            onChange={(e) => setSelectedId(e.target.value)}
          >
            {students.map((student) => (
              <option key={student.student_id} value={student.student_id}>
                {student.name}
              </option>
            ))}
          </select>
        </section>

        <section className="cards">
          <article className="metric">
            <span>👥</span>
            <p>Total Students</p>
            <h2>{students.length}</h2>
            <small>Registered students</small>
          </article>

          <article className="metric">
            <span>📊</span>
            <p>Average Marks</p>
            <h2>
              {selectedStudent
                ? `${selectedStudent.average_marks}%`
                : "--"}
            </h2>
            <small>Selected student</small>
          </article>

          <article className="metric">
            <span>📅</span>
            <p>Attendance</p>
            <h2>
              {selectedStudent
                ? `${selectedStudent.attendance_percentage}%`
                : "--"}
            </h2>
            <small>Selected student</small>
          </article>
        </section>

        <section className="bottom-grid">
          <article className="panel">
            <p className="eyebrow">STUDENT PROFILE</p>
            <h2>{selectedStudent?.name || "Student profile"}</h2>
            <p className="subheading">
              Academic performance intelligence
            </p>

            <div className="profile-line">
              <span>Student ID</span>
              <strong>{selectedStudent?.student_id ?? "--"}</strong>
            </div>

            <div className="profile-line">
              <span>Average Marks</span>
              <strong>{selectedStudent?.average_marks ?? "--"}%</strong>
            </div>

            <div className="profile-line">
              <span>Attendance</span>
              <strong>
                {selectedStudent?.attendance_percentage ?? "--"}%
              </strong>
            </div>
          </article>

          <article className="panel">
            <p className="eyebrow">AI / ML INSIGHTS</p>
            <h2>Risk Prediction</h2>

            <div className="risk">
              {selectedStudent?.predicted_risk || "No prediction"}
            </div>

            <p className="subheading">
              Predicted using the trained student risk model.
            </p>

            <h3>Prediction Confidence</h3>

            {selectedStudent?.prediction_confidence &&
              Object.entries(selectedStudent.prediction_confidence).map(
                ([label, value]) => (
                  <div className="confidence" key={label}>
                    <div>
                      <span>{label}</span>
                      <strong>{value}%</strong>
                    </div>
                    <div className="bar">
                      <div style={{ width: `${value}%` }} />
                    </div>
                  </div>
                )
              )}
          </article>
        </section>

        <h2 className="section-heading">Academic Analytics</h2>

        <section className="chart-grid">
          <article className="panel chart-panel">
            <p className="eyebrow">PERFORMANCE COMPARISON</p>
            <h2>Student-wise Marks</h2>

            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={performanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar
                  dataKey="marks"
                  name="Average Marks (%)"
                  fill="#6875d9"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </article>

          <article className="panel chart-panel">
            <p className="eyebrow">ATTENDANCE ANALYSIS</p>
            <h2>Student-wise Attendance</h2>

            <ResponsiveContainer width="100%" height={280}>
              <BarChart data={attendanceData}>
                <CartesianGrid strokeDasharray="3 3" />
                <XAxis dataKey="name" />
                <YAxis domain={[0, 100]} />
                <Tooltip />
                <Bar
                  dataKey="attendance"
                  name="Attendance (%)"
                  fill="#20a779"
                  radius={[6, 6, 0, 0]}
                />
              </BarChart>
            </ResponsiveContainer>
          </article>

          <article className="panel chart-panel risk-chart-panel">
            <p className="eyebrow">PREDICTIVE ANALYTICS</p>
            <h2>Student Risk Distribution</h2>

            {riskData.length > 0 ? (
              <ResponsiveContainer width="100%" height={300}>
                <PieChart>
                  <Pie
                    data={riskData}
                    dataKey="value"
                    nameKey="name"
                    cx="50%"
                    cy="45%"
                    outerRadius={95}
                    label
                  >
                    {riskData.map((entry, index) => (
                      <Cell
                        key={entry.name}
                        fill={riskColors[
                          ["Low Risk", "Medium Risk", "High Risk"]
                            .indexOf(entry.name)
                        ]}
                      />
                    ))}
                  </Pie>
                  <Tooltip />
                  <Legend />
                </PieChart>
              </ResponsiveContainer>
            ) : (
              <p>No prediction data available.</p>
            )}
          </article>
        </section>

        <footer>
          EduTwin © 2026 · AI-Powered Student Digital Twin
        </footer>
      </main>
    </div>
  );
}

export default App;
