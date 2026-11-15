
import os
import joblib
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import create_engine, text
from dotenv import load_dotenv


# ---------------- ENVIRONMENT ----------------

load_dotenv()

DATABASE_URL = os.getenv("DATABASE_URL")

engine = create_engine(
    DATABASE_URL,
    pool_pre_ping=True
)


# ---------------- ML MODEL ----------------

MODEL_PATH = (
    Path(__file__).resolve().parent
    / "ml"
    / "student_risk_model.joblib"
)

model = joblib.load(MODEL_PATH)


# ---------------- FASTAPI APP ----------------

app = FastAPI(
    title="EduTwin API",
    description="Student Performance Intelligence System",
    version="1.0.0"
)


# ---------------- CORS CONFIGURATION ----------------

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://localhost:5174",
        "http://127.0.0.1:5173",
        "http://127.0.0.1:5174"
    ],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------- HOME API ----------------

@app.get("/")
def home():
    return {
        "message": "Welcome to EduTwin API"
    }


# ---------------- DATABASE HEALTH CHECK ----------------

@app.get("/health")
def health():
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))

        return {
            "status": "connected",
            "database": "PostgreSQL"
        }

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=str(e)
        )


# ---------------- STUDENT API ----------------

@app.get("/students")
def get_students():

    with engine.connect() as connection:

        result = connection.execute(text("""
            SELECT
                student_id,
                name,
                email,
                department,
                semester
            FROM students
            ORDER BY student_id
        """))

        return [
            dict(row._mapping)
            for row in result
        ]


# ---------------- PERFORMANCE API ----------------

@app.get("/students/{student_id}/performance")
def get_performance(student_id: int):

    with engine.connect() as connection:

        result = connection.execute(text("""
            SELECT
                s.student_id,
                s.name,
                ROUND(
                    AVG(
                        m.marks_obtained * 100.0
                        / a.max_marks
                    ), 2
                ) AS average_percentage

            FROM students s

            JOIN marks m
                ON s.student_id = m.student_id

            JOIN assessments a
                ON m.assessment_id = a.assessment_id

            WHERE s.student_id = :sid

            GROUP BY
                s.student_id,
                s.name
        """), {"sid": student_id})

        row = result.mappings().first()

        if not row:
            raise HTTPException(
                status_code=404,
                detail="Student or performance records not found"
            )

        return dict(row)


# ---------------- ATTENDANCE API ----------------

@app.get("/attendance/summary")
def attendance_summary():

    with engine.connect() as connection:

        result = connection.execute(text("""
            SELECT
                s.student_id,
                s.name,

                COUNT(a.attendance_id) AS total_classes,

                COUNT(*) FILTER (
                    WHERE a.status = 'Present'
                ) AS present_classes

            FROM students s

            LEFT JOIN attendance a
                ON s.student_id = a.student_id

            GROUP BY
                s.student_id,
                s.name

            ORDER BY s.student_id
        """))

        return [
            dict(row._mapping)
            for row in result
        ]


# ---------------- AI / ML RISK PREDICTION API ----------------

# ---------------- STUDENT IMPROVEMENT RECOMMENDATIONS ----------------

@app.get("/recommendations/{student_id}")
def get_recommendations(student_id: int):

    with engine.connect() as connection:

        result = connection.execute(text("""
            SELECT
                s.student_id,
                s.name,

                COALESCE(
                    AVG(
                        m.marks_obtained * 100.0
                        / NULLIF(a.max_marks, 0)
                    ), 0
                ) AS average_marks,

                COALESCE(
                    100.0 * COUNT(*) FILTER (
                        WHERE att.status = 'Present'
                    ) / NULLIF(COUNT(att.attendance_id), 0),
                    0
                ) AS attendance_percentage

            FROM students s

            LEFT JOIN marks m
                ON s.student_id = m.student_id

            LEFT JOIN assessments a
                ON m.assessment_id = a.assessment_id

            LEFT JOIN attendance att
                ON s.student_id = att.student_id

            WHERE s.student_id = :sid

            GROUP BY s.student_id, s.name
        """), {"sid": student_id})

        student = result.mappings().first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    marks = float(student["average_marks"])
    attendance_pct = float(student["attendance_percentage"])

    recommendations = []

    if attendance_pct < 75:
        recommendations.append({
            "title": "Improve Attendance",
            "priority": "High",
            "message": "Your attendance is below 75%. Attend upcoming classes regularly and avoid unnecessary absences."
        })

    if marks < 65:
        recommendations.append({
            "title": "Strengthen Academic Performance",
            "priority": "High",
            "message": "Revise difficult subjects, practise questions regularly and seek help from faculty."
        })

    elif marks < 80:
        recommendations.append({
            "title": "Improve Academic Performance",
            "priority": "Medium",
            "message": "Work on weaker topics and practise previous assessment questions to improve your scores."
        })

    if marks >= 80 and attendance_pct >= 75:
        recommendations.append({
            "title": "Maintain Your Performance",
            "priority": "Low",
            "message": "Your marks and attendance are on track. Continue your consistent study routine."
        })

    if not recommendations:
        recommendations.append({
            "title": "Maintain Consistency",
            "priority": "Low",
            "message": "Continue monitoring your academic progress and attendance."
        })

    return {
        "student_id": student_id,
        "name": student["name"],
        "average_marks": round(marks, 2),
        "attendance_percentage": round(attendance_pct, 2),
        "recommendations": recommendations
    }

@app.get("/predict/{student_id}")
def predict_student_risk(student_id: int):

    with engine.connect() as connection:

        result = connection.execute(text("""
            WITH performance AS (

                SELECT
                    m.student_id,

                    AVG(
                        m.marks_obtained * 100.0
                        / a.max_marks
                    ) AS average_marks

                FROM marks m

                JOIN assessments a
                    ON m.assessment_id = a.assessment_id

                GROUP BY m.student_id
            ),

            attendance_stats AS (

                SELECT
                    student_id,

                    COUNT(*) AS total_classes,

                    COUNT(*) FILTER (
                        WHERE status = 'Present'
                    ) AS present_classes

                FROM attendance

                GROUP BY student_id
            )

            SELECT
                s.student_id,
                s.name,

                COALESCE(
                    p.average_marks, 0
                ) AS average_marks,

                COALESCE(
                    100.0 * ats.present_classes
                    / NULLIF(ats.total_classes, 0),
                    0
                ) AS attendance_percentage

            FROM students s

            LEFT JOIN performance p
                ON s.student_id = p.student_id

            LEFT JOIN attendance_stats ats
                ON s.student_id = ats.student_id

            WHERE s.student_id = :sid

        """), {"sid": student_id})

        student = result.mappings().first()

    if not student:
        raise HTTPException(
            status_code=404,
            detail="Student not found"
        )

    marks = float(student["average_marks"])
    attendance_pct = float(
        student["attendance_percentage"]
    )

    # ML Prediction

    prediction = model.predict([
        [marks, attendance_pct]
    ])[0]

    probabilities = model.predict_proba([
        [marks, attendance_pct]
    ])[0]

    confidence = {
        label: round(float(prob) * 100, 2)
        for label, prob in zip(
            model.classes_,
            probabilities
        )
    }

    return {
        "student_id": student_id,
        "name": student["name"],
        "average_marks": round(marks, 2),
        "attendance_percentage": round(
            attendance_pct, 2
        ),
        "predicted_risk": prediction,
        "prediction_confidence": confidence
    }
