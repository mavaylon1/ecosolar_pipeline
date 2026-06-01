from dotenv import load_dotenv
from pathlib import Path
load_dotenv(Path.home() / ".env")

import logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s — %(message)s",
)

from flask import Flask, request, jsonify
from pipeline.runner import run_pipeline

app = Flask(__name__)


@app.route("/webhook", methods=["POST"])
def webhook():
    body = request.get_json(force=True) or {}
    # JNB webhook payload uses field names with spaces and sends primary_id as a plain string.
    # Key field is always "jnid". Fall back to "id" for manually posted payloads.
    jnid = body.get("jnid") or body.get("id")
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
