from app import create_app

app = create_app()

if __name__ == "__main__":
    # For local dev only. Render will use gunicorn later.
    app.run(host="0.0.0.0", port=5001, debug=True)
