from fastapi import FastAPI, Header, HTTPException, Request, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import time
import random
import os
from fastapi import UploadFile, File
from pdf_utils import extract_text_from_pdf
from ai_service import translate_pdf_text
from ai_service import generate_lesson, user_usage, build_usage_response
from pdf_generator import create_pdf

# 🔐 Firebase
import firebase_admin
from firebase_admin import credentials, auth

cred = credentials.Certificate("firebase_key.json")
firebase_admin.initialize_app(cred)

app = FastAPI()

# ✅ CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

user_last_request_time = {}
COOLDOWN_SECONDS = 60
otp_store = {}


# =========================
# 🔐 AUTH
# =========================
def verify_token(authorization: str):
    if not authorization:
        raise HTTPException(status_code=401, detail="No token")

    try:
        token = authorization.split(" ")[1]
        return auth.verify_id_token(token)
    except:
        raise HTTPException(status_code=401, detail="Invalid token")


def check_cooldown(user_id):
    now = time.time()

    if user_id in user_last_request_time:
        diff = now - user_last_request_time[user_id]

        if diff < COOLDOWN_SECONDS:
            raise HTTPException(status_code=429, detail="Cooldown active")

    user_last_request_time[user_id] = now


# =========================
# 🔐 OTP
# =========================
@app.post("/send-otp")
async def send_otp(req: Request):
    data = await req.json()
    email = data.get("email")

    otp = str(random.randint(1000, 9999))

    otp_store[email] = {
        "otp": otp,
        "expires": time.time() + 300
    }

    print("🔥 OTP:", otp)

    return {"success": True}


@app.post("/verify-otp")
async def verify_otp(req: Request):
    data = await req.json()
    email = data.get("email")
    code = data.get("code")

    if email not in otp_store:
        return {"success": False}

    if otp_store[email]["otp"] != code:
        return {"success": False}

    del otp_store[email]

    return {"success": True}


# =========================
# 🚀 GENERATE PDF
# =========================
@app.get("/generate-pdf")
def generate_pdf(
    level: str = "N3",
    topic: str = "Grammar",
    pages: int = 1,
    difficulty: str = "Medium",
    authorization: str = Header(None)
):
    user = verify_token(authorization)
    user_id = user["uid"]

    check_cooldown(user_id)

    result = generate_lesson(user_id, level, topic, pages, difficulty, True, True, "")

    filename = f"{uuid.uuid4()}.pdf"
    file_path = os.path.join(os.getcwd(), filename)

    create_pdf(file_path, result["text"])

    return {
        "filename": filename,
        "usage": result["usage"]
    }


# =========================
# 🔥 TRANSLATE PDF (FIXED)
# =========================
@app.post("/translate-pdf")
async def translate_pdf(file: UploadFile = File(...)):

    try:
        # save uploaded file
        input_path = f"input_{uuid.uuid4()}.pdf"
        output_path = f"translated_{uuid.uuid4()}.pdf"

        with open(input_path, "wb") as f:
            f.write(await file.read())

        # 🔥 SIMULATE GEMINI (replace with your real code)
        # For now just copy file
        with open(input_path, "rb") as f_in:
            with open(output_path, "wb") as f_out:
                f_out.write(f_in.read())

        os.remove(input_path)

        return {
            "success": True,
            "filename": output_path
        }

    except Exception as e:
        print(e)
        return {"success": False}


# =========================
# 📥 DOWNLOAD
# =========================
@app.get("/download/{filename}")
def download_file(filename: str):
    path = os.path.join(os.getcwd(), filename)

    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=path,
        media_type="application/pdf",
        filename="file.pdf"
    )

# =========================
# 🌐 TRANSLATE PDF (GEMINI)
# =========================
@app.post("/translate-pdf")
async def translate_pdf(file: UploadFile = File(...)):
    try:
        input_filename = f"input_{uuid.uuid4()}.pdf"
        output_filename = f"translated_{uuid.uuid4()}.pdf"

        input_path = os.path.join(os.getcwd(), input_filename)
        output_path = os.path.join(os.getcwd(), output_filename)

        # 📥 Save uploaded file
        with open(input_path, "wb") as f:
            f.write(await file.read())

        # 📖 Extract text
        text = extract_text_from_pdf(input_path)
        print("🧾 TEXT SAMPLE:", text[:300])  # 🔥 DEBUG
        if not text.strip():
            return {"success": False, "error": "Empty PDF"}

        # ⚠️ LIMIT TEXT (VERY IMPORTANT)
        text = text[:12000]

        # 🤖 Gemini translation
        translated_text = translate_pdf_text(text)

        # 📄 Create new PDF
        create_pdf(output_path, translated_text)

        # 🧹 cleanup input
        os.remove(input_path)

        return {
            "success": True,
            "filename": output_filename
        }

    except Exception as e:
        print("❌ TRANSLATE ERROR:", e)
        return {"success": False, "error": str(e)}