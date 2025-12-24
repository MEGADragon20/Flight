from routes import app


if __name__ == '__main__':
    print("=" * 50)
    print("✈️  AIRLINE MANAGER - Web App")
    print("=" * 50)
    print("\n🚀 Server startet...")
    print("📱 Öffne im Browser: http://localhost:5000")
    print("🛑 Zum Beenden: Strg+C\n")
    app.run(debug=True)