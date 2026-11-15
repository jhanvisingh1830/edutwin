
import numpy as np
import joblib

from pathlib import Path
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score, classification_report

# Reproducible sample dataset
np.random.seed(42)

# Features: average marks and attendance percentage
average_marks = np.random.uniform(20, 100, 500)
attendance = np.random.uniform(30, 100, 500)

X = np.column_stack((average_marks, attendance))

# Demo labels based on academic risk rules
y = []

for marks, attendance_pct in X:
    if marks < 45 or attendance_pct < 60:
        y.append("High Risk")
    elif marks < 65 or attendance_pct < 75:
        y.append("Medium Risk")
    else:
        y.append("Low Risk")

y = np.array(y)

# Split data
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

# Train model
model = RandomForestClassifier(
    n_estimators=100,
    random_state=42
)

model.fit(X_train, y_train)

# Evaluate
predictions = model.predict(X_test)

print("Model Accuracy:", accuracy_score(y_test, predictions))
print("\nClassification Report:")
print(classification_report(y_test, predictions))

# Save trained model
model_path = Path(__file__).resolve().parent / "student_risk_model.joblib"
joblib.dump(model, model_path)

print("\nModel saved successfully!")
print("Location:", model_path)
