import streamlit as st
from pytubefix import YouTube
from pytubefix.cli import on_progress
import os
import tempfile
import re

# Workaround untuk error 403
from pytubefix import innertube

def fix_403_error():
    """Fix untuk error 403 Forbidden"""
    innertube._default_clients["ANDROID"]["context"]["client"]["clientVersion"] = "19.09.36"
    innertube._default_clients["IOS"]["context"]["client"]["clientVersion"] = "19.09.36"
    innertube._default_clients["WEB"]["context"]["client"]["clientVersion"] = "2.20240304.00.00"

fix_403_error()

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
    
    return re.match(youtube_regex, url) is not None


def get_video_info(url):
    """Mendapatkan informasi video dengan retry mechanism"""
    max_retries = 3
    
    for attempt in range(max_retries):
        try:
            yt = YouTube(
                url, 
                on_progress_callback=on_progress,
                use_oauth=False,
                allow_oauth_cache=True,
                client='ANDROID'
            )
            # Test apakah bisa akses video
            _ = yt.title
            return yt
        except Exception as e:
            if attempt < max_retries - 1:
                st.warning(f"⏳ Mencoba ulang... ({attempt + 1}/{max_retries})")
                continue
            else:
                st.error(f"❌ Error: {str(e)}")
                return None


def get_available_formats(yt):
    """Mendapatkan format video yang tersedia"""
    video_formats = []
    
    try:
        # Progressive streams (video + audio, lebih cepat!)
        progressive_streams = yt.streams.filter(
            progressive=True, 
            file_extension='mp4'
        ).order_by('resolution').desc()
        
        seen_resolutions = set()
        
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
        
        # Adaptive streams (resolusi tinggi, tapi perlu merge)
        adaptive_streams = yt.streams.filter(
            adaptive=True, 
            file_extension='mp4', 
            only_video=True
        ).order_by('resolution').desc()
        
        for stream in adaptive_streams:
            if stream.resolution and stream.resolution not in seen_resolutions:
                height = int(stream.resolution.replace('p', ''))
                # Batasi sampai 1080p untuk performa
                if height <= 1080:
                    seen_resolutions.add(stream.resolution)
                    video_formats.append({
                        'itag': stream.itag,
                        'quality': stream.resolution,
                        'fps': stream.fps,
                        'filesize': stream.filesize,
                        'type': 'adaptive'
                    })
        
        # Sort by resolution
        video_formats.sort(
            key=lambda x: int(x['quality'].replace('p', '')), 
            reverse=True
        )
        
        return video_formats
    
    except Exception as e:
        st.error(f"Error: {str(e)}")
        return []


def download_media(yt, download_type, quality_format=None, format_info=None):
    """Download video atau audio"""
    temp_dir = tempfile.gettempdir()
    
    try:
        if download_type == "🎵 Audio (MP3)":
            # Download audio
            audio_stream = yt.streams.filter(
                only_audio=True,
                file_extension='mp4'
            ).order_by('abr').desc().first()
            
            if not audio_stream:
                audio_stream = yt.streams.filter(only_audio=True).first()
            
            if not audio_stream:
                return None, "Format audio tidak tersedia"
            
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
            
            status_text.text("📥 Starting download...")
            output_file = audio_stream.download(output_path=temp_dir)
            
            # Rename ke .mp3
            mp3_file = output_file.rsplit('.', 1)[0] + '.mp3'
            if output_file != mp3_file:
                os.rename(output_file, mp3_file)
                output_file = mp3_file
            
            progress_bar.progress(100)
            status_text.text("✅ Done!")
            
            return output_file, yt.title
        
        else:
            # Download video
            video_stream = None
            is_progressive = False
            
            if quality_format:
                # Prioritas progressive (lebih cepat!)
                video_stream = yt.streams.filter(
                    progressive=True, 
                    file_extension='mp4', 
                    resolution=quality_format
                ).first()
                
                if video_stream:
                    is_progressive = True
                else:
                    # Kalau tidak ada, coba adaptive
                    if format_info and format_info.get('type') == 'adaptive':
                        video_stream = yt.streams.filter(
                            adaptive=True, 
                            file_extension='mp4', 
                            resolution=quality_format, 
                            only_video=True
                        ).first()
            else:
                # Default: progressive terbaik
                video_stream = yt.streams.filter(
                    progressive=True, 
                    file_extension='mp4'
                ).order_by('resolution').desc().first()
                is_progressive = True
            
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
                status_text.text(f"📥 Downloading... {percentage}%")
            
            yt.register_on_progress_callback(progress_callback)
            
            status_text.text("📥 Downloading video...")
            video_file = video_stream.download(output_path=temp_dir)
            
            # Kalau progressive, langsung selesai
            if is_progressive:
                progress_bar.progress(100)
                status_text.text("✅ Done!")
                return video_file, yt.title
            
            # Kalau adaptive, perlu merge
            status_text.text("📥 Downloading audio...")
            audio_stream = yt.streams.filter(
                only_audio=True
            ).order_by('abr').desc().first()
            
            audio_file = audio_stream.download(
                output_path=temp_dir, 
                filename_prefix="audio_"
            )
            
            # Merge dengan ffmpeg
            status_text.text("🔄 Merging video and audio...")
            output_filename = f"{yt.title}.mp4"
            output_filename = "".join(
                c for c in output_filename 
                if c.isalnum() or c in (' ', '-', '_', '.')
            ).rstrip()
            output_path = os.path.join(temp_dir, output_filename)
            
            import subprocess
            cmd = [
                'ffmpeg', '-i', video_file, '-i', audio_file,
                '-c', 'copy', output_path, '-y', '-loglevel', 'quiet'
            ]
            
            try:
                subprocess.run(cmd, check=True)
                os.remove(video_file)
                os.remove(audio_file)
                video_file = output_path
            except Exception as merge_error:
                status_text.warning("⚠️ Merge gagal, returning video only (tanpa audio)")
            
            progress_bar.progress(100)
            status_text.text("✅ Done!")
            
            return video_file, yt.title
            
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
            yt = get_video_info(url)
            
            if yt:
                # Preview video
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
                
                selected_quality = None
                selected_format = None
                
                # Pilih kualitas
                if download_type == "🎬 Video (MP4)":
                    video_formats = get_available_formats(yt)
                    
                    if video_formats:
                        quality_display = []
                        for f in video_formats:
                            size_mb = f.get('filesize', 0) / (1024 * 1024) if f.get('filesize') else 0
                            speed_icon = "⚡" if f['type'] == 'progressive' else "🐌"
                            
                            if size_mb > 0:
                                quality_display.append(
                                    f"{speed_icon} {f['quality']} (~{size_mb:.1f} MB)"
                                )
                            else:
                                quality_display.append(f"{speed_icon} {f['quality']}")
                        
                        selected_index = st.selectbox(
                            "Pilih kualitas video:",
                            range(len(quality_display)),
                            format_func=lambda i: quality_display[i],
                            help="⚡ = Download cepat (sudah include audio)\n🐌 = Download lambat (perlu merge audio)"
                        )
                        
                        selected_format = video_formats[selected_index]
                        selected_quality = selected_format['quality']
                        
                        # Info tambahan
                        if selected_format['type'] == 'adaptive':
                            st.info("ℹ️ Resolusi ini membutuhkan penggabungan video dan audio (lebih lama)")
                    else:
                        st.info("📺 Menggunakan kualitas terbaik yang tersedia")
                
                # Tombol download
                if st.button("⬇️ Download Sekarang", type="primary"):
                    filename, title = download_media(
                        yt, 
                        download_type, 
                        selected_quality,
                        selected_format
                    )
                    
                    if filename and os.path.exists(filename):
                        # Baca file
                        with open(filename, 'rb') as f:
                            file_data = f.read()
                        
                        # Tentukan nama file
                        file_ext = '.mp3' if download_type == "🎵 Audio (MP3)" else '.mp4'
                        download_filename = f"{title}{file_ext}"
                        download_filename = "".join(
                            c for c in download_filename 
                            if c.isalnum() or c in (' ', '-', '_', '.')
                        ).rstrip()
                        
                        st.success("✅ Download berhasil!")
                        
                        # Tombol download
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
            💡 <strong>Tips:</strong> Pilih format dengan ⚡ untuk download lebih cepat
        </p>
        <p style='font-size: 0.85rem; opacity: 0.7; margin-top: 1rem;'>
            Made with ❤️ using Streamlit | Revaldy Hazza Daniswara
        </p>
    </div>
""", unsafe_allow_html=True)
