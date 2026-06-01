from dotenv import load_dotenv
load_dotenv()

from flask import Flask, request, jsonify
from pipeline.runner import run_pipeline

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json(force=True) or {}
    # JNB may send the full record or just metadata — extract jnid from either shape
    jnid = body.get("jnid") or body.get("id") or (body.get("data") or {}).get("jnid")
    if not jnid:
        return jsonify({"error": "could not find jnid in payload"}), 400
    try:
        result = run_pipeline(jnid)
        return jsonify(result), 200
    except ValueError as e:
        return jsonify({"error": str(e)}), 422
    except Exception as e:
        app.logger.exception("Pipeline error for jnid=%s", jnid)
        return jsonify({"error": str(e)}), 500


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"}), 200


if __name__ == "__main__":
    app.run(port=8000, debug=True)
