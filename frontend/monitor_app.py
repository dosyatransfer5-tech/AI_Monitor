"""
Uzaktan İzleme Uygulaması — Tire Curing Press
Veriyi Firebase Realtime Database'den okur.
Chatbot içermez — sadece izleme.
"""

import base64
import os
import sys
from datetime import date as _date

import requests
import streamlit as st

# ─── Firebase ayarları ────────────────────────────────────────────────────────
try:
    _FB_URL    = st.secrets.get("FIREBASE_URL", "").rstrip("/")
    _FB_SECRET = st.secrets.get("FIREBASE_SECRET", "")
except Exception:
    _FB_URL    = os.environ.get("FIREBASE_URL", "").rstrip("/")
    _FB_SECRET = os.environ.get("FIREBASE_SECRET", "")

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from auth import check_credentials, load_machines

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def _find_logo() -> str | None:
    """Logo dosyasını büyük/küçük harf farkına bakmadan bulur."""
    for name in ("logo.png", "Logo.png", "logo.PNG", "LOGO.PNG", "logo.jpg", "Logo.jpg"):
        p = os.path.join(_BASE_DIR, "data", name)
        if os.path.exists(p):
            return p
    return None


def _fb_get(path: str):
    """Firebase'den veri okur. Hata durumunda None döner."""
    if not _FB_URL or not _FB_SECRET:
        return None
    try:
        r = requests.get(f"{_FB_URL}/{path}.json?auth={_FB_SECRET}", timeout=5)
        return r.json() if r.ok else None
    except Exception:
        return None


def _fb_get_all() -> dict:
    """press1 altındaki tüm veriyi tek seferde çeker."""
    return _fb_get("press1") or {}


def _logo_b64_img(width: int = 60) -> str:
    """Header içinde kullanılmak üzere base64 img etiketi döner."""
    p = _find_logo()
    if not p:
        return ""
    with open(p, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    ext = os.path.splitext(p)[1].lstrip(".").lower() or "png"
    return (
        f'<img src="data:image/{ext};base64,{b64}" '
        f'style="width:{width}px;height:{width}px;object-fit:contain;border-radius:8px;" />'
    )


# ─── Sayfa yapılandırması ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pres İzleme",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── Global CSS ───────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stHeader"],
#MainMenu { display: none !important; height: 0 !important; min-height: 0 !important; }

.block-container { padding-top: 0.8rem !important; }

[data-testid="stAppViewContainer"] { background-color: #0f1117; }

.header-card {
    background: linear-gradient(135deg, #1a2035 0%, #0d1520 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 16px 24px;
    display: flex;
    align-items: center;
    gap: 18px;
    margin-bottom: 10px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.header-title { font-size: 1.5rem; font-weight: 700; color: #e8f4ff; margin: 0; line-height: 1.2; }
.header-sub   { font-size: 0.75rem; color: #4a7fa5; margin-top: 4px; letter-spacing: 0.5px; }
.header-badge {
    margin-left: auto;
    background: #0d2a1a;
    border: 1px solid #1a4a2a;
    border-radius: 20px;
    padding: 6px 16px;
    color: #4caf7a;
    font-size: 0.8rem;
    font-weight: 600;
}
.section-title {
    font-size: 0.85rem; font-weight: 700; text-transform: uppercase;
    letter-spacing: 1.2px; color: #5a9ec8;
    padding: 6px 0 4px 0; border-bottom: 1px solid #1e2a3a;
    margin-bottom: 10px; margin-top: 6px;
}
[data-testid="stMetric"] {
    background-color: #1a2235; border: 1px solid #1e2e42;
    border-radius: 8px; padding: 8px 12px !important;
}
[data-testid="stMetricLabel"] { font-size: 0.7rem !important; color: #5a8aaa !important; }
[data-testid="stMetricValue"] { font-size: 1.05rem !important; color: #c8e6ff !important; }
.alarm-none {
    background: linear-gradient(90deg,#0d2a1a,#112a1a); border:1px solid #1a4a2a;
    border-radius:8px; padding:10px 16px; color:#4caf7a; font-size:0.85rem; font-weight:600; margin-bottom:6px;
}
.alarm-active {
    background: linear-gradient(90deg,#2a0d0d,#2a1010); border:1px solid #6a1a1a;
    border-radius:8px; padding:10px 16px; color:#ff6b6b; font-size:0.85rem; font-weight:600; margin-bottom:6px;
}
hr { border-color: #1e2a3a !important; margin: 10px 0 !important; }
/* Görseller üzerinde büyütme / tam ekran butonunu gizle */
[data-testid="stElementToolbar"] { display: none !important; }
[data-testid="stFullScreenFrame"] { display: none !important; }
[data-testid="stButton"] > button {
    background-color:#1a2a3f; border:1px solid #1e3a5a; border-radius:8px;
    color:#8ab8d8; font-size:0.82rem; font-weight:500; padding:10px 16px;
}
</style>
""", unsafe_allow_html=True)

# ─── Session state ─────────────────────────────────────────────────────────────

for _k, _v in [("authenticated", False), ("machine_selected", False),
                ("current_user", {}), ("selected_machine", {}), ("lang", "tr")]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─── UI metinleri (TR / EN) ───────────────────────────────────────────────────

_UI_MON = {
    "tr": {
        "app_title":        "Makina İzleme",
        "app_sub":          "Hydraulic Tire Curing Press — Uzaktan İzleme",
        "login_user":       "Kullanıcı Adı",
        "login_pass":       "Şifre",
        "login_btn":        "Giriş Yap",
        "login_err":        "Kullanıcı adı veya şifre hatalı.",
        "welcome":          "Hoş geldiniz",
        "select_machine":   "İzlemek istediğiniz makineyi seçin",
        "logout":           "← Çıkış Yap",
        "exit":             "🚪 Çıkış",
        "tab_status":       "🖥️ Makina Durumu",
        "tab_alarm":        "⚠️ Alarm & Anomali",
        "tab_energy":       "⚡ Enerji Tüketimi",
        "sec_status":       "Makina Durumu",
        "sec_alarms":       "Aktif Alarmlar",
        "sec_pressures":    "Basınçlar",
        "sec_temps":        "Sıcaklıklar",
        "sec_positions":    "LVDT Pozisyonlar",
        "sec_anomaly":      "Anomali Durumu",
        "sec_daily":        "Bugünün İstatistikleri",
        "sec_trend":        "7 Günlük Trend",
        "sec_top_alarms":   "En Çok Tekrar Eden Alarmlar",
        "sec_energy":       "Anlık & Günlük Enerji",
        "sec_shift":        "Vardiya Özeti",
        "sec_ene_trend":    "Enerji Trendi (Son 24 Saat)",
        "sec_cycle_ene":    "Cycle Bazlı Tüketim (Son 20)",
        "alarm_none":       "✔ Alarm Yok",
        "alarm_active":     "Aktif Alarm",
        "curing_active":    "✅ Aktif",
        "curing_inactive":  "⏸ Pasif",
        "mod":              "Mod",
        "curing":           "Pişirme",
        "oil":              "HPU Yağ Seviyesi",
        "loader_unldr":     "Loader / Unloader",
        "cycle_count":      "Cycle Sayısı",
        "alarm_count":      "Alarm Sayısı",
        "anomaly_rate":     "Anomali Oranı",
        "avg_duration":     "Ort. Cycle Süresi",
        "live_kw":          "Anlık Güç",
        "air_flow":         "Hava Debisi",
        "daily_kwh":        "Günlük kWh",
        "daily_nm3":        "Günlük m³",
        "kwh_tire":         "kWh/Lastik",
        "nm3_tire":         "m³/Lastik",
        "no_data":          "Veri henüz yok.",
        "no_trend":         "Trend verisi henüz yok (ilk 5 dk içinde gelir).",
        "not_enough":       "Yeterli veri yok",
        "cycles_recorded":  "cycle kayıtlı (min 10)",
        "anomaly_found":    "⚠️ Anomali tespit edildi!",
        "anomaly_ok":       "✅ Son cycle normal",
        "cycles_analyzed":  "cycle analiz edildi",
        "fb_not_cfg":       "Firebase yapılandırılmamış. Secrets → FIREBASE_URL ve FIREBASE_SECRET ekleyin.",
        "fb_no_data":       "Firebase'de henüz veri yok. Backend çalışıyor mu?",
        "badge_not_cfg":    "⚙️ Yapılandırılmadı",
        "badge_connected":  "🟢 Bağlı",
        "badge_no_data":    "🔴 Bağlantı Yok",
        "shift_col":        ["Vardiya", "kWh", "m³", "Çalışma %"],
        "lbl_cycle":        "Cycle",
        "lbl_anomaly":      "Anomali",
        "lbl_alarm":        "Alarm",
        "lbl_power":        "Güç (kW)",
        "lbl_air":          "Hava (m³/h)",
        "lbl_cycle_id":     "Cycle ID",
        "shift_no_data":    "Vardiya verisi henüz yok.",
    },
    "en": {
        "app_title":        "Machine Monitor",
        "app_sub":          "Hydraulic Tire Curing Press — Remote Monitoring",
        "login_user":       "Username",
        "login_pass":       "Password",
        "login_btn":        "Sign In",
        "login_err":        "Invalid username or password.",
        "welcome":          "Welcome",
        "select_machine":   "Select the machine to monitor",
        "logout":           "← Sign Out",
        "exit":             "🚪 Sign Out",
        "tab_status":       "🖥️ Machine Status",
        "tab_alarm":        "⚠️ Alarm & Anomaly",
        "tab_energy":       "⚡ Energy",
        "sec_status":       "Machine Status",
        "sec_alarms":       "Active Alarms",
        "sec_pressures":    "Pressures",
        "sec_temps":        "Temperatures",
        "sec_positions":    "LVDT Positions",
        "sec_anomaly":      "Anomaly Status",
        "sec_daily":        "Today's Statistics",
        "sec_trend":        "7-Day Trend",
        "sec_top_alarms":   "Most Frequent Alarms",
        "sec_energy":       "Live & Daily Energy",
        "sec_shift":        "Shift Summary",
        "sec_ene_trend":    "Energy Trend (Last 24h)",
        "sec_cycle_ene":    "Cycle Energy (Last 20)",
        "alarm_none":       "✔ No Alarms",
        "alarm_active":     "Active Alarm",
        "curing_active":    "✅ Active",
        "curing_inactive":  "⏸ Idle",
        "mod":              "Mode",
        "curing":           "Curing",
        "oil":              "HPU Oil Level",
        "loader_unldr":     "Loader / Unloader",
        "cycle_count":      "Cycle Count",
        "alarm_count":      "Alarm Count",
        "anomaly_rate":     "Anomaly Rate",
        "avg_duration":     "Avg. Cycle Duration",
        "live_kw":          "Live Power",
        "air_flow":         "Air Flow",
        "daily_kwh":        "Daily kWh",
        "daily_nm3":        "Daily m³",
        "kwh_tire":         "kWh/Tire",
        "nm3_tire":         "m³/Tire",
        "no_data":          "No data yet.",
        "no_trend":         "No trend data yet (available in first 5 min).",
        "not_enough":       "Not enough data",
        "cycles_recorded":  "cycles recorded (min 10)",
        "anomaly_found":    "⚠️ Anomaly detected!",
        "anomaly_ok":       "✅ Last cycle normal",
        "cycles_analyzed":  "cycles analyzed",
        "fb_not_cfg":       "Firebase not configured. Add FIREBASE_URL and FIREBASE_SECRET to Secrets.",
        "fb_no_data":       "No data in Firebase yet. Is the backend running?",
        "badge_not_cfg":    "⚙️ Not Configured",
        "badge_connected":  "🟢 Connected",
        "badge_no_data":    "🔴 Not Connected",
        "shift_col":        ["Shift", "kWh", "m³", "Running %"],
        "lbl_cycle":        "Cycle",
        "lbl_anomaly":      "Anomaly",
        "lbl_alarm":        "Alarm",
        "lbl_power":        "Power (kW)",
        "lbl_air":          "Air (m³/h)",
        "lbl_cycle_id":     "Cycle ID",
        "shift_no_data":    "No shift data yet.",
    },
}

# ─── Giriş ekranı ─────────────────────────────────────────────────────────────

def _show_login():
    _u = _UI_MON[st.session_state.lang]

    # Login sayfasında arka planı açık yap + beyaz kart stili
    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f0f4f8 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        box-shadow: 0 8px 40px rgba(0,0,0,0.12) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    # Dil seçici — sağ üst
    _lc1, _lc2 = st.columns([6, 1])
    with _lc2:
        _sel = st.selectbox("🌐", ["TR", "EN"],
                            index=0 if st.session_state.lang == "tr" else 1,
                            key="login_lang_sel", label_visibility="collapsed")
        st.session_state.lang = _sel.lower()
        _u = _UI_MON[st.session_state.lang]

    _, _c2, _ = st.columns([1, 1.4, 1])
    with _c2:
        with st.container(border=True):
            # Logo üstte ortada, başlık altında
            st.html(f"""
            <div style="text-align:center;margin:14px 0 22px 0;">
              {_logo_b64_img(110)}
              <div style="font-size:1.6rem;font-weight:800;color:#1a2540;
                          letter-spacing:-0.5px;margin-top:16px;">
                {_u['app_title']}
              </div>
              <div style="font-size:0.82rem;color:#6b7fa8;margin-top:6px;">
                {_u['app_sub']}
              </div>
            </div>
            """)

            # Form
            with st.form("login_form"):
                _user = st.text_input(_u["login_user"], placeholder=_u["login_user"].lower())
                _pass = st.text_input(_u["login_pass"], type="password", placeholder="••••••••")
                if st.form_submit_button(_u["login_btn"], type="primary", use_container_width=True):
                    _usr = check_credentials(_user, _pass)
                    if _usr:
                        st.session_state.authenticated = True
                        st.session_state.current_user  = _usr
                        st.rerun()
                    else:
                        st.error(_u["login_err"])


def _show_machine_select():
    _u = _UI_MON[st.session_state.lang]
    _display = st.session_state.current_user.get("display_name", "")

    st.markdown("""
    <style>
    [data-testid="stAppViewContainer"] { background-color: #f0f4f8 !important; }
    [data-testid="stVerticalBlockBorderWrapper"] {
        background: #ffffff !important;
        box-shadow: 0 8px 40px rgba(0,0,0,0.12) !important;
    }
    </style>
    """, unsafe_allow_html=True)

    _, _c2, _ = st.columns([1, 1.4, 1])
    with _c2:
        with st.container(border=True):
            # Logo üstte ortada
            st.html(f"""
            <div style="text-align:center;margin:14px 0 8px 0;">
              {_logo_b64_img(90)}
              <div style="font-size:1.1rem;font-weight:700;color:#1a2540;margin-top:14px;">
                {_u['welcome']}, {_display}!
              </div>
              <div style="font-size:0.82rem;color:#6b7fa8;margin-top:4px;">
                {_u['select_machine']}
              </div>
            </div>
            """)

            st.markdown("<div style='height:8px'></div>", unsafe_allow_html=True)

            for _m in load_machines():
                if st.button(f"🏭  {_m['name']}  —  {_m['model']}    📍 {_m.get('location','')}",
                             key=f"mach_{_m['id']}", use_container_width=True):
                    st.session_state.machine_selected = True
                    st.session_state.selected_machine = _m
                    st.rerun()

            st.divider()
            if st.button(_u["logout"], use_container_width=True):
                st.session_state.authenticated    = False
                st.session_state.machine_selected = False
                st.rerun()

# ─── Auth kapısı ──────────────────────────────────────────────────────────────

if not st.session_state.authenticated:
    _show_login()
    st.stop()

if not st.session_state.machine_selected:
    _show_machine_select()
    st.stop()

# ─── Yardımcılar ──────────────────────────────────────────────────────────────

def _out_of_range(v, lo, hi) -> bool:
    if lo is None and hi is None: return False
    if lo is not None and v < lo: return True
    if hi is not None and v > hi: return True
    return False

from datetime import datetime as _dt

_fb_ok = bool(_FB_URL and _FB_SECRET)

# ─── Header (5 sn'de bir yenilenir — bağlantı ikonu canlı kalır) ─────────────

@st.fragment(run_every="5s")
def _header_fragment():
    _u            = _UI_MON[st.session_state.lang]
    _mach         = st.session_state.selected_machine
    _user_display = st.session_state.current_user.get("display_name", "")

    # Bağlantı kontrolü: timestamp'in yaşına göre karar ver
    _backend_online = False
    if _fb_ok:
        _d = _fb_get_all()
        if _d:
            _ts_str = (_d.get("status") or {}).get("timestamp")
            if _ts_str:
                try:
                    _age = (_dt.now() - _dt.fromisoformat(_ts_str)).total_seconds()
                    _backend_online = abs(_age) < 20
                except Exception:
                    _backend_online = True
            else:
                _backend_online = bool(_d)

    if not _fb_ok:
        _badge = f'<div class="header-badge" style="background:#1a1a0d;border-color:#4a4a1a;color:#cccc44;">{_u["badge_not_cfg"]}</div>'
    elif _backend_online:
        _badge = f'<div class="header-badge">{_u["badge_connected"]}</div>'
    else:
        _badge = f'<div class="header-badge" style="background:#2a0d0d;border-color:#6a1a1a;color:#ff6b6b;">{_u["badge_no_data"]}</div>'

    _hcol1, _hcol2, _hcol3 = st.columns([6, 1, 1])
    with _hcol1:
        st.html(f"""
<div class="header-card">
  {_logo_b64_img(52)}
  <div>
    <div class="header-title">{_mach.get('name','Pres')} — {_u["app_title"]}</div>
    <div class="header-sub">{_mach.get('model','')} &nbsp;|&nbsp; 📍 {_mach.get('location','')} &nbsp;|&nbsp; 👤 {_user_display}</div>
  </div>
  {_badge}
</div>
""")
    with _hcol2:
        _sel = st.selectbox("🌐", ["TR", "EN"],
                            index=0 if st.session_state.lang == "tr" else 1,
                            key="main_lang_sel", label_visibility="collapsed")
        if _sel.lower() != st.session_state.lang:
            st.session_state.lang = _sel.lower()
            st.rerun()
    with _hcol3:
        _u2 = _UI_MON[st.session_state.lang]
        if st.button(_u2["exit"], key="header_logout"):
            st.session_state.authenticated    = False
            st.session_state.machine_selected = False
            st.rerun()

_header_fragment()

# ─── Firebase / bağlantı uyarıları ────────────────────────────────────────────

_u = _UI_MON[st.session_state.lang]

if not _fb_ok:
    st.error(_u["fb_not_cfg"])
    st.stop()

# ─── Sekmeler ─────────────────────────────────────────────────────────────────

_tab_status, _tab_alarm, _tab_energy = st.tabs([
    _u["tab_status"],
    _u["tab_alarm"],
    _u["tab_energy"],
])

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 1 — MAKİNA DURUMU  (3 sn'de bir yenile)
# ══════════════════════════════════════════════════════════════════════════════

with _tab_status:

    @st.fragment(run_every="3s")
    def _status_fragment():
        _u = _UI_MON[st.session_state.lang]
        _d = _fb_get_all()

        # ── Durum kartları ─────────────────────────────────────────────────
        st.html(f'<div class="section-title">{_u["sec_status"]}</div>')
        _s = _d.get("status") or {}
        _sc1, _sc2, _sc3, _sc4 = st.columns(4)
        _sc1.metric(_u["mod"],          str(_s.get("mod", "—")))
        _sc2.metric(_u["curing"],       _u["curing_active"] if _s.get("pisirme_aktif") else _u["curing_inactive"])
        _oil = _s.get("hpu_yag_seviyesi_lt")
        _sc3.metric(_u["oil"],          f"{_oil:.1f} L" if _oil is not None else "—")
        _lt = _s.get("loader_sure_s"); _ut = _s.get("unloader_sure_s")
        _sc4.metric(_u["loader_unldr"],
                    f"{_lt:.1f}s / {_ut:.1f}s" if _lt is not None and _ut is not None else "—")

        # ── Alarmlar ───────────────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_alarms"]}</div>')
        _al = _d.get("alarms") or {}
        _cnt = _al.get("active_alarm_count", 0)
        if _cnt == 0:
            st.html(f'<div class="alarm-none">{_u["alarm_none"]}</div>')
        else:
            st.html(f'<div class="alarm-active">⚠️ {_cnt} {_u["alarm_active"]}</div>')
            for _a in _al.get("active_alarms", []):
                st.markdown(f"- **{_a.get('code','')}** — {_a.get('name','')}")

        # ── Threshold değerleri ─────────────────────────────────────────────
        _thresh = _fb_get("press1/thresholds") or {}
        _PRESS_THRESH = {"Squeeze Pressure": (_thresh.get("sqz_min"), _thresh.get("sqz_max"))}
        _TEMP_THRESH  = {
            "Segment temperature":      (_thresh.get("segment_temp_min"),   _thresh.get("segment_temp_max")),
            "External steam Top":       (_thresh.get("upper_platen_min"),   _thresh.get("upper_platen_max")),
            "External steam Bottom":    (_thresh.get("lower_platen_min"),   _thresh.get("lower_platen_max")),
            "External steam Container": (_thresh.get("container_temp_min"), _thresh.get("container_temp_max")),
            "Condensate trap":          (_thresh.get("trap_temp_min"),      _thresh.get("trap_temp_max")),
        }

        # ── Basınçlar ──────────────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_pressures"]}</div>')
        _pcols = st.columns(4); _pi = 0
        for _val in (_d.get("pressures") or {}).values():
            if isinstance(_val, dict) and _val.get("value") is not None:
                _v = _val["value"]; _desc = _val.get("desc",""); _unit = _val.get("unit","")
                _lims = _PRESS_THRESH.get(_desc)
                _label = f"{_desc} ❗" if _lims and _out_of_range(_v, _lims[0], _lims[1]) else _desc
                _pcols[_pi % 4].metric(_label, f"{_v:.1f} {_unit}"); _pi += 1

        # ── Sıcaklıklar ────────────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_temps"]}</div>')
        _tcols = st.columns(4); _ti = 0
        for _val in (_d.get("temperatures") or {}).values():
            if isinstance(_val, dict) and _val.get("value") is not None:
                _v = _val["value"]; _desc = _val.get("desc",""); _unit = _val.get("unit","")
                _lims = _TEMP_THRESH.get(_desc)
                _label = f"{_desc} ❗" if _lims and _out_of_range(_v, _lims[0], _lims[1]) else _desc
                _tcols[_ti % 4].metric(_label, f"{_v:.1f} {_unit}"); _ti += 1

        # ── Pozisyonlar ────────────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_positions"]}</div>')
        _pocols = st.columns(4); _poi = 0
        for _val in (_d.get("positions") or {}).values():
            if isinstance(_val, dict) and _val.get("value") is not None:
                _pocols[_poi % 4].metric(_val.get("desc",""), f"{_val['value']:.1f} {_val.get('unit','')}"); _poi += 1

    _status_fragment()

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 2 — ALARM & ANOMALİ (30 sn'de bir yenile)
# ══════════════════════════════════════════════════════════════════════════════

with _tab_alarm:

    @st.fragment(run_every="30s")
    def _alarm_fragment():
        import plotly.graph_objects as go
        _u = _UI_MON[st.session_state.lang]
        _d = _fb_get_all()

        # ── Anomali durumu ─────────────────────────────────────────────────
        st.html(f'<div class="section-title">{_u["sec_anomaly"]}</div>')
        _an = _d.get("anomaly_latest") or {}
        if not _an:
            st.info(_u["no_data"])
        elif not _an.get("enough_data"):
            st.info(f'{_u["not_enough"]} — {_an.get("total_cycles", 0)} {_u["cycles_recorded"]}')
        elif _an.get("has_anomaly"):
            st.html(f'<p style="color:#ff9800;font-weight:600;">{_u["anomaly_found"]}</p>')
            for _line in _an.get("detail_lines", []):
                st.markdown(f"- {_line}")
        else:
            st.html(f'<p style="color:#4caf7a;font-weight:600;">{_u["anomaly_ok"]}</p>')
            st.caption(f'{_an.get("total_cycles", 0)} {_u["cycles_analyzed"]}')

        # ── Günlük istatistikler ───────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_daily"]}</div>')
        _dd = _d.get("daily_stats") or {}
        if _dd:
            _dc1, _dc2, _dc3, _dc4 = st.columns(4)
            _dc1.metric(_u["cycle_count"],   _dd.get("cycles",{}).get("count", 0))
            _dc2.metric(_u["alarm_count"],   _dd.get("alarms",{}).get("count", 0))
            _dc3.metric(_u["anomaly_rate"],  f'{_dd.get("cycles",{}).get("anomaly_rate", 0):.1f}%')
            _dc4.metric(_u["avg_duration"],  f'{_dd.get("cycles",{}).get("avg_duration", 0):.0f} s')
            _top = _dd.get("alarms",{}).get("top_codes",[])
            if _top:
                st.html(f'<div class="section-title" style="margin-top:12px;">{_u["sec_top_alarms"]}</div>')
                for _item in _top[:5]:
                    st.markdown(f"- **{_item.get('code','')}** — {_item.get('name','')}  `×{_item.get('count','')}`")
        else:
            st.info(_u["no_data"])

        # ── 7 günlük trend ─────────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_trend"]}</div>')
        _tdata = _d.get("trend_7d") or []
        if _tdata and isinstance(_tdata, list):
            _dates  = [r.get("date","")        for r in _tdata]
            _cycles = [r.get("cycle_count",0)  for r in _tdata]
            _anoms  = [r.get("anomaly_count",0) for r in _tdata]
            _alarms = [r.get("alarm_count",0)  for r in _tdata]
            _fig = go.Figure()
            _fig.add_trace(go.Bar(name=_u["lbl_cycle"], x=_dates, y=_cycles,
                                  marker_color="#2a6496", opacity=0.8))
            _fig.add_trace(go.Scatter(name=_u["lbl_anomaly"], x=_dates, y=_anoms,
                                      mode="lines+markers", line=dict(color="#ff9800", width=2)))
            _fig.add_trace(go.Scatter(name=_u["lbl_alarm"], x=_dates, y=_alarms,
                                      mode="lines+markers", line=dict(color="#f44336", width=2, dash="dot")))
            _fig.update_layout(
                height=300, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font=dict(color="#8ab8d8", size=11),
                xaxis=dict(gridcolor="#1e2a3a"), yaxis=dict(gridcolor="#1e2a3a"),
                legend=dict(orientation="h", yanchor="bottom", y=1.02),
                margin=dict(l=40, r=20, t=10, b=40),
            )
            st.plotly_chart(_fig, key="alarm_trend_chart")
        else:
            st.info(_u["no_trend"])

    _alarm_fragment()

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 3 — ENERJİ TÜKETİMİ (30 sn'de bir yenile)
# ══════════════════════════════════════════════════════════════════════════════

with _tab_energy:

    @st.fragment(run_every="30s")
    def _energy_fragment():
        import plotly.graph_objects as go
        import pandas as pd
        _u = _UI_MON[st.session_state.lang]
        _d = _fb_get_all()

        # ── Anlık + günlük metrikler ───────────────────────────────────────
        st.html(f'<div class="section-title">{_u["sec_energy"]}</div>')
        _em1, _em2, _em3, _em4, _em5, _em6 = st.columns(6)
        _cur = _d.get("energy_current") or {}
        _em1.metric(_u["live_kw"],   f'{_cur.get("energy_kw") or 0:.1f} kW')
        _em2.metric(_u["air_flow"],  f'{_cur.get("air_flow")  or 0:.1f} m³/h')
        _tod = _d.get("energy_today") or {}
        _em3.metric(_u["daily_kwh"], f'{_tod.get("kwh_total")    or 0:.1f}')
        _em4.metric(_u["daily_nm3"], f'{_tod.get("nm3_total")    or 0:.1f}')
        _em5.metric(_u["kwh_tire"],  f'{_tod.get("kwh_per_tire") or 0:.3f}')
        _em6.metric(_u["nm3_tire"],  f'{_tod.get("nm3_per_tire") or 0:.4f}')

        # ── Vardiya özeti ──────────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_shift"]}</div>')
        _sv = _d.get("shift_summary") or []
        if _sv and isinstance(_sv, list):
            _sdf = pd.DataFrame(_sv)
            _cols = [c for c in ["shift","kwh_total","nm3_total","running_pct"] if c in _sdf.columns]
            if _cols:
                _sdf = _sdf[_cols]
                _sdf.columns = _u["shift_col"][:len(_cols)]
                st.dataframe(_sdf, hide_index=True)
        else:
            st.info(_u["shift_no_data"])

        # ── 24 saatlik trend ───────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_ene_trend"]}</div>')
        _et = _d.get("energy_trend") or []
        if _et and isinstance(_et, list):
            _hours = [r.get("hour","")          for r in _et]
            _kw    = [r.get("kw_mean",0)        for r in _et]
            _air   = [r.get("air_flow_mean",0)  for r in _et]
            _fig2  = go.Figure()
            _fig2.add_trace(go.Scatter(name=_u["lbl_power"], x=_hours, y=_kw,
                                       mode="lines", line=dict(color="#2196f3",width=2),
                                       fill="tozeroy", fillcolor="rgba(33,150,243,0.15)"))
            _fig2.add_trace(go.Scatter(name=_u["lbl_air"], x=_hours, y=_air,
                                       mode="lines", line=dict(color="#4caf50",width=2), yaxis="y2"))
            _fig2.update_layout(
                height=280, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font=dict(color="#8ab8d8",size=11),
                xaxis=dict(gridcolor="#1e2a3a"),
                yaxis=dict(gridcolor="#1e2a3a", title=_u["lbl_power"]),
                yaxis2=dict(overlaying="y",side="right",title=_u["lbl_air"],showgrid=False),
                legend=dict(orientation="h",yanchor="bottom",y=1.02),
                margin=dict(l=50,r=50,t=10,b=40),
            )
            st.plotly_chart(_fig2, key="energy_trend_chart")
        else:
            st.info(_u["no_trend"])

        # ── Cycle bazlı tüketim ────────────────────────────────────────────
        st.divider()
        st.html(f'<div class="section-title">{_u["sec_cycle_ene"]}</div>')
        _ec = _d.get("cycle_energy") or []
        if _ec and isinstance(_ec, list):
            _cids = [str(r.get("cycle_id","")) for r in _ec]
            _kwhs = [r.get("kwh_cycle",0)      for r in _ec]
            _nm3s = [r.get("nm3_cycle",0)      for r in _ec]
            _fig3 = go.Figure()
            _fig3.add_trace(go.Bar(name="kWh", x=_cids, y=_kwhs, marker_color="#2196f3", opacity=0.85))
            _fig3.add_trace(go.Bar(name="m³",  x=_cids, y=_nm3s, marker_color="#4caf50", opacity=0.85))
            _fig3.update_layout(
                barmode="group", height=260, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font=dict(color="#8ab8d8",size=11),
                xaxis=dict(gridcolor="#1e2a3a",title=_u["lbl_cycle_id"]),
                yaxis=dict(gridcolor="#1e2a3a"),
                legend=dict(orientation="h",yanchor="bottom",y=1.02),
                margin=dict(l=40,r=20,t=10,b=40),
            )
            st.plotly_chart(_fig3, key="cycle_energy_chart")
        else:
            st.info(_u["no_data"])

    _energy_fragment()
