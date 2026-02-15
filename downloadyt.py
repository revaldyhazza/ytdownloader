import streamlit as st
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from pathlib import Path
import tempfile
import re

# Konfigurasi halaman
st.set_page_config(
    page_title="YouTube Downloader",
    page_icon="🎥",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS untuk UI yang menarik
st.markdown("""
<style>

/* ===== Google Font - Inter tetap bagus & modern ===== */
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@300;400;500;600;700&display=swap');

html, body, [class*="css"], [data-testid="stAppViewContainer"] {
    font-family: 'Inter', system-ui, sans-serif !important;
}

/* ===== Background - Dark & subtle ===== */
[data-testid="stAppViewContainer"] {
    background: #0f0f17;
    background: 
        radial-gradient(circle at 10% 20%, rgba(79,70,229,0.08) 0%, transparent 50%),
        radial-gradient(circle at 90% 80%, rgba(139,92,246,0.06) 0%, transparent 50%),
        #0f0f17;
}

/* ===== Mengurangi padding berlebih ===== */
.block-container {
    padding-top: 2.5rem !important;
    padding-bottom: 3rem !important;
    max-width: 780px !important;   /* biar tidak terlalu lebar di layar besar */
}

/* ===== Glass Card - lebih subtle & premium ===== */
.download-card {
    background: rgba(20, 25, 40, 0.65);
    backdrop-filter: blur(16px) saturate(180%);
    -webkit-backdrop-filter: blur(16px) saturate(180%);
    border: 1px solid rgba(255, 255, 255, 0.08);
    border-radius: 20px;
    padding: 2.4rem 2.8rem;
    box-shadow: 
        0 8px 32px rgba(0,0,0,0.35),
        inset 0 1px 1px rgba(255,255,255,0.04);
    margin: 1.8rem auto;
    color: #e2e8f0;
}

/* ===== Header - lebih clean ===== */
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

/* ===== Text Input - clean & modern ===== */
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

/* ===== Primary Button - lebih elegan ===== */
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

/* ===== Download Button ===== */
div.stDownloadButton > button {
    background: linear-gradient(135deg, #10b981, #059669);
}

div.stDownloadButton > button:hover {
    box-shadow: 0 10px 25px rgba(16,185,129,0.3);
}

/* ===== Segmented Radio - modern minimal ===== */
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

/* ===== Success / Error ===== */
div.stSuccess, div.stError {
    border-radius: 12px;
    padding: 1rem 1.3rem;
    border: 1px solid;
}

/* ===== Spinner ===== */
div.stSpinner > div > div {
    border-top-color: #a78bfa !important;
}

/* ===== Hilangkan branding Streamlit ===== */
#MainMenu {visibility: hidden;}
footer {visibility: hidden;}
header {visibility: hidden;}

/* Responsive fix kecil */
@media (max-width: 640px) {
    .download-card {
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
    
    youtube_regex_match = re.match(youtube_regex, url)
    return youtube_regex_match is not None

def get_video_info(url):
    """Mendapatkan informasi video"""
    try:
        yt = YouTube(url, on_progress_callback=on_progress)
        return yt
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return None

def get_available_formats(yt):
    """Mendapatkan format video yang tersedia"""
    video_formats = []
    audio_formats = []
    
    # Coba progressive dulu (video+audio jadi 1)
    progressive_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
    
    # Tambahkan adaptive streams (resolusi tinggi, video only)
    adaptive_streams = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc()
    
    seen_resolutions = set()
    
    # Progressive streams (biasanya max 720p)
    for stream in progressive_streams:
        if stream.resolution and stream.resolution not in seen_resolutions:
            seen_resolutions.add(stream.resolution)
            video_formats.append({
                'itag': stream.itag,
                'quality': stream.resolution,
                'fps': stream.fps,
                'filesize': stream.filesize,
                'type': 'progressive'
            })
    
    # Adaptive streams (bisa 1080p, 1440p, 4K)
    for stream in adaptive_streams:
        if stream.resolution and stream.resolution not in seen_resolutions:
            seen_resolutions.add(stream.resolution)
            video_formats.append({
                'itag': stream.itag,
                'quality': stream.resolution,
                'fps': stream.fps,
                'filesize': stream.filesize,
                'type': 'adaptive'
            })
    
    # Audio formats
    audio_streams = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc()
    seen_abr = set()
    for stream in audio_streams:
        if stream.abr and stream.abr not in seen_abr:
            seen_abr.add(stream.abr)
            audio_formats.append({
                'itag': stream.itag,
                'quality': stream.abr,
                'filesize': stream.filesize
            })
    
    # Sort video formats by resolution (descending)
    def get_resolution_number(quality):
        return int(quality.replace('p', ''))
    
    video_formats.sort(key=lambda x: get_resolution_number(x['quality']), reverse=True)
    
    return video_formats, audio_formats

def download_media(yt, download_type, quality_format=None, format_info=None):
    """Download video atau audio"""
    temp_dir = tempfile.gettempdir()
    
    try:
        if download_type == "🎵 Audio (MP3)":
            # Download audio langsung sebagai mp4 dulu
            audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(stream, chunk, bytes_remaining):
                total_size = stream.filesize
                bytes_downloaded = total_size - bytes_remaining
                percentage = int((bytes_downloaded / total_size) * 100)
                progress_bar.progress(percentage)
                status_text.text(f"📥 Downloading... {percentage}%")
            
            yt.register_on_progress_callback(progress_callback)
            
            # Download
            status_text.text("📥 Starting download...")
            output_file = audio_stream.download(output_path=temp_dir)
            
            # Rename ke .mp3 (file audio mp4 bisa langsung direname ke mp3)
            mp3_file = output_file.replace('.mp4', '.mp3').replace('.webm', '.mp3')
            if output_file != mp3_file:
                os.rename(output_file, mp3_file)
                output_file = mp3_file
            
            progress_bar.progress(100)
            status_text.text("✅ Done!")
            
            return output_file, yt.title
        else:
            # Download video
            video_stream = None
            is_adaptive = format_info and format_info.get('type') == 'adaptive'
            
            if quality_format:
                # Coba progressive dulu
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=quality_format).first()
                
                # Kalau gak ada, coba adaptive
                if not video_stream:
                    video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', resolution=quality_format, only_video=True).first()
                    is_adaptive = True
            
            # Fallback ke kualitas terbaik
            if not video_stream:
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
                if not video_stream:
                    video_stream = yt.streams.filter(adaptive=True, file_extension='mp4', only_video=True).order_by('resolution').desc().first()
                    is_adaptive = True
            
            if not video_stream:
                return None, "Format tidak tersedia"
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(stream, chunk, bytes_remaining):
                total_size = stream.filesize
                bytes_downloaded = total_size - bytes_remaining
                percentage = int((bytes_downloaded / total_size) * 100)
                progress_bar.progress(percentage)
                status_text.text(f"📥 Downloading video... {percentage}%")
            
            yt.register_on_progress_callback(progress_callback)
            
            # Download video
            status_text.text("📥 Downloading video...")
            video_file = video_stream.download(output_path=temp_dir, filename_prefix="video_")
            
            # Kalau adaptive, perlu download audio dan merge
            if is_adaptive:
                status_text.text("📥 Downloading audio...")
                audio_stream = yt.streams.filter(only_audio=True).order_by('abr').desc().first()
                audio_file = audio_stream.download(output_path=temp_dir, filename_prefix="audio_")
                
                # Merge menggunakan ffmpeg
                status_text.text("🔄 Merging video and audio...")
                output_filename = f"{yt.title}.mp4"
                # Bersihkan nama file dari karakter ilegal
                output_filename = "".join(c for c in output_filename if c.isalnum() or c in (' ', '-', '_', '.')).rstrip()
                output_path = os.path.join(temp_dir, output_filename)
                
                # Gunakan ffmpeg untuk merge
                import subprocess
                cmd = f'ffmpeg -i "{video_file}" -i "{audio_file}" -c copy "{output_path}" -y -loglevel quiet'
                
                try:
                    subprocess.run(cmd, shell=True, check=True)
                    # Hapus file temporary
                    os.remove(video_file)
                    os.remove(audio_file)
                    video_file = output_path
                except:
                    # Kalau ffmpeg gagal, return video aja (tanpa audio)
                    status_text.text("⚠️ Merging failed, returning video only")
                    pass
            
            progress_bar.progress(100)
            status_text.text("✅ Done!")
            
            return video_file, yt.title
            
    except Exception as e:
        return None, str(e)

# Header
st.markdown("""
    <div class="header">
        <h1>🎥 YouTube Downloader</h1>
        <p>Download video atau audio dari YouTube dengan kualitas pilihan Anda</p>
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
            yt = get_video_info(url)
            
            if yt:
                # Tampilkan preview video
                col1, col2 = st.columns([1, 2])
                
                with col1:
                    if yt.thumbnail_url:
                        st.image(yt.thumbnail_url, use_container_width=True)
                
                with col2:
                    st.markdown(f"**{yt.title}**")
                    st.caption(f"👤 {yt.author}")
                    st.caption(f"⏱️ Durasi: {yt.length // 60} menit {yt.length % 60} detik")
                    st.caption(f"👁️ {yt.views:,} views")
                
                st.markdown("---")
                
                # Pilih tipe download
                download_type = st.radio(
                    "Pilih format download:",
                    ["🎬 Video (MP4)", "🎵 Audio (MP3)"],
                    horizontal=True
                )
                
                # Pilih kualitas
                if download_type == "🎬 Video (MP4)":
                    video_formats, _ = get_available_formats(yt)
                    
                    if video_formats:
                        # Tampilkan info ukuran file jika ada
                        quality_display = []
                        for f in video_formats:
                            size_mb = f.get('filesize', 0) / (1024 * 1024) if f.get('filesize') else 0
                            if size_mb > 0:
                                quality_display.append(f"{f['quality']} (~{size_mb:.1f} MB)")
                            else:
                                quality_display.append(f['quality'])
                        
                        selected_index = st.selectbox(
                            "Pilih kualitas video:",
                            range(len(quality_display)),
                            format_func=lambda i: quality_display[i],
                            help="Kualitas yang lebih tinggi = ukuran file lebih besar. Resolusi >720p membutuhkan ffmpeg."
                        )
                        
                        selected_format = video_formats[selected_index]
                        selected_quality = selected_format['quality']
                        
                        # Info jika butuh merge
                        if selected_format.get('type') == 'adaptive':
                            st.info("ℹ️ Resolusi ini membutuhkan penggabungan video dan audio")
                    else:
                        selected_quality = None
                        selected_format = None
                        st.info("📺 Menggunakan kualitas terbaik yang tersedia")
                else:
                    audio_qualities = ["320", "256", "192", "128"]
                    selected_quality = st.selectbox(
                        "Pilih kualitas audio:",
                        ["320kbps", "256kbps", "192kbps", "128kbps"],
                        index=2,
                        help="Kualitas yang lebih tinggi = suara lebih jernih"
                    )
                    selected_quality = selected_quality.replace('kbps', '')
                
                # Tombol download
                if st.button("⬇️ Download Sekarang", type="primary"):
                    format_info = selected_format if download_type == "🎬 Video (MP4)" else None
                    filename, title = download_media(
                        yt, 
                        download_type, 
                        selected_quality,
                        format_info
                    )
                    
                    if filename and os.path.exists(filename):
                        # Baca file
                        with open(filename, 'rb') as f:
                            file_data = f.read()
                        
                        # Tentukan nama file untuk download
                        file_ext = '.mp3' if download_type == "🎵 Audio (MP3)" else '.mp4'
                        download_filename = f"{title}{file_ext}"
                        
                        # Tombol download
                        st.success("✅ Download berhasil!")
                        st.download_button(
                            label=f"💾 Simpan {download_filename}",
                            data=file_data,
                            file_name=download_filename,
                            mime='audio/mpeg' if file_ext == '.mp3' else 'video/mp4'
                        )
                        
                        # Hapus file temporary
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

# Footer info
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: white; padding: 2rem;'>
        <p style='font-size: 0.9rem; opacity: 0.8;'>
            💡 <strong>Tips:</strong> Pilih kualitas yang lebih rendah untuk download lebih cepat dan ukuran file lebih kecil
        </p>
        <p style='font-size: 0.8rem; opacity: 0.6; margin-top: 1rem;'>
            Streamlit | Revaldy Hazza Daniswara
        </p>
    </div>
""", unsafe_allow_html=True)
