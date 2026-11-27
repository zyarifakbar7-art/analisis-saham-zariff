import os
import re
import json
import math
import time
import html
import base64
import hashlib
import urllib.request
import urllib.parse
import urllib.error
import xml.etree.ElementTree as ET
from concurrent.futures import ThreadPoolExecutor
from datetime import date, datetime, timezone, timedelta
import yfinance as yf
import pandas as pd
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import streamlit.components.v1 as components
from dotenv import load_dotenv

try:
    from google import genai
    from google.genai import types
except Exception:
    genai = None
    types = None

# ================= KONFIGURASI HALAMAN & TEMA DARK =================
st.set_page_config(
    page_title="Analisis Saham by Zariff — Live IHSG & Watchlist",
    page_icon="📈",
    layout="wide",
    initial_sidebar_state="collapsed"
)

st.markdown("""
<style>
@keyframes popIn {
    0% { opacity: 0; transform: translateY(8px) scale(0.99); }
    100% { opacity: 1; transform: translateY(0) scale(1); }
}
@keyframes pulseDot {
    0% { box-shadow: 0 0 0 0 rgba(0, 200, 5, 0.7); }
    70% { box-shadow: 0 0 0 7px rgba(0, 200, 5, 0); }
    100% { box-shadow: 0 0 0 0 rgba(0, 200, 5, 0); }
}
.stApp { background-color: #0e1116; color: #f0f3fa; }
header[data-testid="stHeader"] { background-color: #0e1116; }

.live-badge {
    display: inline-flex; align-items: center; gap: 7px;
    background-color: #161b22; border: 1px solid #262c36;
    padding: 4px 11px; border-radius: 20px;
    font-size: 12px; font-weight: 600; color: #00c805;
}
.live-dot {
    width: 8px; height: 8px; background-color: #00c805;
    border-radius: 50%; animation: pulseDot 1.8s infinite;
}
.login-box-wrap {
    max-width: 420px; margin: 60px auto 20px auto;
    background: linear-gradient(180deg, #151b24 0%, #10151c 100%);
    border: 1px solid #273244; border-radius: 14px; padding: 26px 24px;
    box-shadow: 0 18px 45px rgba(0, 0, 0, 0.65); text-align: center;
}
.stButton > button, div[data-testid="stFormSubmitButton"] > button {
    border-radius: 8px; font-weight: 600; transition: all 0.18s ease !important;
}
.stButton > button:hover, div[data-testid="stFormSubmitButton"] > button:hover {
    border-color: #00c805 !important; transform: scale(1.02);
    box-shadow: 0 4px 14px rgba(0, 200, 5, 0.2);
}
div[data-testid="stDialog"] div[role="dialog"] {
    background-color: #131722; border: 1px solid #2a3240;
    border-radius: 14px; box-shadow: 0 20px 50px rgba(0, 0, 0, 0.85);
    animation: popIn 0.22s ease-out;
}
.stTabs [data-baseweb="tab-list"] { gap: 18px; border-bottom: 1px solid #262c36; }
.stTabs [data-baseweb="tab"] { color: #8b949e; font-weight: 600; font-size: 13px; padding-bottom: 8px; }
.stTabs [aria-selected="true"] { color: #00c805 !important; border-bottom: 2px solid #00c805 !important; }

.popup-stat-grid { display: grid; grid-template-columns: repeat(4, 1fr); gap: 8px; margin-top: 6px; }
.popup-stat-card {
    background-color: #161b22; border: 1px solid #242b35; border-radius: 9px;
    padding: 8px 12px; transition: transform 0.18s ease, border-color 0.18s ease;
}
.popup-stat-card:hover { transform: scale(1.02); border-color: #00c805; background-color: #1a212b; }
.popup-stat-label { font-size: 11px; color: #8b949e; font-weight: 600; margin-bottom: 2px; }
.popup-stat-val { font-size: 15px; font-weight: 700; color: #f0f3fa; }

/* ================= KARTU KANDIDAT SCREENER NAIK & TURUN ================= */
.sc-card {
    background: linear-gradient(180deg, #141a23 0%, #10151c 100%);
    border: 1px solid #232b38; border-radius: 11px; padding: 10px 12px;
    margin-bottom: 4px; transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.sc-card:hover { transform: translateY(-2px); border-color: #00c805; box-shadow: 0 8px 20px rgba(0,0,0,0.4); }
.sc-card-down {
    background: linear-gradient(180deg, #1a1418 0%, #131015 100%);
    border: 1px solid #2f2228; border-radius: 11px; padding: 10px 12px;
    margin-bottom: 4px; transition: transform 0.18s ease, border-color 0.18s ease, box-shadow 0.18s ease;
}
.sc-card-down:hover { transform: translateY(-2px); border-color: #ff3b30; box-shadow: 0 8px 20px rgba(0,0,0,0.4); }
.sc-head-left { display: flex; align-items: center; gap: 7px; min-width: 0; }
.sc-pill-row { display: flex; gap: 4px; margin-top: 6px; flex-wrap: wrap; }
.sc-pill { font-size: 10px; font-weight: 700; padding: 2px 6px; border-radius: 5px; }

.filter-info-pill {
    background-color: #141a23; border: 1px solid #263040; border-radius: 9px;
    padding: 7px 11px; font-size: 11.5px; color: #c9d1d9; text-align: center; line-height: 1.35;
}

/* ================= TABEL & KARTU HASIL ANALISIS AI (DENGAN LOGO) ================= */
.ai-sec-heading {
    font-size: 15px; font-weight: 800; color: #f0f3fa;
    margin: 12px 0 8px 0; display: flex; align-items: center; gap: 8px;
}
.ai-sec-heading:first-child { margin-top: 2px; }
.ai-tbl-wrap {
    width: 100%; overflow-x: auto; border-radius: 10px;
    border: 1px solid #263040; margin-bottom: 12px; background-color: #0f141d;
}
.ai-tbl { width: 100%; border-collapse: collapse; font-size: 12.5px; }
.ai-tbl th {
    background-color: #17202e; color: #9ca3af; font-weight: 700;
    padding: 10px 11px; border-bottom: 1px solid #2a3547; text-align: left; white-space: nowrap;
}
.ai-tbl td {
    padding: 9px 11px; border-bottom: 1px solid #1b2331;
    vertical-align: middle; color: #e6edf3; line-height: 1.42;
}
.ai-tbl tr:last-child td { border-bottom: none; }
.ai-tbl tr:hover td { background-color: #161f2d; }
.ai-stock-cell { display: flex; align-items: center; gap: 9px; min-width: 155px; }
.ai-stock-info { display: flex; flex-direction: column; line-height: 1.2; min-width: 0; }
.ai-stock-tk { font-size: 13.5px; font-weight: 800; color: #f0f3fa; }
.ai-stock-nm {
    font-size: 10.5px; color: #8b949e; max-width: 138px;
    white-space: nowrap; overflow: hidden; text-overflow: ellipsis;
}
.ai-pill-fokus {
    display: inline-block; padding: 3px 8px; border-radius: 6px;
    font-size: 11px; font-weight: 700; white-space: nowrap;
}
.ai-pick-grid {
    display: grid; grid-template-columns: repeat(3, minmax(0, 1fr));
    gap: 10px; margin-bottom: 10px;
}
@media (max-width: 960px) {
    .ai-pick-grid { grid-template-columns: 1fr; }
}
.ai-pick-card {
    background-color: #131923; border: 1px solid #242e3e;
    border-radius: 10px; padding: 11px 13px;
}
.ai-pick-head {
    display: flex; align-items: center; justify-content: space-between; gap: 8px;
    padding-bottom: 8px; margin-bottom: 8px; border-bottom: 1px solid #202837;
}
.ai-pick-rank {
    font-size: 11px; font-weight: 800; padding: 2px 8px;
    border-radius: 6px; background-color: #1c293d; color: #6cb6ff; flex-shrink: 0;
}
.ai-pick-ul {
    margin: 0; padding-left: 16px; font-size: 12px; color: #d1d5db; line-height: 1.48;
}
.ai-pick-ul li { margin-bottom: 4px; }
.ai-footer-note {
    margin-top: 8px; padding-top: 8px; border-top: 1px solid #212936;
    font-size: 11.5px; color: #8b949e; display: flex; justify-content: space-between; flex-wrap: wrap; gap: 6px;
}

.ob-meta-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 6px 18px;
    background-color: #10141b; border: 1px solid #1e2530; border-radius: 10px;
    padding: 10px 14px; margin-bottom: 10px; font-size: 12.5px;
}
.ob-meta-row { display: flex; justify-content: space-between; align-items: center; padding: 2px 0; }
.ob-meta-lbl { color: #8b949e; }
.ob-meta-val { font-weight: 700; color: #f0f3fa; }
.ob-table-wrap {
    background-color: #10141b; border: 1px solid #1e2530; border-radius: 10px;
    overflow: hidden; margin-bottom: 10px;
}
.ob-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.ob-table th { color: #8b949e; font-weight: 600; padding: 7px 6px; border-bottom: 1px solid #1e2530; background-color: #141922; }
.ob-table td { padding: 5px 6px; border-bottom: 1px solid #171c26; vertical-align: middle; }
.ob-bar-bg { width: 100%; height: 3px; background-color: #1d2430; border-radius: 2px; margin-top: 2px; overflow: hidden; }
.ob-bar-bid { height: 100%; background-color: #ff4d4f; float: right; }
.ob-bar-ask { height: 100%; background-color: #00c805; float: left; }
.ob-sum-bar {
    display: flex; justify-content: space-between; align-items: center;
    background-color: #141922; border: 1px solid #1e2530; border-radius: 8px;
    padding: 8px 12px; font-size: 12.5px; font-weight: 700; margin-bottom: 12px;
}
.ob-ratio-track {
    flex: 1; height: 6px; margin: 0 12px; background-color: #2962ff;
    border-radius: 99px; overflow: hidden; display: flex;
}
.rt-wrap { background-color: #10141b; border: 1px solid #1e2530; border-radius: 10px; padding: 10px 12px; }
.rt-table { width: 100%; border-collapse: collapse; font-size: 12px; }
.rt-table th { color: #8b949e; font-weight: 600; text-align: left; padding: 6px 4px; border-bottom: 1px solid #1e2530; }
.rt-table td { padding: 5px 4px; border-bottom: 1px solid #171c26; }

.sb-row {
    display: flex; align-items: center; justify-content: space-between;
    padding: 10px 14px; min-height: 60px; border-radius: 12px;
    background-color: #11151c; border: 1px solid #1b2028; width: 100%; box-sizing: border-box;
    transition: transform 0.2s ease, background-color 0.2s ease, border-color 0.2s ease;
}
.sb-row:hover { transform: scale(1.016); background-color: #181e28; border-color: #00c805; box-shadow: 0 6px 18px rgba(0,0,0,0.35); }
.sb-left { display: flex; align-items: center; gap: 10px; width: 46%; min-width: 130px; }
.sb-logo-img { width: 36px; height: 36px; border-radius: 50%; object-fit: cover; background-color: #fff; border: 1px solid #2b3340; flex-shrink: 0; }
.sb-avatar-fallback {
    width: 36px; height: 36px; border-radius: 50%; display: flex; align-items: center;
    justify-content: center; font-weight: 800; font-size: 10.5px; color: #fff; flex-shrink: 0;
}
.sb-info { display: flex; flex-direction: column; overflow: hidden; }
.sb-ticker-line { display: flex; align-items: center; gap: 5px; }
.sb-ticker { font-size: 14.5px; font-weight: 700; color: #f0f3fa; line-height: 1.25; }
.sb-badge-c {
    display: inline-flex; align-items: center; justify-content: center;
    width: 15px; height: 15px; border-radius: 4px; background-color: #3b235a;
    color: #c792ea; font-size: 10px; font-weight: 800;
}
.sb-name { font-size: 11.5px; color: #8b949e; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; max-width: 210px; }
.sb-mid { width: 22%; display: flex; justify-content: center; align-items: center; }
.sb-right { width: 32%; text-align: right; line-height: 1.25; }
.sb-price { font-size: 14.5px; font-weight: 700; color: #f0f3fa; }
.sb-chg { font-size: 11.5px; font-weight: 600; }

.news-card {
    display: flex; justify-content: space-between; align-items: flex-start; gap: 12px;
    padding: 13px 14px; border-radius: 12px; background-color: #11151c;
    border: 1px solid #1b2028; margin-bottom: 10px;
    transition: transform 0.2s ease, border-color 0.2s ease, background-color 0.2s ease;
}
.news-card:hover { transform: scale(1.015); background-color: #161c26; border-color: #00c805; box-shadow: 0 6px 18px rgba(0,0,0,0.35); }
.news-body { flex: 1; min-width: 0; }
.news-title-link { display: block; font-size: 14px; font-weight: 700; color: #f0f3fa; text-decoration: none; line-height: 1.38; margin-bottom: 6px; }
.news-title-link:hover { color: #00c805; }
.news-meta { display: flex; align-items: center; gap: 6px; font-size: 11.5px; color: #8b949e; margin-bottom: 8px; }
.news-src-dot {
    width: 14px; height: 14px; border-radius: 4px; background-color: #1f4e78; color: #7cc4fa;
    display: inline-flex; align-items: center; justify-content: center; font-size: 9px; font-weight: 800; flex-shrink: 0;
}
.news-actions { display: flex; align-items: center; gap: 14px; font-size: 12px; color: #6e7681; }
.news-thumb { width: 96px; height: 64px; border-radius: 8px; object-fit: cover; border: 1px solid #242c3a; background-color: #171c26; flex-shrink: 0; }
.news-thumb-fallback {
    width: 96px; height: 64px; border-radius: 8px; border: 1px solid #242c3a;
    background: linear-gradient(135deg, #16202c 0%, #1c2838 100%); color: #8b949e;
    display: flex; align-items: center; justify-content: center; font-size: 11px; font-weight: 700; flex-shrink: 0;
}

.sb-box-card { background-color: #141920; border: 1px solid #222933; border-radius: 10px; padding: 11px 14px; }
.sb-box-title { color: #8b949e; font-size: 12px; font-weight: 600; margin-bottom: 6px; }
.sb-stat-line { display: flex; justify-content: space-between; font-size: 13px; padding: 2px 0; }

.chat-user {
    background-color: #1c2533; border: 1px solid #2e3d52; padding: 9px 13px;
    border-radius: 12px 12px 2px 12px; margin: 8px 0 4px auto; max-width: 85%; color: #f0f3fa; font-size: 13.5px;
}
.chat-ai {
    background-color: #161b22; border-left: 3px solid #00c805; padding: 11px 15px;
    border-radius: 4px 12px 12px 12px; margin: 4px 0 12px 0; color: #e6edf3; font-size: 13.5px;
}
.chat-ai-down {
    background-color: #191316; border-left: 3px solid #ff3b30; padding: 11px 15px;
    border-radius: 4px 12px 12px 12px; margin: 4px 0 12px 0; color: #e6edf3; font-size: 13.5px;
}
</style>
""", unsafe_allow_html=True)

load_dotenv()

def ambil_secret_aman(nama_key: str) -> str:
    val = os.getenv(nama_key, "").strip()
    if val:
        return val
    try:
        if nama_key in st.secrets:
            return str(st.secrets[nama_key]).strip()
    except Exception:
        pass
    return ""

groq_api_key = ambil_secret_aman("GROQ_API_KEY")
gemini_api_key = ambil_secret_aman("GEMINI_API_KEY")
app_password_aktif = ambil_secret_aman("APP_PASSWORD")
discord_webhook_url = ambil_secret_aman("DISCORD_WEBHOOK_URL")

# ================= PROTEKSI PASSWORD LOGIN SEDERHANA =================
if app_password_aktif:
    if "sudah_login_terminal" not in st.session_state:
        st.session_state.sudah_login_terminal = False

    if not st.session_state.sudah_login_terminal:
        st.markdown("""
        <div class="login-box-wrap">
            <div style="font-size:32px; margin-bottom:6px;">🔐</div>
            <div style="font-size:20px; font-weight:800; color:#f0f3fa;">Analisis Saham by Zariff</div>
            <div style="font-size:12.5px; color:#8b949e; margin-top:4px;">Masukkan Password Akses Pribadi untuk membuka terminal &amp; kuota AI.</div>
        </div>
        """, unsafe_allow_html=True)
        _, col_login_mid, _ = st.columns([1.2, 1.4, 1.2])
        with col_login_mid:
            with st.form("form_login_terminal"):
                pwd_input = st.text_input("Password Akses", type="password", placeholder="Ketik password...", label_visibility="collapsed")
                klik_login = st.form_submit_button("🔓 Buka Terminal", type="primary", use_container_width=True)
            if klik_login:
                if pwd_input == app_password_aktif:
                    st.session_state.sudah_login_terminal = True
                    st.rerun()
                else:
                    st.error("Password salah. Coba lagi.")
        st.stop()

gemini_client = (
    genai.Client(api_key=gemini_api_key, http_options=types.HttpOptions(timeout=60000))
    if (gemini_api_key and genai is not None and types is not None)
    else None
)

WIB_TZ = timezone(timedelta(hours=7))

HARI_ID_MAP = {
    0: "Senin", 1: "Selasa", 2: "Rabu", 3: "Kamis",
    4: "Jumat", 5: "Sabtu", 6: "Minggu"
}
BULAN_ID_MAP = {
    1: "Jan", 2: "Feb", 3: "Mar", 4: "Apr", 5: "Mei", 6: "Jun",
    7: "Jul", 8: "Agu", 9: "Sep", 10: "Okt", 11: "Nov", 12: "Des"
}

# Daftar tanggal merah / libur bursa BEI (format "YYYY-MM-DD")
LIBUR_BEI_SET = {
    "2026-12-25",  # Hari Raya Natal
}

def waktu_wib_sekarang() -> datetime:
    return datetime.now(WIB_TZ)

def _format_tgl_id(tgl: date) -> str:
    return f"{HARI_ID_MAP[tgl.weekday()]}, {tgl.day:02d} {BULAN_ID_MAP[tgl.month]} {tgl.year}"

def _is_hari_bursa_aktif(tgl: date) -> bool:
    return tgl.weekday() < 5 and tgl.isoformat() not in LIBUR_BEI_SET

def _hari_bursa_berikutnya(mulai_dari: date) -> date:
    calon = mulai_dari + timedelta(days=1)
    while not _is_hari_bursa_aktif(calon):
        calon += timedelta(days=1)
    return calon

# ================= INTEGRASI DISCORD WEBHOOK =================
def kirim_ke_discord(judul: str, isi_pesan: str, warna: int = 3066993) -> tuple:
    """Mengirim ringkasan screener atau analisis AI ke channel Discord pribadi."""
    url_dc = ambil_secret_aman("DISCORD_WEBHOOK_URL")
    if not url_dc:
        return False, "DISCORD_WEBHOOK_URL belum diisi di Streamlit Secrets."

    teks_bersih = str(isi_pesan or "").strip()
    if len(teks_bersih) > 3900:
        teks_bersih = teks_bersih[:3900] + "\n...(terpotong agar muat di Discord)"

    payload = {
        "username": "Bot Saham Zariff",
        "embeds": [
            {
                "title": str(judul)[:250],
                "description": teks_bersih,
                "color": warna,
                "footer": {
                    "text": f"Analisis Saham by Zariff • {waktu_wib_sekarang().strftime('%d %b %Y %H:%M WIB')}"
                }
            }
        ]
    }
    try:
        req = urllib.request.Request(
            url_dc,
            data=json.dumps(payload).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "User-Agent": "Mozilla/5.0"
            },
            method="POST"
        )
        with urllib.request.urlopen(req, timeout=12) as resp:
            if resp.status in (200, 204):
                return True, "Terkirim ke Discord!"
            return False, f"HTTP {resp.status}"
    except urllib.error.HTTPError as he:
        return False, f"HTTP Error {he.code}"
    except Exception as e:
        return False, str(e)

def format_laporan_screener_discord(paket_hasil: dict, top10_list: list, min_h: int, max_h: int, mode_turun: bool = False) -> str:
    parsed = paket_hasil.get("parsed") if isinstance(paket_hasil, dict) else {}
    if not isinstance(parsed, dict):
        parsed = {}
    ks = konteks_sesi_screener()

    baris = [f"**Rentang Filter:** Rp {min_h:,} – Rp {max_h:,} | **Update:** {paket_hasil.get('waktu', '-')}\n"]
    baris.append("**📋 Ringkasan Top 10 Emiten:**")
    for idx, item in enumerate(top10_list[:10], start=1):
        kd = item["ticker"]
        hrg = item["price"]
        pct = item["pct_day"]
        skor = item["skor_turun_total"] if mode_turun else item["skor_naik_total"]
        baris.append(f"`{idx:02d}.` **{kd}** — Rp {hrg:,.0f} ({pct:+.2f}%) | Skor: **{skor}** | RSI: {item['rsi']:.0f}")

    s2_list = parsed.get("top_sesi2") or []
    if s2_list:
        judul_s2 = f"⚠️ Paling Rawan Turun ({ks['label_short_1']})" if mode_turun else f"⚡ Top Pick ({ks['label_short_1']})"
        baris.append(f"\n**{judul_s2}:**")
        for p in s2_list[:3]:
            kd_p = str(p.get("kode", "")).upper()
            alasan_p = "; ".join(p.get("alasan") or [])
            baris.append(f"• **{kd_p}**: {alasan_p}")

    esok_list = parsed.get("top_esok") or []
    if esok_list:
        judul_es = f"🔻 Paling Rawan Turun ({ks['label_short_2']})" if mode_turun else f"🌅 Top Pick ({ks['label_short_2']})"
        baris.append(f"\n**{judul_es}:**")
        for p in esok_list[:3]:
            kd_p = str(p.get("kode", "")).upper()
            alasan_p = "; ".join(p.get("alasan") or [])
            baris.append(f"• **{kd_p}**: {alasan_p}")

    return "\n".join(baris)

def status_jam_bursa_bei() -> dict:
    now_wib = waktu_wib_sekarang()
    hari_ini = now_wib.date()
    hari = now_wib.weekday()
    detik_sekarang = now_wib.hour * 3600 + now_wib.minute * 60 + now_wib.second
    jam_str = now_wib.strftime("%H:%M:%S WIB")

    if not _is_hari_bursa_aktif(hari_ini):
        tgl_lanjut = _hari_bursa_berikutnya(hari_ini)
        lanjut_str = _format_tgl_id(tgl_lanjut)
        alasan_libur = "Akhir Pekan" if hari >= 5 else "Tanggal Merah / Libur Bursa"
        label_singkat = "🔴 MARKET TUTUP (Akhir Pekan)" if hari >= 5 else "🔴 MARKET TUTUP (Tanggal Merah)"
        return {
            "label": label_singkat,
            "bg": "#2b161a", "fg": "#ff8080",
            "sesi_aktif": "Sesi 1",
            "tanggal_lanjutan": tgl_lanjut,
            "info": (
                f"Pasar saham tutup ({alasan_libur} • {_format_tgl_id(hari_ini)}) dan akan dilanjutkan pada "
                f"{lanjut_str} pukul 09:00 WIB (Sesi 1) • {jam_str}"
            )
        }

    if hari == 4:
        sesi1_tutup = 11 * 3600 + 30 * 60
        sesi2_buka = 14 * 3600
    else:
        sesi1_tutup = 12 * 3600
        sesi2_buka = 13 * 3600 + 30 * 60

    pre_open = 8 * 3600 + 45 * 60
    sesi1_buka = 9 * 3600
    pre_close = 15 * 3600 + 49 * 60
    market_tutup = 16 * 3600 + 15 * 60

    def format_sisa_dtk(detik_target: int) -> str:
        sisa = max(0, detik_target - detik_sekarang)
        j, rem = divmod(sisa, 3600)
        m, d = divmod(rem, 60)
        if j > 0:
            return f"{j} jam {m} mnt {d:02d} dtk"
        if m > 0:
            return f"{m} mnt {d:02d} dtk"
        return f"{d} detik"

    sesi_berjalan = "Sesi 2" if detik_sekarang >= sesi2_buka else "Sesi 1"

    if detik_sekarang < pre_open:
        return {
            "label": "⏸ PRA-PEMBUKAAN • SESI 1",
            "bg": "#1c2432", "fg": "#9ecbff",
            "sesi_aktif": "Sesi 1",
            "tanggal_lanjutan": hari_ini,
            "info": f"Fokus Sesi 1 ({_format_tgl_id(hari_ini)}) • Pre-Opening dalam {format_sisa_dtk(pre_open)} (08:45 WIB) • {jam_str}"
        }
    if pre_open <= detik_sekarang < sesi1_buka:
        return {
            "label": "🟡 PRE-OPENING BEI • SESI 1",
            "bg": "#2d2312", "fg": "#f5a623",
            "sesi_aktif": "Sesi 1",
            "tanggal_lanjutan": hari_ini,
            "info": f"Pembukaan Sesi 1 dalam {format_sisa_dtk(sesi1_buka)} (09:00 WIB) • {jam_str}"
        }
    if sesi1_buka <= detik_sekarang < sesi1_tutup:
        return {
            "label": "🟢 SESI 1 AKTIF",
            "bg": "#122b18", "fg": "#00c805",
            "sesi_aktif": "Sesi 1",
            "tanggal_lanjutan": hari_ini,
            "info": f"Istirahat Sesi 1 dalam {format_sisa_dtk(sesi1_tutup)} • {jam_str}"
        }
    if sesi1_tutup <= detik_sekarang < sesi2_buka:
        return {
            "label": "☕ ISTIRAHAT SIANG BEI",
            "bg": "#262115", "fg": "#e3b341",
            "sesi_aktif": "Sesi 1",
            "tanggal_lanjutan": hari_ini,
            "info": f"Sesi 2 dibuka dalam {format_sisa_dtk(sesi2_buka)} • {jam_str}"
        }
    if sesi2_buka <= detik_sekarang < pre_close:
        return {
            "label": "🟢 SESI 2 AKTIF (Zona BSJP)",
            "bg": "#122b18", "fg": "#00c805",
            "sesi_aktif": "Sesi 2",
            "tanggal_lanjutan": hari_ini,
            "info": f"Pre-Closing dalam {format_sisa_dtk(pre_close)} (15:49 WIB) • {jam_str}"
        }
    if pre_close <= detik_sekarang < market_tutup:
        return {
            "label": "🟠 PRE-CLOSING & POST-TRADING",
            "bg": "#301e14", "fg": "#ff9e7d",
            "sesi_aktif": sesi_berjalan,
            "tanggal_lanjutan": _hari_bursa_berikutnya(hari_ini),
            "info": f"Penutupan penuh dalam {format_sisa_dtk(market_tutup)} (16:15 WIB) • {jam_str}"
        }

    tgl_lanjut = _hari_bursa_berikutnya(hari_ini)
    return {
        "label": "🔴 MARKET TUTUP",
        "bg": "#2b161a", "fg": "#ff8080",
        "sesi_aktif": "Sesi 1",
        "tanggal_lanjutan": tgl_lanjut,
        "info": f"Pasar saham tutup hari ini • Dilanjutkan Sesi 1 pada {_format_tgl_id(tgl_lanjut)} pukul 09:00 WIB • {jam_str}"
    }

def render_banner_jam_bursa_realtime():
    sesi_init = status_jam_bursa_bei()
    libur_json = json.dumps(sorted(list(LIBUR_BEI_SET)))

    html_banner = f"""
    <!DOCTYPE html>
    <html>
    <head>
    <meta charset="utf-8">
    <style>
      body {{
        margin: 0; padding: 0; background: transparent;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, sans-serif;
      }}
      .idx-banner {{
        display: flex; justify-content: space-between; align-items: center;
        flex-wrap: wrap; gap: 8px;
        background: linear-gradient(90deg, #131923 0%, #17202e 100%);
        border: 1px solid #253042; border-radius: 10px;
        padding: 7px 14px; font-size: 12.5px; color: #c9d1d9; box-sizing: border-box;
      }}
      .idx-left {{ display: flex; align-items: center; gap: 10px; flex-wrap: wrap; }}
      .idx-brand {{ font-size: 14px; font-weight: 800; color: #00c805; letter-spacing: 0.2px; }}
      .idx-pill {{
        display: inline-flex; align-items: center; gap: 6px;
        padding: 3px 10px; border-radius: 999px; font-weight: 700; font-size: 11.5px;
      }}
      .idx-info {{ font-variant-numeric: tabular-nums; }}
      .idx-note {{ color: #8b949e; font-size: 11.5px; }}
    </style>
    </head>
    <body>
      <div class="idx-banner">
        <div class="idx-left">
          <span class="idx-brand">📈 Analisis Saham by Zariff</span>
          <span style="color:#303a4b;">|</span>
          <span id="pill-status" class="idx-pill" style="background:{sesi_init['bg']}; color:{sesi_init['fg']};">{sesi_init['label']}</span>
          <span id="info-status" class="idx-info">{sesi_init['info']}</span>
        </div>
        <span class="idx-note">⭐ Watchlist tersimpan otomatis di URL (aman di-bookmark)</span>
      </div>

      <script>
        const LIBUR_SET = new Set({libur_json});
        const NAMA_HARI = ["Minggu", "Senin", "Selasa", "Rabu", "Kamis", "Jumat", "Sabtu"];
        const NAMA_BULAN = ["", "Jan", "Feb", "Mar", "Apr", "Mei", "Jun", "Jul", "Agu", "Sep", "Okt", "Nov", "Des"];

        function pad2(n) {{ return String(n).padStart(2, "0"); }}

        function getWibParts() {{
          const now = new Date();
          const parts = new Intl.DateTimeFormat("en-CA", {{
            timeZone: "Asia/Jakarta",
            year: "numeric", month: "2-digit", day: "2-digit",
            hour: "2-digit", minute: "2-digit", second: "2-digit",
            hour12: false
          }}).formatToParts(now);
          const map = {{}};
          for (const p of parts) map[p.type] = p.value;
          const y = parseInt(map.year, 10);
          const m = parseInt(map.month, 10);
          const d = parseInt(map.day, 10);
          const hh = parseInt(map.hour, 10);
          const mm = parseInt(map.minute, 10);
          const ss = parseInt(map.second, 10);
          const utcDate = new Date(Date.UTC(y, m - 1, d));
          const dow = utcDate.getUTCDay();
          const iso = `${{y}}-${{pad2(m)}}-${{pad2(d)}}`;
          return {{ y, m, d, hh, mm, ss, dow, iso, utcDate }};
        }}

        function formatTglId(utcDate) {{
          const hName = NAMA_HARI[utcDate.getUTCDay()];
          const d = pad2(utcDate.getUTCDate());
          const bName = NAMA_BULAN[utcDate.getUTCMonth() + 1];
          const y = utcDate.getUTCFullYear();
          return `${{hName}}, ${{d}} ${{bName}} ${{y}}`;
        }}

        function isHariBursaAktif(utcDate, iso) {{
          const dow = utcDate.getUTCDay();
          return dow >= 1 && dow <= 5 && !LIBUR_SET.has(iso);
        }}

        function hariBursaBerikutnya(utcDate) {{
          let cur = new Date(utcDate.getTime());
          for (let i = 0; i < 14; i++) {{
            cur = new Date(cur.getTime() + 86400000);
            const iso = `${{cur.getUTCFullYear()}}-${{pad2(cur.getUTCMonth()+1)}}-${{pad2(cur.getUTCDate())}}`;
            if (isHariBursaAktif(cur, iso)) return cur;
          }}
          return cur;
        }}

        function formatSisaDetik(targetSec, nowSec) {{
          const diff = Math.max(0, targetSec - nowSec);
          const j = Math.floor(diff / 3600);
          const m = Math.floor((diff % 3600) / 60);
          const s = diff % 60;
          if (j > 0) return `${{j}} jam ${{m}} mnt ${{pad2(s)}} dtk`;
          if (m > 0) return `${{m}} mnt ${{pad2(s)}} dtk`;
          return `${{s}} detik`;
        }}

        function updateBanner() {{
          const p = getWibParts();
          const jamStr = `${{pad2(p.hh)}}:${{pad2(p.mm)}}:${{pad2(p.ss)}} WIB`;
          const pill = document.getElementById("pill-status");
          const info = document.getElementById("info-status");
          if (!pill || !info) return;

          if (!isHariBursaAktif(p.utcDate, p.iso)) {{
            const nextDay = hariBursaBerikutnya(p.utcDate);
            const isWeekend = (p.dow === 0 || p.dow === 6);
            pill.textContent = isWeekend ? "🔴 MARKET TUTUP (Akhir Pekan)" : "🔴 MARKET TUTUP (Tanggal Merah)";
            pill.style.background = "#2b161a";
            pill.style.color = "#ff8080";
            info.textContent = `Pasar saham tutup (${{isWeekend ? "Akhir Pekan" : "Libur Bursa"}} • ${{formatTglId(p.utcDate)}}) • Lanjut ${{formatTglId(nextDay)}} 09:00 WIB • ${{jamStr}}`;
            return;
          }}

          const nowSec = p.hh * 3600 + p.mm * 60 + p.ss;
          const isFriday = (p.dow === 5);
          const preOpen = 8 * 3600 + 45 * 60;
          const sesi1Buka = 9 * 3600;
          const sesi1Tutup = isFriday ? (11 * 3600 + 30 * 60) : (12 * 3600);
          const sesi2Buka = isFriday ? (14 * 3600) : (13 * 3600 + 30 * 60);
          const preClose = 15 * 3600 + 49 * 60;
          const marketTutup = 16 * 3600 + 15 * 60;

          if (nowSec < preOpen) {{
            pill.textContent = "⏸ PRA-PEMBUKAAN • SESI 1";
            pill.style.background = "#1c2432"; pill.style.color = "#9ecbff";
            info.textContent = `Fokus Sesi 1 (${{formatTglId(p.utcDate)}}) • Pre-Opening dalam ${{formatSisaDetik(preOpen, nowSec)}} (08:45 WIB) • ${{jamStr}}`;
          }} else if (nowSec < sesi1Buka) {{
            pill.textContent = "🟡 PRE-OPENING BEI • SESI 1";
            pill.style.background = "#2d2312"; pill.style.color = "#f5a623";
            info.textContent = `Pembukaan Sesi 1 dalam ${{formatSisaDetik(sesi1Buka, nowSec)}} (09:00 WIB) • ${{jamStr}}`;
          }} else if (nowSec < sesi1Tutup) {{
            pill.textContent = "🟢 SESI 1 AKTIF";
            pill.style.background = "#122b18"; pill.style.color = "#00c805";
            info.textContent = `Istirahat Sesi 1 dalam ${{formatSisaDetik(sesi1Tutup, nowSec)}} • ${{jamStr}}`;
          }} else if (nowSec < sesi2Buka) {{
            pill.textContent = "☕ ISTIRAHAT SIANG BEI";
            pill.style.background = "#262115"; pill.style.color = "#e3b341";
            info.textContent = `Sesi 2 dibuka dalam ${{formatSisaDetik(sesi2Buka, nowSec)}} • ${{jamStr}}`;
          }} else if (nowSec < preClose) {{
            pill.textContent = "🟢 SESI 2 AKTIF (Zona BSJP)";
            pill.style.background = "#122b18"; pill.style.color = "#00c805";
            info.textContent = `Pre-Closing dalam ${{formatSisaDetik(preClose, nowSec)}} (15:49 WIB) • ${{jamStr}}`;
          }} else if (nowSec < marketTutup) {{
            pill.textContent = "🟠 PRE-CLOSING & POST-TRADING";
            pill.style.background = "#301e14"; pill.style.color = "#ff9e7d";
            info.textContent = `Penutupan penuh dalam ${{formatSisaDetik(marketTutup, nowSec)}} (16:15 WIB) • ${{jamStr}}`;
          }} else {{
            const nextDay = hariBursaBerikutnya(p.utcDate);
            pill.textContent = "🔴 MARKET TUTUP";
            pill.style.background = "#2b161a"; pill.style.color = "#ff8080";
            info.textContent = `Pasar saham tutup hari ini • Dilanjutkan Sesi 1 pada ${{formatTglId(nextDay)}} pukul 09:00 WIB • ${{jamStr}}`;
          }}
        }}

        updateBanner();
        setInterval(updateBanner, 1000);
      </script>
    </body>
    </html>
    """
    components.html(html_banner, height=48, scrolling=False)

def konteks_sesi_screener() -> dict:
    now_wib = waktu_wib_sekarang()
    hari_ini = now_wib.date()
    hari = now_wib.weekday()
    menit = now_wib.hour * 60 + now_wib.minute

    if not _is_hari_bursa_aktif(hari_ini):
        tgl_lanjut = _hari_bursa_berikutnya(hari_ini)
        lbl_hari = _format_tgl_id(tgl_lanjut)
        return {
            "label_short_1": f"Sesi 1 ({lbl_hari})",
            "label_short_2": f"Sesi 2 ({lbl_hari})",
            "fokus_pilihan": f"Sesi 1 {lbl_hari} / Sesi 2 {lbl_hari} / Keduanya",
            "instruksi_waktu": (
                f"Saat ini hari libur ({_format_tgl_id(hari_ini)}). "
                f"Bursa baru akan buka kembali pada {lbl_hari}. "
                f"Rujuklah ke {lbl_hari} (Sesi 1 & Sesi 2)."
            ),
        }

    sesi2_buka = (14 * 60) if hari == 4 else (13 * 60 + 30)
    sesi1_buka = 9 * 60

    if menit < sesi1_buka:
        return {
            "label_short_1": "Sesi 1 Hari Ini",
            "label_short_2": "Sesi 2 Hari Ini",
            "fokus_pilihan": "Sesi 1 Hari Ini / Sesi 2 Hari Ini / Keduanya",
            "instruksi_waktu": (
                f"Sekarang jam {now_wib.strftime('%H:%M:%S WIB')} ({_format_tgl_id(hari_ini)}), "
                f"Sesi 1 belum buka (buka 09:00 WIB). Fokuskan analisis untuk Sesi 1 dan Sesi 2 hari ini, "
                f"bukan 'Esok'."
            ),
        }
    if menit < sesi2_buka:
        return {
            "label_short_1": "Sesi 1 (Jalan)",
            "label_short_2": "Sesi 2 Hari Ini",
            "fokus_pilihan": "Sesi 1 / Sesi 2 Hari Ini / Keduanya",
            "instruksi_waktu": (
                f"Sekarang jam {now_wib.strftime('%H:%M:%S WIB')} ({_format_tgl_id(hari_ini)}) saat Sesi 1 berlangsung. "
                f"Fokuskan pada lanjutan Sesi 1 dan persiapan Sesi 2 hari ini."
            ),
        }

    tgl_besok = _hari_bursa_berikutnya(hari_ini)
    return {
        "label_short_1": "Sesi 2 (Jalan)",
        "label_short_2": f"Esok ({_format_tgl_id(tgl_besok)})",
        "fokus_pilihan": "Sesi 2 / Esok / Keduanya",
        "instruksi_waktu": (
            f"Sekarang jam {now_wib.strftime('%H:%M:%S WIB')} ({_format_tgl_id(hari_ini)}) saat/setelah Sesi 2. "
            f"Fokuskan pada Sesi 2 hari ini dan potensi hari bursa berikutnya ({_format_tgl_id(tgl_besok)})."
        ),
    }

DEFAULT_WATCHLIST = [
    "ATAP", "BIPI", "BNBR", "BSDE", "BULL",
    "BUMI", "DEWA", "HUMI", "INPC", "KOTA", "MDIA"
]

DEFAULT_TRENDING = [
    "KOTA", "TMPO", "BBRI", "BBCA", "BMRI", "BUMI",
    "BRPT", "TINS", "BRMS", "TLKM", "ADRO", "ANTM",
    "PTBA", "PGAS", "GOTO", "ASII", "INDF", "MDKA"
]

EXTRA_SCAN_POOL = [
    "ERAA", "ACES", "PWON", "CTRA", "SMRA", "ASRI", "ELSA", "ENRG",
    "DOID", "HRUM", "MBMA", "NCKL", "ASSA", "BIRD", "SMDR", "TMAS",
    "SOCI", "MNCN", "SCMA", "EMTK", "BUKA", "WIRG", "WIFI", "INET",
    "VKTR", "RAJA", "PNLF", "BGTG", "BJBR", "BJTM", "MAIN", "LSIP",
    "GZCO", "SSMS", "AALI", "MEDC", "PSAB", "ARCI", "DKFT", "NICL",
    "ESSA", "AGII", "SRTG", "MPMX", "AUTO", "GJTL", "IMAS", "WOOD",
    "MARK", "DRMA", "MTEL", "TOWR", "TBIG", "EXCL", "ISAT", "JPFA",
    "CPIN", "KLBF", "SIDO", "MYOR", "ICBP", "UNVR", "AMRT", "MAPI",
    "INKP", "TKIM", "ITMG", "UNTR", "AKRA", "BRIS", "BTPS", "ARTO",
    "BBTN", "BNGA", "NISP", "BDMN", "BBNI", "AMMN", "PANI", "CUAN"
]

NAMA_EMITEN_MAP = {
    "ATAP": "Trimitra Prawara Goldland Tbk.", "BIPI": "Astrindo Nusantara Infrastruktur Tbk.",
    "BNBR": "Bakrie & Brothers Tbk", "BSDE": "Bumi Serpong Damai Tbk.",
    "BULL": "Buana Lintas Lautan Tbk.", "BUMI": "Bumi Resources Tbk",
    "DEWA": "Darma Henwa Tbk", "HUMI": "Humpuss Maritim Internasional Tbk.",
    "INPC": "Bank Artha Graha Internasional Tbk.", "KOTA": "DMS Propertindo Tbk.",
    "MDIA": "Intermedia Capital Tbk", "TMPO": "Tempo Inti Media Tbk.",
    "BBCA": "Bank Central Asia Tbk.", "BBRI": "Bank Rakyat Indonesia (Persero) Tbk.",
    "BMRI": "Bank Mandiri (Persero) Tbk.", "BBNI": "Bank Negara Indonesia (Persero) Tbk.",
    "BRPT": "Barito Pacific Tbk.", "TINS": "Timah Tbk.",
    "BRMS": "Bumi Resources Minerals Tbk.", "TLKM": "Telkom Indonesia (Persero) Tbk.",
    "ADRO": "Alamtri Resources Indonesia Tbk.", "ANTM": "Aneka Tambang Tbk.",
    "PTBA": "Bukit Asam Tbk.", "PGAS": "Perusahaan Gas Negara Tbk.",
    "GOTO": "GoTo Gojek Tokopedia Tbk.", "ASII": "Astra International Tbk.",
    "INDF": "Indofood Sukses Makmur Tbk.", "ICBP": "Indofood CBP Sukses Makmur Tbk.",
    "MDKA": "Merdeka Copper Gold Tbk.", "ERAA": "Erajaya Swasembada Tbk.",
    "ACES": "Aspirasi Hidup Indonesia Tbk.", "PWON": "Pakuwon Jati Tbk.",
    "CTRA": "Ciputra Development Tbk.", "SMRA": "Summarecon Agung Tbk.",
    "ASRI": "Alam Sutera Realty Tbk.", "ELSA": "Elnusa Tbk.",
    "ENRG": "Energi Mega Persada Tbk.", "DOID": "Delta Dunia Makmur Tbk.",
    "HRUM": "Harum Energy Tbk.", "MBMA": "Merdeka Battery Materials Tbk.",
    "NCKL": "Trimegah Bangun Persada Tbk.", "ASSA": "Adi Sarana Armada Tbk.",
    "BIRD": "Blue Bird Tbk.", "SMDR": "Samudera Indonesia Tbk.",
    "TMAS": "Temas Tbk.", "SOCI": "Soechi Lines Tbk.",
    "MNCN": "Media Nusantara Citra Tbk.", "SCMA": "Surya Citra Media Tbk.",
    "EMTK": "Elang Mahkota Teknologi Tbk.", "BUKA": "Bukalapak.com Tbk.",
    "WIRG": "WIR ASIA Tbk.", "WIFI": "Solusi Sinergi Digital Tbk.",
    "INET": "Sinergi Inti Andalan Prima Tbk.", "VKTR": "VKTR Teknologi Mobilitas Tbk.",
    "RAJA": "Rukun Raharja Tbk.", "PNLF": "Panin Financial Tbk.",
    "BGTG": "Bank Ganesha Tbk.", "BJBR": "Bank Pembangunan Daerah Jawa Barat Tbk.",
    "BJTM": "Bank Pembangunan Daerah Jawa Timur Tbk.", "MAIN": "Malindo Feedmill Tbk.",
    "LSIP": "PP London Sumatra Indonesia Tbk.", "GZCO": "Gozco Plantations Tbk.",
    "SSMS": "Sawit Sumbermas Sarana Tbk.", "AALI": "Astra Agro Lestari Tbk.",
    "MEDC": "Medco Energi Internasional Tbk.", "PSAB": "J Resources Asia Pasifik Tbk.",
    "ARCI": "Archi Indonesia Tbk.", "DKFT": "Central Omega Resources Tbk.",
    "NICL": "PAM Mineral Tbk.", "ESSA": "ESSA Industries Indonesia Tbk.",
    "AGII": "Samator Indo Gas Tbk.", "SRTG": "Saratoga Investama Sedaya Tbk.",
    "MPMX": "Mitra Pinasthika Mustika Tbk.", "AUTO": "Astra Otoparts Tbk.",
    "GJTL": "Gajah Tunggal Tbk.", "IMAS": "Indomobil Sukses Internasional Tbk.",
    "WOOD": "Integra Indocabinet Tbk.", "MARK": "Mark Dynamics Indonesia Tbk.",
    "DRMA": "Dharma Polimetal Tbk.", "MTEL": "Dayamitra Telekomunikasi Tbk.",
    "TOWR": "Sarana Menara Nusantara Tbk.", "TBIG": "Tower Bersama Infrastructure Tbk.",
    "EXCL": "XL Axiata Tbk.", "ISAT": "Indosat Tbk.",
    "JPFA": "Japfa Comfeed Indonesia Tbk.", "CPIN": "Charoen Pokphand Indonesia Tbk.",
    "KLBF": "Kalbe Farma Tbk.", "SIDO": "Industri Jamu dan Farmasi Sido Muncul Tbk.",
    "MYOR": "Mayora Indah Tbk.", "UNVR": "Unilever Indonesia Tbk.",
    "AMRT": "Sumber Alfaria Trijaya Tbk.", "MAPI": "Mitra Adiperkasa Tbk.",
    "INKP": "Indah Kiat Pulp & Paper Tbk.", "TKIM": "Pabrik Kertas Tjiwi Kimia Tbk.",
    "ITMG": "Indo Tambangraya Megah Tbk.", "UNTR": "United Tractors Tbk.",
    "AKRA": "AKR Corporindo Tbk.", "BRIS": "Bank Syariah Indonesia Tbk.",
    "BTPS": "Bank BTPN Syariah Tbk.", "ARTO": "Bank Jago Tbk.",
    "BBTN": "Bank Tabungan Negara (Persero) Tbk.", "BNGA": "Bank CIMB Niaga Tbk.",
    "NISP": "Bank OCBC NISP Tbk.", "BDMN": "Bank Danamon Indonesia Tbk.",
    "AMMN": "Amman Mineral Internasional Tbk.", "PANI": "Pantai Indah Kapuk Dua Tbk.",
    "CUAN": "Petrindo Jaya Kreasi Tbk."
}

SAHAM_BADGE_C = {"KOTA", "BBCA"}
AVATAR_COLORS = ["#1f6feb", "#238636", "#8957e5", "#d29922", "#da3633", "#0969da", "#2ea043", "#bf4b8a", "#e16f24"]

def _angka_aman(val, fallback: float = 0.0) -> float:
    try:
        f = float(val)
        return f if math.isfinite(f) else float(fallback)
    except Exception:
        return float(fallback)

def warna_avatar(ticker: str) -> str:
    idx = int(hashlib.md5(ticker.encode()).hexdigest(), 16) % len(AVATAR_COLORS)
    return AVATAR_COLORS[idx]

def buat_html_logo_saham(ticker: str, ukuran: int = 36) -> str:
    tk = ticker.upper().strip()
    bg_av = warna_avatar(tk)
    font_sz = max(9, int(ukuran * 0.32))
    url_logo = f"https://assets.stockbit.com/logos/companies/{tk}.png"
    return (
        f'<img src="{url_logo}" class="sb-logo-img" style="width:{ukuran}px; height:{ukuran}px;" '
        f'onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';" />'
        f'<div class="sb-avatar-fallback" style="display:none; width:{ukuran}px; height:{ukuran}px; font-size:{font_sz}px; background-color:{bg_av};">{tk[:4]}</div>'
    )

def format_teks_ai_aman(teks: str) -> str:
    escaped = html.escape(str(teks or ""))
    escaped = re.sub(r"\*\*(.+?)\*\*", r"<b>\1</b>", escaped)
    return escaped

# ================= WATCHLIST PERMANEN VIA QUERY PARAMS =================

def muat_watchlist_awal() -> list:
    try:
        raw_wl = st.query_params.get("wl", "")
        if isinstance(raw_wl, list):
            raw_wl = ",".join(raw_wl)
        if raw_wl:
            parsed = [
                re.sub(r"[^A-Z0-9]", "", k.upper().strip())
                for k in str(raw_wl).split(",")
            ]
            valid = list(dict.fromkeys([k for k in parsed if 2 <= len(k) <= 6]))
            if valid:
                return valid
    except Exception:
        pass
    return DEFAULT_WATCHLIST.copy()

def simpan_watchlist_ke_url(daftar_wl: list):
    try:
        bersih = list(dict.fromkeys([k.upper().strip() for k in daftar_wl if k]))
        if bersih:
            st.query_params["wl"] = ",".join(bersih)
    except Exception:
        pass

# ================= FUNGSI PENGAMBIL DATA CEPAT (TTL 10 DETIK) =================

@st.cache_data(ttl=10)
def ambil_data_tunggal(ticker: str, timeframe: str = "1D"):
    if ticker != "^JKSE" and not ticker.endswith(".JK"):
        ticker = f"{ticker.upper()}.JK"
    saham = yf.Ticker(ticker)
    hist_6mo = saham.history(period="6mo", interval="1d")
    info = saham.info if ticker != "^JKSE" else {}

    tf_map = {"1D": ("1d", "1m"), "1W": ("5d", "15m"), "1M": ("1mo", "1d"), "3M": ("3mo", "1d"), "1Y": ("1y", "1d")}
    p, iv = tf_map.get(timeframe, ("1d", "1m"))
    df_chart = saham.history(period=p, interval=iv)
    if df_chart.empty:
        df_chart = hist_6mo.tail(30)
    return ticker, df_chart, hist_6mo, info

@st.cache_data(ttl=10)
def ambil_data_saham_batch(tickers: list):
    hasil = []
    if not tickers:
        return hasil
    jk_tickers = [f"{t}.JK" for t in tickers]
    try:
        df_intra = yf.download(jk_tickers, period="1d", interval="2m", group_by="ticker", progress=False, threads=True)
        df_daily = yf.download(jk_tickers, period="5d", interval="1d", group_by="ticker", progress=False, threads=True)
    except Exception:
        return hasil

    for t in tickers:
        tk = f"{t}.JK"
        try:
            sub_d = df_daily[tk].dropna(subset=["Close"]) if len(tickers) > 1 else df_daily.dropna(subset=["Close"])
            sub_i = df_intra[tk].dropna(subset=["Close"]) if len(tickers) > 1 else df_intra.dropna(subset=["Close"])
            if sub_d.empty:
                continue

            prev_close = _angka_aman(sub_d["Close"].iloc[-2] if len(sub_d) >= 2 else sub_d["Open"].iloc[-1], 0.0)
            raw_spark = sub_i["Close"].dropna().tolist() if len(sub_i) >= 3 else sub_d["Close"].dropna().tolist()
            series_spark = [_angka_aman(x, prev_close) for x in raw_spark if math.isfinite(_angka_aman(x, float("nan")))]
            if not series_spark or prev_close <= 0:
                continue
            last_price = series_spark[-1]
            diff = last_price - prev_close
            pct = (diff / prev_close) * 100 if prev_close else 0.0

            hasil.append({
                "ticker": t,
                "name": NAMA_EMITEN_MAP.get(t, f"{t} Tbk."),
                "price": last_price,
                "prev": prev_close,
                "diff": diff,
                "pct": pct,
                "spark": series_spark
            })
        except Exception:
            continue
    return hasil

def buat_svg_sparkline(prices: list, prev_close: float, diff: float) -> str:
    clean_prices = [_angka_aman(p, prev_close) for p in (prices or []) if math.isfinite(_angka_aman(p, float("nan")))]
    if len(clean_prices) < 2:
        return ""
    w, h, pad = 86, 26, 3
    all_vals = clean_prices + [_angka_aman(prev_close, clean_prices[0])]
    v_min, v_max = min(all_vals), max(all_vals)
    span = (v_max - v_min) if v_max != v_min else 1.0

    def to_y(val):
        return h - pad - ((val - v_min) / span) * (h - 2 * pad)

    pts = [f"{(i / (len(clean_prices) - 1)) * w:.1f},{to_y(val):.1f}" for i, val in enumerate(clean_prices)]
    y_prev = to_y(_angka_aman(prev_close, clean_prices[0]))
    stroke_color = "#00c805" if diff >= 0 else "#ff3b30"
    return f'<svg width="{w}" height="{h}" viewBox="0 0 {w} {h}" xmlns="http://www.w3.org/2000/svg"><line x1="0" y1="{y_prev:.1f}" x2="{w}" y2="{y_prev:.1f}" stroke="#5c6672" stroke-width="1" stroke-dasharray="3,3" /><polyline fill="none" stroke="{stroke_color}" stroke-width="1.6" stroke-linejoin="round" points="{" ".join(pts)}" /></svg>'

def hitung_indikator(hist: pd.DataFrame):
    close = hist["Close"].dropna() if not hist.empty and "Close" in hist.columns else pd.Series(dtype=float)
    if close.empty:
        return {"ma20": 0.0, "ma50": 0.0, "rsi": 50.0, "macd": 0.0, "macd_signal": 0.0, "support": 0.0, "resistance": 0.0, "vol_now": 0.0, "vol_avg": 0.0}

    last_c = _angka_aman(close.iloc[-1], 0.0)
    ma20 = _angka_aman(close.rolling(20, min_periods=1).mean().iloc[-1], last_c)
    ma50 = _angka_aman(close.rolling(50, min_periods=1).mean().iloc[-1], last_c)

    delta = close.diff()
    gain = delta.where(delta > 0, 0.0).rolling(14, min_periods=1).mean()
    loss = (-delta.where(delta < 0, 0.0)).rolling(14, min_periods=1).mean()
    rs = gain / loss.replace(0, math.nan)
    rsi = _angka_aman((100.0 - (100.0 / (1.0 + rs))).iloc[-1], 50.0)

    ema12 = close.ewm(span=12, adjust=False).mean()
    ema26 = close.ewm(span=26, adjust=False).mean()
    macd_line = ema12 - ema26
    macd = _angka_aman(macd_line.iloc[-1], 0.0)
    signal = _angka_aman(macd_line.ewm(span=9, adjust=False).mean().iloc[-1], 0.0)

    low_s = hist["Low"].dropna() if "Low" in hist.columns else pd.Series(dtype=float)
    high_s = hist["High"].dropna() if "High" in hist.columns else pd.Series(dtype=float)
    vol_s = hist["Volume"].dropna() if "Volume" in hist.columns else pd.Series(dtype=float)

    return {
        "ma20": ma20, "ma50": ma50, "rsi": rsi,
        "macd": macd, "macd_signal": signal,
        "support": _angka_aman(low_s.tail(20).min() if not low_s.empty else close.min(), last_c),
        "resistance": _angka_aman(high_s.tail(20).max() if not high_s.empty else close.max(), last_c),
        "vol_now": _angka_aman(vol_s.iloc[-1] if not vol_s.empty else 0.0, 0.0),
        "vol_avg": _angka_aman(vol_s.tail(20).mean() if not vol_s.empty else 0.0, 0.0)
    }

def fraksi_bei(harga: float) -> int:
    h = _angka_aman(harga, 100.0)
    if h < 200:
        return 1
    if h < 500:
        return 2
    if h < 2000:
        return 5
    if h < 5000:
        return 10
    return 25

def format_singkat_nilai(val: float) -> str:
    v = _angka_aman(val, 0.0)
    abs_v = abs(v)
    if abs_v >= 1e12:
        return f"{v/1e12:,.2f}T"
    if abs_v >= 1e9:
        return f"{v/1e9:,.2f}B"
    if abs_v >= 1e6:
        return f"{v/1e6:,.2f}M"
    if abs_v >= 1e3:
        return f"{v/1e3:,.1f}K"
    return f"{v:,.0f}"

def bangun_orderbook_dan_running_trade(kode: str, s_df: pd.DataFrame, s_hist: pd.DataFrame):
    hist_clean = s_hist.dropna(subset=["Close"]).copy() if not s_hist.empty and "Close" in s_hist.columns else pd.DataFrame()
    df_clean = s_df.dropna(subset=["Close"]).copy() if not s_df.empty and "Close" in s_df.columns else pd.DataFrame()

    fallback_price = 100.0
    if not df_clean.empty:
        fallback_price = _angka_aman(df_clean["Close"].iloc[-1], fallback_price)
    elif not hist_clean.empty:
        fallback_price = _angka_aman(hist_clean["Close"].iloc[-1], fallback_price)
    if fallback_price <= 0:
        fallback_price = 100.0

    if hist_clean.empty:
        prev_close = open_p = high_p = low_p = fallback_price
        vol_saham = 0.0
    else:
        last_row = hist_clean.iloc[-1]
        prev_close = _angka_aman(hist_clean["Close"].iloc[-2] if len(hist_clean) >= 2 else last_row.get("Open", fallback_price), fallback_price)
        if prev_close <= 0:
            prev_close = fallback_price
        open_p = _angka_aman(last_row.get("Open", prev_close), prev_close)
        last_price_raw = _angka_aman(df_clean["Close"].iloc[-1] if not df_clean.empty else last_row["Close"], prev_close)
        high_p = max(_angka_aman(last_row.get("High", last_price_raw), last_price_raw), last_price_raw, open_p)
        low_p = min(_angka_aman(last_row.get("Low", last_price_raw), last_price_raw), last_price_raw, open_p)
        vol_saham = _angka_aman(last_row.get("Volume", 0.0), 0.0)

    last_price = _angka_aman(df_clean["Close"].iloc[-1] if not df_clean.empty else prev_close, prev_close)
    total_lot = max(int(_angka_aman(vol_saham / 100.0, 1000.0)), 1000)
    typical_p = (high_p + low_p + last_price) / 3.0
    if not math.isfinite(typical_p) or typical_p <= 0:
        typical_p = max(last_price, 1.0)
    total_val = total_lot * 100 * typical_p

    ara_p = max(int(round(_angka_aman(prev_close * 1.25, last_price * 1.25))), int(round(_angka_aman(high_p, last_price))), 1)
    arb_p = max(1, int(round(_angka_aman(prev_close * 0.75, last_price * 0.75))))
    if arb_p >= ara_p:
        arb_p = max(1, ara_p - 10)

    seed_base = int(hashlib.md5(f"{kode}_{waktu_wib_sekarang().strftime('%Y%m%d')}".encode()).hexdigest(), 16)
    rasio_fbuy = 0.42 + ((seed_base % 25) / 100.0)
    f_buy_val = total_val * rasio_fbuy * 0.35
    f_sell_val = total_val * (1.0 - rasio_fbuy) * 0.32
    freq_total = max(int(total_lot / 350), 120)

    tick = fraksi_bei(max(last_price, 1.0))
    base_bid = min(ara_p, max(arb_p, int(round(_angka_aman(last_price, prev_close))) - tick))
    base_ask = max(arb_p, min(ara_p, int(round(_angka_aman(last_price, prev_close))) + tick))

    levels = 10
    bid_rows, ask_rows = [], []
    for i in range(levels):
        b_price = max(arb_p, base_bid - i * tick)
        a_price = min(ara_p, base_ask + i * tick)
        w_b = (levels - i) * (1.0 + ((seed_base >> (i * 2)) % 7) * 0.25)
        w_a = (levels - i) * (1.0 + ((seed_base >> (i * 2 + 1)) % 7) * 0.25)
        b_lot = max(int((total_lot * 0.22) * (w_b / 45.0)), 10)
        a_lot = max(int((total_lot * 0.22) * (w_a / 45.0)), 10)
        b_freq = max(int(b_lot / (45 + (i % 5) * 20)), 1) if i > 0 else None
        a_freq = max(int(a_lot / (45 + ((i + 2) % 5) * 20)), 1) if i > 0 else None
        bid_rows.append({"freq": b_freq, "lot": b_lot, "price": b_price})
        ask_rows.append({"price": a_price, "lot": a_lot, "freq": a_freq})

    max_lot_bar = max(max(r["lot"] for r in bid_rows), max(r["lot"] for r in ask_rows), 1)
    for r in bid_rows:
        r["pct_bar"] = min(100, int((r["lot"] / max_lot_bar) * 100))
    for r in ask_rows:
        r["pct_bar"] = min(100, int((r["lot"] / max_lot_bar) * 100))

    sum_bid_lot = sum(r["lot"] for r in bid_rows)
    sum_ask_lot = sum(r["lot"] for r in ask_rows)
    sum_bid_freq = sum(r["freq"] for r in bid_rows if r["freq"])
    sum_ask_freq = sum(r["freq"] for r in ask_rows if r["freq"])

    rt_items = []
    recent_closes = df_clean["Close"].tail(10).tolist() if not df_clean.empty else [last_price] * 10
    now_clock = waktu_wib_sekarang()
    for idx in range(10):
        raw_p = recent_closes[-(idx + 1)] if idx < len(recent_closes) else last_price
        p_item = _angka_aman(raw_p, last_price)
        chg_pct = ((p_item - prev_close) / prev_close * 100) if prev_close else 0.0
        is_buy = ((seed_base + idx * 7) % 10) < 6
        lot_item = max(int((total_lot / 800) * (1 + ((seed_base >> idx) % 6))), 1)
        if idx == 0 and (seed_base % 5 == 0):
            lot_item = max(lot_item * 12, 250)
        val_item = lot_item * 100 * p_item
        detik_mundur = max(0, 58 - idx * 6)
        rt_items.append({
            "time": f"{now_clock.strftime('%H:%M')}:{detik_mundur:02d}",
            "price": p_item, "chg_pct": chg_pct,
            "action": "Buy" if is_buy else "Sell",
            "lot": lot_item, "val_str": format_singkat_nilai(val_item)
        })

    return {
        "open": open_p, "prev": prev_close, "lot": total_lot,
        "high": high_p, "ara": ara_p, "val_str": format_singkat_nilai(total_val),
        "low": low_p, "arb": arb_p, "avg": typical_p,
        "fbuy_str": format_singkat_nilai(f_buy_val),
        "fsell_str": format_singkat_nilai(f_sell_val),
        "freq_str": format_singkat_nilai(freq_total),
        "bid_rows": bid_rows, "ask_rows": ask_rows,
        "sum_bid_lot": sum_bid_lot, "sum_ask_lot": sum_ask_lot,
        "sum_bid_freq": sum_bid_freq, "sum_ask_freq": sum_ask_freq,
        "rt_items": rt_items
    }

def buka_url_google_news(url_artikel: str) -> str:
    if "news.google.com" in url_artikel and "/articles/" in url_artikel:
        try:
            slug = url_artikel.split("/articles/", 1)[1].split("?", 1)[0]
            padded = slug + "=" * ((4 - len(slug) % 4) % 4)
            decoded = base64.urlsafe_b64decode(padded.encode("utf-8")).decode("latin1", errors="ignore")
            for u in re.findall(r'https?://[^\s"\'<>\\]+', decoded):
                if "news.google.com" not in u and "google.com" not in u:
                    return u
        except Exception:
            pass
    return url_artikel

@st.cache_data(ttl=600)
def ambil_og_image_artikel(url_artikel: str) -> str:
    if not url_artikel or not url_artikel.startswith("http"):
        return ""
    target_url = buka_url_google_news(url_artikel)
    try:
        req = urllib.request.Request(
            target_url,
            headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"}
        )
        with urllib.request.urlopen(req, timeout=3.0) as resp:
            final_url = resp.geturl()
            potongan = resp.read(98304).decode("utf-8", errors="ignore")
        pola_meta = [
            r'<meta[^>]+property=["\']og:image(?::secure_url)?["\'][^>]+content=["\']([^"\']+)["\']',
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image(?::secure_url)?["\']',
            r'<meta[^>]+name=["\']twitter:image(?::src)?["\'][^>]+content=["\']([^"\']+)["\']',
        ]
        for pola in pola_meta:
            cocok = re.search(pola, potongan, flags=re.IGNORECASE)
            if cocok:
                img_cand = html.unescape(cocok.group(1)).strip()
                if img_cand.startswith("//"):
                    img_cand = "https:" + img_cand
                elif img_cand.startswith("/"):
                    img_cand = urllib.parse.urljoin(final_url, img_cand)
                if img_cand.startswith("http") and not any(x in img_cand.lower() for x in ["logo", "icon", "sprite", "1x1", "blank", "avatar"]):
                    return img_cand
    except Exception:
        pass
    return ""

@st.cache_data(ttl=180)
def ambil_feed_berita_saham(kode_bersih: str = "IHSG", limit: int = 8, fetch_og: bool = True):
    kata_kunci = "saham emiten BEI IHSG hari ini" if kode_bersih == "IHSG" else f"saham {kode_bersih} IDX BEI"
    url_rss = f"https://news.google.com/rss/search?q={urllib.parse.quote(kata_kunci)}&hl=id&gl=ID&ceid=ID:id"
    items_out = []
    try:
        req = urllib.request.Request(url_rss, headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=4.0) as response:
            root = ET.fromstring(response.read())
        for item in root.findall('.//item')[:limit]:
            raw_title = item.find('title').text if item.find('title') is not None else ""
            link_url = item.find('link').text if item.find('link') is not None else "#"
            pub_date = item.find('pubDate').text if item.find('pubDate') is not None else ""
            src_el = item.find('source')
            sumber = src_el.text.strip() if (src_el is not None and src_el.text) else ""
            desc_raw = item.find('description').text if (item.find('description') is not None and item.find('description').text) else ""

            if not sumber and " - " in raw_title:
                judul, sumber = [x.strip() for x in raw_title.rsplit(" - ", 1)]
            else:
                judul = raw_title.rsplit(" - ", 1)[0].strip() if " - " in raw_title else raw_title.strip()

            img_url = ""
            if fetch_og:
                for child in item:
                    tag_lo = child.tag.lower()
                    if tag_lo.endswith("content") or tag_lo.endswith("thumbnail") or tag_lo == "enclosure":
                        cand = child.attrib.get("url", "").strip()
                        if cand.startswith("http"):
                            img_url = cand
                            break
                if not img_url and desc_raw:
                    img_match = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', desc_raw)
                    if img_match:
                        img_url = html.unescape(img_match.group(1)).strip()
                if not img_url and link_url.startswith("http"):
                    img_url = ambil_og_image_artikel(link_url)

            items_out.append({
                "title": judul,
                "link": link_url,
                "source": sumber if sumber else "Berita Pasar",
                "time": pub_date[:16].strip() if pub_date else "Terbaru",
                "image": img_url
            })
    except Exception:
        pass
    return items_out

def ambil_google_news_cepat(kode_bersih: str, limit: int = 4):
    daftar = ambil_feed_berita_saham(kode_bersih, limit=limit, fetch_og=False)
    if not daftar:
        return "Belum ada rilis berita terbaru di Google News."
    return "\n".join([f"- [{b['time']}] {b['title']} ({b['source']})" for b in daftar])

# ================= GRAFIK IHSG & CHART PRO =================

def buat_chart_area_saham(df: pd.DataFrame, perubahan: float, prev_close: float = None, height: int = 230, is_ihsg: bool = True):
    df_c = df.dropna(subset=["Close"]).copy() if not df.empty and "Close" in df.columns else pd.DataFrame()
    if df_c.empty:
        return go.Figure()

    warna_garis = "#00c805" if perubahan >= 0 else "#ff3b30"
    warna_fill = "rgba(0, 200, 5, 0.14)" if perubahan >= 0 else "rgba(255, 59, 48, 0.14)"

    val_max = _angka_aman(df_c['Close'].max(), 1.0)
    val_min = _angka_aman(df_c['Close'].min(), val_max)
    prev_safe = _angka_aman(prev_close, val_min) if prev_close is not None else None
    y_low = min(val_min, prev_safe) if prev_safe is not None else val_min
    y_high = max(val_max, prev_safe) if prev_safe is not None else val_max
    margin = (y_high - y_low) * 0.18 if y_high != y_low else max(y_high * 0.005, 1.0)

    fig = go.Figure()
    if prev_safe is not None and math.isfinite(prev_safe):
        fig.add_hline(y=prev_safe, line_dash="dash", line_color="#5c6672", line_width=1)

    fig.add_trace(go.Scatter(
        x=df_c.index, y=df_c['Close'], mode='lines',
        line=dict(color=warna_garis, width=2.2), fill='tozeroy', fillcolor=warna_fill,
        hovertemplate="Harga: %{y:,.2f}<br>%{x}<extra></extra>"
    ))
    fig.update_layout(
        template="plotly_dark", paper_bgcolor="rgba(0,0,0,0)", plot_bgcolor="rgba(0,0,0,0)",
        margin=dict(l=5, r=10, t=6, b=4), height=height, uirevision="live_area_chart",
        xaxis=dict(showgrid=False, zeroline=False),
        yaxis=dict(side="right", showgrid=True, gridcolor="#1b2028", range=[y_low - margin, y_high + margin], tickformat=",.2f" if is_ihsg else ",.0f"),
        showlegend=False
    )
    return fig

def buat_chart_candlestick_pro(hist: pd.DataFrame, ind: dict):
    df = hist.dropna(subset=["Close"]).tail(75).copy() if not hist.empty and "Close" in hist.columns else pd.DataFrame()
    if df.empty:
        return go.Figure()

    df['MA20'] = hist['Close'].rolling(20, min_periods=1).mean().reindex(df.index)
    df['MA50'] = hist['Close'].rolling(50, min_periods=1).mean().reindex(df.index)

    fig = make_subplots(rows=2, cols=1, shared_xaxes=True, vertical_spacing=0.04, row_heights=[0.78, 0.22])
    fig.add_trace(go.Candlestick(
        x=df.index, open=df['Open'], high=df['High'], low=df['Low'], close=df['Close'],
        increasing_line_color='#00c805', increasing_fillcolor='#00c805',
        decreasing_line_color='#ff3b30', decreasing_fillcolor='#ff3b30', name="OHLC"
    ), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA20'], mode='lines', line=dict(color='#f5a623', width=1.4), name="MA 20"), row=1, col=1)
    fig.add_trace(go.Scatter(x=df.index, y=df['MA50'], mode='lines', line=dict(color='#2962ff', width=1.4), name="MA 50"), row=1, col=1)
    fig.add_hline(y=_angka_aman(ind['resistance'], float(df['High'].max())), line_dash="dot", line_color="#ff3b30", annotation_text="Resistance", row=1, col=1)
    fig.add_hline(y=_angka_aman(ind['support'], float(df['Low'].min())), line_dash="dot", line_color="#00c805", annotation_text="Support", row=1, col=1)
    warna_vol = ['#00c805' if _angka_aman(c) >= _angka_aman(o) else '#ff3b30' for c, o in zip(df['Close'], df['Open'])]
    fig.add_trace(go.Bar(x=df.index, y=df['Volume'], marker_color=warna_vol, name="Volume", opacity=0.7), row=2, col=1)

    fig.update_layout(
        template="plotly_dark", paper_bgcolor="#131722", plot_bgcolor="#131722",
        margin=dict(l=10, r=10, t=20, b=10), height=360, uirevision="live_candle_chart",
        xaxis_rangeslider_visible=False, dragmode="drawline",
        newshape=dict(line_color="#00e5ff", line_width=2),
        yaxis=dict(side="right", showgrid=True, gridcolor="#1e222d"),
        yaxis2=dict(side="right", showgrid=False),
        legend=dict(orientation="h", y=1.04, x=0)
    )
    return fig

# ================= MESIN GROQ AI SUPER CEPAT + JSON MODE & AUTO-REPAIR =================

GROQ_MODELS_PRIORITAS = [
    "openai/gpt-oss-120b",
    "qwen/qwen3.8-27b",
    "openai/gpt-oss-20b"
]

@st.cache_data(ttl=300, show_spinner=False)
def _panggil_groq_cached(nama_model: str, prompt: str, max_tokens: int, json_mode: bool = False) -> str:
    url = "https://api.groq.com/openai/v1/chat/completions"
    payload = {
        "model": nama_model,
        "messages": [
            {
                "role": "system",
                "content": (
                    "Kamu adalah Kepala Riset Kuantitatif & Analis Pasar Modal Indonesia (BEI) pada platform Analisis Saham by Zariff. "
                    "Selalu jawab dalam Bahasa Indonesia yang tajam, terstruktur, padat, dan berbasis angka yang diberikan."
                )
            },
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "max_tokens": max_tokens
    }
    if json_mode:
        payload["response_format"] = {"type": "json_object"}

    req = urllib.request.Request(
        url,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {groq_api_key}",
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36"
        },
        method="POST"
    )
    with urllib.request.urlopen(req, timeout=55) as resp:
        data = json.loads(resp.read().decode("utf-8"))
        choices = data.get("choices") or []
        if choices:
            teks = (choices[0].get("message", {}).get("content") or "").strip()
            teks = re.sub(r"<think>.*?</think>", "", teks, flags=re.DOTALL).strip()
            return teks
    return ""

@st.cache_data(ttl=300, show_spinner=False)
def _panggil_gemini_cadangan_cached(prompt: str, max_tokens: int, json_mode: bool = False) -> tuple:
    if not gemini_client:
        return "", ""
    cfg_kwargs = {"temperature": 0.2, "max_output_tokens": max_tokens}
    if json_mode:
        cfg_kwargs["response_mime_type"] = "application/json"
    konfig = types.GenerateContentConfig(**cfg_kwargs)
    err_gem = ""
    for model_gem in ["gemini-3.5-flash-lite", "gemini-2.5-flash"]:
        try:
            response = gemini_client.models.generate_content(
                model=model_gem,
                contents=prompt,
                config=konfig
            )
            teks = (getattr(response, "text", None) or "").strip()
            if teks:
                return teks, f"Cadangan AI: {model_gem}"
        except Exception as e:
            err_gem = str(e)
            if "404" in err_gem or "NOT_FOUND" in err_gem:
                continue
            raise e
    raise RuntimeError(err_gem)

def panggil_ai_raw(prompt: str, max_tokens: int = 1600, json_mode: bool = False) -> tuple:
    if not groq_api_key and not gemini_client:
        return (
            "⚠️ **`GROQ_API_KEY` belum diisi di file `.env` atau *Secrets* Streamlit.**\n\n"
            "Ambil API Key gratis di `console.groq.com/keys`, masukkan `GROQ_API_KEY=gsk_...`, lalu *restart* aplikasi.",
            ""
        )

    error_terakhir = ""

    if groq_api_key:
        for nama_model in GROQ_MODELS_PRIORITAS:
            for mode_j in ([True, False] if json_mode else [False]):
                try:
                    teks = _panggil_groq_cached(nama_model, prompt, max_tokens, json_mode=mode_j)
                    if teks:
                        return teks, f"Groq AI: {nama_model}"
                except urllib.error.HTTPError as he:
                    body_err = ""
                    try:
                        body_err = he.read().decode("utf-8", errors="ignore")
                    except Exception:
                        pass
                    error_terakhir = f"[Groq {nama_model} HTTP {he.code}] {body_err[:200]}"
                    if he.code == 400 and mode_j:
                        continue
                    if he.code in (429, 503, 504):
                        time.sleep(1.0)
                        break
                    if he.code == 401:
                        break
                    break
                except Exception as e:
                    error_terakhir = f"[Groq {nama_model}] {e}"
                    break
            if "401" in error_terakhir:
                break
    else:
        error_terakhir = "[Groq] GROQ_API_KEY belum terbaca"

    if gemini_client:
        try:
            teks_gem, label_gem = _panggil_gemini_cadangan_cached(prompt, max_tokens, json_mode=json_mode)
            if teks_gem:
                return teks_gem, label_gem
        except Exception as eg:
            error_terakhir = f"{error_terakhir} | [Gemini] {eg}"

    if "401" in error_terakhir or "invalid_api_key" in error_terakhir.lower():
        return "⚠️ **API Key Groq Tidak Valid (Error 401).** Periksa kembali `GROQ_API_KEY` di `.env` / *Secrets*.", ""
    if "429" in error_terakhir or "rate_limit" in error_terakhir.lower():
        return (
            "⚠️ **Batas Kecepatan Token Per Menit (TPM) Groq Tercapai.**\n\n"
            "Tunggu **30–60 detik** lalu klik tombol analisis sekali lagi.\n\n"
            f"Detail: `{error_terakhir[:220]}`",
            ""
        )
    return f"⚠️ Gagal terhubung ke layanan AI.\n\nDetail error: `{error_terakhir[:260]}`", ""

def panggil_ai_aman(prompt: str, max_tokens: int = 1600) -> str:
    teks, label_model = panggil_ai_raw(prompt, max_tokens=max_tokens, json_mode=False)
    if label_model and not teks.startswith("⚠️"):
        return f"{teks}\n\n---\n*⚡ {label_model} • Analisis Saham by Zariff*"
    return teks

def _kumpulkan_objek_json_valid(bagian_teks: str) -> list:
    hasil_obj = []
    if not bagian_teks:
        return hasil_obj
    n = len(bagian_teks)
    i = 0
    while i < n:
        if bagian_teks[i] == "{":
            depth = 0
            in_str = False
            esc = False
            end_pos = -1
            for j in range(i, n):
                ch = bagian_teks[j]
                if esc:
                    esc = False
                    continue
                if ch == "\\" and in_str:
                    esc = True
                    continue
                if ch == '"':
                    in_str = not in_str
                    continue
                if not in_str:
                    if ch == "{":
                        depth += 1
                    elif ch == "}":
                        depth -= 1
                        if depth == 0:
                            end_pos = j
                            break
            if end_pos != -1:
                potongan = bagian_teks[i:end_pos + 1]
                try:
                    obj = json.loads(potongan)
                    if isinstance(obj, dict) and obj.get("kode"):
                        hasil_obj.append(obj)
                except Exception:
                    pass
                i = end_pos + 1
                continue
        i += 1
    return hasil_obj

def _ekstrak_json_ai(teks: str):
    if not teks:
        return None
    bersih = teks.strip()
    if "```" in bersih:
        m_blk = re.search(r"```(?:json)?\s*(\{.*)\s*```", bersih, flags=re.DOTALL | re.IGNORECASE)
        if m_blk:
            bersih = m_blk.group(1).strip()
        else:
            bersih = re.sub(r"^```(?:json)?\s*", "", bersih, flags=re.IGNORECASE).strip()

    start_idx = bersih.find("{")
    if start_idx == -1:
        return None
    kandidat = bersih[start_idx:]

    end_idx = kandidat.rfind("}")
    if end_idx > 0:
        try:
            obj_full = json.loads(kandidat[:end_idx + 1])
            if isinstance(obj_full, dict) and obj_full.get("ringkasan_tabel"):
                return obj_full
        except Exception:
            pass

    def ambil_segmen_key(src: str, key_nama: str, next_keys: list) -> str:
        m = re.search(rf'"{key_nama}"\s*:\s*\[', src)
        if not m:
            return ""
        mulai = m.end()
        batas = len(src)
        for nk in next_keys:
            mn = re.search(rf'"{nk}"\s*:\s*\[', src[mulai:])
            if mn:
                batas = min(batas, mulai + mn.start())
        return src[mulai:batas]

    seg_tbl = ambil_segmen_key(kandidat, "ringkasan_tabel", ["top_sesi2", "top_esok"])
    seg_s2 = ambil_segmen_key(kandidat, "top_sesi2", ["top_esok"])
    seg_esok = ambil_segmen_key(kandidat, "top_esok", [])

    tbl_items = _kumpulkan_objek_json_valid(seg_tbl)
    s2_items = _kumpulkan_objek_json_valid(seg_s2)
    esok_items = _kumpulkan_objek_json_valid(seg_esok)

    if tbl_items:
        return {
            "ringkasan_tabel": tbl_items,
            "top_sesi2": s2_items,
            "top_esok": esok_items
        }
    return None

def buat_konteks_saham(kode: str, data_ihsg: dict, data_saham: dict, info: dict, berita_ihsg: str, berita_saham: str) -> str:
    ks = konteks_sesi_screener()
    return f"""
    Waktu WIB: {waktu_wib_sekarang().strftime('%A, %d %b %Y %H:%M:%S WIB')} | {ks['instruksi_waktu']}
    IHSG (^JKSE): {_angka_aman(data_ihsg.get('harga', 0)):,.2f} ({_angka_aman(data_ihsg.get('pct', 0)):+.2f}%) | MA20: {_angka_aman(data_ihsg.get('ind', {}).get('ma20', 0)):,.2f} | RSI: {_angka_aman(data_ihsg.get('ind', {}).get('rsi', 0)):.1f} | Sup: {_angka_aman(data_ihsg.get('ind', {}).get('support', 0)):,.2f} | Res: {_angka_aman(data_ihsg.get('ind', {}).get('resistance', 0)):,.2f}
    Berita IHSG:
    {berita_ihsg}

    Saham {kode} ({info.get('longName', kode)}): Harga Rp {_angka_aman(data_saham['harga']):,.0f} ({_angka_aman(data_saham['pct']):+.2f}%) | PER: {info.get('trailingPE', 'N/A')} | PBV: {info.get('priceToBook', 'N/A')} | ROE: {info.get('returnOnEquity', 'N/A')} | MA20: Rp {_angka_aman(data_saham['ind']['ma20']):,.0f} | MA50: Rp {_angka_aman(data_saham['ind']['ma50']):,.0f} | RSI: {_angka_aman(data_saham['ind']['rsi']):.1f} | MACD: {_angka_aman(data_saham['ind']['macd']):.2f} | Vol: {_angka_aman(data_saham['ind']['vol_now']):,.0f} (Avg20: {_angka_aman(data_saham['ind']['vol_avg']):,.0f}) | Sup: Rp {_angka_aman(data_saham['ind']['support']):,.0f} | Res: Rp {_angka_aman(data_saham['ind']['resistance']):,.0f}
    Berita {kode}:
    {berita_saham}
    """

def jalankan_prediksi_ai(kode: str, konteks_data: str) -> str:
    ks = konteks_sesi_screener()
    prompt = f"""
    Buat analisis saham ringkas, padat, dan tajam dalam Bahasa Indonesia berdasarkan data berikut:
    {konteks_data}

    Konteks waktu bursa: {ks['instruksi_waktu']}

    Format output:
    ### 1. Prediksi IHSG (1–5 Hari Bursa)
- **Probabilitas:** [X% Naik vs Y% Turun]
- **Inti Analisis:** (1–2 kalimat tajam)

    ### 2. Prediksi Saham {kode}
- **Probabilitas:** [X% Naik vs Y% Turun]
- **Teknikal & Volume:** (1–2 kalimat)
- **Fundamental & Berita:** (1–2 kalimat)
- **Bullish / Bearish Case:** (singkat)

    ### 3. Strategi Trading
- **Entry:** | **TP:** | **Cut Loss:**
    *(Catatan singkat: analisis bersifat probabilistik, bukan ajakan mutlak membeli/menjual).*
    """
    return panggil_ai_aman(prompt, max_tokens=1600)

def jawab_pertanyaan_ai(kode: str, pertanyaan: str, konteks_data: str, riwayat_chat: list) -> str:
    ks = konteks_sesi_screener()
    riwayat_teks = "\n".join([f"{m['role'].upper()}: {m['text']}" for m in riwayat_chat[-3:]])
    prompt = f"""
    Jawab pertanyaan pengguna tentang saham {kode} secara lugas, tuntas, dan berbasis data berikut dalam Bahasa Indonesia:
    Konteks waktu bursa: {ks['instruksi_waktu']}
    {konteks_data}
    Riwayat singkat:
    {riwayat_teks}
    Pertanyaan: "{pertanyaan}"
    """
    return panggil_ai_aman(prompt, max_tokens=2200)

# ================= POP-UP MODAL JENDELA SAHAM (@st.dialog) =================

@st.dialog("📈 Analisis Saham by Zariff — Riset & Tanya AI", width="large")
def popup_detail_saham(kode: str, ihsg_paket: dict):
    _, s_df, s_hist, s_info = ambil_data_tunggal(kode, "1D")
    hist_ok = s_hist.dropna(subset=["Close"]) if not s_hist.empty and "Close" in s_hist.columns else pd.DataFrame()
    df_ok = s_df.dropna(subset=["Close"]) if not s_df.empty and "Close" in s_df.columns else pd.DataFrame()

    if hist_ok.empty and df_ok.empty:
        st.error(f"Kode saham **{kode}** tidak ditemukan atau data kosong di BEI.")
        return

    s_last = _angka_aman(df_ok['Close'].iloc[-1] if not df_ok.empty else hist_ok['Close'].iloc[-1], 0.0)
    s_prev = _angka_aman(hist_ok['Close'].iloc[-2] if len(hist_ok) >= 2 else (hist_ok['Open'].iloc[-1] if not hist_ok.empty else s_last), s_last)
    s_diff = s_last - s_prev
    s_pct = (s_diff / s_prev) * 100 if s_prev else 0.0
    ind_saham = hitung_indikator(hist_ok if not hist_ok.empty else df_ok)
    warna_s = "#00c805" if s_diff >= 0 else "#ff3b30"
    logo_popup = buat_html_logo_saham(kode, ukuran=40)

    head_left, head_right = st.columns([3.5, 1.3])
    with head_left:
        st.markdown(
            f'<div style="display:flex; align-items:center; gap:10px;">{logo_popup}'
            f'<div><span style="font-size:20px; font-weight:800;">{kode}</span> '
            f'<span style="font-size:18px; font-weight:800; margin-left:6px;">Rp {s_last:,.0f}</span> '
            f'<span style="color:{warna_s}; font-size:13px; font-weight:700;">({s_diff:+,.0f} | {s_pct:+.2f}%)</span><br>'
            f'<span style="color:#8b949e; font-size:12px;">{s_info.get("longName", NAMA_EMITEN_MAP.get(kode, kode))}</span></div></div>',
            unsafe_allow_html=True
        )
    with head_right:
        if kode not in st.session_state.watchlist:
            if st.button("⭐ + Watchlist", key=f"wl_add_{kode}", use_container_width=True):
                st.session_state.watchlist.insert(0, kode)
                simpan_watchlist_ke_url(st.session_state.watchlist)
                st.toast(f"⭐ {kode} disimpan permanen ke Watchlist!", icon="✅")
                st.rerun()
        else:
            if st.button("🗑️ Hapus Watchlist", key=f"wl_del_{kode}", use_container_width=True):
                if len(st.session_state.watchlist) > 1:
                    st.session_state.watchlist.remove(kode)
                    simpan_watchlist_ke_url(st.session_state.watchlist)
                    st.toast(f"🗑️ {kode} dihapus dari Watchlist")
                    st.rerun()
                else:
                    st.toast("⚠️ Minimal 1 saham harus ada di Watchlist")

    t_ov, t_ob, t_cb, t_ai = st.tabs(["📊 Overview", "📋 Orderbook & Running Trade", "🕯️ Chart Pro", "🧠 Analisis & Tanya AI"])

    key_analisis = f"hasil_analisis_{kode}"
    key_chat = f"riwayat_chat_{kode}"
    if key_analisis not in st.session_state:
        st.session_state[key_analisis] = ""
    if key_chat not in st.session_state:
        st.session_state[key_chat] = []

    def render_isi_overview():
        _, cur_df, cur_hist, cur_info = ambil_data_tunggal(kode, "1D")
        c_hist = cur_hist.dropna(subset=["Close"]) if not cur_hist.empty and "Close" in cur_hist.columns else pd.DataFrame()
        c_df = cur_df.dropna(subset=["Close"]) if not cur_df.empty and "Close" in cur_df.columns else pd.DataFrame()
        if c_hist.empty and c_df.empty:
            return
        cur_last = _angka_aman(c_df['Close'].iloc[-1] if not c_df.empty else c_hist['Close'].iloc[-1], 0.0)
        cur_prev = _angka_aman(c_hist['Close'].iloc[-2] if len(c_hist) >= 2 else (c_hist['Open'].iloc[-1] if not c_hist.empty else cur_last), cur_last)
        cur_diff = cur_last - cur_prev
        cur_ind = hitung_indikator(c_hist if not c_hist.empty else c_df)

        st.caption(f"⏱️ Cek data tiap 10 detik • Terakhir dicek: {waktu_wib_sekarang().strftime('%H:%M:%S WIB')}")
        st.plotly_chart(buat_chart_area_saham(c_df if not c_df.empty else c_hist, cur_diff, cur_prev, height=205, is_ihsg=False), use_container_width=True)

        per_val, pbv_val, roe_val = cur_info.get("trailingPE"), cur_info.get("priceToBook"), cur_info.get("returnOnEquity")
        per_str = f"{per_val:.2f}x" if isinstance(per_val, (int, float)) and math.isfinite(per_val) and 0 < per_val < 500 else "N/A"
        pbv_str = f"{pbv_val:.2f}x" if isinstance(pbv_val, (int, float)) and math.isfinite(pbv_val) and 0 < pbv_val < 200 else "N/A"
        roe_str = f"{roe_val*100:.1f}%" if isinstance(roe_val, (int, float)) and math.isfinite(roe_val) else "N/A"

        st.markdown(f"""
        <div class="popup-stat-grid">
            <div class="popup-stat-card"><div class="popup-stat-label">PER</div><div class="popup-stat-val">{per_str}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">PBV</div><div class="popup-stat-val">{pbv_str}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">ROE</div><div class="popup-stat-val" style="color:#00c805;">{roe_str}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">RSI (14)</div><div class="popup-stat-val" style="color:#f5a623;">{_angka_aman(cur_ind['rsi'], 50.0):.1f}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">Support (20H)</div><div class="popup-stat-val" style="color:#00c805;">Rp {_angka_aman(cur_ind['support']):,.0f}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">Resistance (20H)</div><div class="popup-stat-val" style="color:#ff3b30;">Rp {_angka_aman(cur_ind['resistance']):,.0f}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">MA 20</div><div class="popup-stat-val">Rp {_angka_aman(cur_ind['ma20']):,.0f}</div></div>
            <div class="popup-stat-card"><div class="popup-stat-label">Volume Hari Ini</div><div class="popup-stat-val">{_angka_aman(cur_ind['vol_now'])/1e6:,.1f}M</div></div>
        </div>
        """, unsafe_allow_html=True)

    def render_isi_orderbook():
        _, cur_df, cur_hist, _ = ambil_data_tunggal(kode, "1D")
        c_hist = cur_hist.dropna(subset=["Close"]) if not cur_hist.empty and "Close" in cur_hist.columns else pd.DataFrame()
        c_df = cur_df.dropna(subset=["Close"]) if not cur_df.empty and "Close" in cur_df.columns else pd.DataFrame()
        if c_hist.empty and c_df.empty:
            return
        ob = bangun_orderbook_dan_running_trade(kode, c_df, c_hist)
        st.caption(f"⏱️ Cek tiap 10 detik ({waktu_wib_sekarang().strftime('%H:%M:%S WIB')}) • Estimasi Bid/Ask & Running Trade dari data yfinance.")

        st.markdown(f"""
        <div class="ob-meta-grid">
            <div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Open</span><span class="ob-meta-val" style="color:#00c805;">{ob['open']:,.0f}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">High</span><span class="ob-meta-val" style="color:#00c805;">{ob['high']:,.0f}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Low</span><span class="ob-meta-val" style="color:#ff4d4f;">{ob['low']:,.0f}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">F Buy</span><span class="ob-meta-val" style="color:#00c805;">{ob['fbuy_str']}</span></div>
            </div>
            <div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Prev</span><span class="ob-meta-val">{ob['prev']:,.0f}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">ARA</span><span class="ob-meta-val" style="color:#00c805;">{ob['ara']:,}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">ARB</span><span class="ob-meta-val" style="color:#ff4d4f;">{ob['arb']:,}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">F Sell</span><span class="ob-meta-val" style="color:#ff4d4f;">{ob['fsell_str']}</span></div>
            </div>
            <div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Lot</span><span class="ob-meta-val" style="color:#ff4d4f;">{format_singkat_nilai(ob['lot'])}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Val</span><span class="ob-meta-val" style="color:#ff4d4f;">{ob['val_str']}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Avg</span><span class="ob-meta-val" style="color:#00c805;">{ob['avg']:,.0f}</span></div>
                <div class="ob-meta-row"><span class="ob-meta-lbl">Freq</span><span class="ob-meta-val" style="color:#00c805;">{ob['freq_str']}</span></div>
            </div>
        </div>
        """, unsafe_allow_html=True)

        rows_html = []
        for idx in range(len(ob["bid_rows"])):
            b, a = ob["bid_rows"][idx], ob["ask_rows"][idx]
            b_freq_txt = f'<span style="color:#2ea8ff; font-weight:600;">{b["freq"]:,}</span>' if b["freq"] else '<span style="color:#6e7681;">-</span>'
            a_freq_txt = f'<span style="color:#2ea8ff; font-weight:600;">{a["freq"]:,}</span>' if a["freq"] else '<span style="color:#6e7681;">-</span>'
            b_col_color = "#ff4d4f" if b["price"] < ob["prev"] else ("#00c805" if b["price"] > ob["prev"] else "#e6edf3")
            a_col_color = "#00c805" if a["price"] > ob["prev"] else ("#ff4d4f" if a["price"] < ob["prev"] else "#e6edf3")
            rows_html.append(
                f"<tr><td style='text-align:left;'>{b_freq_txt}</td>"
                f"<td style='text-align:right; color:#e6edf3; font-weight:600;'>{b['lot']:,}<div class='ob-bar-bg'><div class='ob-bar-bid' style='width:{b['pct_bar']}%;'></div></div></td>"
                f"<td style='text-align:center; color:{b_col_color}; font-weight:700; border-right:1px solid #222a36;'>{b['price']:,}</td>"
                f"<td style='text-align:center; color:{a_col_color}; font-weight:700;'>{a['price']:,}</td>"
                f"<td style='text-align:left; color:#e6edf3; font-weight:600;'>{a['lot']:,}<div class='ob-bar-bg'><div class='ob-bar-ask' style='width:{a['pct_bar']}%;'></div></div></td>"
                f"<td style='text-align:right;'>{a_freq_txt}</td></tr>"
            )

        total_bid_ask_lot = max(ob["sum_bid_lot"] + ob["sum_ask_lot"], 1)
        bid_pct_bar = int((ob["sum_bid_lot"] / total_bid_ask_lot) * 100)
        st.markdown(f"""
        <div class="ob-table-wrap"><table class="ob-table">
            <thead><tr><th style="text-align:left;">Freq</th><th style="text-align:right;">Lot</th><th style="text-align:center; border-right:1px solid #222a36;">Bid</th><th style="text-align:center;">Ask</th><th style="text-align:left;">Lot</th><th style="text-align:right;">Freq</th></tr></thead>
            <tbody>{"".join(rows_html)}</tbody>
        </table></div>
        <div class="ob-sum-bar">
            <div><span style="color:#2ea8ff; margin-right:8px;">{ob['sum_bid_freq']:,}</span><span>{ob['sum_bid_lot']:,}</span></div>
            <div class="ob-ratio-track"><div style="width:{bid_pct_bar}%; background-color:#2ea8ff; height:100%;"></div></div>
            <div><span>{ob['sum_ask_lot']:,}</span><span style="color:#2ea8ff; margin-left:8px;">{ob['sum_ask_freq']:,}</span></div>
        </div>
        """, unsafe_allow_html=True)

        rt_rows_html = []
        for item_rt in ob["rt_items"]:
            act_color = "#00c805" if item_rt["action"] == "Buy" else "#ff4d4f"
            chg_c = item_rt["chg_pct"]
            p_color = "#00c805" if chg_c > 0 else ("#ff4d4f" if chg_c < 0 else "#e6edf3")
            rt_rows_html.append(
                f"<tr><td style='color:#e6edf3;'>{item_rt['time']}</td>"
                f"<td style='color:{p_color}; font-weight:700;'>{item_rt['price']:,.0f} ({chg_c:+.2f}%)</td>"
                f"<td style='color:{act_color}; font-weight:700;'>{item_rt['action']}</td>"
                f"<td style='color:#e6edf3; font-weight:600;'>{item_rt['lot']:,}</td>"
                f"<td style='color:{act_color}; font-weight:700;'>{item_rt['val_str']}</td></tr>"
            )
        st.markdown(f"""
        <div class="rt-wrap">
            <div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:6px;">
                <span style="font-size:14px; font-weight:700; color:#f0f3fa;">Running Trade</span>
                <span style="font-size:12px; color:#8b949e; background:#161c26; padding:3px 9px; border-radius:6px; border:1px solid #242d3b;">📅 {waktu_wib_sekarang().strftime('%d %b %y')}</span>
            </div>
            <table class="rt-table"><thead><tr><th>Time</th><th>Price</th><th>Action</th><th>Lot</th><th>Val</th></tr></thead><tbody>{"".join(rt_rows_html)}</tbody></table>
        </div>
        """, unsafe_allow_html=True)

    with t_ov:
        if hasattr(st, "fragment") and live_mode:
            @st.fragment(run_every=10)
            def ov_live_frag():
                render_isi_overview()
            ov_live_frag()
        else:
            render_isi_overview()

    with t_ob:
        if hasattr(st, "fragment") and live_mode:
            @st.fragment(run_every=10)
            def ob_live_frag():
                render_isi_orderbook()
            ob_live_frag()
        else:
            render_isi_orderbook()

    with t_cb:
        col_tf_cb, col_ref_cb = st.columns([3.2, 1])
        with col_tf_cb:
            st.caption("Candlestick harian otomatis mengikuti jam bursa BEI (09.00 – 16.00 WIB).")
        with col_ref_cb:
            if st.button("🔄 Update Candle", key=f"upd_c_{kode}", use_container_width=True):
                st.cache_data.clear()
        config_toolbar = {"modeBarButtonsToAdd": ["drawline", "drawopenpath", "drawrect", "eraseshape"], "displaylogo": False}
        st.plotly_chart(buat_chart_candlestick_pro(s_hist, ind_saham), use_container_width=True, config=config_toolbar)

    with t_ai:
        st.caption("⚡ Mesin AI: **Groq (`GPT-OSS-120B` / `Qwen-3.8-27B`)**")
        if st.button(f"🚀 Jalankan Analisis Mendalam ({kode} & IHSG)", type="primary", use_container_width=True):
            with st.status(f"Menyusun riset {kode}...", expanded=True) as status:
                b_ihsg = ambil_google_news_cepat("IHSG")
                b_saham = ambil_google_news_cepat(kode)
                konteks = buat_konteks_saham(kode, ihsg_paket, {"harga": s_last, "pct": s_pct, "ind": ind_saham}, s_info, b_ihsg, b_saham)
                laporan = jalankan_prediksi_ai(kode, konteks)
                st.session_state[key_analisis] = laporan
                status.update(label="Selesai!", state="complete", expanded=False)

        if st.session_state[key_analisis]:
            st.markdown(st.session_state[key_analisis])
            if st.button(f"📲 Kirim Analisis {kode} ke Discord", key=f"dc_popup_{kode}"):
                ok_dc, msg_dc = kirim_ke_discord(
                    judul=f"📈 Analisis Saham {kode} (Rp {s_last:,.0f} | {s_pct:+.2f}%)",
                    isi_pesan=st.session_state[key_analisis],
                    warna=3066993 if s_diff >= 0 else 15158332
                )
                if ok_dc:
                    st.toast(f"✅ {kode} terkirim ke Discord!", icon="📲")
                else:
                    st.error(f"Gagal kirim Discord: {msg_dc}")

        st.divider()
        st.markdown(f"#### 💬 Tanya AI Seputar Saham {kode}")
        popup_chat_box = st.container()

        q1, q2, q3 = st.columns(3)
        pertanyaan_cepat = ""
        with q1:
            if st.button("🎯 Area Entry & Cut Loss?", key=f"q1_{kode}", use_container_width=True):
                pertanyaan_cepat = f"Berdasarkan support, resistance, dan RSI {kode} saat ini, di harga berapa area entry paling aman, target profit, dan batas cut loss-nya?"
        with q2:
            if st.button("💰 Murah atau Mahal?", key=f"q2_{kode}", use_container_width=True):
                pertanyaan_cepat = f"Evaluasi fundamental dan valuasi {kode} berdasarkan PER, PBV, dan ROE saat ini. Apakah tergolong murah, wajar, atau mahal?"
        with q3:
            if st.button("⚡ Layak Scalping / Swing?", key=f"q3_{kode}", use_container_width=True):
                pertanyaan_cepat = f"Melihat volume, tren MA20/MA50, dan MACD {kode} hari ini, apakah saham ini lebih cocok untuk scalping harian atau swing trading?"

        with st.form(key=f"form_tanya_{kode}", clear_on_submit=True):
            col_in, col_sub = st.columns([4, 1])
            with col_in:
                input_user = st.text_input("Tulis pertanyaan...", placeholder=f"Contoh: Apakah {kode} masih kuat naik atau rawan koreksi?", label_visibility="collapsed")
            with col_sub:
                kirim_tanya = st.form_submit_button("Kirim ➤", use_container_width=True)

        pertanyaan_aktif = pertanyaan_cepat if pertanyaan_cepat else (input_user.strip() if kirim_tanya else "")
        if pertanyaan_aktif:
            st.session_state[key_chat].append({"role": "user", "text": pertanyaan_aktif})
            with popup_chat_box:
                with st.status(f"Menjawab pertanyaan tentang {kode}...", expanded=False) as st_chat:
                    b_ihsg = ambil_google_news_cepat("IHSG")
                    b_saham = ambil_google_news_cepat(kode)
                    konteks = buat_konteks_saham(kode, ihsg_paket, {"harga": s_last, "pct": s_pct, "ind": ind_saham}, s_info, b_ihsg, b_saham)
                    jawaban = jawab_pertanyaan_ai(kode, pertanyaan_aktif, konteks, st.session_state[key_chat])
                    st.session_state[key_chat].append({"role": "ai", "text": jawaban})
                    st_chat.update(label="Jawaban siap", state="complete")

        with popup_chat_box:
            if st.session_state[key_chat]:
                for pesan in st.session_state[key_chat]:
                    cls_chat = "chat-user" if pesan["role"] == "user" else "chat-ai"
                    prefix = "🧑 " if pesan["role"] == "user" else ""
                    st.markdown(f'<div class="{cls_chat}">{prefix}{pesan["text"]}</div>', unsafe_allow_html=True)
                if st.button("🧹 Bersihkan Riwayat Tanya AI", key=f"clear_{kode}"):
                    st.session_state[key_chat] = []
                    st.rerun()

# ================= INISIALISASI STATE =================
if "watchlist" not in st.session_state:
    st.session_state.watchlist = muat_watchlist_awal()
    simpan_watchlist_ke_url(st.session_state.watchlist)
if "chat_market" not in st.session_state:
    st.session_state.chat_market = []
if "ihsg_paket_cache" not in st.session_state:
    st.session_state.ihsg_paket_cache = {}
if "hasil_prediksi_sesi2_besok" not in st.session_state:
    st.session_state.hasil_prediksi_sesi2_besok = None
if "hasil_prediksi_turun_sesi2_besok" not in st.session_state:
    st.session_state.hasil_prediksi_turun_sesi2_besok = None
if "sig_naik_terakhir" not in st.session_state:
    st.session_state.sig_naik_terakhir = ""
if "sig_turun_terakhir" not in st.session_state:
    st.session_state.sig_turun_terakhir = ""
if "auto_sync_ai_top10" not in st.session_state:
    st.session_state.auto_sync_ai_top10 = True
if "chat_sc_naik" not in st.session_state:
    st.session_state.chat_sc_naik = []
if "chat_sc_turun" not in st.session_state:
    st.session_state.chat_sc_turun = []
if "filter_min_harga" not in st.session_state:
    st.session_state.filter_min_harga = 0
if "filter_max_harga" not in st.session_state:
    st.session_state.filter_max_harga = 5000
if "filter_min_tx_miliar" not in st.session_state:
    st.session_state.filter_min_tx_miliar = 1.0

# ================= HEADER BRANDING, BANNER JAM BURSA REALTIME & BILAH PENCARIAN ATAS =================
ks_aktif = konteks_sesi_screener()
render_banner_jam_bursa_realtime()

s_bar1, s_bar2, s_bar3 = st.columns([3.1, 1.8, 1.1])
with s_bar1:
    with st.form("form_pencarian_saham", clear_on_submit=True):
        f_col1, f_col2 = st.columns([4, 1.1])
        with f_col1:
            cari_saham_input = st.text_input("Search symbol", placeholder="🔍 Ketik kode saham (misal: HUMI, BBCA, BUMI) lalu Enter...", label_visibility="collapsed")
        with f_col2:
            submit_cari = st.form_submit_button("🔍 Cari", use_container_width=True)
with s_bar2:
    tf_ihsg = st.radio("Rentang IHSG:", ["1D", "1W", "1M", "3M", "1Y"], horizontal=True, label_visibility="collapsed")
with s_bar3:
    live_mode = st.toggle("🟢 Live (10s)", value=True)

if submit_cari and cari_saham_input.strip():
    popup_detail_saham(cari_saham_input.strip().upper(), st.session_state.ihsg_paket_cache)

# ================= AREA BERANDA: KIRI (IHSG & WATCHLIST) | KANAN (TRENDING & BERITA) =================
def render_kolom_kiri(ihsg_paket_out: dict):
    _, ihsg_df, ihsg_hist, _ = ambil_data_tunggal("^JKSE", tf_ihsg)
    waktu_update = waktu_wib_sekarang().strftime("%H:%M:%S WIB")
    status_html = (
        f'<div class="live-badge"><span class="live-dot"></span>LIVE STREAM • Update {waktu_update}</div>'
        if live_mode else f'<div class="live-badge" style="color:#8b949e;">⏸ PAUSED • {waktu_update}</div>'
    )
    st.markdown(
        f'<div style="display:flex; justify-content:space-between; align-items:center; margin-bottom:4px;">'
        f'<span style="color:#00c805; font-weight:700; font-size:15px; border-bottom:2px solid #00c805; padding-bottom:4px;">🇮🇩 MARKET OVERVIEW</span>'
        f'{status_html}</div>',
        unsafe_allow_html=True
    )

    i_hist = ihsg_hist.dropna(subset=["Close"]) if not ihsg_hist.empty and "Close" in ihsg_hist.columns else pd.DataFrame()
    i_df = ihsg_df.dropna(subset=["Close"]) if not ihsg_df.empty and "Close" in ihsg_df.columns else pd.DataFrame()

    if not i_hist.empty or not i_df.empty:
        ihsg_last = _angka_aman(i_df['Close'].iloc[-1] if not i_df.empty else i_hist['Close'].iloc[-1], 0.0)
        ihsg_prev = _angka_aman(i_hist['Close'].iloc[-2] if (tf_ihsg == "1D" and len(i_hist) >= 2) else (i_df['Close'].iloc[0] if not i_df.empty else ihsg_last), ihsg_last)
        ihsg_diff = ihsg_last - ihsg_prev
        ihsg_pct = (ihsg_diff / ihsg_prev) * 100 if ihsg_prev else 0.0
        ind_ihsg = hitung_indikator(i_hist if not i_hist.empty else i_df)
        paket = {"harga": ihsg_last, "pct": ihsg_pct, "ind": ind_ihsg}
        ihsg_paket_out.clear()
        ihsg_paket_out.update(paket)
        st.session_state.ihsg_paket_cache = paket

        warna_i = "#00c805" if ihsg_diff >= 0 else "#ff3b30"
        st.markdown(
            f'<div style="margin-top:8px; margin-bottom:2px; display:flex; justify-content:space-between; align-items:center;">'
            f'<div><span style="border-left:3px solid {warna_i}; padding-left:8px; font-size:17px; font-weight:700;">IHSG</span><br>'
            f'<span style="font-size:24px; font-weight:800;">{ihsg_last:,.2f}</span>'
            f'<span style="color:{warna_i}; font-size:15px; font-weight:600; margin-left:6px;">{ihsg_diff:+.2f} ({ihsg_pct:+.2f}%)</span></div>'
            f'<div style="color:#00c805; font-size:13px; font-weight:600; background:#161b22; padding:6px 12px; border-radius:6px; border:1px solid #262c36;">📅 {waktu_wib_sekarang().strftime("%d %b %y")}</div></div>',
            unsafe_allow_html=True
        )
        st.plotly_chart(buat_chart_area_saham(i_df if not i_df.empty else i_hist, ihsg_diff, ihsg_prev, height=230, is_ihsg=True), use_container_width=True)

        ref_row = i_hist.iloc[-1] if not i_hist.empty else i_df.iloc[-1]
        o_val = _angka_aman(ref_row.get('Open', ihsg_last), ihsg_last)
        h_val = _angka_aman(ref_row.get('High', ihsg_last), ihsg_last)
        l_val = _angka_aman(ref_row.get('Low', ihsg_last), ihsg_last)
        v_val = _angka_aman(ref_row.get('Volume', 0.0), 0.0) / 1e9

        c_box1, c_box2 = st.columns(2)
        with c_box1:
            st.markdown(f'<div class="sb-box-card"><div class="sb-box-title">Intraday</div><div class="sb-stat-line"><span style="color:#8b949e;">Open</span><span style="color:#00c805; font-weight:600;">{o_val:,.2f}</span></div><div class="sb-stat-line"><span style="color:#8b949e;">High</span><span style="color:#00c805; font-weight:600;">{h_val:,.2f}</span></div><div class="sb-stat-line"><span style="color:#8b949e;">Low</span><span style="color:#ff3b30; font-weight:600;">{l_val:,.2f}</span></div></div>', unsafe_allow_html=True)
        with c_box2:
            st.markdown(f'<div class="sb-box-card"><div class="sb-box-title">Market Summary</div><div class="sb-stat-line"><span style="color:#8b949e;">Prev Close</span><span style="color:#f0f3fa; font-weight:600;">{ihsg_prev:,.2f}</span></div><div class="sb-stat-line"><span style="color:#8b949e;">Volume (B)</span><span style="color:#f0f3fa; font-weight:600;">{v_val:,.2f}B</span></div><div class="sb-stat-line"><span style="color:#8b949e;">RSI (14)</span><span style="color:#f5a623; font-weight:600;">{_angka_aman(ind_ihsg["rsi"], 50.0):.1f}</span></div></div>', unsafe_allow_html=True)

    st.write("")
    st.markdown("### Watchlist")
    data_wl = ambil_data_saham_batch(st.session_state.watchlist)
    paket_aktif = ihsg_paket_out if ihsg_paket_out else st.session_state.ihsg_paket_cache

    if data_wl:
        for item in data_wl:
            tk, nm = item["ticker"], item["name"]
            pr, df_val, pct_val = _angka_aman(item["price"]), _angka_aman(item["diff"]), _angka_aman(item["pct"])
            warna_txt = "#00c805" if df_val >= 0 else "#ff3b30"
            badge_c = '<span class="sb-badge-c">C</span>' if tk in SAHAM_BADGE_C else ""

            col_card, col_open, col_del = st.columns([17.0, 2.5, 1.5], vertical_alignment="center")
            with col_card:
                st.markdown(
                    f'<div class="sb-row">'
                    f'<div class="sb-left">{buat_html_logo_saham(tk, 36)}<div class="sb-info"><div class="sb-ticker-line"><span class="sb-ticker">{tk}</span>{badge_c}</div><span class="sb-name">{nm}</span></div></div>'
                    f'<div class="sb-mid">{buat_svg_sparkline(item["spark"], item["prev"], df_val)}</div>'
                    f'<div class="sb-right"><div class="sb-price">{pr:,.0f}</div><div class="sb-chg" style="color:{warna_txt};">{df_val:+,.0f} ({pct_val:+.2f}%)</div></div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
            with col_open:
                if st.button("Buka", key=f"klik_wl_{tk}", use_container_width=True):
                    popup_detail_saham(tk, paket_aktif)
            with col_del:
                if st.button("✖", key=f"hapus_wl_{tk}", help=f"Hapus {tk} dari Watchlist", use_container_width=True):
                    if len(st.session_state.watchlist) > 1:
                        st.session_state.watchlist.remove(tk)
                        simpan_watchlist_ke_url(st.session_state.watchlist)
                        st.toast(f"🗑️ {tk} dihapus dari Watchlist")
                        st.rerun()
                    else:
                        st.toast("⚠️ Minimal 1 saham harus ada di Watchlist")
    else:
        st.info("Memuat data Watchlist...")

def render_isi_trending(paket_aktif: dict):
    st.caption("18 saham aktif dipantau di pasar (update tiap 10 detik saat Live aktif).")
    data_tr = ambil_data_saham_batch(DEFAULT_TRENDING)
    if not data_tr:
        st.info("Memuat daftar Trending...")
        return

    for item in data_tr:
        tk, nm = item["ticker"], item["name"]
        pr, df_val, pct_val = _angka_aman(item["price"]), _angka_aman(item["diff"]), _angka_aman(item["pct"])
        warna_txt = "#00c805" if df_val >= 0 else "#ff3b30"
        badge_c = '<span class="sb-badge-c">C</span>' if tk in SAHAM_BADGE_C else ""

        c_row, c_btn = st.columns([18, 2.8], vertical_alignment="center")
        with c_row:
            st.markdown(
                f'<div class="sb-row">'
                f'<div class="sb-left">{buat_html_logo_saham(tk, 36)}<div class="sb-info"><div class="sb-ticker-line"><span class="sb-ticker">{tk}</span>{badge_c}</div><span class="sb-name">{nm}</span></div></div>'
                f'<div class="sb-right" style="width:52%;"><div class="sb-price">{pr:,.0f}</div><div class="sb-chg" style="color:{warna_txt};">{df_val:+,.0f}({pct_val:+.2f}%)</div></div>'
                f'</div>',
                unsafe_allow_html=True
            )
        with c_btn:
            if st.button("Buka", key=f"klik_tr_{tk}", use_container_width=True):
                popup_detail_saham(tk, paket_aktif)

def render_isi_berita():
    col_f1, col_f2 = st.columns([2.2, 1.2])
    with col_f1:
        topik_berita = st.selectbox("Topik Berita", ["IHSG & Pasar", "BUMI", "BBCA", "BBRI", "BMRI", "KOTA", "HUMI"], label_visibility="collapsed")
    with col_f2:
        if st.button("🔄 Refresh Berita", key="ref_news_home", use_container_width=True):
            ambil_feed_berita_saham.clear()
            ambil_og_image_artikel.clear()

    kode_query = "IHSG" if topik_berita == "IHSG & Pasar" else topik_berita
    daftar_berita = ambil_feed_berita_saham(kode_query, limit=8, fetch_og=True)
    if not daftar_berita:
        st.info("Belum ada berita terbaru yang bisa dimuat.")
        return

    for b in daftar_berita:
        judul_esc, sumber_esc, waktu_esc, link_esc = html.escape(b["title"]), html.escape(b["source"]), html.escape(b["time"]), html.escape(b["link"])
        inisial_src = html.escape((b["source"][:1] or "B").upper())
        if b["image"]:
            thumb_html = (
                f'<img src="{html.escape(b["image"])}" class="news-thumb" referrerpolicy="no-referrer" '
                f'onerror="this.style.display=\'none\'; this.nextElementSibling.style.display=\'flex\';" />'
                f'<div class="news-thumb-fallback" style="display:none;">{inisial_src}</div>'
            )
        else:
            thumb_html = f'<div class="news-thumb-fallback">{inisial_src}</div>'

        st.markdown(f"""
        <div class="news-card">
            <div class="news-body">
                <a href="{link_esc}" target="_blank" class="news-title-link">{judul_esc}</a>
                <div class="news-meta"><span class="news-src-dot">{inisial_src}</span><span>{sumber_esc}</span><span>•</span><span>{waktu_esc}</span></div>
                <div class="news-actions"><span>👍</span><span>👎</span><span>↗</span><span>💬</span></div>
            </div>
            {thumb_html}
        </div>
        """, unsafe_allow_html=True)

ihsg_paket_runtime = {}
kol_kiri, kol_kanan = st.columns([1.45, 1.0], gap="large")

with kol_kiri:
    if hasattr(st, "fragment") and live_mode:
        @st.fragment(run_every=10)
        def live_left_wrapper():
            render_kolom_kiri(ihsg_paket_runtime)
        live_left_wrapper()
    else:
        render_kolom_kiri(ihsg_paket_runtime)

with kol_kanan:
    st.markdown(
        '<div style="margin-bottom:6px;"><span style="color:#00c805; font-weight:700; font-size:15px; border-bottom:2px solid #00c805; padding-bottom:4px;">⚡ TRENDING & BERITA</span></div>',
        unsafe_allow_html=True
    )
    tab_tr, tab_br = st.tabs(["🔥 Trending", "📰 Berita"])
    paket_kanan = ihsg_paket_runtime if ihsg_paket_runtime else st.session_state.ihsg_paket_cache

    with tab_tr:
        if hasattr(st, "fragment") and live_mode:
            @st.fragment(run_every=10)
            def live_trending_wrapper():
                render_isi_trending(paket_kanan)
            live_trending_wrapper()
        else:
            render_isi_trending(paket_kanan)
    with tab_br:
        render_isi_berita()

# ================= SCREENER 10 SAHAM NAIK & 10 SAHAM TURUN DENGAN FILTER HARGA & LIKUIDITAS =================

@st.cache_data(ttl=25)
def hitung_skor_semua_saham(tickers: tuple):
    kandidat_all = []
    unik_tickers = list(dict.fromkeys([t.upper().strip() for t in tickers if t]))
    if not unik_tickers:
        return kandidat_all

    jk_tickers = [f"{t}.JK" for t in unik_tickers]
    try:
        df_daily = yf.download(jk_tickers, period="1mo", interval="1d", group_by="ticker", progress=False, threads=True)
        df_intra = yf.download(jk_tickers, period="1d", interval="5m", group_by="ticker", progress=False, threads=True)
    except Exception:
        return kandidat_all

    for t in unik_tickers:
        tk = f"{t}.JK"
        try:
            sub_d = df_daily[tk].dropna(subset=["Close"]) if len(unik_tickers) > 1 else df_daily.dropna(subset=["Close"])
            sub_i = df_intra[tk].dropna(subset=["Close"]) if len(unik_tickers) > 1 else df_intra.dropna(subset=["Close"])
            if len(sub_d) < 3:
                continue

            prev_close = _angka_aman(sub_d["Close"].iloc[-2], 0.0)
            last_price = _angka_aman(sub_i["Close"].iloc[-1] if not sub_i.empty else sub_d["Close"].iloc[-1], prev_close)
            if last_price <= 0 or prev_close <= 0:
                continue

            pct_day = ((last_price - prev_close) / prev_close) * 100.0
            close_s = sub_d["Close"].dropna()
            ema9 = _angka_aman(close_s.ewm(span=9, adjust=False).mean().iloc[-1], last_price)
            ma20 = _angka_aman(close_s.tail(20).mean(), last_price)

            ema12 = close_s.ewm(span=12, adjust=False).mean()
            ema26 = close_s.ewm(span=26, adjust=False).mean()
            macd_hist = _angka_aman(((ema12 - ema26) - (ema12 - ema26).ewm(span=9, adjust=False).mean()).iloc[-1], 0.0)

            delta = close_s.diff()
            gain = delta.where(delta > 0, 0.0).rolling(14, min_periods=1).mean()
            loss = (-delta.where(delta < 0, 0.0)).rolling(14, min_periods=1).mean()
            rsi = _angka_aman((100.0 - (100.0 / (1.0 + (gain / loss.replace(0, math.nan))))).iloc[-1], 50.0)

            vol_now = _angka_aman(sub_d["Volume"].iloc[-1], 0.0)
            vol_avg = _angka_aman(sub_d["Volume"].tail(20).mean(), 1.0)
            vol_ratio = (vol_now / vol_avg) if vol_avg > 0 else 1.0

            val_tx_rp = vol_now * last_price
            if val_tx_rp <= 0 and vol_avg > 0:
                val_tx_rp = vol_avg * last_price
            val_tx_miliar = val_tx_rp / 1e9

            support_20 = _angka_aman(sub_d["Low"].dropna().tail(20).min(), last_price * 0.94)
            resistance_20 = _angka_aman(sub_d["High"].dropna().tail(20).max(), last_price * 1.06)

            if not sub_i.empty:
                high_i = max(_angka_aman(sub_i["High"].max(), last_price), last_price)
                low_i = min(_angka_aman(sub_i["Low"].min(), last_price), last_price)
                vol_i = sub_i["Volume"].fillna(0.0)
                vwap_i = _angka_aman((sub_i["Close"] * vol_i).sum() / vol_i.sum(), last_price) if vol_i.sum() > 0 else last_price
            else:
                high_i = max(_angka_aman(sub_d["High"].iloc[-1], last_price), last_price)
                low_i = min(_angka_aman(sub_d["Low"].iloc[-1], last_price), last_price)
                vwap_i = last_price

            clv = ((last_price - low_i) / (high_i - low_i)) if high_i > low_i else 0.5
            pct_30m = 0.0
            if len(sub_i) >= 6:
                p_30m = _angka_aman(sub_i["Close"].iloc[-6], last_price)
                if p_30m > 0:
                    pct_30m = ((last_price - p_30m) / p_30m) * 100.0

            skor_naik_s2 = 45.0
            if last_price >= vwap_i:
                skor_naik_s2 += 12.0
            if clv >= 0.70:
                skor_naik_s2 += 12.0
            elif clv < 0.35:
                skor_naik_s2 -= 8.0
            if pct_30m > 0:
                skor_naik_s2 += min(pct_30m * 4.0, 12.0)
            if vol_ratio >= 1.2:
                skor_naik_s2 += min((vol_ratio - 1.0) * 9.0, 14.0)
            if 0.5 <= pct_day <= 14.0:
                skor_naik_s2 += min(pct_day * 1.4, 12.0)
            elif pct_day > 18.0:
                skor_naik_s2 -= 6.0

            skor_naik_esok = 45.0
            if last_price > ema9 > ma20:
                skor_naik_esok += 16.0
            elif last_price > ma20:
                skor_naik_esok += 10.0
            if macd_hist > 0:
                skor_naik_esok += 8.0
            if 50.0 <= rsi <= 72.0:
                skor_naik_esok += 10.0
            elif rsi > 78.0:
                skor_naik_esok -= 9.0
            if clv >= 0.75 and pct_day > 0:
                skor_naik_esok += 10.0
            if vol_ratio >= 1.15:
                skor_naik_esok += min((vol_ratio - 1.0) * 8.0, 12.0)

            skor_naik_s2 = round(min(max(skor_naik_s2, 10.0), 99.0), 1)
            skor_naik_esok = round(min(max(skor_naik_esok, 10.0), 99.0), 1)
            skor_naik_total = round((skor_naik_s2 * 0.5) + (skor_naik_esok * 0.5), 1)

            skor_turun_s2 = 45.0
            if last_price < vwap_i:
                skor_turun_s2 += 12.0
            if clv <= 0.30:
                skor_turun_s2 += 14.0
            elif clv > 0.70:
                skor_turun_s2 -= 8.0
            if pct_30m < 0:
                skor_turun_s2 += min(abs(pct_30m) * 4.0, 12.0)
            if pct_day < -0.5:
                skor_turun_s2 += min(abs(pct_day) * 1.6, 13.0)
            elif pct_day > 16.0 and clv < 0.55:
                skor_turun_s2 += 10.0
            if vol_ratio >= 1.2 and (pct_day < 0 or clv < 0.35):
                skor_turun_s2 += min((vol_ratio - 1.0) * 9.0, 14.0)

            skor_turun_esok = 45.0
            if last_price < ema9 < ma20:
                skor_turun_esok += 16.0
            elif last_price < ma20:
                skor_turun_esok += 10.0
            if macd_hist < 0:
                skor_turun_esok += 8.0
            if rsi > 76.0:
                skor_turun_esok += 12.0
            elif 28.0 <= rsi <= 45.0:
                skor_turun_esok += 10.0
            if clv <= 0.25 and pct_day < 0:
                skor_turun_esok += 10.0
            if vol_ratio >= 1.15 and pct_day < 0:
                skor_turun_esok += min((vol_ratio - 1.0) * 8.0, 12.0)

            skor_turun_s2 = round(min(max(skor_turun_s2, 10.0), 99.0), 1)
            skor_turun_esok = round(min(max(skor_turun_esok, 10.0), 99.0), 1)
            skor_turun_total = round((skor_turun_s2 * 0.5) + (skor_turun_esok * 0.5), 1)

            kandidat_all.append({
                "ticker": t,
                "name": NAMA_EMITEN_MAP.get(t, f"{t} Tbk."),
                "price": last_price,
                "pct_day": pct_day,
                "pct_30m": pct_30m,
                "vwap": vwap_i,
                "clv": clv,
                "vol_ratio": vol_ratio,
                "val_tx_miliar": round(val_tx_miliar, 2),
                "rsi": rsi,
                "ema9": ema9,
                "ma20": ma20,
                "macd_hist": macd_hist,
                "support": support_20,
                "resistance": resistance_20,
                "skor_naik_s2": skor_naik_s2,
                "skor_naik_esok": skor_naik_esok,
                "skor_naik_total": skor_naik_total,
                "skor_turun_s2": skor_turun_s2,
                "skor_turun_esok": skor_turun_esok,
                "skor_turun_total": skor_turun_total
            })
        except Exception:
            continue

    return kandidat_all

def saring_top10_naik_dan_turun(kandidat_all: list, min_harga: float, max_harga: float, min_tx_miliar: float = 0.0):
    low_b = min(float(min_harga), float(max_harga))
    high_b = max(float(min_harga), float(max_harga))
    min_liq = max(0.0, float(min_tx_miliar))
    terfilter = [
        x for x in kandidat_all
        if low_b <= x["price"] <= high_b and _angka_aman(x.get("val_tx_miliar", 0.0), 0.0) >= min_liq
    ]

    top10_naik = sorted(terfilter, key=lambda x: x["skor_naik_total"], reverse=True)[:10]
    kode_naik_set = {x["ticker"] for x in top10_naik}

    sisa = [x for x in terfilter if x["ticker"] not in kode_naik_set]
    top10_turun = sorted(sisa, key=lambda x: x["skor_turun_total"], reverse=True)[:10]
    return top10_naik, top10_turun, len(terfilter)

def signature_top10(daftar_top10: list) -> str:
    return ",".join([x["ticker"].upper() for x in (daftar_top10 or [])])

def prediksi_10_saham_naik_ai(top10: list, data_ihsg: dict, min_h: int, max_h: int) -> dict:
    ks = konteks_sesi_screener()
    kode_list = ["IHSG"] + [k["ticker"] for k in top10]
    berita_map = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(ambil_google_news_cepat, kd, 2): kd for kd in kode_list}
        for fut, kd in futures.items():
            try:
                berita_map[kd] = fut.result()
            except Exception:
                berita_map[kd] = "Tidak ada berita baru."

    blok_10_saham = []
    for idx, k in enumerate(top10, start=1):
        blok_10_saham.append(
            f"{idx}. {k['ticker']} | Harga: Rp {k['price']:,.0f} ({k['pct_day']:+.2f}%) | Tx: Rp {k.get('val_tx_miliar', 0):.1f}B | "
            f"VWAP: Rp {k['vwap']:,.0f} | CLV: {k['clv']*100:.0f}% | Vol: {k['vol_ratio']:.2f}x | EMA9: Rp {k['ema9']:,.0f} | "
            f"MA20: Rp {k['ma20']:,.0f} | RSI: {k['rsi']:.1f} | MACD: {k['macd_hist']:+.2f} | Sup20: Rp {k['support']:,.0f} | "
            f"Res20: Rp {k['resistance']:,.0f} | Skor {ks['label_short_1']}: {k['skor_naik_s2']}, {ks['label_short_2']}: {k['skor_naik_esok']} | Berita: {berita_map.get(k['ticker'], '-')}"
        )

    prompt = f"""
    Analisis 10 saham kandidat naik (rentang Rp {min_h:,} – Rp {max_h:,}).
    Konteks waktu bursa: {ks['instruksi_waktu']}
    IHSG: {_angka_aman(data_ihsg.get('harga', 0)):,.2f} ({_angka_aman(data_ihsg.get('pct', 0)):+.2f}%) | Berita IHSG: {berita_map.get('IHSG', '-')}

    Data 10 Saham:
    {chr(10).join(blok_10_saham)}

    BALAS HANYA DALAM FORMAT JSON VALID (singkat & padat, maksimal 12 kata per field teks) dengan struktur persis:
    {{
      "ringkasan_tabel": [
        {{
          "kode": "KODE_SAHAM",
          "fokus": "{ks['fokus_pilihan']}",
          "teknikal": "Ringkasan indikator padat",
          "berita": "Sentimen berita singkat",
          "entry": "Rp ...",
          "target": "Rp ...",
          "cutloss": "Rp ..."
        }}
      ],
      "top_sesi2": [
        {{
          "kode": "KODE_SAHAM",
          "alasan": ["Poin teknikal/VWAP/CLV", "Poin katalis berita", "Poin risiko profit taking"]
        }}
      ],
      "top_esok": [
        {{
          "kode": "KODE_SAHAM",
          "alasan": ["Poin tren EMA9/MA20/RSI", "Poin katalis berita", "Poin strategi swing/hold"]
        }}
      ]
    }}
    Wajib sertakan semua 10 kode saham di `ringkasan_tabel`, 3 saham di `top_sesi2` (untuk {ks['label_short_1']}), dan 3 saham di `top_esok` (untuk {ks['label_short_2']}).
    """
    raw_teks, label_model = panggil_ai_raw(prompt, max_tokens=4096, json_mode=True)
    parsed = _ekstrak_json_ai(raw_teks)
    return {
        "parsed": parsed,
        "raw": raw_teks,
        "model": label_model,
        "top10": top10,
        "sig": signature_top10(top10),
        "min_h": min_h,
        "max_h": max_h,
        "waktu": waktu_wib_sekarang().strftime("%H:%M:%S WIB")
    }

def prediksi_10_saham_turun_ai(top10_turun: list, data_ihsg: dict, min_h: int, max_h: int) -> dict:
    ks = konteks_sesi_screener()
    kode_list = ["IHSG"] + [k["ticker"] for k in top10_turun]
    berita_map = {}
    with ThreadPoolExecutor(max_workers=6) as ex:
        futures = {ex.submit(ambil_google_news_cepat, kd, 2): kd for kd in kode_list}
        for fut, kd in futures.items():
            try:
                berita_map[kd] = fut.result()
            except Exception:
                berita_map[kd] = "Tidak ada berita baru."

    blok_10_turun = []
    for idx, k in enumerate(top10_turun, start=1):
        blok_10_turun.append(
            f"{idx}. {k['ticker']} | Harga: Rp {k['price']:,.0f} ({k['pct_day']:+.2f}%) | Tx: Rp {k.get('val_tx_miliar', 0):.1f}B | "
            f"VWAP: Rp {k['vwap']:,.0f} | CLV: {k['clv']*100:.0f}% | Vol: {k['vol_ratio']:.2f}x | EMA9: Rp {k['ema9']:,.0f} | "
            f"MA20: Rp {k['ma20']:,.0f} | RSI: {k['rsi']:.1f} | MACD: {k['macd_hist']:+.2f} | Sup20: Rp {k['support']:,.0f} | "
            f"Res20: Rp {k['resistance']:,.0f} | Skor Turun {ks['label_short_1']}: {k['skor_turun_s2']}, {ks['label_short_2']}: {k['skor_turun_esok']} | Berita: {berita_map.get(k['ticker'], '-')}"
        )

    prompt = f"""
    Analisis 10 saham berisiko turun / koreksi (rentang Rp {min_h:,} – Rp {max_h:,}).
    Konteks waktu bursa: {ks['instruksi_waktu']}
    IHSG: {_angka_aman(data_ihsg.get('harga', 0)):,.2f} ({_angka_aman(data_ihsg.get('pct', 0)):+.2f}%) | Berita IHSG: {berita_map.get('IHSG', '-')}

    Data 10 Saham:
    {chr(10).join(blok_10_turun)}

    BALAS HANYA DALAM FORMAT JSON VALID (singkat & padat, maksimal 12 kata per field teks) dengan struktur persis:
    {{
      "ringkasan_tabel": [
        {{
          "kode": "KODE_SAHAM",
          "fokus": "{ks['fokus_pilihan']}",
          "teknikal": "Penyebab tekanan teknikal singkat",
          "berita": "Sentimen berita singkat",
          "support": "Rp ...",
          "reentry": "Rp ...",
          "breakdown": "Rp ..."
        }}
      ],
      "top_sesi2": [
        {{
          "kode": "KODE_SAHAM",
          "alasan": ["Tekanan VWAP/CLV intraday", "Sentimen berita/profit taking", "Level breakdown jangka pendek"]
        }}
      ],
      "top_esok": [
        {{
          "kode": "KODE_SAHAM",
          "alasan": ["Risiko pelemahan tren lanjutan", "Faktor distribusi/overbought", "Saran manajemen risiko"]
        }}
      ]
    }}
    Wajib sertakan semua 10 kode saham di `ringkasan_tabel`, 3 saham di `top_sesi2` (untuk {ks['label_short_1']}), dan 3 saham di `top_esok` (untuk {ks['label_short_2']}).
    """
    raw_teks, label_model = panggil_ai_raw(prompt, max_tokens=4096, json_mode=True)
    parsed = _ekstrak_json_ai(raw_teks)
    return {
        "parsed": parsed,
        "raw": raw_teks,
        "model": label_model,
        "top10": top10_turun,
        "sig": signature_top10(top10_turun),
        "min_h": min_h,
        "max_h": max_h,
        "waktu": waktu_wib_sekarang().strftime("%H:%M:%S WIB")
    }

def _badge_fokus_html(fokus_str: str, mode_turun: bool = False) -> str:
    f_low = str(fokus_str or "").lower()
    if "keduanya" in f_low:
        bg, fg = ("#361922", "#ff85a1") if mode_turun else ("#162d24", "#3fb950")
    elif "sesi 1" in f_low:
        bg, fg = ("#331d18", "#ff9e7d") if mode_turun else ("#17263b", "#6cb6ff")
    elif "sesi 2" in f_low:
        bg, fg = ("#2c2115", "#f5a623") if mode_turun else ("#1d2a3d", "#79c0ff")
    else:
        bg, fg = ("#2c2115", "#f5a623") if mode_turun else ("#261c38", "#c792ea")
    return f'<span class="ai-pill-fokus" style="background:{bg}; color:{fg};">{html.escape(str(fokus_str))}</span>'

def _bangun_baris_fallback_kuantitatif(item_s: dict, mode_turun: bool = False) -> dict:
    ks = konteks_sesi_screener()
    kd = item_s["ticker"]
    hrg = _angka_aman(item_s.get("price", 0.0), 0.0)
    sup = _angka_aman(item_s.get("support", hrg * 0.94), hrg * 0.94)
    res = _angka_aman(item_s.get("resistance", hrg * 1.06), hrg * 1.06)
    s2 = item_s.get("skor_turun_s2", 50) if mode_turun else item_s.get("skor_naik_s2", 50)
    es = item_s.get("skor_turun_esok", 50) if mode_turun else item_s.get("skor_naik_esok", 50)
    fokus = "Keduanya" if abs(s2 - es) <= 6 else (ks["label_short_1"] if s2 > es else ks["label_short_2"])

    if mode_turun:
        return {
            "kode": kd,
            "fokus": fokus,
            "teknikal": f"RSI {item_s.get('rsi', 50):.0f}, CLV {item_s.get('clv', 0.5)*100:.0f}%, Vol {item_s.get('vol_ratio', 1.0):.1f}x vs MA20 Rp {item_s.get('ma20', hrg):,.0f}",
            "berita": "Pantau tekanan jual & aksi profit taking.",
            "support": f"Rp {sup:,.0f}",
            "reentry": f"Rp {max(1.0, sup * 0.97):,.0f}",
            "breakdown": f"Rp {max(1.0, sup * 0.94):,.0f}"
        }
    return {
        "kode": kd,
        "fokus": fokus,
        "teknikal": f"Harga di atas EMA9 Rp {item_s.get('ema9', hrg):,.0f}, RSI {item_s.get('rsi', 50):.0f}, Vol {item_s.get('vol_ratio', 1.0):.1f}x",
        "berita": "Katalis teknikal & akumulasi jangka pendek.",
        "entry": f"Rp {hrg:,.0f}",
        "target": f"Rp {max(hrg + fraksi_bei(hrg), res):,.0f}",
        "cutloss": f"Rp {sup:,.0f}"
    }

def ringkas_konteks_screener_untuk_chat(top10: list, paket_hasil: dict, data_ihsg: dict, mode_turun: bool = False) -> str:
    ks = konteks_sesi_screener()
    label_arah = "POTENSI TURUN / KOREKSI" if mode_turun else "POTENSI NAIK"
    baris_saham = []
    for idx, k in enumerate(top10, start=1):
        skor_s2 = k["skor_turun_s2"] if mode_turun else k["skor_naik_s2"]
        skor_esok = k["skor_turun_esok"] if mode_turun else k["skor_naik_esok"]
        baris_saham.append(
            f"{idx}. {k['ticker']} ({k['name']}): Harga Rp {k['price']:,.0f} ({k['pct_day']:+.2f}%), Tx Rp {k.get('val_tx_miliar', 0):.1f}B, "
            f"VWAP Rp {k['vwap']:,.0f}, CLV {k['clv']*100:.0f}%, Vol {k['vol_ratio']:.1f}x, "
            f"EMA9 Rp {k['ema9']:,.0f}, MA20 Rp {k['ma20']:,.0f}, RSI {k['rsi']:.1f}, "
            f"Sup20 Rp {k['support']:,.0f}, Res20 Rp {k['resistance']:,.0f}, "
            f"Skor {ks['label_short_1']} {skor_s2}, Skor {ks['label_short_2']} {skor_esok}"
        )

    ringkasan_ai = ""
    if isinstance(paket_hasil, dict):
        parsed = paket_hasil.get("parsed")
        if isinstance(parsed, dict):
            ringkasan_ai = json.dumps(parsed, ensure_ascii=False)[:2400]

    return (
        f"Konteks Waktu Bursa: {ks['instruksi_waktu']}\n"
        f"Konteks Screener 10 Saham {label_arah}:\n"
        f"IHSG: {_angka_aman(data_ihsg.get('harga', 0)):,.2f} ({_angka_aman(data_ihsg.get('pct', 0)):+.2f}%)\n"
        f"Daftar 10 Saham:\n{chr(10).join(baris_saham)}\n\n"
        f"Hasil Tabel & Top Pick AI Sebelumnya:\n{ringkasan_ai}"
    )

def render_kotak_tanya_screener(prefix_key: str, top10: list, paket_hasil: dict, data_ihsg: dict, mode_turun: bool = False):
    chat_state_key = "chat_sc_turun" if mode_turun else "chat_sc_naik"
    judul_chat = (
        "💬 Tanya AI Soal Prediksi 10 Saham Potensi Turun Ini"
        if mode_turun else
        "💬 Tanya AI Soal Prediksi 10 Saham Potensi Naik Ini"
    )
    st.markdown(f"<div style='font-size:14px; font-weight:700; color:#f0f3fa; margin:10px 0 6px 0;'>{judul_chat}</div>", unsafe_allow_html=True)

    chat_box = st.container()

    with st.form(key=f"{prefix_key}_form_tanya", clear_on_submit=True):
        c_in, c_btn = st.columns([4.4, 1.0])
        with c_in:
            ph_txt = (
                "Tanya apa saja soal 10 saham potensi turun di atas (misal: Kapan waktu aman masuk kembali ke saham yang terkoreksi?)..."
                if mode_turun else
                "Tanya apa saja soal 10 saham potensi naik di atas (misal: Bandingkan 2 kandidat terkuat untuk sesi hari ini)..."
            )
            teks_input = st.text_input("Tanya prediksi", placeholder=ph_txt, label_visibility="collapsed")
        with c_btn:
            klik_kirim = st.form_submit_button("Tanya AI ➤", use_container_width=True)

    pertanyaan_final = teks_input.strip() if klik_kirim else ""
    if pertanyaan_final:
        st.session_state[chat_state_key].append({"role": "user", "text": pertanyaan_final})
        with chat_box:
            with st.status("Groq AI sedang membedah data 10 saham...", expanded=False) as st_q:
                konteks_sc = ringkas_konteks_screener_untuk_chat(top10, paket_hasil, data_ihsg, mode_turun=mode_turun)
                jwb = jawab_pertanyaan_ai("Screener 10 Saham", pertanyaan_final, konteks_sc, st.session_state[chat_state_key])
                st.session_state[chat_state_key].append({"role": "ai", "text": jwb})
                st_q.update(label="Jawaban siap!", state="complete")

    with chat_box:
        if st.session_state[chat_state_key]:
            cls_ai_box = "chat-ai-down" if mode_turun else "chat-ai"
            for msg in st.session_state[chat_state_key]:
                if msg["role"] == "user":
                    st.markdown(f'<div class="chat-user">🧑 {html.escape(msg["text"])}</div>', unsafe_allow_html=True)
                else:
                    st.markdown(f'<div class="{cls_ai_box}">{msg["text"]}</div>', unsafe_allow_html=True)
            if st.button("🧹 Bersihkan Riwayat Tanya Prediksi", key=f"{prefix_key}_clear_chat"):
                st.session_state[chat_state_key] = []
                st.rerun()

def render_hasil_screener_ai(paket_hasil: dict, top10_aktif: list, data_ihsg: dict, min_h_aktif: int, max_h_aktif: int, mode_turun: bool = False):
    if not paket_hasil:
        return

    raw_teks = paket_hasil.get("raw", "")
    if raw_teks.startswith("⚠️"):
        st.warning(raw_teks)
        return

    ks = konteks_sesi_screener()
    top10_list = top10_aktif if top10_aktif else (paket_hasil.get("top10") or [])
    waktu = paket_hasil.get("waktu", "")
    judul_exp = (
        f"📉 Tabel, Top Pick & Tanya AI — 10 Saham Potensi Turun ({ks['label_short_1']} & {ks['label_short_2']} • Rp {min_h_aktif:,} – Rp {max_h_aktif:,}) • Update {waktu}"
        if mode_turun else
        f"📊 Tabel, Top Pick & Tanya AI — 10 Saham Potensi Naik ({ks['label_short_1']} & {ks['label_short_2']} • Rp {min_h_aktif:,} – Rp {max_h_aktif:,}) • Update {waktu}"
    )

    with st.expander(judul_exp, expanded=True):
        btn_dc_key = "btn_dc_screener_turun" if mode_turun else "btn_dc_screener_naik"
        btn_dc_label = (
            "📲 Kirim Laporan 10 Saham Turun ke Discord"
            if mode_turun else
            "📲 Kirim Laporan 10 Saham Naik ke Discord"
        )
        if st.button(btn_dc_label, key=btn_dc_key):
            teks_dc = format_laporan_screener_discord(paket_hasil, top10_list, min_h_aktif, max_h_aktif, mode_turun=mode_turun)
            judul_dc = (
                f"📉 Laporan Top 10 Saham Potensi Turun (Rp {min_h_aktif:,} – Rp {max_h_aktif:,})"
                if mode_turun else
                f"🚀 Laporan Top 10 Saham Potensi Naik (Rp {min_h_aktif:,} – Rp {max_h_aktif:,})"
            )
            ok_dc, msg_dc = kirim_ke_discord(
                judul=judul_dc,
                isi_pesan=teks_dc,
                warna=15158332 if mode_turun else 3066993
            )
            if ok_dc:
                st.toast(f"✅ {msg_dc}", icon="📲")
            else:
                st.error(f"Gagal mengirim ke Discord: {msg_dc}")

        parsed = paket_hasil.get("parsed")
        if not isinstance(parsed, dict) and raw_teks:
            parsed = _ekstrak_json_ai(raw_teks)
        if not isinstance(parsed, dict):
            parsed = {}

        data_map = {item["ticker"].upper(): item for item in top10_list}
        kode_aktif_set = set(data_map.keys())

        ai_rows_map = {}
        for r in parsed.get("ringkasan_tabel", []) or []:
            if isinstance(r, dict) and r.get("kode"):
                kd_clean = str(r["kode"]).upper().strip()
                if kd_clean in kode_aktif_set:
                    ai_rows_map[kd_clean] = r

        daftar_baris_lengkap = []
        for item_s in top10_list:
            kd_u = item_s["ticker"].upper()
            if kd_u in ai_rows_map:
                daftar_baris_lengkap.append(ai_rows_map[kd_u])
            else:
                daftar_baris_lengkap.append(_bangun_baris_fallback_kuantitatif(item_s, mode_turun=mode_turun))

        rows_tbl = []
        for row in daftar_baris_lengkap:
            kd = str(row.get("kode", "")).upper().strip()
            if not kd:
                continue
            info_s = data_map.get(kd, {})
            harga_val = _angka_aman(info_s.get("price", 0.0), 0.0)
            pct_val = _angka_aman(info_s.get("pct_day", 0.0), 0.0)
            tx_b = _angka_aman(info_s.get("val_tx_miliar", 0.0), 0.0)
            w_pct = "#00c805" if pct_val >= 0 else "#ff3b30"
            harga_html = (
                f'<div style="font-weight:700; color:#f0f3fa; white-space:nowrap;">Rp {harga_val:,.0f}</div>'
                f'<div style="font-size:11px; font-weight:600; color:{w_pct};">{pct_val:+.2f}% • Tx {tx_b:.1f}B</div>'
                if harga_val > 0 else "-"
            )
            nama_pt = html.escape(NAMA_EMITEN_MAP.get(kd, info_s.get("name", f"{kd} Tbk.")))
            logo_html = buat_html_logo_saham(kd, ukuran=28)
            fokus_html = _badge_fokus_html(row.get("fokus", "-"), mode_turun=mode_turun)
            tek_txt = format_teks_ai_aman(row.get("teknikal", "-"))
            brt_txt = format_teks_ai_aman(row.get("berita", "-"))

            if mode_turun:
                c5 = html.escape(str(row.get("support", "-")))
                c6 = html.escape(str(row.get("reentry", "-")))
                c7 = html.escape(str(row.get("breakdown", "-")))
                kol_angka = (
                    f'<td style="text-align:right; font-weight:700; color:#f5a623; white-space:nowrap;">{c5}</td>'
                    f'<td style="text-align:right; font-weight:700; color:#00c805; white-space:nowrap;">{c6}</td>'
                    f'<td style="text-align:right; font-weight:700; color:#ff4d4f; white-space:nowrap;">{c7}</td>'
                )
            else:
                c5 = html.escape(str(row.get("entry", "-")))
                c6 = html.escape(str(row.get("target", "-")))
                c7 = html.escape(str(row.get("cutloss", "-")))
                kol_angka = (
                    f'<td style="text-align:right; font-weight:700; color:#6cb6ff; white-space:nowrap;">{c5}</td>'
                    f'<td style="text-align:right; font-weight:700; color:#00c805; white-space:nowrap;">{c6}</td>'
                    f'<td style="text-align:right; font-weight:700; color:#ff4d4f; white-space:nowrap;">{c7}</td>'
                )

            rows_tbl.append(
                f"<tr>"
                f"<td><div class='ai-stock-cell'>{logo_html}<div class='ai-stock-info'><span class='ai-stock-tk'>{html.escape(kd)}</span><span class='ai-stock-nm'>{nama_pt}</span></div></div></td>"
                f"<td style='text-align:right;'>{harga_html}</td>"
                f"<td>{fokus_html}</td>"
                f"<td><div><b style='color:#9ecbff;'>Teknikal:</b> {tek_txt}</div><div style='margin-top:2px;'><b style='color:#c792ea;'>Berita:</b> {brt_txt}</div></td>"
                f"{kol_angka}"
                f"</tr>"
            )

        if mode_turun:
            th_kanan = "<th style='text-align:right;'>Support Terdekat</th><th style='text-align:right;'>Area Re-entry</th><th style='text-align:right;'>Rawan Breakdown</th>"
            judul_tbl = f"📉 Ringkasan 10 Saham Potensi Turun / Koreksi (Rp {min_h_aktif:,} – Rp {max_h_aktif:,})"
            judul_s2 = f"⚠️ Paling Rawan Turun • {ks['label_short_1']}"
            judul_esok = f"🔻 Paling Rawan Turun • {ks['label_short_2']}"
        else:
            th_kanan = "<th style='text-align:right;'>Area Entry</th><th style='text-align:right;'>Target Profit</th><th style='text-align:right;'>Cut Loss</th>"
            judul_tbl = f"📊 Ringkasan 10 Saham Potensi Naik (Rp {min_h_aktif:,} – Rp {max_h_aktif:,})"
            judul_s2 = f"⚡ Top Pick • {ks['label_short_1']}"
            judul_esok = f"🌅 Top Pick • {ks['label_short_2']}"

        st.markdown(
            f'<div class="ai-sec-heading">{judul_tbl}</div>'
            f'<div class="ai-tbl-wrap"><table class="ai-tbl">'
            f'<thead><tr><th>Saham</th><th style="text-align:right;">Harga &amp; Tx</th><th>Fokus</th><th>Katalis Teknikal &amp; Berita</th>{th_kanan}</tr></thead>'
            f'<tbody>{"".join(rows_tbl)}</tbody>'
            f'</table></div>',
            unsafe_allow_html=True
        )

        raw_s2_list = [
            p for p in (parsed.get("top_sesi2") or [])
            if isinstance(p, dict) and str(p.get("kode", "")).upper().strip() in kode_aktif_set
        ]
        if len(raw_s2_list) < 3 and top10_list:
            key_s2_sort = "skor_turun_s2" if mode_turun else "skor_naik_s2"
            sudah_s2 = {str(p.get("kode", "")).upper().strip() for p in raw_s2_list}
            urut_s2 = sorted(top10_list, key=lambda x: x.get(key_s2_sort, 0), reverse=True)
            for x in urut_s2:
                if x["ticker"].upper() not in sudah_s2:
                    raw_s2_list.append({
                        "kode": x["ticker"],
                        "alasan": [
                            f"Skor {ks['label_short_1']} {x.get(key_s2_sort, 0)} (VWAP Rp {x['vwap']:,.0f}, CLV {x['clv']*100:.0f}%)",
                            f"Volume {x['vol_ratio']:.1f}x rata-rata 20 hari (Tx Rp {x.get('val_tx_miliar', 0):.1f}B)",
                            f"Support Rp {x['support']:,.0f} • Resistance Rp {x['resistance']:,.0f}"
                        ]
                    })
                if len(raw_s2_list) >= 3:
                    break

        raw_esok_list = [
            p for p in (parsed.get("top_esok") or [])
            if isinstance(p, dict) and str(p.get("kode", "")).upper().strip() in kode_aktif_set
        ]
        if len(raw_esok_list) < 3 and top10_list:
            key_es_sort = "skor_turun_esok" if mode_turun else "skor_naik_esok"
            sudah_es = {str(p.get("kode", "")).upper().strip() for p in raw_esok_list}
            urut_es = sorted(top10_list, key=lambda x: x.get(key_es_sort, 0), reverse=True)
            for x in urut_es:
                if x["ticker"].upper() not in sudah_es:
                    raw_esok_list.append({
                        "kode": x["ticker"],
                        "alasan": [
                            f"Skor {ks['label_short_2']} {x.get(key_es_sort, 0)} (EMA9 Rp {x['ema9']:,.0f}, MA20 Rp {x['ma20']:,.0f})",
                            f"RSI harian {x['rsi']:.1f} dengan MACD {x['macd_hist']:+.2f}",
                            f"Support Rp {x['support']:,.0f} • Resistance Rp {x['resistance']:,.0f}"
                        ]
                    })
                if len(raw_esok_list) >= 3:
                    break

        def render_kartu_top_pick(daftar_pick: list, judul_bagian: str):
            if not daftar_pick:
                return
            cards_html = []
            for idx_p, pk in enumerate(daftar_pick[:3], start=1):
                kd_p = str(pk.get("kode", "")).upper().strip()
                info_p = data_map.get(kd_p, {})
                hrg_p = _angka_aman(info_p.get("price", 0.0), 0.0)
                pct_p = _angka_aman(info_p.get("pct_day", 0.0), 0.0)
                w_p = "#00c805" if pct_p >= 0 else "#ff3b30"
                logo_p = buat_html_logo_saham(kd_p, ukuran=28)
                nm_p = html.escape(NAMA_EMITEN_MAP.get(kd_p, info_p.get("name", kd_p)))
                sub_hrg = f"Rp {hrg_p:,.0f} ({pct_p:+.2f}%)" if hrg_p > 0 else nm_p
                rank_style = 'background:#361519; color:#ff8080;' if mode_turun else 'background:#162c22; color:#3fb950;'
                poin_list = pk.get("alasan") or []
                li_html = "".join([f"<li>{format_teks_ai_aman(x)}</li>" for x in poin_list])
                cards_html.append(
                    f'<div class="ai-pick-card">'
                    f'<div class="ai-pick-head">'
                    f'<div class="ai-stock-cell" style="min-width:0;">{logo_p}<div class="ai-stock-info"><span class="ai-stock-tk">{html.escape(kd_p)}</span><span class="ai-stock-nm" style="color:{w_p}; font-weight:600;">{sub_hrg}</span></div></div>'
                    f'<span class="ai-pick-rank" style="{rank_style}">#{idx_p}</span>'
                    f'</div>'
                    f'<ul class="ai-pick-ul">{li_html}</ul>'
                    f'</div>'
                )
            st.markdown(
                f'<div class="ai-sec-heading">{judul_bagian}</div>'
                f'<div class="ai-pick-grid">{"".join(cards_html)}</div>',
                unsafe_allow_html=True
            )

        render_kartu_top_pick(raw_s2_list, judul_s2)
        render_kartu_top_pick(raw_esok_list, judul_esok)

        model_lbl = html.escape(str(paket_hasil.get("model", "Groq AI")))
        st.markdown(
            f'<div class="ai-footer-note">'
            f'<span>*Catatan: Analisis bersifat probabilistik berdasarkan data teknikal &amp; berita terbaru, bukan ajakan mutlak membeli/menjual.</span>'
            f'<span>⚡ {model_lbl} • Analisis Saham by Zariff</span>'
            f'</div>',
            unsafe_allow_html=True
        )

        st.markdown('<hr style="border:none; border-top:1px solid #242e3e; margin:12px 0 4px 0;">', unsafe_allow_html=True)
        prefix_chat = "sc_turun" if mode_turun else "sc_naik"
        render_kotak_tanya_screener(prefix_chat, top10_list, paket_hasil, data_ihsg, mode_turun=mode_turun)

# ================= BARIS KONTROL FILTER RENTANG HARGA & LIKUIDITAS SCREENER =================
st.write("")
st.markdown(
    '<div style="margin-top:8px; margin-bottom:6px;">'
    '<span style="color:#00c805; font-weight:700; font-size:15px; border-bottom:2px solid #00c805; padding-bottom:4px;">🎛️ FILTER HARGA &amp; LIKUIDITAS SCREENER (PREDIKSI NAIK &amp; TURUN)</span>'
    '</div>',
    unsafe_allow_html=True
)

PRESET_RENTANG_HARGA = {
    "Rp 0 – Rp 5.000": (0, 5000),
    "Rp 100 – Rp 1.000": (100, 1000),
    "Rp 50 – Rp 500": (50, 500),
    "Rp 1.000 – Rp 10.000": (1000, 10000),
    "Semua Harga (Rp 0 – Rp 100.000)": (0, 100000),
}

def terapkan_preset_harga():
    pilihan = st.session_state.get("preset_harga_pilihan", "Rp 0 – Rp 5.000")
    if pilihan in PRESET_RENTANG_HARGA:
        mn, mx = PRESET_RENTANG_HARGA[pilihan]
        st.session_state.filter_min_harga = mn
        st.session_state.filter_max_harga = mx

f_col_preset, f_col_min, f_col_max, f_col_liq, f_col_stat, f_col_sync = st.columns([1.45, 1.0, 1.0, 1.05, 1.35, 1.15], vertical_alignment="bottom")
with f_col_preset:
    st.selectbox(
        "Preset Cepat",
        options=list(PRESET_RENTANG_HARGA.keys()),
        key="preset_harga_pilihan",
        on_change=terapkan_preset_harga
    )
with f_col_min:
    st.number_input("Harga Min (Rp)", min_value=0, max_value=500000, step=50, key="filter_min_harga")
with f_col_max:
    st.number_input("Harga Max (Rp)", min_value=1, max_value=500000, step=100, key="filter_max_harga")
with f_col_liq:
    st.number_input(
        "Min Transaksi (Miliar Rp)",
        min_value=0.0,
        max_value=500.0,
        step=0.5,
        key="filter_min_tx_miliar",
        help="Saring saham sepi agar Top 10 yang tampil benar-benar likuid."
    )

harga_min_aktif = min(int(st.session_state.filter_min_harga), int(st.session_state.filter_max_harga))
harga_max_aktif = max(int(st.session_state.filter_min_harga), int(st.session_state.filter_max_harga))
min_tx_aktif = float(st.session_state.filter_min_tx_miliar)

semesta_saham = tuple(dict.fromkeys(st.session_state.watchlist + DEFAULT_TRENDING + EXTRA_SCAN_POOL))
semua_skor_saham = hitung_skor_semua_saham(semesta_saham)
top10_naik, top10_turun, jumlah_lolos_filter = saring_top10_naik_dan_turun(
    semua_skor_saham, harga_min_aktif, harga_max_aktif, min_tx_aktif
)
paket_sc = ihsg_paket_runtime if ihsg_paket_runtime else st.session_state.ihsg_paket_cache

with f_col_stat:
    st.markdown(
        f'<div class="filter-info-pill">'
        f'Rp {harga_min_aktif:,}–{harga_max_aktif:,} • Tx ≥ <b style="color:#00c805;">{min_tx_aktif:.1f}B</b><br>'
        f'<span style="color:#8b949e; font-size:11px;">{jumlah_lolos_filter} emiten likuid lolos</span>'
        f'</div>',
        unsafe_allow_html=True
    )
with f_col_sync:
    st.toggle(
        "🔄 Auto-Sync AI",
        key="auto_sync_ai_top10",
        help="Otomatis memperbarui analisis AI setiap kali daftar Top 10 saham berubah."
    )

# ---------------- BAGIAN A: PREDIKSI 10 SAHAM NAIK (URUTAN KIRI ATAS = TERKUAT) ----------------
st.write("")
st.markdown(
    f'<div style="margin-top:6px; margin-bottom:4px;">'
    f'<span style="color:#00c805; font-weight:700; font-size:15px; border-bottom:2px solid #00c805; padding-bottom:4px;">🚀 PREDIKSI 10 SAHAM NAIK • {ks_aktif["label_short_1"]} &amp; {ks_aktif["label_short_2"]} (HARGA Rp {harga_min_aktif:,} – Rp {harga_max_aktif:,})</span>'
    f'</div>',
    unsafe_allow_html=True
)

col_sc_info, col_sc_btn = st.columns([3.2, 1.4], vertical_alignment="center")
with col_sc_info:
    st.caption(f"Urutan **kiri atas = prediksi naik terkuat** • Filter aktif: **Rp {harga_min_aktif:,} – Rp {harga_max_aktif:,}** &amp; Transaksi ≥ **Rp {min_tx_aktif:.1f} Miliar**.")
with col_sc_btn:
    klik_scan_naik_ai = st.button(f"🔮 Analisis 10 Saham Naik • {ks_aktif['label_short_1']} & {ks_aktif['label_short_2']} (Groq AI)", type="primary", use_container_width=True)

if top10_naik:
    for row_start in range(0, len(top10_naik), 5):
        baris_items = top10_naik[row_start:row_start + 5]
        cols_baris = st.columns(5)
        for idx_col, item_s in enumerate(baris_items):
            idx_global = row_start + idx_col
            w_pct = "#00c805" if item_s["pct_day"] >= 0 else "#ff3b30"
            logo_kartu = buat_html_logo_saham(item_s["ticker"], ukuran=26)
            with cols_baris[idx_col]:
                st.markdown(
                    f'<div class="sc-card">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div class="sc-head-left">{logo_kartu}<span style="font-weight:800; font-size:14px; color:#f0f3fa;">{item_s["ticker"]}</span></div>'
                    f'<span style="font-size:10.5px; font-weight:700; color:#00c805; background:#122b18; padding:2px 6px; border-radius:6px;">Skor {item_s["skor_naik_total"]}</span>'
                    f'</div>'
                    f'<div style="font-size:15px; font-weight:700; margin-top:5px;">Rp {item_s["price"]:,.0f} '
                    f'<span style="color:{w_pct}; font-size:12px;">({item_s["pct_day"]:+.2f}%)</span></div>'
                    f'<div class="sc-pill-row">'
                    f'<span class="sc-pill" style="background:#17263b; color:#6cb6ff;">{ks_aktif["label_short_1"]}: {item_s["skor_naik_s2"]}</span>'
                    f'<span class="sc-pill" style="background:#261c38; color:#c792ea;">{ks_aktif["label_short_2"]}: {item_s["skor_naik_esok"]}</span>'
                    f'</div>'
                    f'<div style="font-size:10.5px; color:#8b949e; margin-top:5px;">Tx: {item_s.get("val_tx_miliar", 0):.1f}B • Vol: {item_s["vol_ratio"]:.1f}x • RSI: {item_s["rsi"]:.0f}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button(f"Buka {item_s['ticker']}", key=f"sc_up_open_{item_s['ticker']}_{idx_global}", use_container_width=True):
                    popup_detail_saham(item_s["ticker"], paket_sc)
else:
    st.info(f"Belum ditemukan saham kandidat naik di rentang harga Rp {harga_min_aktif:,} – Rp {harga_max_aktif:,} dengan transaksi ≥ Rp {min_tx_aktif:.1f} Miliar.")

sig_naik_sekarang = signature_top10(top10_naik)
perlu_auto_update_naik = (
    st.session_state.auto_sync_ai_top10
    and st.session_state.hasil_prediksi_sesi2_besok is not None
    and bool(sig_naik_sekarang)
    and sig_naik_sekarang != st.session_state.sig_naik_terakhir
)

if klik_scan_naik_ai or perlu_auto_update_naik:
    if not top10_naik:
        st.warning("Data kandidat saham naik belum tersedia pada filter ini.")
    else:
        label_proses_naik = (
            "Top 10 saham naik berubah — memperbarui tabel analisis Groq AI otomatis..."
            if perlu_auto_update_naik and not klik_scan_naik_ai else
            "Mengumpulkan berita terbaru kandidat naik & menyusun tabel analisis dengan Groq AI..."
        )
        with st.status(label_proses_naik, expanded=True) as st_sc:
            hasil_sc = prediksi_10_saham_naik_ai(top10_naik, paket_sc, harga_min_aktif, harga_max_aktif)
            st.session_state.hasil_prediksi_sesi2_besok = hasil_sc
            st.session_state.sig_naik_terakhir = sig_naik_sekarang
            st_sc.update(label="Tabel & Top Pick Saham Naik Selesai!", state="complete", expanded=False)

if st.session_state.hasil_prediksi_sesi2_besok:
    render_hasil_screener_ai(
        st.session_state.hasil_prediksi_sesi2_besok,
        top10_naik,
        paket_sc,
        harga_min_aktif,
        harga_max_aktif,
        mode_turun=False
    )

# ---------------- BAGIAN B: PREDIKSI 10 SAHAM TURUN (URUTAN KIRI ATAS = TERKUAT) ----------------
st.write("")
st.markdown(
    f'<div style="margin-top:10px; margin-bottom:4px;">'
    f'<span style="color:#ff3b30; font-weight:700; font-size:15px; border-bottom:2px solid #ff3b30; padding-bottom:4px;">📉 PREDIKSI 10 SAHAM TURUN / KOREKSI • {ks_aktif["label_short_1"]} &amp; {ks_aktif["label_short_2"]} (HARGA Rp {harga_min_aktif:,} – Rp {harga_max_aktif:,})</span>'
    f'</div>',
    unsafe_allow_html=True
)

col_dn_info, col_dn_btn = st.columns([3.2, 1.4], vertical_alignment="center")
with col_dn_info:
    st.caption(f"Urutan **kiri atas = prediksi turun terkuat** • Filter aktif: **Rp {harga_min_aktif:,} – Rp {harga_max_aktif:,}** &amp; Transaksi ≥ **Rp {min_tx_aktif:.1f} Miliar**.")
with col_dn_btn:
    klik_scan_turun_ai = st.button(f"📉 Analisis 10 Saham Turun • {ks_aktif['label_short_1']} & {ks_aktif['label_short_2']} (Groq AI)", use_container_width=True)

if top10_turun:
    for row_start in range(0, len(top10_turun), 5):
        baris_items = top10_turun[row_start:row_start + 5]
        cols_baris = st.columns(5)
        for idx_col, item_s in enumerate(baris_items):
            idx_global = row_start + idx_col
            w_pct = "#00c805" if item_s["pct_day"] >= 0 else "#ff3b30"
            logo_kartu = buat_html_logo_saham(item_s["ticker"], ukuran=26)
            with cols_baris[idx_col]:
                st.markdown(
                    f'<div class="sc-card-down">'
                    f'<div style="display:flex; justify-content:space-between; align-items:center;">'
                    f'<div class="sc-head-left">{logo_kartu}<span style="font-weight:800; font-size:14px; color:#f0f3fa;">{item_s["ticker"]}</span></div>'
                    f'<span style="font-size:10.5px; font-weight:700; color:#ff6b6b; background:#361519; padding:2px 6px; border-radius:6px;">Skor {item_s["skor_turun_total"]}</span>'
                    f'</div>'
                    f'<div style="font-size:15px; font-weight:700; margin-top:5px;">Rp {item_s["price"]:,.0f} '
                    f'<span style="color:{w_pct}; font-size:12px;">({item_s["pct_day"]:+.2f}%)</span></div>'
                    f'<div class="sc-pill-row">'
                    f'<span class="sc-pill" style="background:#33181c; color:#ff8080;">{ks_aktif["label_short_1"]}: {item_s["skor_turun_s2"]}</span>'
                    f'<span class="sc-pill" style="background:#2d1f14; color:#ffb36b;">{ks_aktif["label_short_2"]}: {item_s["skor_turun_esok"]}</span>'
                    f'</div>'
                    f'<div style="font-size:10.5px; color:#8b949e; margin-top:5px;">Tx: {item_s.get("val_tx_miliar", 0):.1f}B • Vol: {item_s["vol_ratio"]:.1f}x • RSI: {item_s["rsi"]:.0f}</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )
                if st.button(f"Buka {item_s['ticker']}", key=f"sc_dn_open_{item_s['ticker']}_{idx_global}", use_container_width=True):
                    popup_detail_saham(item_s["ticker"], paket_sc)
else:
    st.info(f"Belum ditemukan saham kandidat turun di rentang harga Rp {harga_min_aktif:,} – Rp {harga_max_aktif:,} dengan transaksi ≥ Rp {min_tx_aktif:.1f} Miliar.")

sig_turun_sekarang = signature_top10(top10_turun)
perlu_auto_update_turun = (
    st.session_state.auto_sync_ai_top10
    and st.session_state.hasil_prediksi_turun_sesi2_besok is not None
    and bool(sig_turun_sekarang)
    and sig_turun_sekarang != st.session_state.sig_turun_terakhir
)

if klik_scan_turun_ai or perlu_auto_update_turun:
    if not top10_turun:
        st.warning("Data kandidat saham turun belum tersedia pada filter ini.")
    else:
        label_proses_turun = (
            "Top 10 saham turun berubah — memperbarui tabel analisis Groq AI otomatis..."
            if perlu_auto_update_turun and not klik_scan_turun_ai else
            "Mengumpulkan berita terbaru emiten berisiko turun & menyusun tabel analisis dengan Groq AI..."
        )
        with st.status(label_proses_turun, expanded=True) as st_dn:
            hasil_dn = prediksi_10_saham_turun_ai(top10_turun, paket_sc, harga_min_aktif, harga_max_aktif)
            st.session_state.hasil_prediksi_turun_sesi2_besok = hasil_dn
            st.session_state.sig_turun_terakhir = sig_turun_sekarang
            st_dn.update(label="Tabel & Top Pick Saham Turun Selesai!", state="complete", expanded=False)

if st.session_state.hasil_prediksi_turun_sesi2_besok:
    render_hasil_screener_ai(
        st.session_state.hasil_prediksi_turun_sesi2_besok,
        top10_turun,
        paket_sc,
        harga_min_aktif,
        harga_max_aktif,
        mode_turun=True
    )

# ================= KOTAK TANYA AI PASAR & IHSG =================
st.write("")
with st.expander("💬 Tanya AI Seputar IHSG & Kondisi Pasar Hari Ini"):
    ihsg_chat_box = st.container()

    with st.form("form_tanya_ihsg", clear_on_submit=True):
        cm1, cm2 = st.columns([4.5, 1])
        with cm1:
            tanya_ihsg = st.text_input("Tanya IHSG...", placeholder="Contoh: Kenapa IHSG koreksi hari ini? Sektor apa yang menarik?", label_visibility="collapsed")
        with cm2:
            kirim_ihsg = st.form_submit_button("Tanya AI ➤", use_container_width=True)

    if kirim_ihsg and tanya_ihsg.strip():
        st.session_state.chat_market.append({"role": "user", "text": tanya_ihsg.strip()})
        with ihsg_chat_box:
            with st.status("Groq AI sedang menganalisis kondisi IHSG & pasar...", expanded=False) as st_mkt:
                b_ihsg = ambil_google_news_cepat("IHSG")
                konteks_ihsg = (
                    f"IHSG saat ini {_angka_aman(paket_sc.get('harga', 0)):,.2f} ({_angka_aman(paket_sc.get('pct', 0)):+.2f}%), "
                    f"MA20: {_angka_aman(paket_sc.get('ind', {}).get('ma20', 0)):,.2f}, RSI: {_angka_aman(paket_sc.get('ind', {}).get('rsi', 0)):.1f}.\n"
                    f"Berita IHSG:\n{b_ihsg}"
                )
                jwb_ihsg = jawab_pertanyaan_ai("IHSG", tanya_ihsg.strip(), konteks_ihsg, st.session_state.chat_market)
                st.session_state.chat_market.append({"role": "ai", "text": jwb_ihsg})
                st_mkt.update(label="Selesai", state="complete")

    with ihsg_chat_box:
        for idx_m, msg in enumerate(st.session_state.chat_market):
            cls_m = "chat-user" if msg["role"] == "user" else "chat-ai"
            pref_m = "🧑 " if msg["role"] == "user" else ""
            st.markdown(f'<div class="{cls_m}">{pref_m}{msg["text"]}</div>', unsafe_allow_html=True)
            if msg["role"] == "ai" and idx_m == len(st.session_state.chat_market) - 1:
                if st.button("📲 Kirim Jawaban IHSG ke Discord", key=f"dc_ihsg_{idx_m}"):
                    ok_dc, msg_dc = kirim_ke_discord(
                        judul="🇮🇩 Analisis IHSG & Pasar Hari Ini",
                        isi_pesan=msg["text"],
                        warna=3066993
                    )
                    if ok_dc:
                        st.toast(f"✅ {msg_dc}", icon="📲")
                    else:
                        st.error(f"Gagal kirim Discord: {msg_dc}")
