import streamlit as st
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
from pathlib import Path
import tempfile
import re
from moviepy.editor import AudioFileClip

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
    /* Import Google Fonts */
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    /* Main container */
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 2rem;
    }
    
    /* Card style */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    }
    
    .download-card {
        background: white;
        padding: 2.5rem;
        border-radius: 20px;
        box-shadow: 0 20px 60px rgba(0,0,0,0.15);
        margin: 2rem auto;
        max-width: 700px;
    }
    
    /* Header */
    .header {
        text-align: center;
        margin-bottom: 2rem;
    }
    
    .header h1 {
        color: #2d3748;
        font-weight: 700;
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
    }
    
    .header p {
        color: #718096;
        font-size: 1.1rem;
    }
    
    /* Input field */
    .stTextInput input {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 1rem;
        font-size: 1rem;
        transition: all 0.3s ease;
    }
    
    .stTextInput input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 3px rgba(102, 126, 234, 0.1);
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        transition: all 0.3s ease;
        width: 100%;
        margin-top: 1rem;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(102, 126, 234, 0.3);
    }
    
    /* Radio buttons */
    .stRadio > label {
        font-weight: 600;
        color: #2d3748;
        font-size: 1.1rem;
        margin-bottom: 0.5rem;
    }
    
    .stRadio > div {
        background: #f7fafc;
        padding: 1rem;
        border-radius: 12px;
        border: 2px solid #e2e8f0;
    }
    
    /* Selectbox */
    .stSelectbox > label {
        font-weight: 600;
        color: #2d3748;
        font-size: 1rem;
    }
    
    .stSelectbox select {
        border-radius: 12px;
        border: 2px solid #e2e8f0;
        padding: 0.75rem;
    }
    
    /* Success/Error messages */
    .stSuccess {
        background: #f0fff4;
        border: 2px solid #68d391;
        border-radius: 12px;
        padding: 1rem;
        color: #22543d;
    }
    
    .stError {
        background: #fff5f5;
        border: 2px solid #fc8181;
        border-radius: 12px;
        padding: 1rem;
        color: #742a2a;
    }
    
    /* Info box */
    .info-box {
        background: #ebf8ff;
        border-left: 4px solid #4299e1;
        padding: 1rem;
        border-radius: 8px;
        margin: 1rem 0;
        color: #2c5282;
    }
    
    /* Download button */
    .stDownloadButton button {
        background: linear-gradient(135deg, #48bb78 0%, #38a169 100%);
        color: white;
        border: none;
        border-radius: 12px;
        padding: 0.75rem 2rem;
        font-weight: 600;
        font-size: 1rem;
        width: 100%;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 10px 25px rgba(72, 187, 120, 0.3);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-color: #667eea;
    }
    
    /* Hide Streamlit branding */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
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
    video_streams = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc()
    audio_streams = yt.streams.filter(only_audio=True, file_extension='mp4').order_by('abr').desc()
    
    video_formats = []
    audio_formats = []
    
    # Video formats
    seen_resolutions = set()
    for stream in video_streams:
        if stream.resolution and stream.resolution not in seen_resolutions:
            seen_resolutions.add(stream.resolution)
            video_formats.append({
                'itag': stream.itag,
                'quality': stream.resolution,
                'fps': stream.fps,
                'filesize': stream.filesize
            })
    
    # Audio formats
    seen_abr = set()
    for stream in audio_streams:
        if stream.abr and stream.abr not in seen_abr:
            seen_abr.add(stream.abr)
            audio_formats.append({
                'itag': stream.itag,
                'quality': stream.abr,
                'filesize': stream.filesize
            })
    
    return video_formats, audio_formats

def download_media(yt, download_type, quality_format=None):
    """Download video atau audio"""
    temp_dir = tempfile.gettempdir()
    
    try:
        if download_type == "🎵 Audio (MP3)":
            # Download audio
            audio_stream = yt.streams.filter(only_audio=True, file_extension='mp4').first()
            
            # Progress bar
            progress_bar = st.progress(0)
            status_text = st.empty()
            
            def progress_callback(stream, chunk, bytes_remaining):
                total_size = stream.filesize
                bytes_downloaded = total_size - bytes_remaining
                percentage = int((bytes_downloaded / total_size) * 100)
                progress_bar.progress(percentage)
                status_text.text(f"Downloading... {percentage}%")
            
            yt.register_on_progress_callback(progress_callback)
            
            # Download
            audio_file = audio_stream.download(output_path=temp_dir, filename="temp_audio.mp4")
            
            # Convert to MP3
            status_text.text("Converting to MP3...")
            mp3_file = os.path.join(temp_dir, f"{yt.title}.mp3")
            audio_clip = AudioFileClip(audio_file)
            audio_clip.write_audiofile(mp3_file, codec='mp3', bitrate=f"{quality_format if quality_format else '192'}k", verbose=False, logger=None)
            audio_clip.close()
            
            # Hapus file temporary
            os.remove(audio_file)
            
            progress_bar.progress(100)
            status_text.text("Done!")
            
            return mp3_file, yt.title
        else:
            # Download video
            if quality_format:
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4', resolution=quality_format).first()
            else:
                video_stream = yt.streams.filter(progressive=True, file_extension='mp4').order_by('resolution').desc().first()
            
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
                status_text.text(f"Downloading... {percentage}%")
            
            yt.register_on_progress_callback(progress_callback)
            
            # Download
            video_file = video_stream.download(output_path=temp_dir)
            
            progress_bar.progress(100)
            status_text.text("Done!")
            
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
                        quality_options = [f['quality'] for f in video_formats]
                        selected_quality = st.selectbox(
                            "Pilih kualitas video:",
                            quality_options,
                            help="Kualitas yang lebih tinggi = ukuran file lebih besar"
                        )
                    else:
                        selected_quality = None
                        st.info("Menggunakan kualitas terbaik yang tersedia")
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
                    filename, title = download_media(
                        yt, 
                        download_type, 
                        selected_quality
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
            Dibuat dengan ❤️ menggunakan Streamlit • yt-dlp
        </p>
    </div>
""", unsafe_allow_html=True)
