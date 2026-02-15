import streamlit as st
import yt_dlp
import os
import tempfile
import re
import json

# Konfigurasi halaman
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', system-ui, sans-serif !important;
}

[data-testid="stAppViewContainer"] {
    background: #0f0f17;
    background: 
        radial-gradient(circle at 10% 20%, rgba(79,70,229,0.08) 0%, transparent 50%),
        radial-gradient(circle at 90% 80%, rgba(139,92,246,0.06) 0%, transparent 50%),
        #0f0f17;
}

.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 780px !important;
}

.header {
    text-align: center;
    margin-bottom: 2rem;
}

.header h1 {
    font-size: 2.4rem;
    font-weight: 700;
    letter-spacing: -0.4px;
    margin-bottom: 0.6rem;
    background: linear-gradient(90deg, #c084fc, #a78bfa, #7dd3fc);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.header p {
    color: #94a3b8;
    font-size: 1.05rem;
    font-weight: 400;
}

div[data-testid="stTextInput"] input {
    border-radius: 12px;
    border: 1px solid #334155;
    background: rgba(30, 41, 59, 0.6);
    color: #e2e8f0;
    padding: 0.75rem 1rem;
    font-size: 0.98rem;
    transition: all 0.2s ease;
}

div[data-testid="stTextInput"] input:focus {
    border-color: #a78bfa;
    box-shadow: 0 0 0 3px rgba(167,139,250,0.18);
    background: rgba(30, 41, 59, 0.8);
}

div.stButton > button {
    background: linear-gradient(135deg, #7c3aed, #a855f7);
    color: white;
    border: none;
    border-radius: 12px;
    padding: 0.78rem 1.4rem;
    font-weight: 600;
    font-size: 0.98rem;
    width: 100%;
    margin-top: 1.2rem;
    transition: all 0.22s ease;
}

div.stButton > button:hover {
    transform: translateY(-1px);
    box-shadow: 0 10px 25px rgba(168,85,247,0.3);
    filter: brightness(1.08);
}

div.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #059669) !important;
    color: white !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 0.78rem 1.4rem !important;
    font-weight: 600 !important;
    width: 100% !important;
}

div.stDownloadButton > button:hover {
    box-shadow: 0 10px 25px rgba(16,185,129,0.3) !important;
    transform: translateY(-1px) !important;
}

div[data-testid="stRadio"] [role="radiogroup"] {
    flex-direction: row !important;
    background: rgba(30,41,59,0.5);
    border-radius: 999px;
    padding: 5px;
    border: 1px solid rgba(255,255,255,0.06);
    width: fit-content;
    margin: 0 auto;
}

div[data-testid="stRadio"] label {
    color: #cbd5e1;
    font-weight: 500;
    padding: 0.55rem 1.3rem;
    border-radius: 999px;
    transition: all 0.18s ease;
}

div[data-testid="stRadio"] input[type="radio"]:checked + label {
    background: rgba(255,255,255,0.12);
    color: white;
    box-shadow: 0 2px 8px rgba(0,0,0,0.2);
}

div.stSuccess, div.stError, div.stInfo, div.stWarning {
    border-radius: 12px;
    padding: 1rem 1.3rem;
}

div.stSpinner > div > div {
    border-top-color: #a78bfa !important;
}

#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

@media (max-width: 640px) {
    .block-container {
        padding: 1.8rem 1.5rem;
        margin: 1rem;
    }
    .header h1 { font-size: 2.1rem; }
}
</style>
""", unsafe_allow_html=True)


def is_valid_youtube_url(url):
    """Validasi URL YouTube"""
    youtube_regex = (
        r'(https?://)?(www\.)?'
        '(youtube|youtu|youtube-nocookie)\.(com|be)/'
        '(watch\?v=|embed/|v/|.+\?v=)?([^&=%\?]{11})')
    
    return re.match(youtube_regex, url) is not None


def get_video_info(url):
    """Mendapatkan informasi video"""
    try:
        ydl_opts = {
            'quiet': True,
            'no_warnings': True,
            'extract_flat': False,
            'skip_download': True,
        }
        
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=False)
            return info
    except Exception as e:
        st.error(f"❌ Error: {str(e)}")
        return None


def format_filesize(bytes_size):
    """Format ukuran file ke MB"""
    if bytes_size:
        return f"{bytes_size / (1024 * 1024):.1f} MB"
    return "N/A"


def get_available_formats(info):
    """Mendapatkan format video yang tersedia"""
    video_formats = []
    formats = info.get('formats', [])
    
    seen_resolutions = {}
    
    for f in formats:
        height = f.get('height')
        vcodec = f.get('vcodec', 'none')
        acodec = f.get('acodec', 'none')
        ext = f.get('ext', '')
        
        # Filter: hanya video dengan codec valid dan extension mp4/webm
        if height and vcodec != 'none' and ext in ['mp4', 'webm']:
            quality = f"{height}p"
            filesize = f.get('filesize') or f.get('filesize_approx', 0)
            
            # Prioritas: progressive (video+audio) > adaptive video only
            has_audio = acodec != 'none'
            
            # Simpan format terbaik per resolusi
            if quality not in seen_resolutions or (has_audio and not seen_resolutions[quality].get('has_audio')):
                seen_resolutions[quality] = {
                    'quality': quality,
                    'height': height,
                    'filesize': filesize,
                    'has_audio': has_audio,
                    'ext': ext
                }
    
    # Convert ke list dan sort
    video_formats = list(seen_resolutions.values())
    video_formats.sort(key=lambda x: x['height'], reverse=True)
    
    return video_formats


def download_media(url, download_type, quality_format=None):
    """Download video atau audio"""
    temp_dir = tempfile.gettempdir()
    
    try:
        if download_type == "🎵 Audio (MP3)":
            # Konfigurasi untuk audio
            ydl_opts = {
                'format': 'bestaudio/best',
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'postprocessors': [{
                    'key': 'FFmpegExtractAudio',
                    'preferredcodec': 'mp3',
                    'preferredquality': '192',
                }],
                'quiet': False,
                'no_warnings': True,
            }
        else:
            # Konfigurasi untuk video
            if quality_format:
                height = quality_format.replace('p', '')
                # Format: pilih video dengan height yang sesuai + audio terbaik
                format_str = f'bestvideo[height<={height}][ext=mp4]+bestaudio[ext=m4a]/best[height<={height}]'
            else:
                format_str = 'bestvideo[ext=mp4]+bestaudio[ext=m4a]/best'
            
            ydl_opts = {
                'format': format_str,
                'outtmpl': os.path.join(temp_dir, '%(title)s.%(ext)s'),
                'merge_output_format': 'mp4',
                'quiet': False,
                'no_warnings': True,
            }
        
        # Progress tracking
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        downloaded_bytes = [0]  # Gunakan list agar bisa dimodifikasi di nested function
        total_bytes = [0]
        
        def progress_hook(d):
            if d['status'] == 'downloading':
                total = d.get('total_bytes') or d.get('total_bytes_estimate', 0)
                downloaded = d.get('downloaded_bytes', 0)
                
                if total > 0:
                    downloaded_bytes[0] = downloaded
                    total_bytes[0] = total
                    percentage = int((downloaded / total) * 100)
                    progress_bar.progress(min(percentage, 100))
                    status_text.text(f"📥 Downloading... {percentage}%")
                else:
                    # Fallback jika total tidak diketahui
                    mb = downloaded / (1024 * 1024)
                    status_text.text(f"📥 Downloading... {mb:.1f} MB")
            
            elif d['status'] == 'finished':
                status_text.text("🔄 Processing...")
        
        ydl_opts['progress_hooks'] = [progress_hook]
        
        # Download
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            
            # Get filename
            base_filename = ydl.prepare_filename(info)
            
            # Untuk audio, ekstensi akan berubah ke .mp3
            if download_type == "🎵 Audio (MP3)":
                filename = base_filename.rsplit('.', 1)[0] + '.mp3'
            else:
                filename = base_filename
            
            progress_bar.progress(100)
            status_text.text("✅ Done!")
            
            return filename, info.get('title', 'video')
    
    except Exception as e:
        return None, str(e)


# ========== MAIN APP ==========

# Header
st.markdown("""
    <div class="header">
        <h1>🎥 YouTube Downloader</h1>
        <p>Download video atau audio dari YouTube dengan mudah dan cepat</p>
    </div>
""", unsafe_allow_html=True)

# Input URL
url = st.text_input(
    "Masukkan URL YouTube",
    placeholder="https://www.youtube.com/watch?v=...",
    help="Paste link YouTube di sini"
)

if url:
    if is_valid_youtube_url(url):
        with st.spinner("🔍 Mengambil informasi video..."):
            info = get_video_info(url)
            
            if info:
                # Preview video
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    thumbnail = info.get('thumbnail')
                    if thumbnail:
                        st.image(thumbnail, use_container_width=True)
                
                with col2:
                    st.markdown(f"**{info.get('title', 'Unknown')}**")
                    st.caption(f"👤 {info.get('uploader', 'Unknown')}")
                    duration = info.get('duration', 0)
                    st.caption(f"⏱️ Durasi: {duration // 60} menit {duration % 60} detik")
                    views = info.get('view_count', 0)
                    st.caption(f"👁️ {views:,} views")
                
                st.markdown("---")
                
                # Pilih tipe download
                download_type = st.radio(
                    "Pilih format download:",
                    ["🎬 Video (MP4)", "🎵 Audio (MP3)"],
                    horizontal=True
                )
                
                selected_quality = None
                
                # Pilih kualitas
                if download_type == "🎬 Video (MP4)":
                    video_formats = get_available_formats(info)
                    
                    if video_formats:
                        quality_display = []
                        for f in video_formats:
                            size = format_filesize(f['filesize'])
                            audio_icon = "🔊" if f['has_audio'] else "🔇"
                            quality_display.append(
                                f"{audio_icon} {f['quality']} (~{size})"
                            )
                        
                        selected_index = st.selectbox(
                            "Pilih kualitas video:",
                            range(len(quality_display)),
                            format_func=lambda i: quality_display[i],
                            help="🔊 = Sudah include audio\n🔇 = Perlu merge audio (otomatis)"
                        )
                        
                        selected_quality = video_formats[selected_index]['quality']
                    else:
                        st.info("📺 Menggunakan kualitas terbaik yang tersedia")
                
                # Tombol download
                if st.button("⬇️ Download Sekarang", type="primary"):
                    filename, title = download_media(url, download_type, selected_quality)
                    
                    if filename and os.path.exists(filename):
                        # Baca file
                        with open(filename, 'rb') as f:
                            file_data = f.read()
                        
                        # Tentukan nama file
                        file_ext = '.mp3' if download_type == "🎵 Audio (MP3)" else '.mp4'
                        download_filename = f"{title}{file_ext}"
                        
                        # Clean filename
                        download_filename = "".join(
                            c for c in download_filename 
                            if c.isalnum() or c in (' ', '-', '_', '.')
                        ).rstrip()
                        
                        st.success("✅ Download berhasil!")
                        
                        st.download_button(
                            label=f"💾 Simpan {download_filename}",
                            data=file_data,
                            file_name=download_filename,
                            mime='audio/mpeg' if file_ext == '.mp3' else 'video/mp4'
                        )
                        
                        # Cleanup
                        try:
                            os.remove(filename)
                        except:
                            pass
                    else:
                        st.error(f"❌ Gagal mendownload: {title}")
            else:
                st.error("❌ Tidak dapat mengambil informasi video. Pastikan URL valid dan video dapat diakses.")
    else:
        st.warning("⚠️ URL YouTube tidak valid. Pastikan Anda memasukkan link yang benar.")

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #94a3b8; padding: 2rem;'>
        <p style='font-size: 0.9rem;'>
            💡 <strong>Tips:</strong> Pilih format dengan 🔊 untuk hasil terbaik
        </p>
        <p style='font-size: 0.85rem; opacity: 0.7; margin-top: 1rem;'>
            Made with ❤️ using Streamlit | Revaldy Hazza Daniswara
        </p>
    </div>
""", unsafe_allow_html=True)
