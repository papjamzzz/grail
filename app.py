from flask import Flask, request, jsonify, send_from_directory
import json, os, time, requests as req

app = Flask(__name__)

BASE = os.path.dirname(__file__)
HEALTH_FILE  = os.path.join(BASE, 'health_data.json')
SYMPTOM_FILE = os.path.join(BASE, 'symptoms.json')
MEAL_FILE    = os.path.join(BASE, 'meals.json')

FI_URL = 'http://127.0.0.1:5562/ask'

DEFAULT_HEALTH = {
    "heart_rate": None, "hrv": None, "spo2": None,
    "sleep_hours": None, "respiratory_rate": None,
    "vo2_max": None, "resting_hr": None, "temperature": None,
    "glucose": None, "testosterone": None, "crp": None,
    "last_updated": None
}

# ------- helpers -------

def rjson(path, default):
    if os.path.exists(path):
        with open(path) as f:
            return json.load(f)
    return default() if callable(default) else default

def wjson(path, data):
    with open(path, 'w') as f:
        json.dump(data, f, indent=2)

# ------- routes -------

@app.route('/')
def index():
    return send_from_directory('.', 'index.html')

# Health ingest from Shortcuts / Health export parser
@app.route('/ingest', methods=['POST'])
def ingest():
    body = request.get_json(force=True, silent=True) or {}
    data = rjson(HEALTH_FILE, DEFAULT_HEALTH.copy())
    fields = list(DEFAULT_HEALTH.keys())
    fields.remove('last_updated')
    for f in fields:
        if f in body and body[f] is not None:
            try:
                data[f] = float(body[f])
            except (ValueError, TypeError):
                pass
    data['last_updated'] = time.strftime('%H:%M')
    wjson(HEALTH_FILE, data)
    print(f"[Grail] Ingest: {body}")
    return jsonify({"ok": True, "data": data})

@app.route('/api/data')
def api_data():
    return jsonify(rjson(HEALTH_FILE, DEFAULT_HEALTH.copy()))

# Symptom log
@app.route('/log/symptom', methods=['POST'])
def log_symptom():
    body = request.get_json(force=True, silent=True) or {}
    symptoms = rjson(SYMPTOM_FILE, [])
    entry = {
        "text": str(body.get("text", ""))[:200],
        "severity": int(body.get("severity", 3)),
        "ts": time.strftime('%Y-%m-%d %H:%M')
    }
    symptoms.insert(0, entry)
    symptoms = symptoms[:50]
    wjson(SYMPTOM_FILE, symptoms)
    return jsonify({"ok": True, "entry": entry})

@app.route('/api/symptoms')
def api_symptoms():
    return jsonify(rjson(SYMPTOM_FILE, []))

# Meal log
@app.route('/log/meal', methods=['POST'])
def log_meal():
    body = request.get_json(force=True, silent=True) or {}
    meals = rjson(MEAL_FILE, [])
    entry = {
        "description": str(body.get("description", ""))[:300],
        "meal_type": str(body.get("meal_type", "meal")),
        "ts": time.strftime('%Y-%m-%d %H:%M')
    }
    meals.insert(0, entry)
    meals = meals[:100]
    wjson(MEAL_FILE, meals)
    return jsonify({"ok": True, "entry": entry})

@app.route('/api/meals')
def api_meals():
    return jsonify(rjson(MEAL_FILE, []))

# Grail Guide — full synthesis via 5i
@app.route('/api/grail-guide', methods=['POST'])
def grail_guide():
    health   = rjson(HEALTH_FILE, DEFAULT_HEALTH.copy())
    symptoms = rjson(SYMPTOM_FILE, [])[:10]
    meals    = rjson(MEAL_FILE, [])[:14]
    body     = request.get_json(force=True, silent=True) or {}
    score    = body.get("score", "unknown")

    symptom_lines = "\n".join([f"- {s['ts']}: {s['text']} (severity {s['severity']}/5)" for s in symptoms]) or "None logged"
    meal_lines    = "\n".join([f"- {m['ts']} [{m['meal_type']}]: {m['description']}" for m in meals]) or "None logged"

    def fmt(v, unit="", dec=0):
        if v is None: return "not recorded"
        return f"{round(v, dec) if dec else int(round(v))}{unit}"

    prompt = f"""You are a precision health advisor reviewing a biohacker's complete profile. Current Grail Guide Score: {score}/100.

BIOMETRICS:
- Resting Heart Rate: {fmt(health['resting_hr'], ' bpm')}
- Current Heart Rate: {fmt(health['heart_rate'], ' bpm')}
- HRV (RMSSD): {fmt(health['hrv'], ' ms')}
- Blood Oxygen: {fmt(health['spo2'], '%')}
- Sleep: {fmt(health['sleep_hours'], ' hours', 1)}
- Respiratory Rate: {fmt(health['respiratory_rate'], ' breaths/min', 1)}
- VO2 Max: {fmt(health['vo2_max'], ' ml/kg/min', 1)}
- Wrist Temperature: {fmt(health['temperature'], '°F', 1)}
- Fasting Glucose: {fmt(health['glucose'], ' mg/dL')}
- Testosterone: {fmt(health['testosterone'], ' ng/dL')}
- CRP (Inflammation): {fmt(health['crp'], ' mg/L', 1)}

RECENT SYMPTOMS:
{symptom_lines}

MEAL LOG (last 14 entries):
{meal_lines}

Based on this complete profile, provide a precise 7-day dietary and lifestyle protocol to improve the Grail Guide Score. Be specific — name foods, timing, quantities where relevant. Identify the 2-3 highest-leverage interventions."""

    try:
        resp = req.post(FI_URL, json={
            "prompt": prompt,
            "verdict": True,
            "models": ["claude", "gpt", "gemini"]
        }, timeout=60)
        result = resp.json()
        return jsonify({
            "ok": True,
            "verdict": result.get("verdict", ""),
            "results": result.get("results", {}),
            "elapsed": result.get("elapsed", 0)
        })
    except Exception as e:
        return jsonify({"ok": False, "error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5566, debug=True)
