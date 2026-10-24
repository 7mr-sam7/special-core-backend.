
import os
from functools import wraps

from flask import Flask, jsonify, request
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": ["https://7mr-sam7.github.io"]
        }
    }
)

SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_SECRET_KEY = os.environ.get("SUPABASE_SECRET_KEY")
ADMIN_TOKEN = os.environ.get("ADMIN_TOKEN")

if not SUPABASE_URL or not SUPABASE_SECRET_KEY:
    raise RuntimeError("Configure as variáveis do Supabase no Render.")

supabase = create_client(SUPABASE_URL, SUPABASE_SECRET_KEY)


@app.get("/")
def home():
    return jsonify({
        "service": "Special Core Backend",
        "status": "online"
    })


@app.get("/health")
def health():
    try:
        supabase.table("site_settings").select(
            "setting_key"
        ).limit(1).execute()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })

    except Exception:
        app.logger.exception("Erro ao testar o Supabase")
        return jsonify({
            "status": "error",
            "message": "Falha ao acessar o banco"
        }), 500


def admin_required(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        if not ADMIN_TOKEN:
            return jsonify({
                "error": "ADMIN_TOKEN não configurado no servidor"
            }), 503

        token = request.headers.get("X-Admin-Token", "")

        if token != ADMIN_TOKEN:
            return jsonify({
                "error": "Não autorizado"
            }), 401

        return func(*args, **kwargs)

    return wrapper


@app.get("/api/settings")
def get_settings():
    try:
        result = supabase.table("site_settings").select(
            "setting_key,setting_value,updated_at"
        ).execute()

        settings = {
            row["setting_key"]: row["setting_value"]
            for row in result.data
        }

        return jsonify({"settings": settings})

    except Exception:
        app.logger.exception("Erro ao ler configurações")
        return jsonify({
            "error": "Não foi possível ler as configurações"
        }), 500


@app.put("/api/settings/<setting_key>")
@admin_required
def update_setting(setting_key):
    if not setting_key or len(setting_key) > 100:
        return jsonify({"error": "Chave inválida"}), 400

    body = request.get_json(silent=True)

    if not isinstance(body, dict) or "value" not in body:
        return jsonify({
            "error": "Envie um JSON com o campo value"
        }), 400

    try:
        result = supabase.table("site_settings").upsert(
            {
                "setting_key": setting_key,
                "setting_value": body["value"]
            },
            on_conflict="setting_key"
        ).execute()

        return jsonify({
            "status": "ok",
            "saved": result.data
        })

    except Exception:
        app.logger.exception("Erro ao salvar configuração")
        return jsonify({
            "error": "Não foi possível salvar a configuração"
        }), 500


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 10000)))
