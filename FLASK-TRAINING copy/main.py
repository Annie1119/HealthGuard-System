import os # 操作系統相關功能 讀取.env的檔案
import json
import httpx # 呼叫 Gemini API
from dotenv import load_dotenv # 從.env檔案載入環境變數到os.environ
from fastapi import FastAPI, Header, HTTPException, Depends, Body # FastAPI 核心元件
from pydantic import BaseModel # 用來定義資料驗證模型
from supabase import create_client, Client # sdk -> kit 工具包 
from typing import Dict, Any # python 型別註解
from fastapi.middleware.cors import CORSMiddleware # 處理跨來源資源共享 (CORS) Cross origin Resource Sharing
import jwt # 用於解碼和驗證的 JWT Token
from jwt import PyJWTError # JWT 錯誤處理
from typing import List
from typing import Optional
from models import predict_cardio_probability, predict_stroke_probability

#---1．配置與初始化 —--
load_dotenv() # 執行載入.env檔案

#======================================================
# Supabase配置 從.env檔案讀取key and address
#======================================================
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_SERVICE_KEY = os.getenv("SUPABASE_SERVICE_KEY")
SUPABASE_JWT_SECRET = os.getenv("SUPABASE_JWT_SECRET")

# Gemini 配置
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

# Gemini API 終端點
GEMINI_MODEL = "gemini-2.5-flash"
GEMINI_API_BASE = "https://generativelanguage.googleapis.com"
GEMINI_API_PATH = f"/v1beta/models/{GEMINI_MODEL}:generateContent"

# 檢查必要變數是否存在 若沒有則報錯
if not SUPABASE_URL or not SUPABASE_SERVICE_KEY or not SUPABASE_JWT_SECRET:
    raise RuntimeError("Supabase configuration missing. Please check the .env file for URL, Service Key, and JWT Secret.")
if not GEMINI_API_KEY:
    # This WARNING is acceptable because the Canvas environment may provide the key at runtime
    print("WARNING: GEMINI_API_KEY is not set. It will rely on the Canvas environment to provide it at runtime.")

app = FastAPI() # 建立 FastAPI 應用實例
supabase : Client = create_client(SUPABASE_URL, SUPABASE_SERVICE_KEY) # 初始化 Supabase 客戶端
http_client = httpx.AsyncClient(timeout=120.0) # 初始化 HTTP 非同步客戶端，設定超時時間為120秒

# ======================================================
# CORS 配置
# ======================================================
origins =[
    "http://localhost:5173",  # 允許 vite（前端框架） 常有的預設埠號
    "http://127:0.0.1:5173",
] 
 
# 加上允許的定義條件
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins, # 允許來源的請求
    allow_credentials=True, # 允許攜帶cookie 或認證資訊
    allow_methods=["*"], # 允許所有HTTP方法 (GET, POST, etc.)
    allow_headers=["*"], # 允許所有header
)
# ======================================================

# 2. 數據模型
# 定義前端傳入的數據格式
class PredictionInput(BaseModel):
    age: int
    gender: str
    systolic_bp: int
    diastolic_bp: int
    cholesterol: Optional[int] = None
    glucose: Optional[int] = None
    smoke: int
    alcohol: int
    active: int
    height: float
    weight: float
    stress_level: int 
    high_fat_diet: int 
    symptoms: List[str]=[]

    hypertension: int
    family_heart_disease: int
    avg_glucose_level: float
    bmi: Optional[float] = None
    smoking_status: str

    medical_history: str

class PossibleDisease(BaseModel):
    name: str
    # severity: str  # High | Medium | Low
    probability: float  # 0~100

# 定義後端回傳給前端的報告格式
class RiskReport(BaseModel):
    llm_report: Dict[str, Any]
    rule_report: Dict[str, Any]

class OverallInsightInput(BaseModel):
    start_date: Optional[str] = None
    end_date: Optional[str] = None

# def is_english(text: str) -> bool:
#     return all(ord(c) < 128 for c in text if c.isalpha())

# --- 3. 身份驗證依賴（PyJWT 離線驗證）---
async def get_current_user(authorization: str = Header(None)): # FaceAPI的一種自動題取機制, None就像defalut is optional, 從 Header 取出 Authorization 欄位 儲存到 authorization 變數
# Ex.
# POST /predict HTTP/1.1
# Host: localhost:8000
# Content-Type: application/json
# Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...  <-- Header 就是抓這一行
    """從 Header 中提取 JWT Token 並進行離線驗證。"""
    if not authorization or not authorization.startswith("Bearer "):
        raise HTTPException(status_code=401, detail="Authorization token missing or invalid format")
    
    token = authorization.split(" ")[1] # token 就像通行證 是亂碼, Bearer 後面的有一個空格 split 把它切開取第二個元素 Ex. eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

    try:
        # 使用 SUPABASE_JWT_SECRET 進行離線解碼
        # JWT (supabase 提供的驗證服務)
        # 使用密鑰進行 離線驗證
        payload = jwt.decode( 
            token, 
            SUPABASE_JWT_SECRET, 
            algorithms=["HS256"],
            audience = "authenticated" # 確保這個 token 是給已驗證用戶的
        )
        print(f"INFO: JWT verification successful, User ID: {payload.get('sub')}") # sub 是 JWT 的標準欄位之一，通常用來存放用戶的唯一識別碼 User ID
        return {"id" : payload.get("sub"), "user_metadata": payload}
# Ex. Inside token payload
# {
#   "sub": "550e8400-e29b-41d4-a716-446655440000", # never repeat
#   "email": "user@example.com",
#   "role": "authenticated",
#   "aud": "authenticated",
#   "exp": 1725456000
# }
    
    except PyJWTError as e:
        print(f"JWT verification failed: {e}")
        raise HTTPException(status_code=401, detail="")
    except Exception as e:
        print(f"Unexpected error during authentication: {e}")
        raise HTTPException(status_code=401, detail="")

# --- 4. 機率計算邏輯（使用 dataset / 規則 / ML）---
from models import predict_cardio_probability

def rule_hypertension(data):
    sbp = data.systolic_bp
    dbp = data.diastolic_bp
    if sbp >= 140 or dbp >= 90:
        return {"name": "Hypertension (high blood pressure)", "probability": 70.0}
    elif 120 <= sbp <= 139 or 80 <= dbp <= 89:
        return {"name": "Hypertension (high blood pressure)", "probability": 40.0}
    else:
        return {"name": "Hypertension (high blood pressure)", "probability": 10.0}

# https://www.hpa.gov.tw/Pages/Detail.aspx?nodeid=127&pid=8159

def rule_hyperlipidemia(data):
    chol = data.cholesterol
    if chol is None:
        return {"name": "Hyperlipidemia (high cholesterol)", "probability": 10.0}
    if chol > 240:
        return {"name": "Hyperlipidemia (high cholesterol)", "probability": 65.0}
    elif 200 <= chol <= 239:
        return {"name": "Hyperlipidemia (high cholesterol)", "probability": 35.0}
    else:
        return {"name": "Hyperlipidemia (high cholesterol)", "probability": 10.0}

# https://wwwv.tsgh.ndmutsgh.edu.tw/unit/10012/12867

def rule_atherosclerosis(data):
    age = data.age
    smoker = data.smoke
    sbp = data.systolic_bp
    dbp = data.diastolic_bp
    chol = data.cholesterol  
    family_hd = getattr(data, "family_heart_disease", False)  

    high_bp = (sbp >= 140 or dbp >= 90)
    high_chol = (chol is not None and chol > 240)

    conditions = 0
    conditions += 1 if age > 50 else 0
    conditions += 1 if smoker == 1 else 0
    conditions += 1 if high_bp else 0
    conditions += 1 if high_chol else 0
    conditions += 1 if family_hd else 0 

    if conditions >= 4:
        probability = 70.0
    elif conditions == 3:
        probability = 60.0
    elif conditions == 2:
        probability = 35.0
    else:
        probability = 15.0

    return {"name": "Atherosclerosis (artery hardening)", "probability": probability}

# https://www.ntuh.gov.tw/telehealth/Fpage.action?fid=1547
# https://www.liver.org.tw/journalView.php?cat=73&sid=1067&page=1

def rule_arrhythmia_by_symptoms(data):
    """
    根據勾選的心悸症狀 + 高風險因素計算機率
    """
    symptoms = getattr(data, "arrhythmia_symptoms", [])
    symptom_count = len(symptoms)

    risk_factors = 0
    if getattr(data, "hypertension", 0) == 1:
        risk_factors += 1
    if getattr(data, "family_heart_disease", 0) == 1:
        risk_factors += 1
    if getattr(data, "smoke", 0) == 1:
        risk_factors += 1
    if getattr(data, "active", 0) == 0:
        risk_factors += 1
    if getattr(data, "cholesterol", 0) > 240:
        risk_factors += 1

    total_score = symptom_count + risk_factors

    if total_score == 0:
        probability = 10.0
    elif total_score <= 3:
        probability = 35.0
    elif total_score <= 6:
        probability = 55.0
    else:
        probability = 70.0

    return {"name": "Arrhythmia (irregular heartbeat)", "probability": probability}

# https://helloyishi.com.tw/heart-health/arrhythmias/what-are-heart-palpitations/

def rule_cad(data):
    """
    根據高風險因子計算 CAD 機率
    """
    score = 0

    if getattr(data, "age", 0) >= 40:
        score += 1

    if getattr(data, "gender", "Female") == "Male":
        score += 1

    if getattr(data, "hypertension", 0) == 1:
        score += 2

    if getattr(data, "family_heart_disease", 0) == 1:
        score += 2

    if getattr(data, "bmi", 0) >= 30:
        score += 1

    if getattr(data, "cholesterol", 0) >= 240:
        score += 2

    if getattr(data, "smoke", 0) == 1:
        score += 2

    if getattr(data, "alcohol", 0) == 1:
        score += 1

    if getattr(data, "active", 1) == 0:
        score += 1

    stress = getattr(data, "stress_level", 0)
    if stress == 1:
        score += 1
    elif stress == 2:
        score += 2

    diet = getattr(data, "high_fat_diet", 0)
    if diet == 1:
        score += 1
    elif diet == 2:
        score += 2

    symptoms = getattr(data, "symptoms", [])
    if any(sym in symptoms for sym in ["chest_discomfort", "shortness_of_breath", "chest_tightness"]):
        score += 2

    if score == 0:
        probability = 5.0
    elif score <= 4:
        probability = 25.0
    elif score <= 8:
        probability = 50.0
    elif score <= 12:
        probability = 70.0
    else:
        probability = 90.0

    return {"name": "Coronary Artery Disease (heart artery block)", "probability": probability}

# https://www.tsmh.org.tw/sites/nursing_department/int_13.html
# https://wd.vghtpe.gov.tw/cvs/Fpage.action?muid=11018&fid=10428


    
def calculate_disease_probabilities(data):
    cardio_prob = predict_cardio_probability(data)
    stroke_prob = predict_stroke_probability(data)

    # Rule-based probabilities
    htn = rule_hypertension(data)
    hpl = rule_hyperlipidemia(data)
    ath = rule_atherosclerosis(data)
    cad = rule_cad(data)
    arr = rule_arrhythmia_by_symptoms(data)

    # 1) 用給 LLM 的 probabilities（可以包含全部）
    probabilities = [
        {"name": "Cardiovascular Disease (heart/vessel issues)", "probability": cardio_prob},
        {"name": "Stroke (brain blood loss)", "probability": stroke_prob},
        htn,
        hpl,
        ath,
        cad,
        arr
    ]

    # 2) rule_report 只放 rule 的部分（你也可以放全部）
    rule_report = {
        "possible_diseases": [htn, hpl, ath, arr, cad]
    }
    frontend_probabilities = [d for d in probabilities if d["probability"] >= 30]

    

    return probabilities, frontend_probabilities, rule_report

# --- 5.  LLM 交互邏輯（使用 Gemini API）---
async def call_LLM_for_Prediction(
    data: PredictionInput,
    probabilities: List[dict],
    low_risk_diseases: List[str]
) -> Dict[str, Any]: # data 必須要符合 PredictionInput 的 3 個格式, 回傳一個 Dict[str, Any] key 是字串, value 可以是任何型別

    # user_text = f"{data.gender} {data.medical_history}"
    # # 如果是英文，先翻中文
    # if is_english(user_text):
    #     user_text = await translate_to_chinese(user_text)
    #     print("INFO: 使用者輸入為英文，已翻譯成繁體中文。")
    #     print(user_text)
    user_text = data.medical_history

    # System Prompt： 強制 JSON 輸出格式並要求 Google 搜尋
    system_prompt = f"""
    You are a friendly and professional health analyst.

    You will be given:
    1. The user's basic health information
    2. A list of possible diseases and their calculated probabilities

    Your task:
    - Explain the results in simple and clear English that a non-medical person can understand
    - DO NOT change disease names or invent new diseases
    - DO NOT calculate or modify probabilities
    - Use the provided numbers verbatim for probabilities >= 30%
    - For probabilities below 30%, do NOT display the number. Instead, set the value to "Low risk"
    - At the END of the summary, add ONE sentence:
    "Additionally, you may also keep an eye on: {{low risk disease names}}."
    - This sentence must NOT include probabilities.
    - Only list disease names.
    - If there are no low risk diseases, skip this sentence.

    ⚠️ Output MUST be a single valid JSON object.
    ⚠️ No extra text, no markdown.

    The JSON MUST strictly follow this structure:

    {{
    "possible_diseases": [
        {{
        "name": "Disease name",
        "probability": 0.0 
        }}
    ],
    "summary": "Concise explanation of the overall risk in simple language",
    "recommendations": [
        "Actionable recommendation 1",
        "Actionable recommendation 2",
        "Sport recommendation with reason",
        "Food recommendation with reason"
    ]
    }}

    Rules:
    - possible_diseases MUST match the provided list
    - probability is a percentage (0–100) or "Low risk" if below 30%
    - recommendations must include:
        1. Safe actionable steps
        2. At least two sport/exercise suggestion with reason why
        3. At least two food/diet suggestion with reason why
    - Always output in English
    """

    # User query
    user_query = f"""
    User Information:
    - Age: {data.age}
    - Gender: {data.gender}
    - Height: {data.height}
    - Weight: {data.weight}
    - Hypertension: {data.hypertension}
    - Heart Disease: {data.family_heart_disease}
    - Avg Glucose Level: {data.avg_glucose_level}
    - BMI: {data.bmi}
    - Smoking Status: {data.smoking_status}
    - Family Heart Disease: {data.family_heart_disease}
    - Strees Level: {data.stress_level}
    - High Fat Diet: {data.high_fat_diet}
    - Medical history: {data.medical_history}

    Calculated cardiovascular risk probabilities:
    {json.dumps(probabilities, indent=2)}
    Low risk conditions (do NOT show percentages):
    {json.dumps(low_risk_diseases)}
    """ # """ 三引號可以讓程式碼換行 而不需要寫/n

    # --- 構造 Gemini API Payload ---
    payload = {
        "contents": [{ "parts": [{"text": user_query}]}], # 使用者查詢內容 []型態是list
        "systemInstruction": { "parts": [{ "text": system_prompt}] }, # 系統提示
        # 啟用 Google Search Tool 以進行數據 grounded 地毯式搜尋
        "tools" : [{ "google_search": {}}], 
        "generationConfig": { # 生成參數 0~2 之間 1以上越有創意 0越穩定
            "temperature": 0.1, # 降低溫度以增加輸出的穩定性
        }
    } 

    try: 
        # 確保 URL 協議和路徑完整
        full_url = f"{GEMINI_API_BASE}{GEMINI_API_PATH}?key={GEMINI_API_KEY}"

        print("DEBUG: Calling Gemini API...")
        response = await http_client.post(
            full_url, 
            json=payload # 將 payload（dict）轉換為 JSON 格式發送
        )
        response.raise_for_status() # 檢查HTTP 狀態碼

        result = response.json() # 轉換成 python dict(API 回應為 JSON 格式)

        # 解析 Gemini 響應並清理
        candidate = result.get('candidates', [{}])[0] # 取得第一個候選回應
        # 如果有 content 就抓 沒有就預設為 Json 字串'{}' 
        # 以此類推
        # 取出 parts 裡面的 text 如果沒有就預設為 Json 字串'{}' 並去除前後空白
        json_string_raw = candidate.get('content', {}).get('parts', [{}])[0].get('text', '{}').strip() 
        # 1. 如果 AI 報錯，回傳的 JSON 可能沒有 content。
        # 2. 如果連線不穩，parts 可能是一個空的清單。

        # 增強 JSON 字符串清理邏輯：提取第一個｛ 到最後一個 ｝之間的內容
        # try:
        #     start_index = json_string_raw.find("{") # find 從頭找到尾
        #     end_index = json_string_raw.rfind("}") # reversefind 從尾巴找到頭 
        #     # 找不到會回傳 -1
        #     if start_index != -1 and end_index != -1 and end_index > start_index: # end 要大於 start 因為他位置在後面
        #         json_string = json_string_raw[start_index : end_index + 1]
        #     else: 
        #         json_string = json_string_raw
            
        #     report_data = json.loads(json_string) # 將清理後的 JSON 字符串解析為 Python 字典

        # except (ValueError, json.JSONDecodeError) as e:
        #     print(f"ERROR:JSON 清理或解析失敗。原始錯: {e}")
        #     raise json.JSONDecodeError("無法從 LLM 輸出中解析純淨的 JSON 物件。", json_string_raw, 0) # 0 是錯誤位置 主要看 174 行有沒有找到 沒找到代表一開始就出錯 位置 0

        # 修改後的 JSON 處理邏輯
        try:
            start_index = json_string_raw.find("{")
            end_index = json_string_raw.rfind("}")
            if start_index != -1 and end_index != -1:
                json_string = json_string_raw[start_index : end_index + 1]
                
                # 關鍵：處理 LLM 可能回傳的非法轉義字元
                import re
                json_string = re.sub(r'[\x00-\x1F\x7F]', '', json_string) 

                report_data = json.loads(json_string)

            else:
                raise ValueError("LLM returned content does not contain JSON format")

        except Exception as e:
            print(f"JSON parsing failed: {e}")
            # 給予預設值防止報錯
            report_data = {
            "possible_diseases": probabilities,
            "summary": "Analysis could not be generated, please try again.",
            "recommendations": ["Please consult a professional healthcare provider."]
            }

        # 驗證 'risk_level'
        # if report_data.get("risk_level") not in ["high", "medium", "low", "High", "Medium", "Low"]:
        #     raise ValueError(f"LLM returned invalid or missing risk_level ('{report_data.get('risk_level')}').")
        
        # possible = report_data.get("possible_diseases")
        
        report_data["possible_diseases"] = probabilities

        # 防呆：如果 LLM 沒回 summary / recommendations，就補預設
        if not isinstance(report_data.get("summary"), str):
            report_data["summary"] = "Analysis could not be generated, please try again."

        if not isinstance(report_data.get("recommendations"), list):
            report_data["recommendations"] = ["Please consult a professional healthcare provider."]

        return report_data


        # user_wants_english = is_english(f"{data.gender} {data.medical_history}")
        # if user_wants_english:
        #     report_data = await translate_report_to_english(user_text)
        #     print("INFO: 使用者輸入為英文，已將報告翻譯成英文。")

    except httpx.HTTPStatusError as e:
        error_details = e.response.text  # Get error response as text
        print(f"ERROR: Gemini API error, status code {e.response.status_code}: {error_details}")
        raise HTTPException(status_code=500, detail=f"LLM analysis service error (HTTP {e.response.status_code}). Please check your GEMINI_API_KEY or service availability.")
    except json.JSONDecodeError as e:
        print(f"ERROR: {e}")
        raise HTTPException(status_code=500, detail=f"LLM report format error, cannot parse JSON. Please retry. Details: {str(e)[:50]}...")
    except Exception as e:
        print(f"ERROR: Unexpected error occurred when calling Gemini API: {e}")
        raise HTTPException(status_code=500, detail="Unexpected error occurred in LLM analysis service.")

async def call_LLM_for_OverallInsight(diseases: List[dict]) -> Dict[str, Any]:

    system_prompt = """
    You are a creative and expert health educator. 

    Task:
    - Explain health risks by combining deep medical mechanisms with vivid, simple metaphors.
    - Avoid dry, boring medical terms alone. Use analogies (like plumbing, engines, or city traffic).
    - Keep it interesting but scientifically accurate.

    For each disease, provide:
    1. "cause": Use a metaphor to explain the biological mechanism. (e.g., Hypertension is like "water pipes under too much pressure").
    2. "importance": Explain what happens to organs using an interesting scenario. (e.g., "The kidneys are like delicate filters being blasted by a power washer").

    Output MUST be valid JSON ONLY.

    JSON format:
    {
    "diseases": [
        {
        "name": "Disease name",
        "cause": "Vivid metaphor + biological reason",
        "importance": "Vivid scenario of what happens if ignored"
        }
    ],
    "general_note": "A supportive and witty closing remark"
    }
    """

    user_query = f"""
    Diseases observed across selected reports:
    {json.dumps(diseases, indent=2)}
    """

    payload = {
        "contents": [{ "parts": [{"text": user_query}]}],
        "systemInstruction": { "parts": [{"text": system_prompt}] },
        "generationConfig": { "temperature": 0.2 }
    }

    full_url = f"{GEMINI_API_BASE}{GEMINI_API_PATH}?key={GEMINI_API_KEY}"
    response = await http_client.post(full_url, json=payload)
    response.raise_for_status()

    result = response.json()
    text = result["candidates"][0]["content"]["parts"][0]["text"]

    start = text.find("{")
    end = text.rfind("}")
    return json.loads(text[start:end+1])

# --- 6. API Routing ---
@app.post("/predict", response_model=RiskReport)
async def predict_risk(
    data: PredictionInput,
    current_user: Dict[str, Any] = Depends(get_current_user)  # Dependency injection
):
    """
    Receive user input, get risk prediction from LLM, 
    and save the result to Supabase.
    """

    user_id = current_user.get("id")

    # ① 先用 dataset / rule / ML 算機率
    probabilities, frontend_probabilities ,rule_report = calculate_disease_probabilities(data)

    low_risk_diseases = [
        d["name"]
        for d in probabilities
        if 20 <= d.get("probability", 0) < 30
    ]

    # ② 再交給 LLM 解釋
    llm_report_data = await call_LLM_for_Prediction(
        data=data,
        probabilities=probabilities,
        low_risk_diseases=low_risk_diseases
    )

    llm_report_data["possible_diseases"] = frontend_probabilities
    
    # ③ 把 rule_report 合併到 LLM report 裡面
    merged_report = {
        "llm_report": llm_report_data,
        "rule_report": rule_report
    }

    # Save report to Supabase
    storage_data = {
        "user_id": user_id,
        "input_data": data.model_dump(),
        "llm_report": llm_report_data,
        "rule_report": rule_report
    }
        
    try:
        # Insert data using Supabase service account
        # Collection path could be /artifacts/{appId}/users/{userId}/{your_collection_name}
        # Here simplified as direct insertion into 'risk_reports' table, relying on RLS for permissions
        supabase.table("risk_reports").insert(storage_data).execute()
        print("INFO: Report data successfully saved to Supabase.")

    except Exception as e:
        print(f"WARNING: Failed to save data to Supabase: {e}. Please check if 'risk_reports' table exists and RLS rules.")

    # Return the LLM report
    return merged_report

@app.post("/overall-insight")
async def get_overall_insight(
    # 直接接收 List[dict]，不要再用 payload: OverallInsightInput
    diseases_input: List[dict] = Body(...), 
    current_user: Dict[str, Any] = Depends(get_current_user)
):
    user_id = current_user["id"]
    print(f"DEBUG: Received diseases from frontend: {diseases_input}") # 偵錯用

    # 1. 確保有收到疾病資料
    if not diseases_input:
        return {
            "diseases": [],
            "general_note": "No diseases detected in the selected reports."
        }

    # 2. 過濾出中高風險疾病 (機率 >= 30)
    # 這是為了確保送給 Gemini 的資料是乾淨且符合你需求的
    valid_diseases = []
    for d in diseases_input:
        prob = d.get("probability", 0)
        if prob >= 30:
            valid_diseases.append(d)

    if not valid_diseases:
        return {
            "diseases": [],
            "general_note": "No medium or high risk conditions to analyze."
        }

    try:
        # 3. 呼叫 LLM 進行分析 (這會回傳包含 cause 和 importance 的 JSON)
        overall_report = await call_LLM_for_OverallInsight(valid_diseases)

        # 4. 存入 Supabase (可選，但建議先註解掉這段測試，確認 LLM 沒問題再開)
   
        try:
            supabase.table("overall_reports").insert({
                "user_id": user_id,
                "diseases": overall_report.get("diseases"),
                "general_note": overall_report.get("general_note")
            }).execute()
            print("INFO: Overall insight report successfully saved to Supabase.")
        except Exception as se:
            print(f"WARNING: Failed to save overall report to Supabase: {se}")
      

        return overall_report

    except Exception as e:
        print(f"ERROR: LLM Analysis failed: {str(e)}")
        # 回傳 500 錯誤給前端，並顯示具體原因
        raise HTTPException(status_code=500, detail=f"AI Analysis Error: {str(e)}")
    
# async def translate_to_chinese(text: str) -> str:
#     translate_prompt = f"""
#     請將以下英文翻譯成繁體中文，保持原意：
#     {text}
#     """
#     payload = {
#         "contents": [{"parts": [{"text": translate_prompt}]}],
#         "generationConfig": {"temperature": 0}
#     }
#     full_url = f"{GEMINI_API_BASE}{GEMINI_API_PATH}?key={GEMINI_API_KEY}"
#     response = await http_client.post(full_url, json=payload)
#     response.raise_for_status()
#     result = response.json()
#     translated_text = result["candidates"][0]["content"]["parts"][0]["text"]
#     return translated_text.strip()

# async def translate_report_to_english(report: dict) -> dict:
#     translate_prompt = f"""
#     請將以下 JSON 內容完整翻譯成英文。
#     - 保留 JSON 結構
#     - 不要新增或刪除欄位
#     - risk_level 請翻成 High / Medium / Low

# JSON:
# {json.dumps(report, ensure_ascii=False)}
# """
#     payload = {
#         "contents": [{ "parts": [{ "text": translate_prompt }] }],
#         "generationConfig": { "temperature": 0 }
#     }

#     full_url = f"{GEMINI_API_BASE}{GEMINI_API_PATH}?key={GEMINI_API_KEY}"

#     try:
#         response = await http_client.post(full_url, json=payload)
#         response.raise_for_status()
#         result = response.json()

#         # 防呆處理
#         candidates = result.get("candidates")
#         if not candidates or not candidates[0].get("content"):
#             print(f"WARNING: Gemini 英文翻譯回報沒有 candidates 或 content, 原始結果: {result}")
#             return report  # 回傳原始中文報告

#         parts = candidates[0]["content"].get("parts")
#         if not parts or not parts[0].get("text"):
#             print(f"WARNING: Gemini 英文翻譯回報 parts 為空, 原始結果: {result}")
#             return report

#         text = parts[0]["text"].strip()
#         start = text.find("{")
#         end = text.rfind("}")
#         if start == -1 or end == -1:
#             print(f"WARNING: Gemini 英文翻譯回報不包含 JSON, 原始結果: {text}")
#             return report

#         # 清理非法字元
#         import re
#         text_clean = re.sub(r'[\x00-\x1F\x7F]', '', text[start:end+1])
#         return json.loads(text_clean)

#     except Exception as e:
#         print(f"ERROR: 翻譯報告成英文失敗, 使用原中文報告, 錯誤: {e}")
#         return report


