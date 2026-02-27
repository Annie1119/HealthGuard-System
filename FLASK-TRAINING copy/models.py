import pandas as pd
import joblib
import numpy as np
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler

# ==================================================
# 共用設定
# ==================================================
CARDIO_FEATURES = [
    "age_years", "gender",
    "ap_hi", "ap_lo",
    "cholesterol", "gluc",
    "smoke", "alco", "active",
    "height", "weight"
]


# ==================================================
# Cardio Model
# ==================================================
def train_cardio_model():
    df = pd.read_csv("cardio.csv", sep=";")

    # cardio.csv 的 age 是「天數」
    df["age_years"] = df["age"] / 365.25

    # gender: 1=female, 2=male → 0/1
    df["gender"] = df["gender"].map({1: 0, 2: 1})

    X = df[CARDIO_FEATURES]
    y = df["cardio"]

    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = LogisticRegression(max_iter=10000)
    model.fit(X_scaled, y)

    joblib.dump(model, "cardio_model.pkl")
    joblib.dump(scaler, "scaler.pkl")

    print("✅ Cardio model trained and saved")


def predict_cardio_probability(data):
    model = joblib.load("cardio_model.pkl")
    scaler = joblib.load("scaler.pkl")

    # 讀取訓練資料，用來補中位數（避免亂填）
    df = pd.read_csv("cardio.csv", sep=";")
    cholesterol_median = df["cholesterol"].median()
    gluc_median = df["gluc"].median()

    cholesterol = (
        data.cholesterol if data.cholesterol in [1, 2, 3]
        else cholesterol_median
    )
    glucose = (
        data.glucose if data.glucose in [1, 2, 3]
        else gluc_median
    )

    row = {
        "age_years": data.age,  # 前端已是「歲」
        "gender": 1 if data.gender == "Male" else 0,
        "ap_hi": data.systolic_bp,
        "ap_lo": data.diastolic_bp,
        "cholesterol": cholesterol,
        "gluc": glucose,
        "smoke": data.smoke,
        "alco": data.alcohol,
        "active": data.active,
        "height": data.height,
        "weight": data.weight
    }

    X = pd.DataFrame([row], columns=CARDIO_FEATURES)
    X_scaled = scaler.transform(X)

    prob = model.predict_proba(X_scaled)[0][1]

    # 醫療 AI 顯示保護（避免 0% / 100%）
    prob = max(min(prob, 0.95), 0.01)

    return round(prob * 100, 1)


# ==================================================
# Stroke Model
# ==================================================
def train_stroke_model():
    df = pd.read_csv("stroke.csv")

    df["bmi"] = df["bmi"].fillna(df["bmi"].median())

    df["gender"] = df["gender"].map({
        "Male": 0,
        "Female": 1,
        "Other": 2
    })

    df = pd.get_dummies(df, columns=["smoking_status"], drop_first=False)

    smoking_cols = [
        "smoking_status_never smoked",
        "smoking_status_formerly smoked",
        "smoking_status_smokes",
        "smoking_status_N/A"
    ]

    for col in smoking_cols:
        if col not in df.columns:
            df[col] = 0

    features = [
        "age", "gender", "hypertension", "family_heart_disease",
        "avg_glucose_level", "bmi"
    ] + smoking_cols

    X = df[features]
    y = df["stroke"]

    model = LogisticRegression(max_iter=1000)
    model.fit(X, y)

    joblib.dump(model, "stroke_model.pkl")

    print("✅ Stroke model trained and saved")


def predict_stroke_probability(data):
    model = joblib.load("stroke_model.pkl")

    bmi = data.weight / ((data.height / 100) ** 2)

    smoking_map = {
        "never smoked": [1, 0, 0, 0],
        "formerly smoked": [0, 1, 0, 0],
        "smokes": [0, 0, 1, 0],
        "N/A": [0, 0, 0, 1]
    }

    never, former, smokes, na = smoking_map.get(
        data.smoking_status, [0, 0, 0, 1]
    )

    X = pd.DataFrame([{
        "age": data.age,
        "gender": 0 if data.gender == "Male" else 1,
        "hypertension": data.hypertension,
        "family_heart_disease": data.family_heart_disease,
        "avg_glucose_level": data.avg_glucose_level,
        "bmi": bmi,
        "smoking_status_never smoked": never,
        "smoking_status_formerly smoked": former,
        "smoking_status_smokes": smokes,
        "smoking_status_N/A": na
    }])

    prob = model.predict_proba(X)[0][1]
    prob = max(min(prob, 0.95), 0.01)

    return round(prob * 100, 1)


# ==================================================
# 只有直接執行 models.py 才訓練
# ==================================================
if __name__ == "__main__":
    train_cardio_model()
    train_stroke_model()




