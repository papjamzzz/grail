from flask import Flask, request, jsonify, send_from_directory, redirect, make_response
import json, os, time, requests as req, base64, re, urllib.parse, secrets
# routes: / /cells /bodyfigure /console /whoop/*

# Load .env for local dev
_env_path = os.path.join(os.path.dirname(__file__), '.env')
if os.path.exists(_env_path):
    for _line in open(_env_path):
        _line = _line.strip()
        if _line and not _line.startswith('#') and '=' in _line:
            _k, _v = _line.split('=', 1)
            if not os.environ.get(_k.strip()):
                os.environ[_k.strip()] = _v.strip()

app = Flask(__name__)

BASE = os.path.dirname(__file__)
HEALTH_FILE  = os.path.join(BASE, 'health_data.json')
SYMPTOM_FILE = os.path.join(BASE, 'symptoms.json')
MEAL_FILE    = os.path.join(BASE, 'meals.json')

FI_URL = 'http://127.0.0.1:5562/ask'

WHOOP_TOKEN_FILE  = os.path.join(os.path.dirname(__file__), 'whoop_token.json')
WHOOP_AUTH_URL    = 'https://api.prod.whoop.com/oauth/oauth2/auth'
WHOOP_TOKEN_URL   = 'https://api.prod.whoop.com/oauth/oauth2/token'
WHOOP_BASE        = 'https://api.prod.whoop.com/developer/v1'
WHOOP_SCOPES      = 'read:recovery read:sleep read:workout read:body_measurement offline'
WHOOP_REDIRECT    = os.environ.get('WHOOP_REDIRECT_URI', 'http://127.0.0.1:5566/whoop/callback')

DEFAULT_HEALTH = {
    # Heart & circulation (Watch auto)
    "heart_rate": None, "resting_hr": None, "walking_hr": None,
    "hrv": None, "spo2": None, "respiratory_rate": None,
    # Body temp (Watch auto)
    "temperature": None,
    # Activity (Watch auto)
    "daily_steps": None, "walk_run_km": None, "flights_climbed": None,
    "active_calories": None, "resting_calories": None,
    "exercise_minutes": None, "stand_minutes": None,
    # Fitness (Watch auto)
    "vo2_max": None, "cardio_recovery": None, "walking_speed": None,
    # Wellness (Watch auto)
    "daylight_minutes": None, "mindful_minutes": None,
    # Sleep (Watch auto)
    "sleep_hours": None, "deep_sleep_min": None, "rem_sleep_min": None,
    # Body metrics (manual)
    "weight": None, "body_fat": None, "lean_mass": None,
    "systolic_bp": None, "diastolic_bp": None, "waist_cm": None,
    # Labs (manual)
    "glucose": None, "testosterone": None, "crp": None,
    "vitamin_d": None, "ferritin": None, "cortisol": None,
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

# ------- domain → page routing -------

DOMAIN_MAP = {
    'grailcells.creativekonsoles.com': 'cells.html',
    'grailbody.creativekonsoles.com':  'body.html',
    'ailiv.health':                    'ailiv-landing.html',
    'www.ailiv.health':                'ailiv-landing.html',
}

# ------- routes -------

@app.route('/debug-host')
def debug_host():
    return jsonify({'host': request.host, 'headers': dict(request.headers)})

@app.route('/')
def index():
    host = request.host.split(':')[0].lower()
    filename = DOMAIN_MAP.get(host, 'index.html')
    # fallback: if host contains 'ailiv', serve landing
    if filename == 'index.html' and 'ailiv' in host:
        filename = 'ailiv-landing.html'
    return send_from_directory(BASE, filename)

@app.route('/ailiv')
def ailiv_landing():
    return send_from_directory(BASE, 'ailiv-landing.html')

@app.route('/cells')
def cells():
    return send_from_directory(BASE, 'cells.html')

@app.route('/biobaseline')
def biobaseline():
    return send_from_directory(BASE, 'biobaseline-chart.html')

@app.route('/rootcause')
def rootcause():
    resp = make_response(send_from_directory(BASE, 'rootcause-network.html'))
    resp.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    resp.headers['Pragma'] = 'no-cache'
    resp.headers['Expires'] = '0'
    return resp

@app.route('/bodyfigure')
def bodyfigure():
    path = os.path.join(BASE, 'bodyfigure.html')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/console')
def console():
    path = os.path.join(BASE, 'console.html')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/biodata')
def biodata():
    path = os.path.join(BASE, 'biodata.html')
    with open(path, 'r', encoding='utf-8') as f:
        return f.read(), 200, {'Content-Type': 'text/html; charset=utf-8'}

@app.route('/api/ask', methods=['POST'])
def api_ask():
    try:
        import anthropic as ant
    except ImportError:
        return jsonify({'ok': False, 'error': 'anthropic not installed'}), 500
    api_key = os.environ.get('ANTHROPIC_API_KEY', '').strip()
    if not api_key:
        return jsonify({'ok': False, 'error': 'ANTHROPIC_API_KEY not set'}), 400
    body = request.get_json(force=True, silent=True) or {}
    question = str(body.get('question', ''))[:600]
    health = rjson(HEALTH_FILE, DEFAULT_HEALTH.copy())
    vitals = {k: v for k, v in health.items() if v is not None}
    system = f"""You are AILIV, a precision biohacking AI. Help users understand their biomarkers and optimize longevity.
Current biomarker data: {json.dumps(vitals)}
Be concise and specific. Reference the user's actual data when relevant. 2-3 short paragraphs max. No bullet lists."""
    client = ant.Anthropic(api_key=api_key)
    msg = client.messages.create(
        model='claude-haiku-4-5-20251001',
        max_tokens=512,
        system=system,
        messages=[{'role': 'user', 'content': question}]
    )
    return jsonify({'ok': True, 'answer': msg.content[0].text})

@app.route('/debug-files')
def debug_files():
    files = os.listdir(BASE)
    return jsonify({'base': BASE, 'files': sorted(files)})

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
    print(f"[AILIV] Ingest: {body}")
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

# AILIV Guide — full synthesis via 5i
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

    prompt = f"""You are a precision health advisor reviewing a biohacker's complete profile. Current AILIV Guide Score: {score}/100.

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

Based on this complete profile, provide a precise 7-day dietary and lifestyle protocol to improve the AILIV Guide Score. Be specific — name foods, timing, quantities where relevant. Identify the 2-3 highest-leverage interventions."""

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

# -------- WHOOP helpers --------

def whoop_token():
    if os.path.exists(WHOOP_TOKEN_FILE):
        with open(WHOOP_TOKEN_FILE) as f:
            return json.load(f)
    return None

def whoop_save_token(data):
    data['saved_at'] = time.time()
    with open(WHOOP_TOKEN_FILE, 'w') as f:
        json.dump(data, f, indent=2)

def whoop_refresh(token):
    client_id     = os.environ.get('WHOOP_CLIENT_ID', '')
    client_secret = os.environ.get('WHOOP_CLIENT_SECRET', '')
    r = req.post(WHOOP_TOKEN_URL, data={
        'grant_type':    'refresh_token',
        'refresh_token': token['refresh_token'],
        'client_id':     client_id,
        'client_secret': client_secret,
    }, timeout=15)
    r.raise_for_status()
    new_token = r.json()
    if 'refresh_token' not in new_token:
        new_token['refresh_token'] = token['refresh_token']
    whoop_save_token(new_token)
    return new_token

def whoop_get(path, token):
    headers = {'Authorization': f"Bearer {token['access_token']}"}
    r = req.get(f"{WHOOP_BASE}{path}", headers=headers, timeout=15)
    if r.status_code == 401:
        token = whoop_refresh(token)
        headers = {'Authorization': f"Bearer {token['access_token']}"}
        r = req.get(f"{WHOOP_BASE}{path}", headers=headers, timeout=15)
    r.raise_for_status()
    return r.json(), token

# -------- WHOOP routes --------

@app.route('/whoop/connect')
def whoop_connect():
    client_id = os.environ.get('WHOOP_CLIENT_ID', '')
    if not client_id:
        return 'WHOOP_CLIENT_ID not set in .env', 400
    state = secrets.token_urlsafe(16)
    params = urllib.parse.urlencode({
        'client_id':     client_id,
        'redirect_uri':  WHOOP_REDIRECT,
        'response_type': 'code',
        'scope':         WHOOP_SCOPES,
        'state':         state,
    })
    return redirect(f"{WHOOP_AUTH_URL}?{params}")

@app.route('/whoop/callback')
def whoop_callback():
    code  = request.args.get('code')
    error = request.args.get('error')
    if error or not code:
        return redirect('/?whoop=error')
    client_id     = os.environ.get('WHOOP_CLIENT_ID', '')
    client_secret = os.environ.get('WHOOP_CLIENT_SECRET', '')
    r = req.post(WHOOP_TOKEN_URL, data={
        'grant_type':    'authorization_code',
        'code':          code,
        'redirect_uri':  WHOOP_REDIRECT,
        'client_id':     client_id,
        'client_secret': client_secret,
    }, timeout=15)
    if not r.ok:
        print(f'[WHOOP] Token exchange failed: {r.text}')
        return redirect('/?whoop=error')
    whoop_save_token(r.json())
    return redirect('/?whoop=connected')

@app.route('/whoop/status')
def whoop_status():
    token = whoop_token()
    if not token:
        return jsonify({'connected': False})
    return jsonify({
        'connected':    True,
        'last_sync':    token.get('last_sync'),
        'saved_at':     token.get('saved_at'),
    })

@app.route('/whoop/sync', methods=['POST'])
def whoop_sync():
    token = whoop_token()
    if not token:
        return jsonify({'ok': False, 'error': 'Not connected'}), 401

    synced = {}
    errors = []

    try:
        resp, token = whoop_get('/recovery?limit=1', token)
        records = resp.get('records', [])
        if records:
            score = records[0].get('score', {})
            if score.get('recovery_score') is not None:
                synced['recovery_score'] = score['recovery_score']
            if score.get('resting_heart_rate') is not None:
                synced['resting_hr'] = score['resting_heart_rate']
            if score.get('hrv_rmssd_milli') is not None:
                synced['hrv'] = score['hrv_rmssd_milli']
            if score.get('respiratory_rate') is not None:
                synced['respiratory_rate'] = score['respiratory_rate']
            if score.get('spo2_percentage') is not None:
                synced['spo2'] = score['spo2_percentage']
            if score.get('skin_temp_celsius') is not None:
                synced['temperature'] = round(score['skin_temp_celsius'] * 9/5 + 32, 1)
    except Exception as e:
        errors.append(f'recovery: {e}')

    try:
        resp, token = whoop_get('/activity/sleep?limit=1', token)
        records = resp.get('records', [])
        if records:
            score = records[0].get('score', {})
            summary = score.get('stage_summary', {})
            total_ms = (
                summary.get('total_slow_wave_sleep_time_milli', 0) +
                summary.get('total_rem_sleep_time_milli', 0) +
                summary.get('total_light_sleep_time_milli', 0)
            )
            if total_ms:
                synced['sleep_hours'] = round(total_ms / 3600000, 2)
            if score.get('respiratory_rate') is not None and 'respiratory_rate' not in synced:
                synced['respiratory_rate'] = score['respiratory_rate']
    except Exception as e:
        errors.append(f'sleep: {e}')

    try:
        resp, token = whoop_get('/cycle?limit=1', token)
        records = resp.get('records', [])
        if records:
            score = records[0].get('score', {})
            if score.get('strain') is not None:
                synced['whoop_strain'] = round(score['strain'], 2)
    except Exception as e:
        errors.append(f'cycle: {e}')

    data = rjson(HEALTH_FILE, DEFAULT_HEALTH.copy())
    for k, v in synced.items():
        if k != 'whoop_strain':
            data[k] = v
    data['whoop_strain']  = synced.get('whoop_strain')
    data['whoop_recovery'] = synced.get('recovery_score')
    data['last_updated']  = time.strftime('%Y-%m-%dT%H:%M:%S')
    wjson(HEALTH_FILE, data)

    token['last_sync'] = time.strftime('%Y-%m-%dT%H:%M:%S')
    whoop_save_token(token)

    return jsonify({'ok': True, 'synced': synced, 'errors': errors})

@app.route('/whoop/disconnect', methods=['POST'])
def whoop_disconnect():
    if os.path.exists(WHOOP_TOKEN_FILE):
        os.remove(WHOOP_TOKEN_FILE)
    return jsonify({'ok': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5566))
    app.run(host='0.0.0.0', port=port, debug=False)
