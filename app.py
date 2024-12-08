from flask import Flask, render_template, jsonify, request, send_file
from PIL import Image, ImageDraw, ImageFont
import random
import string
import os
import requests
from io import BytesIO
import nest_asyncio

# --- Setup untuk Jupyter Notebook ---
nest_asyncio.apply()

# --- SETUP FONT ---
FONT_URL = "https://github.com/dolbydu/font/raw/master/Sans/Arial/Arial.ttf"
FONT_PATH = "Arial.ttf"

# Unduh font jika belum ada
def download_font():
    if not os.path.exists(FONT_PATH):
        print("Mengunduh font Arial dari URL...")
        response = requests.get(FONT_URL)
        if response.status_code == 200:
            with open(FONT_PATH, "wb") as f:
                f.write(response.content)
            print("Font Arial berhasil diunduh!")
        else:
            raise Exception(f"Gagal mengunduh font. Status code: {response.status_code}")

# Pastikan font tersedia
download_font()

# --- SETUP FLASK ---
app = Flask(__name__)

# Variabel global untuk menyimpan teks CAPTCHA
current_captcha_text = ""

# --- FUNGSI UNTUK MEMBUAT CAPTCHA ---
def generate_captcha(width=300, height=100, font_size=42):
    global current_captcha_text
    current_captcha_text = ''.join(random.choices(string.digits, k=6))
    
    # Buat gambar kosong
    image = Image.new("RGB", (width, height), "white")
    draw = ImageDraw.Draw(image)
    
    # Muat font yang diunduh
    try:
        font = ImageFont.truetype(FONT_PATH, font_size)
    except IOError:
        raise Exception(f"Font tidak ditemukan di lokasi {FONT_PATH}.")
    
    # Hitung bounding box teks menggunakan textbbox
    text_bbox = draw.textbbox((0, 0), current_captcha_text, font=font)
    text_width, text_height = text_bbox[2] - text_bbox[0], text_bbox[3] - text_bbox[1]
    
    # Gambar teks di tengah dengan warna abu-abu dan efek tebal
    text_x = (width - text_width) // 2
    text_y = (height - text_height) // 2
    for offset_x in [-1, 0, 1]:
        for offset_y in [-1, 0, 1]:
            draw.text((text_x + offset_x, text_y + offset_y), current_captcha_text, font=font, fill="gray")
    
    # Tambahkan noise berupa garis horizontal dan diagonal
    for _ in range(200):
        x1, y1 = random.randint(0, width), random.randint(0, height)
        x2, y2 = random.randint(0, width), random.randint(0, height)
        draw.line(((x1, y1), (x2, y2)), fill="gray", width=random.randint(1, 2))
    
    # Tambahkan noise berupa titik kecil
    for _ in range(150):  # Tambahkan titik lebih banyak
        x = random.randint(0, width)  # Koordinat x
        y = random.randint(0, height)  # Koordinat y
        draw.point((x, y), fill="gray")
    
    # Simpan gambar ke memori
    image_bytes = BytesIO()
    image.save(image_bytes, format="PNG")
    image_bytes.seek(0)  # Reset pointer ke awal file
    
    return image_bytes

@app.route('/')
def home():
    return render_template("index.html")  # Gunakan render_template untuk file HTML

@app.route('/generate-captcha', methods=['GET'])
def generate_captcha_api():
    # Generate CAPTCHA
    captcha_image = generate_captcha()
    return send_file(
        captcha_image,
        mimetype="image/png",
        as_attachment=False,
        download_name="captcha.png"
    )

@app.route('/validate-captcha', methods=['POST'])
def validate_captcha():
    global current_captcha_text
    user_input = request.json.get("captcha_input", "")
    if user_input == current_captcha_text:
        return jsonify({"success": True, "message": "CAPTCHA benar!"})
    else:
        return jsonify({"success": False, "message": "CAPTCHA salah, coba lagi."})

if __name__ == '__main__':
    app.run(debug=False, port=5000)
