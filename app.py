from assemble import create_app

app = create_app()

if __name__ == '__main__':
    print("=" * 50)
    print("✈️  AIRLINE MANAGER - Web App")
    print("=" * 50)
    print("\n🚀 Server startet...")
    print("📱 Öffne im Browser: http://localhost:5000")
    print("🛑 Zum Beenden: Strg+C\n")
    app.run(debug=True, host="0.0.0.0", port=5000)

# from flask_session import Session
# app.config['SESSION_TYPE'] = 'filesystem'  # or redis
# Session(app)