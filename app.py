
import os
from flask import Flask, jsonify
from flask_cors import CORS
from supabase import create_client

app = Flask(__name__)

CORS(
    app,
    resources={
        r"/*": {
            "origins": [
                "https://7mr-sam7.github.io"
            ]
        }
    }
)

supabase = None

try:
    url = os.environ["SUPABASE_URL"]
    key = os.environ["SUPABASE_SECRET_KEY"]
    supabase = create_client(url, key)
except Exception as error:
    print("Erro ao configurar Supabase:", error)


@app.route("/")
def home():
    return jsonify({
        "status": "online",
        "projeto": "Special Core Backend"
    })


@app.route("/health")
def health():
    if supabase is None:
        return jsonify({
            "status": "error",
            "mensagem": "Supabase nao configurado"
        }), 500

    try:
        supabase.table("site_settings").select(
            "id"
        ).limit(1).execute()

        return jsonify({
            "status": "ok",
            "database": "connected"
        })

    except Exception:
        app.logger.exception("Falha ao consultar Supabase")
        return jsonify({
            "status": "error",
            "mensagem": "Falha ao acessar o banco"
        }), 500


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
