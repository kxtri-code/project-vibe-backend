from flask import Flask, jsonify, request, send_from_directory
from werkzeug.utils import secure_filename
from google import genai
from google.genai import types
import PIL.Image
import json
import os
import time

# --- CONFIGURATION ---
UPLOAD_FOLDER = 'uploads'
DB_FILE = 'events_db.json'
ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg'}
API_KEY = "AIzaSyBFtqVzgYZQBB7FAPSCVVPv6-ZIfs71Ogs"  # <--- PASTE YOUR KEY HERE!

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

# --- NEW: Serve Images to the Phone ---
@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

def process_image_with_ai(image_path):
    try:
        client = genai.Client(api_key=API_KEY)
        img = PIL.Image.open(image_path)
        
        prompt = """
        Extract event details into a JSON object.
        RULES: 1. If year missing, USE "2026". 2. Format date YYYY-MM-DD.
        {
            "event_name": "Name", "venue": "Location",
            "date": "YYYY-MM-DD", "time": "Time",
            "vibe": ["Tag1", "Tag2", "Tag3"]
        }
        """
        response = client.models.generate_content(
            model="gemini-flash-latest", 
            contents=[img, prompt],
            config=types.GenerateContentConfig(response_mime_type="application/json")
        )
        return json.loads(response.text)
    except Exception as e:
        print(f"AI Error: {e}")
        return None

@app.route('/api/events', methods=['GET'])
def get_events():
    if os.path.exists(DB_FILE):
        with open(DB_FILE, "r") as f: return jsonify(json.load(f))
    return jsonify([])

@app.route('/api/scan', methods=['POST'])
def scan_flyer():
    if 'photo' not in request.files: return jsonify({"error": "No photo"}), 400
    file = request.files['photo']
    
    if file and allowed_file(file.filename):
        # 1. Save File with unique name to prevent overwrites
        filename = f"{int(time.time())}_{secure_filename(file.filename)}"
        filepath = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(filepath)
        
        # 2. Analyze
        event_data = process_image_with_ai(filepath)
        
        if event_data:
            # 3. Add Image Link to Data
            event_data['image_url'] = f"/uploads/{filename}"
            
            # 4. Save to DB
            db_data = []
            if os.path.exists(DB_FILE):
                with open(DB_FILE, "r") as f: db_data = json.load(f)
            db_data.insert(0, event_data)
            with open(DB_FILE, "w") as f: json.dump(db_data, f, indent=4)
                
            return jsonify(event_data)
            
    return jsonify({"error": "Failed"}), 500

if __name__ == '__main__':
    app.run(debug=True, port=5000)