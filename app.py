import os
from flask import Flask, request, jsonify
from supabase import create_client, Client

app = Flask(__name__)

# جلب بيانات الاتصال من متغيرات البيئة الآمنة في Render
SUPABASE_URL = os.environ.get("SUPABASE_URL")
SUPABASE_KEY = os.environ.get("SUPABASE_KEY")

# تهيئة اتصال Supabase
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

@app.route('/api/upload', methods=['POST'])
def upload_game():
    try:
        # 1. استقبال البيانات النصية من إضافة غودوت
        dev_user = request.form.get('developer_username', '').strip()
        game_title = request.form.get('game_title', '').strip()
        game_desc = request.form.get('game_description', '').strip()
        
        if not dev_user or not game_title:
            return jsonify({"status": "error", "message": "اسم المطور وعنوان اللعبة مطلوبان ⚡"}), 400
            
        cover_url = ""
        
        # 2. معالجة وتخزين صورة الغلاف في Supabase Storage
        cover_file = request.files.get('cover')
        if cover_file:
            file_bytes = cover_file.read()
            # إنشاء مسار فريد للملف داخل التخزين السحابي
            file_path = f"covers/{dev_user}_{game_title}_{cover_file.filename}"
            
            # رفع الملف إلى الحاوية (Bucket) المخصصة في Supabase واسمها blorix_storage
            supabase.storage.from_("blorix_storage").upload(
                path=file_path,
                file=file_bytes,
                file_options={"content-type": cover_file.content_type, "upsert": "true"}
            )
            
            # الحصول على الرابط العام والجاهز للصورة
            cover_url = supabase.storage.from_("blorix_storage").get_public_url(file_path)
            
        # 3. حفظ تفاصيل اللعبة داخل جدول قاعدة البيانات (games) في Supabase
        game_data = {
            "developer_username": dev_user,
            "game_title": game_title,
            "game_description": game_desc,
            "cover_url": cover_url
        }
        
        supabase.table("games").insert(game_data).execute()
        
        print(f"تم نشر اللعبة بنجاح: {game_title} للمطور {dev_user} ⚡")
        return jsonify({
            "status": "success",
            "message": "تم نشر اللعبة ورفع الملفات إلى السحاب بنجاح ⚡"
        }), 200
        
    except Exception as e:
        print(f"خطأ أثناء الرفع: {str(e)}")
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
