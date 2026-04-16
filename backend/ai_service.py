import google.generativeai as genai
import os
import time

# 🔑 Load API key
genai.configure(api_key=os.getenv("GEMINI_API_KEY"))

# 🤖 Model
model = genai.GenerativeModel("gemini-3-flash-preview")

# 📊 GLOBAL STORAGE (temporary - resets on restart)
user_usage = {}

# ⚙️ LIMITS
MAX_REQUESTS = 5        # total free requests
RPM_LIMIT = 5           # per minute


# 📊 Build usage response (VERY IMPORTANT)
def build_usage_response(data):
    return {
        "total": data["total"],
        "limit": MAX_REQUESTS,
        "remaining": max(0, MAX_REQUESTS - data["total"]),
        "rpm_used": len(data["timestamps"]),
        "rpm_limit": RPM_LIMIT
    }


# 🚀 MAIN FUNCTION
def generate_lesson(
    user_id,
    level,
    topic,
    pages,
    difficulty,
    furigana,
    translation,
    customTopic
):
    try:
        now = time.time()

        # 🧠 Initialize user
        if user_id not in user_usage:
            user_usage[user_id] = {
                "total": 0,
                "timestamps": []
            }

        data = user_usage[user_id]

        # 🧹 Clean old timestamps (last 60 sec only)
        data["timestamps"] = [
            t for t in data["timestamps"] if now - t < 60
        ]

        # 🚫 RPM LIMIT CHECK
        if len(data["timestamps"]) >= RPM_LIMIT:
            return {
                "error": "⚠️ Too many requests. Please wait a few seconds.",
                "usage": build_usage_response(data)
            }

        # 🚫 TOTAL LIMIT CHECK
        if data["total"] >= MAX_REQUESTS:
            return {
                "error": "🚫 Free limit reached (5 PDFs). Upgrade to premium 🚀",
                "usage": build_usage_response(data)
            }

        # ✅ Update usage
        data["timestamps"].append(now)
        data["total"] += 1

        # 🧠 Build AI prompt
        prompt = f"""
        Create a professional JLPT {level} Japanese lesson.

        Topic: {customTopic if customTopic else topic}
        Difficulty: {difficulty}
        Length: {pages} pages

        Include:
        - Grammar explanations
        - Examples {"with furigana" if furigana else ""}
        - {"Include English translation" if translation else "No translation"}
        - Vocabulary list
        - Practice questions

        Format nicely for PDF.
        """

        # 🤖 Call AI
        response = model.generate_content(prompt)

        return {
            "text": response.text,
            "usage": build_usage_response(data)
        }

    except Exception as e:
        # 🔁 Handle rate limit (Gemini 429)
        if "429" in str(e):
            time.sleep(20)
            response = model.generate_content(prompt)

            return {
                "text": response.text,
                "usage": build_usage_response(data)
            }

        raise e

# =========================
# 📄 PDF TRANSLATION (NEW)
# =========================
def translate_pdf_text(text):
    try:
        if not text or len(text.strip()) < 20:
            return "❌ ERROR: No readable text found in PDF"

        prompt = f"""
        Translate the following text into Japanese.

        STRICT RULES:
        - Translate EVERYTHING
        - Do NOT return original English
        - Do NOT explain
        - Only return Japanese text

        TEXT:
        {text}
        """

        response = model.generate_content(prompt)

        result = response.text.strip()

        print("🧠 Gemini Output Preview:", result[:200])

        return result

    except Exception as e:
        print("Gemini Error:", e)
        raise e