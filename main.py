from flask import Flask, request, jsonify
from flask_cors import CORS
import google.generativeai as genai

app = Flask(__name__)
CORS(app)

# -------------------------
# CONFIGURE GEMINI API KEY
# -------------------------
genai.configure(api_key="YOUR_API_KEY_HERE")

model = genai.GenerativeModel("gemini-2.0-flash")


# -------------------------
# EMOTION DETECTION
# -------------------------
@app.route("/analyze", methods=["POST"])
def analyze():
    try:
        file = request.files["image"]
        img_bytes = file.read()

        print("IMAGE SIZE:", len(img_bytes))

        image_input = {
            "mime_type": file.mimetype,
            "data": img_bytes
        }

        prompt = (
            "Detect emotion from face. "
            "Return ONLY one word from this list: "
            "happy, sad, angry, fear, disgust, surprise, neutral. "
            "If unsure, return the closest match. No sentences."
        )

        response = model.generate_content([prompt, image_input])
        raw = response.text.lower().strip()
        print("RAW GEMINI OUTPUT →", raw)

        # ---- NORMALIZER ----
        def normalize(raw):
            raw = raw.lower()

            EMOTIONS = {
                "happy": ["happy", "joy", "joyful", "delighted", "smiling"],
                "sad": ["sad", "sadness", "down", "upset"],
                "angry": ["angry", "anger", "mad", "furious", "irritated"],
                "fear": ["fear", "afraid", "scared", "terrified"],
                "disgust": ["disgust", "disgusted", "gross"],
                "surprise": ["surprise", "surprised", "shocked", "astonished"],
                "neutral": ["neutral", "calm", "relaxed", "no strong emotion"]
            }

            # direct matching
            for emo, kws in EMOTIONS.items():
                for k in kws:
                    if k in raw:
                        return emo

            # fallback if Gemini returns things like "emotion: happy"
            for emo in EMOTIONS.keys():
                if emo in raw:
                    return emo

            return "neutral"

        emotion = normalize(raw)

        return jsonify({"emotion": emotion, "raw": raw})

    except Exception as e:
        return jsonify({"error": "Emotion detection failed", "details": str(e)})


# -------------------------
# PHISHING
# -------------------------
@app.route("/phishing", methods=["POST"])
def phishing():
    try:
        text = request.json.get("text", "").lower()

        suspicious_keywords = [
            "atm", "kyc", "blocked", "urgent", "password",
            "verification", "click", "click here", "bank",
            "update", "otp", "account suspended", "hacked",
            "retrieve", "recover", "send otp", "fraud",
            "unauthorized", "reset account"
        ]

        matched = [w for w in suspicious_keywords if w in text]
        score = len(matched)

        if score >= 3:
            risk = "high"
        elif score == 2:
            risk = "medium"
        else:
            risk = "safe"

        return jsonify({
            "risk": risk,
            "score": score,
            "matched_keywords": matched
        })

    except Exception as e:
        return jsonify({"error": "Phishing detection failed", "details": str(e)})


# -------------------------
# SECURITY CHECK
# -------------------------
@app.route("/security", methods=["POST"])
def security():
    try:
        filename = request.files["image"].filename.lower()

        if "known" in filename:
            return jsonify({"status": "known", "message": "Known person"})
        else:
            return jsonify({"status": "unknown", "message": "Unknown detected"})

    except Exception as e:
        return jsonify({"error": "Security failed", "details": str(e)})


@app.route("/test")
def test():
    return {"status": "ok"}


if __name__ == "__main__":
    app.run(port=5000, debug=True)

