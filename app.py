# app.py
import os
from flask import Flask, request, jsonify, g
from flask_cors import CORS
import mysql.connector

app = Flask(__name__)
CORS(app)

def get_db():
    if 'db' not in g:
        db_config = {
            'host': os.environ.get('DB_HOST', 'localhost'),
            'user': os.environ.get('DB_USER', 'root'),
            'password': os.environ.get('DB_PASSWORD', ''),
            'database': os.environ.get('DB_NAME', 'pharmadb'),
            'port': int(os.environ.get('DB_PORT', 3306))
        }
        g.db = mysql.connector.connect(**db_config)
    return g.db

@app.teardown_appcontext
def close_db(exc):
    db = g.pop('db', None)
    if db is not None:
        try:
            db.close()
        except Exception:
            pass

@app.route('/')
def home():
    return "✅ PharmaSafe API (deployed)"

# Search endpoint: requires JSON { "user_id": 1, "medicine": "Paracetamol" }
@app.route('/search', methods=['POST'])
def search_medicine():
    data = request.get_json(force=True)
    user_id = data.get('user_id')
    medicine_name = data.get('medicine')
    if not (user_id and medicine_name):
        return jsonify({'error': 'user_id and medicine required'}), 400

    db = get_db()
    cursor = db.cursor(dictionary=True)

    # Find medicine
    cursor.execute("SELECT * FROM medicines WHERE name = %s LIMIT 1", (medicine_name,))
    med = cursor.fetchone()
    if not med:
        cursor.close()
        return jsonify({"message": "Medicine not found"}), 404

    # Store search history
    cursor.execute(
        "INSERT INTO search_history (user_id, medicine_id) VALUES (%s, %s)",
        (user_id, med['id'])
    )
    db.commit()
    cursor.close()

    return jsonify({
        "user_id": user_id,
        "medicine": med['name'],
        "details": {
            "description": med.get('description'),
            "side_effects": med.get('side_effects')
        }
    })

# Optional: user history
@app.route('/history/<int:user_id>', methods=['GET'])
def get_history(user_id):
    db = get_db()
    cursor = db.cursor(dictionary=True)
    cursor.execute("""
        SELECT sh.id, u.name AS user, m.name AS medicine, m.description, sh.searched_at
        FROM search_history sh
        JOIN users u ON sh.user_id = u.id
        JOIN medicines m ON sh.medicine_id = m.id
        WHERE sh.user_id = %s
        ORDER BY sh.searched_at DESC
    """, (user_id,))
    rows = cursor.fetchall()
    cursor.close()
    return jsonify(rows)

if __name__ == "__main__":
    # For local testing. In Render use gunicorn (Procfile).
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
