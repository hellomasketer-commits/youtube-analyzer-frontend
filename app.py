# app.py - VERSI BARU DENGAN FITUR SARAN JUDUL

import os
import json
import requests
import google.generativeai as genai
from flask import Flask, request, jsonify, render_template
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# --- KONFIGURASI ---
YOUTUBE_API_KEY = 'AIzaSyBdpUj5rWBmCf3jHWXPiwGt9bacLqMbSBQ'
GEMINI_API_KEY = 'AIzaSyArI6hUZ9sZrftSAEX05t8uQONUBK6xTLk'
genai.configure(api_key=GEMINI_API_KEY)
vision_model = genai.GenerativeModel('gemini-2.5-flash')
text_model = genai.GenerativeModel('gemini-2.5-flash')
app = Flask(__name__)

# --- FUNGSI HELPER (Termasuk fungsi baru kita) ---

# ... (Semua fungsi helper dari sebelumnya: get_channel_data, get_video_comments, 
# analyze_general_and_titles, analyze_thumbnails_with_gemini, analyze_comments_with_gemini
# tetap sama persis. Pastikan mereka ada di sini.)

def get_channel_data(channel_id):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        channel_request = youtube.channels().list(part='snippet,statistics', id=channel_id)
        channel_response = channel_request.execute()
        if not channel_response.get('items'): return None, "Channel tidak ditemukan."
        channel_info = channel_response['items'][0]
        videos_request = youtube.search().list(part='snippet', channelId=channel_id, maxResults=10, order='date', type='video')
        videos_response = videos_request.execute()
        videos = [{"title": item['snippet']['title'], "video_id": item['id']['videoId'], "thumbnail_url": item['snippet']['thumbnails']['high']['url']} for item in videos_response.get('items', [])]
        return {"channel_name": channel_info['snippet']['title'], "description": channel_info['snippet']['description'], "subscriber_count": channel_info['statistics']['subscriberCount'], "videos": videos}, None
    except Exception as e: return None, f"Error YouTube API: {e}"

def get_video_comments(video_id):
    try:
        youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)
        comment_request = youtube.commentThreads().list(part='snippet', videoId=video_id, maxResults=5, textFormat='plainText', order='relevance')
        comment_response = comment_request.execute()
        comments = [{"author": item['snippet']['topLevelComment']['snippet']['authorDisplayName'], "text": item['snippet']['topLevelComment']['snippet']['textDisplay']} for item in comment_response.get('items', [])]
        return comments, None
    except HttpError as e:
        if e.resp.status == 403: return [], "Komentar dinonaktifkan."
        return [], f"Error saat ambil komentar: {e}"
    except Exception as e: return [], f"Error tak terduga: {e}"

def analyze_general_and_titles(channel_data):
    prompt = f"Anda adalah ahli strategi YouTube. Analisis data channel ini (Nama: {channel_data['channel_name']}, Subs: {channel_data['subscriber_count']}, Deskripsi: {channel_data['description']}, Judul Video: {', '.join([v['title'] for v in channel_data['videos']])}). Berikan analisis (Ringkasan, Analisis Judul, Saran Konten) dalam format Markdown."
    response = text_model.generate_content(prompt)
    return response.text

def analyze_thumbnails_with_gemini(videos):
    try:
        prompt = "Anda adalah desainer grafis. Lihat 10 thumbnail ini. Berikan analisis (Skor rata-rata, Poin Kuat, Area Perbaikan) dalam format Markdown."
        image_parts = []
        for video in videos:
            response = requests.get(video['thumbnail_url'])
            response.raise_for_status()
            image_parts.append({"mime_type": "image/jpeg", "data": response.content})
        response = vision_model.generate_content([prompt] + image_parts)
        return response.text
    except Exception as e: return f"**Gagal menganalisis thumbnail:** {e}"

def analyze_comments_with_gemini(comments):
    if not comments: return "Tidak ada komentar untuk dianalisis."
    comment_texts = [f"- '{c['text']}' oleh {c['author']}" for c in comments]
    prompt = f"Anda adalah analis sentimen. Berikut 5 komentar: {chr(10).join(comment_texts)}. Berikan analisis (Ringkasan Sentimen, Klasifikasi per Komentar) dalam format Markdown."
    response = text_model.generate_content(prompt)
    return response.text

# --- FUNGSI BARU UNTUK SARAN JUDUL ---
def analyze_title_suggestions(channel_data):
    """Membuat 10 saran judul baru berdasarkan konten channel."""
    prompt = f"""
    Anda adalah seorang ahli copywriting dan strategi konten YouTube yang spesialis dalam membuat judul viral dan SEO-friendly.
    Berdasarkan data channel berikut:
    - Nama Channel: {channel_data['channel_name']}
    - Deskripsi: {channel_data['description']}
    - Topik dari 10 Video Terakhir: {', '.join([v['title'] for v in channel_data['videos']])}

    Tugas Anda:
    Buat daftar 10 ide judul baru untuk video selanjutnya di channel ini.
    Judul harus:
    - Menarik rasa penasaran (Clickbait positif).
    - Relevan dengan topik yang sudah ada.
    - Mengandung kata kunci yang kuat untuk pencarian YouTube.
    - Bervariasi dalam format (misalnya, beberapa menggunakan angka, beberapa berupa pertanyaan).

    Sajikan hasilnya dalam format daftar bernomor (numbered list) Markdown.
    """
    response = text_model.generate_content(prompt)
    return response.text

# --- ENDPOINT ---

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/fetch-youtube-data', methods=['POST'])
def fetch_youtube_data():
    channel_id = request.json.get('channel_id')
    if not channel_id: return jsonify({"error": "Channel ID tidak diberikan"}), 400
    
    channel_data, error = get_channel_data(channel_id)
    if error: return jsonify({"error": error}), 500

    latest_video_id = channel_data['videos'][0]['video_id'] if channel_data['videos'] else None
    comments, comment_error_msg = [], None
    if latest_video_id:
        comments, comment_error_msg = get_video_comments(latest_video_id)
    
    channel_data['comments'] = comments
    channel_data['comment_error'] = comment_error_msg
    
    return jsonify(channel_data)

@app.route('/analyze/general', methods=['POST'])
def handle_general_analysis():
    analysis_result = analyze_general_and_titles(request.json)
    return jsonify({'analysis': analysis_result})

@app.route('/analyze/thumbnails', methods=['POST'])
def handle_thumbnail_analysis():
    analysis_result = analyze_thumbnails_with_gemini(request.json.get('videos', []))
    return jsonify({'analysis': analysis_result})

@app.route('/analyze/comments', methods=['POST'])
def handle_comment_analysis():
    analysis_result = analyze_comments_with_gemini(request.json.get('comments', []))
    return jsonify({'analysis': analysis_result})

# --- ENDPOINT BARU UNTUK SARAN JUDUL ---
@app.route('/analyze/title-suggestions', methods=['POST'])
def handle_title_suggestions():
    """Endpoint Tahap 3: Saran Judul."""
    channel_data = request.json
    analysis_result = analyze_title_suggestions(channel_data)
    return jsonify({'analysis': analysis_result})

# --- Menjalankan Aplikasi ---
if __name__ == '__main__':
    app.run(debug=True)