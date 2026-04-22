from flask import Flask, request, jsonify, send_from_directory
import json, os, time, requests as req, base64, re

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

@app.route('/cells')
def cells():
    return send_from_directory('.', 'cells.html')

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

LAB_DEFAULTS_GREEN = {
    'testosterone': 600,  'cortisol': 12,    'dhea': 300,   'igf1': 200,
    'tsh': 1.5,           'glucose': 88,     'insulin': 1.0,'uric_acid': 4.5,
    'crp': 0.4,           'homocysteine': 8, 'apob': 70,    'fibrinogen': 240,
    'vitamin_d': 55,      'b12': 700,        'magnesium': 2.2,'zinc': 90,
    'omega3': 8.5,        'nad': 45,         'ferritin': 100,'albumin': 4.5,
    'alt': 18,
}

EXTRACT_PROMPT = """Extract all lab values from this medical lab report. Return ONLY a raw JSON object — no markdown, no explanation, no units.
Use these exact keys where the value is present: testosterone, cortisol, dhea, igf1, tsh, glucose, insulin, uric_acid, crp, homocysteine, apob, fibrinogen, vitamin_d, b12, magnesium, zinc, omega3, nad, ferritin, albumin, alt.
Also extract any other clearly readable lab values using lowercase_underscore keys.
Values must be numbers only. Example: {"testosterone": 542, "vitamin_d": 48, "tsh": 1.8, "crp": 0.6}
Only include values you can clearly read from the image."""

LAB_FIELDS = [
    'testosterone','cortisol','dhea','igf1','tsh',
    'glucose','insulin','uric_acid',
    'crp','homocysteine','apob','fibrinogen',
    'vitamin_d','b12','magnesium','zinc','omega3','nad',
    'ferritin','albumin','alt'
]

@app.route('/api/import-labs', methods=['POST'])
def import_labs():
    try:
        import anthropic as ant
    except ImportError:
        return jsonify({'ok': False, 'error': 'anthropic library not installed'}), 500

    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return jsonify({'ok': False, 'error': 'ANTHROPIC_API_KEY environment variable not set'}), 400

    files = request.files.getlist('files')
    if not files:
        return jsonify({'ok': False, 'error': 'No files uploaded'}), 400

    client = ant.Anthropic(api_key=api_key)
    extracted = {}

    for f in files:
        raw = f.read()
        if not raw:
            continue
        mime = f.content_type or 'image/jpeg'
        if mime not in ('image/jpeg','image/png','image/gif','image/webp'):
            mime = 'image/jpeg'
        b64 = base64.standard_b64encode(raw).decode('utf-8')

        try:
            msg = client.messages.create(
                model='claude-sonnet-4-6',
                max_tokens=1024,
                messages=[{
                    'role': 'user',
                    'content': [
                        {'type': 'image', 'source': {'type': 'base64', 'media_type': mime, 'data': b64}},
                        {'type': 'text', 'text': EXTRACT_PROMPT}
                    ]
                }]
            )
            text = msg.content[0].text.strip()
            m = re.search(r'\{[\s\S]*\}', text)
            if m:
                parsed = json.loads(m.group())
                for k, v in parsed.items():
                    try:
                        extracted[k.lower().replace(' ','_')] = float(v)
                    except Exception:
                        pass
        except Exception as e:
            print(f'[import-labs] Claude error: {e}')

    data = rjson(HEALTH_FILE, DEFAULT_HEALTH.copy())
    found = []
    for k, v in extracted.items():
        data[k] = v
        found.append(k)

    defaulted = []
    for field, val in LAB_DEFAULTS_GREEN.items():
        if data.get(field) is None:
            data[field] = val
            defaulted.append(field)

    data['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    wjson(HEALTH_FILE, data)
    return jsonify({'ok': True, 'found': found, 'defaulted': defaulted, 'data': data})

@app.route('/api/labs', methods=['POST'])
def api_labs():
    body = request.get_json(force=True, silent=True) or {}
    data = rjson(HEALTH_FILE, DEFAULT_HEALTH.copy())
    for f in LAB_FIELDS:
        if f in body and body[f] is not None:
            try:
                data[f] = float(body[f])
            except (ValueError, TypeError):
                pass
    data['last_updated'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    wjson(HEALTH_FILE, data)
    return jsonify(data)

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
