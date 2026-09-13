import os
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# جلب بيانات الاتصال من متغيرات البيئة
SUPABASE_URL = os.environ.get("SUPABASE_URL", "")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY", "")

# تهيئة Supabase
supabase: Client = None
if SUPABASE_URL and SUPABASE_KEY:
    try:
        supabase = create_client(SUPABASE_URL, SUPABASE_KEY)
    except Exception as e:
        print(f"Supabase Init Error: {e}")

# 1. مسار اختبار السيرفر
@app.route('/', methods=['GET'])
def index():
    return jsonify({
        "status": "online",
        "message": "Blorix Server is running successfully!",
        "supabase_connected": supabase is not None
    }), 200

# 2. مسار جلب قائمة الألعاب
@app.route('/api/games', methods=['GET'])
def get_games():
    try:
        if not supabase:
            return jsonify({"status": "error", "message": "Supabase not configured"}), 500

        response = supabase.table("games").select("*").execute()
        return jsonify({
            "status": "success",
            "games": response.data
        }), 200
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

# 3. مسار رفع لعبة جديدة
@app.route('/api/upload', methods=['POST'])
def upload_game():
    try:
        if not supabase:
            return jsonify({"status": "error", "message": "Supabase not configured"}), 500

        dev_user = request.form.get('developer_username', '').strip()
        game_title = request.form.get('game_title', '').strip()
        game_desc = request.form.get('game_description', '').strip()

        if not dev_user or not game_title:
            return jsonify({"status": "error", "message": "اسم المطور وعنوان اللعبة مطلوبان"}), 400

        cover_url = ""
        cover_file = request.files.get('cover')

        if cover_file:
            file_bytes = cover_file.read()
            file_path = f"covers/{dev_user}_{game_title}_{cover_file.filename}"
            
            supabase.storage.from_("blorix_storage").upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": cover_file.content_type, "upsert": "true"}
            )
            cover_url = supabase.storage.from_("blorix_storage").get_public_url(file_path)

        game_data = {
            "developer_username": dev_user,
            "game_title": game_title,
            "game_description": game_desc,
            "cover_url": cover_url
        }

        supabase.table("games").insert(game_data).execute()
        return jsonify({
            "status": "success",
            "message": f"تم رفع اللعبة '{game_title}' بنجاح!"
        }), 200

    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
