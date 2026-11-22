import os
from flask import Flask, render_template, send_from_directory
from routes.api import api_bp
from config import APP_NAME

def create_app():
    app = Flask(
        __name__,
        static_folder="static",
        template_folder="templates"
    )

    # Konfigurasi aplikasi
    app.config["APP_NAME"] = APP_NAME
    app.config["JSON_SORT_KEYS"] = False
    app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 0
    app.config["TEMPLATES_AUTO_RELOAD"] = True

    # Registrasi Blueprint API
    app.register_blueprint(api_bp)

    @app.after_request
    def add_header(response):
        """Mencegah browser caching file static saat pengembangan/pengujian."""
        response.headers["Cache-Control"] = "no-store, no-cache, must-revalidate, max-age=0"
        response.headers["Pragma"] = "no-cache"
        response.headers["Expires"] = "0"
        return response

    @app.route("/")
    def index():
        return render_template("index.html", app_name=APP_NAME)

    @app.errorhandler(404)
    def not_found(e):
        return {"error": "Endpoint tidak ditemukan."}, 404

    @app.errorhandler(500)
    def server_error(e):
        return {"error": "Terjadi kesalahan internal server.", "detail": str(e)}, 500

    return app

app = create_app()

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"Memulai {APP_NAME} di http://127.0.0.1:{port}")
    app.run(host="127.0.0.1", port=port, debug=True)
