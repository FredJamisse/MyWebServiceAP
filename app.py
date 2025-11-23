from flask import Flask, jsonify, request, Response, render_template, url_for
from datetime import datetime
from urllib.parse import urljoin
import re

app = Flask(__name__)

APP_NAME = globals().get("APP_NAME", "Multiverse Classifier — Marvel vs DC")

def _registry_payload():
    return {
        "name": APP_NAME,
        "config_url": url_for("config_page", _external=True),
        "json_params_url": url_for("config_params", _external=True),
        # user_url fixed GET demo
        "user_url": url_for("deploy_demo", _external=True),
        "analytics_url": url_for("analytics_get_sample", _external=True),
        "analytics_list_url": url_for("analytics_list", _external=True)
    }

@app.get("/")
def registry_root():
    return jsonify(_registry_payload())

@app.get("/registry")
def registry_page():
    return jsonify(_registry_payload())

@app.get("/health")
def health():
    return jsonify({"status": "ok", "service": APP_NAME})


activity_instances = {}
APP_NAME = "Multiverse Classifier — Marvel vs DC"

def extract_heroes(params: dict):
    bucket = {}
    for k, v in params.items():
        m = re.match(r"heroes\[(\d+)\]\[(name|universe)\]", k)
        if m:
            i = int(m.group(1)); field = m.group(2)
            bucket.setdefault(i, {})[field] = v
    heroes = [bucket[i] for i in sorted(bucket.keys()) if "name" in bucket[i] and "universe" in bucket[i]]
    return heroes

@app.get("/config")
def config_page():
    return render_template("config.html", APP_NAME=APP_NAME)

@app.get("/config/params")
def config_params():
    return jsonify([
        {"name": "title", "type": "text/plain", "required": True, "default": "Multiverse Classifier — Marvel vs DC"},
        {"name": "description", "type": "text/plain", "required": False, "default": "Arrasta os heróis para Marvel ou DC."},
        {"name": "shuffle", "type": "boolean", "required": False, "default": True},
        {"name": "enable_hints", "type": "boolean", "required": False, "default": True},
        {"name": "heroes[i][name]", "type": "text/plain", "required": False, "default": ""},
        {"name": "heroes[i][universe]", "type": "text/plain", "required": False, "default": ""},
        {"name": "activityID", "type": "text/plain", "required": False, "default": "demo-activity"}
    ])@app.post("/user")
def user_url():
    data = request.get_json(silent=True) or {}
    activity_id = data.get("activityID") or "demo-" + datetime.utcnow().strftime("%Y%m%d%H%M%S")
    activity_instances.setdefault(activity_id, {"params": {}, "users": {}})
    abs_url = urljoin(request.host_url, "play/" + activity_id)
    return jsonify({"url": abs_url})

@app.post("/play/<activity_id>")
def play_bootstrap(activity_id):
    payload = request.get_json(silent=True) or {}
    std_id = payload.get("Inven!RAstdID") or "std-" + datetime.utcnow().strftime("%H%M%S")
    json_params = payload.get("json_params") or {}
    inst = activity_instances.setdefault(activity_id, {"params": {}, "users": {}})
    inst["params"] = json_params
    inst["users"].setdefault(std_id, {
        "correct_count": 0, "wrong_count": 0, "attempts": 0, "time_spent": 0,
        "score": 0, "accuracy_percent": 0.0,
        "most_confused_universe": "", "session_summary": ""
    })
    abs_url = urljoin(request.host_url, "play/" + activity_id + "/" + std_id)
    return jsonify({"url": abs_url})

@app.get("/play/<activity_id>/<std_id>")
def play_page(activity_id, std_id):
    inst = activity_instances.get(activity_id, {"params": {}, "users": {}})
    params = inst.get("params", {})

    title = params.get("title", APP_NAME)
    description = params.get("description", "")
    enable_hints_flag = str(params.get("enable_hints", "true")).lower() == "true"

    heroes = extract_heroes(params)
    if not heroes:
        heroes = [
            {"name":"Batman","universe":"DC"},
            {"name":"Wonder Woman","universe":"DC"},
            {"name":"Flash","universe":"DC"},
            {"name":"Superman","universe":"DC"},
            {"name":"Aquaman","universe":"DC"},
            {"name":"Green Lantern","universe":"DC"},
            {"name":"Cyborg","universe":"DC"},
            {"name":"Green Arrow","universe":"DC"},
            {"name":"Iron Man","universe":"Marvel"},
            {"name":"Spider-Man","universe":"Marvel"},
            {"name":"Thor","universe":"Marvel"},
            {"name":"Captain America","universe":"Marvel"},
            {"name":"Black Panther","universe":"Marvel"},
            {"name":"Doctor Strange","universe":"Marvel"},
            {"name":"Hulk","universe":"Marvel"},
            {"name":"Black Widow","universe":"Marvel"}
        ]

    return render_template(
        "play.html",
        APP_NAME=title,
        std_id=std_id,
        activity_id=activity_id,
        description=description,
        enable_hints=enable_hints_flag,
        heroes=heroes
    )

@app.post("/track")
def track():
    data = request.get_json(silent=True) or {}
    activity_id = data.get("activityID")
    std_id = data.get("inveniraStdID")
    metrics = data.get("metrics", {})
    qual = data.get("qual", {})
    if activity_id and std_id:
        inst = activity_instances.setdefault(activity_id, {"params": {}, "users": {}})
        cc = int(metrics.get("correct_count", 0) or 0)
        wc = int(metrics.get("wrong_count", 0) or 0)
        at = int(metrics.get("attempts", 0) or 0)
        ts = int(metrics.get("time_spent", 0) or 0)
        score = max(cc - wc, 0)
        accuracy = (cc / (cc + wc) * 100.0) if (cc + wc) > 0 else 0.0
        inst["users"][std_id] = {
            "correct_count": cc,
            "wrong_count": wc,
            "attempts": at,
            "time_spent": ts,
            "score": score,
            "accuracy_percent": round(accuracy, 2),
            "most_confused_universe": str(qual.get("most_confused_universe", "")),
            "session_summary": (qual.get("session_summary", "") or "").strip()[:500]
        }
    return ("", 204)

@app.get("/analytics/list")
def analytics_list():
    return jsonify({
        "qualAnalytics": [
            {"name": "most_confused_universe", "type": "text/plain"},
            {"name": "session_summary", "type": "text/plain"}
        ],
        "quantAnalytics": [
            {"name": "correct_count", "type": "integer"},
            {"name": "wrong_count", "type": "integer"},
            {"name": "attempts", "type": "integer"},
            {"name": "time_spent", "type": "integer"},
            {"name": "score", "type": "integer"},
            {"name": "accuracy_percent", "type": "number"}
        ]
    })

@app.get("/analytics")
def analytics_get_sample():
    from datetime import datetime
    sample = {
        "activity_id": "demo",
        "user_id": "demo-std",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "metrics": {
            "correct_count": 8,
            "wrong_count": 2,
            "attempts": 3,
            "time_spent": 240,
            "score": 6,
            "accuracy_percent": 80.0,
            "most_confused_universe": "Marvel",
            "session_summary": "Classificação concluída com bom desempenho."
        }
    }
    return jsonify(sample)

@app.post("/analytics")
def analytics():
    data = request.get_json(silent=True) or {}
    activity_id = data.get("activityID")
    inst = activity_instances.get(activity_id, {"users": {}})
    results = []
    for std_id, m in inst.get("users", {}).items():
        results.append({
            "inveniraStdID": std_id,
            "quantAnalytics": [
                {"name": "correct_count", "type": "integer", "value": int(m.get("correct_count", 0))},
                {"name": "wrong_count", "type": "integer", "value": int(m.get("wrong_count", 0))},
                {"name": "attempts", "type": "integer", "value": int(m.get("attempts", 0))},
                {"name": "time_spent", "type": "integer", "value": int(m.get("time_spent", 0))},
                {"name": "score", "type": "integer", "value": int(m.get("score", 0))},
                {"name": "accuracy_percent", "type": "number", "value": float(m.get("accuracy_percent", 0.0))}
            ],
            "qualAnalytics": [
                {"name": "most_confused_universe", "type": "text/plain", "value": str(m.get("most_confused_universe", ""))},
                {"name": "session_summary", "type": "text/plain", "value": str(m.get("session_summary", ""))}
            ]
        })
    return jsonify(results)

@app.get("/scoreboard")
def scoreboard():
    activity_id = request.args.get("activityID")
    inst = activity_instances.get(activity_id, {"users": {}})
    rows = []
    for std_id, m in inst.get("users", {}).items():
        rows.append({
            "stdId": std_id,
            "score": int(m.get("score", 0)),
            "accuracy_percent": float(m.get("accuracy_percent", 0.0)),
            "attempts": int(m.get("attempts", 0)),
            "time_spent": int(m.get("time_spent", 0))
        })
    rows.sort(key=lambda r: (-r["score"], -r["accuracy_percent"], r["time_spent"]))
    return jsonify({"activityID": activity_id, "top": rows[:5], "total": len(rows)})

@app.get("/README")
def readme():
    return Response("Endpoints: GET /config, GET /config/params, POST /user, POST /play/<activityID>, GET /play/<activityID>/<stdID>, GET /analytics/list, POST /analytics, GET /scoreboard", mimetype="text/plain; charset=utf-8")

@app.get("/deploy")
def deploy_demo():
    # Minimal demo to satisfy user_url as a fixed GET
    activity_id = "demo"
    std_id = "demo-std"
    title = APP_NAME
    description = "Arrasta os heróis para Marvel ou DC."
    enable_hints_flag = False
    heroes = [
        {"name":"Batman","universe":"DC"},
        {"name":"Superman","universe":"DC"},
        {"name":"Wonder Woman","universe":"DC"},
        {"name":"Flash","universe":"DC"},
        {"name":"Aquaman","universe":"DC"},
        {"name":"Iron Man","universe":"Marvel"},
        {"name":"Captain America","universe":"Marvel"},
        {"name":"Thor","universe":"Marvel"},
        {"name":"Hulk","universe":"Marvel"},
        {"name":"Black Widow","universe":"Marvel"}
    ]
    # Reuse existing play.html template
    return render_template(
        "play.html",
        APP_NAME=title,
        std_id=std_id,
        activity_id=activity_id,
        description=description,
        enable_hints=enable_hints_flag,
        heroes=heroes
    )

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000, debug=True)
