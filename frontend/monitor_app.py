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
_LOGO_PATH = os.path.join(_BASE_DIR, "data", "logo.png")


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


# ─── Sayfa yapılandırması ──────────────────────────────────────────────────────

st.set_page_config(
    page_title="Pres İzleme",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ─── CSS ──────────────────────────────────────────────────────────────────────

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
[data-testid="stButton"] > button {
    background-color:#1a2a3f; border:1px solid #1e3a5a; border-radius:8px;
    color:#8ab8d8; font-size:0.82rem; font-weight:500; padding:10px 16px;
}
.login-box {
    background: linear-gradient(135deg,#1a2035 0%,#0d1520 100%);
    border:1px solid #1e3a5f; border-radius:14px; padding:36px 40px;
    box-shadow:0 8px 32px rgba(0,0,0,0.5); margin-top:20px;
}
</style>
""", unsafe_allow_html=True)

# ─── Logo ─────────────────────────────────────────────────────────────────────

def _logo_html(width: int = 60) -> str:
    if not os.path.exists(_LOGO_PATH):
        return ""
    with open(_LOGO_PATH, "rb") as f:
        b64 = base64.b64encode(f.read()).decode()
    return f'<img src="data:image/png;base64,{b64}" style="width:{width}px;height:{width}px;object-fit:contain;border-radius:8px;" />'

# ─── Session state ─────────────────────────────────────────────────────────────

for _k, _v in [("authenticated", False), ("machine_selected", False),
                ("current_user", {}), ("selected_machine", {})]:
    if _k not in st.session_state:
        st.session_state[_k] = _v

# ─── Giriş ekranı ─────────────────────────────────────────────────────────────

def _show_login():
    _c1, _c2, _c3 = st.columns([1, 1.4, 1])
    with _c2:
        st.markdown(f"""
<div class="login-box">
  <div style="text-align:center;margin-bottom:24px;">
    {_logo_html(100)}
    <div style="font-size:1.4rem;font-weight:700;color:#e8f4ff;margin-top:14px;">Lastik Pişirme Presi</div>
    <div style="font-size:0.8rem;color:#4a7fa5;margin-top:4px;">Hydraulic Tire Curing Press — Uzaktan İzleme</div>
  </div>
</div>
""", unsafe_allow_html=True)
        with st.form("login_form"):
            _user = st.text_input("Kullanıcı Adı", placeholder="kullanıcı adı")
            _pass = st.text_input("Şifre", type="password", placeholder="••••••••")
            if st.form_submit_button("Giriş Yap", type="primary"):
                _u = check_credentials(_user, _pass)
                if _u:
                    st.session_state.authenticated = True
                    st.session_state.current_user  = _u
                    st.rerun()
                else:
                    st.error("Kullanıcı adı veya şifre hatalı.")


def _show_machine_select():
    _c1, _c2, _c3 = st.columns([1, 1.4, 1])
    with _c2:
        _display = st.session_state.current_user.get("display_name", "")
        st.markdown(f"""
<div class="login-box">
  <div style="text-align:center;margin-bottom:20px;">
    {_logo_html(80)}
    <div style="font-size:1.1rem;font-weight:600;color:#e8f4ff;margin-top:12px;">Hoş geldiniz, {_display}!</div>
    <div style="font-size:0.8rem;color:#4a7fa5;margin-top:4px;">İzlemek istediğiniz makineyi seçin</div>
  </div>
</div>
""", unsafe_allow_html=True)
        for _m in load_machines():
            if st.button(f"🏭  {_m['name']}  —  {_m['model']}    📍 {_m.get('location','')}",
                         key=f"mach_{_m['id']}"):
                st.session_state.machine_selected = True
                st.session_state.selected_machine = _m
                st.rerun()
        st.divider()
        if st.button("← Çıkış Yap"):
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

# ─── Firebase bağlantı kontrolü ───────────────────────────────────────────────

_fb_ok = bool(_FB_URL and _FB_SECRET)
_data  = _fb_get_all() if _fb_ok else {}
_backend_online = bool(_data)

# ─── Header ───────────────────────────────────────────────────────────────────

_mach         = st.session_state.selected_machine
_user_display = st.session_state.current_user.get("display_name", "")

if not _fb_ok:
    _badge = '<div class="header-badge" style="background:#1a1a0d;border-color:#4a4a1a;color:#cccc44;">⚙️ Yapılandırılmadı</div>'
elif _backend_online:
    _badge = '<div class="header-badge">🟢 Bağlı</div>'
else:
    _badge = '<div class="header-badge" style="background:#2a0d0d;border-color:#6a1a1a;color:#ff6b6b;">🔴 Veri Yok</div>'

_hcol1, _hcol2 = st.columns([7, 1])
with _hcol1:
    st.markdown(f"""
<div class="header-card">
  {_logo_html(52)}
  <div>
    <div class="header-title">{_mach.get('name','Pres')} — Uzaktan İzleme</div>
    <div class="header-sub">{_mach.get('model','')} &nbsp;|&nbsp; 📍 {_mach.get('location','')} &nbsp;|&nbsp; 👤 {_user_display}</div>
  </div>
  {_badge}
</div>
""", unsafe_allow_html=True)
with _hcol2:
    if st.button("🚪 Çıkış", key="header_logout"):
        st.session_state.authenticated    = False
        st.session_state.machine_selected = False
        st.rerun()

if not _fb_ok:
    st.error("Firebase yapılandırılmamış. Streamlit Cloud → Settings → Secrets → FIREBASE_URL ve FIREBASE_SECRET ekleyin.")
    st.stop()

if not _backend_online:
    st.warning("Firebase'de henüz veri yok. Backend çalışıyor mu? `data/firebase_config.json` dosyasını kontrol edin.")

# ─── Sekmeler ─────────────────────────────────────────────────────────────────

_tab_status, _tab_alarm, _tab_energy = st.tabs([
    "🖥️ Makina Durumu",
    "⚠️ Alarm & Anomali",
    "⚡ Enerji Tüketimi",
])

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 1 — MAKİNA DURUMU  (10 sn'de bir yenile)
# ══════════════════════════════════════════════════════════════════════════════

with _tab_status:

    @st.fragment(run_every="10s")
    def _status_fragment():
        _d = _fb_get_all()

        # ── Durum kartları ─────────────────────────────────────────────────
        st.markdown('<div class="section-title">Makina Durumu</div>', unsafe_allow_html=True)
        _s = _d.get("status") or {}
        _sc1, _sc2, _sc3, _sc4 = st.columns(4)
        _sc1.metric("Mod",             str(_s.get("mod", "—")))
        _sc2.metric("Pişirme",         "✅ Aktif" if _s.get("pisirme_aktif") else "⏸ Pasif")
        _oil = _s.get("hpu_yag_seviyesi_lt")
        _sc3.metric("HPU Yağ Seviyesi", f"{_oil:.1f} L" if _oil is not None else "—")
        _lt = _s.get("loader_sure_s"); _ut = _s.get("unloader_sure_s")
        _sc4.metric("Loader / Unloader",
                    f"{_lt:.1f}s / {_ut:.1f}s" if _lt is not None and _ut is not None else "—")

        # ── Alarmlar ───────────────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">Aktif Alarmlar</div>', unsafe_allow_html=True)
        _al = _d.get("alarms") or {}
        _cnt = _al.get("active_alarm_count", 0)
        if _cnt == 0:
            st.markdown('<div class="alarm-none">✔ Alarm Yok</div>', unsafe_allow_html=True)
        else:
            st.markdown(f'<div class="alarm-active">⚠️ {_cnt} Aktif Alarm</div>', unsafe_allow_html=True)
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
        st.markdown('<div class="section-title">Basınçlar</div>', unsafe_allow_html=True)
        _pcols = st.columns(4); _pi = 0
        for _val in (_d.get("pressures") or {}).values():
            if isinstance(_val, dict) and _val.get("value") is not None:
                _v = _val["value"]; _desc = _val.get("desc",""); _unit = _val.get("unit","")
                _lims = _PRESS_THRESH.get(_desc)
                _label = f"{_desc} ❗" if _lims and _out_of_range(_v, _lims[0], _lims[1]) else _desc
                _pcols[_pi % 4].metric(_label, f"{_v:.1f} {_unit}"); _pi += 1

        # ── Sıcaklıklar ────────────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">Sıcaklıklar</div>', unsafe_allow_html=True)
        _tcols = st.columns(4); _ti = 0
        for _val in (_d.get("temperatures") or {}).values():
            if isinstance(_val, dict) and _val.get("value") is not None:
                _v = _val["value"]; _desc = _val.get("desc",""); _unit = _val.get("unit","")
                _lims = _TEMP_THRESH.get(_desc)
                _label = f"{_desc} ❗" if _lims and _out_of_range(_v, _lims[0], _lims[1]) else _desc
                _tcols[_ti % 4].metric(_label, f"{_v:.1f} {_unit}"); _ti += 1

        # ── Pozisyonlar ────────────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">LVDT Pozisyonlar</div>', unsafe_allow_html=True)
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
        _d = _fb_get_all()

        # ── Anomali durumu ─────────────────────────────────────────────────
        st.markdown('<div class="section-title">Anomali Durumu</div>', unsafe_allow_html=True)
        _an = _d.get("anomaly_latest") or {}
        if not _an:
            st.info("Anomali verisi henüz yok.")
        elif not _an.get("enough_data"):
            st.info(f"Yeterli veri yok — {_an.get('total_cycles',0)} cycle kayıtlı (min 10)")
        elif _an.get("has_anomaly"):
            st.markdown('<span style="color:#ff9800;font-weight:600;">⚠️ Anomali tespit edildi!</span>', unsafe_allow_html=True)
            for _line in _an.get("detail_lines", []):
                st.markdown(f"- {_line}")
        else:
            st.markdown(f'<span style="color:#4caf7a;font-weight:600;">✅ Son cycle normal</span>', unsafe_allow_html=True)
            st.caption(f"{_an.get('total_cycles',0)} cycle analiz edildi")

        # ── Günlük istatistikler ───────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">Bugünün İstatistikleri</div>', unsafe_allow_html=True)
        _dd = _d.get("daily_stats") or {}
        if _dd:
            _dc1, _dc2, _dc3, _dc4 = st.columns(4)
            _dc1.metric("Cycle Sayısı",     _dd.get("cycles",{}).get("count", 0))
            _dc2.metric("Alarm Sayısı",     _dd.get("alarms",{}).get("count", 0))
            _dc3.metric("Anomali Oranı",    f"{_dd.get('cycles',{}).get('anomaly_rate',0):.1f}%")
            _dc4.metric("Ort. Cycle Süresi",f"{_dd.get('cycles',{}).get('avg_duration',0):.0f} s")
            _top = _dd.get("alarms",{}).get("top_codes",[])
            if _top:
                st.markdown('<div class="section-title" style="margin-top:12px;">En Çok Tekrar Eden Alarmlar</div>', unsafe_allow_html=True)
                for _item in _top[:5]:
                    st.markdown(f"- **{_item.get('code','')}** — {_item.get('name','')}  `×{_item.get('count','')}`")
        else:
            st.info("Günlük veri henüz yok.")

        # ── 7 günlük trend ─────────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">7 Günlük Trend</div>', unsafe_allow_html=True)
        _tdata = _d.get("trend_7d") or []
        if _tdata and isinstance(_tdata, list):
            _dates  = [r.get("date","")        for r in _tdata]
            _cycles = [r.get("cycle_count",0)  for r in _tdata]
            _anoms  = [r.get("anomaly_count",0) for r in _tdata]
            _alarms = [r.get("alarm_count",0)  for r in _tdata]
            _fig = go.Figure()
            _fig.add_trace(go.Bar(name="Cycle", x=_dates, y=_cycles, marker_color="#2a6496", opacity=0.8))
            _fig.add_trace(go.Scatter(name="Anomali", x=_dates, y=_anoms,
                                      mode="lines+markers", line=dict(color="#ff9800", width=2)))
            _fig.add_trace(go.Scatter(name="Alarm", x=_dates, y=_alarms,
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
            st.info("Trend verisi henüz yok (ilk 5 dk içinde gelir).")

    _alarm_fragment()

# ══════════════════════════════════════════════════════════════════════════════
# SEKME 3 — ENERJİ TÜKETİMİ (30 sn'de bir yenile)
# ══════════════════════════════════════════════════════════════════════════════

with _tab_energy:

    @st.fragment(run_every="30s")
    def _energy_fragment():
        import plotly.graph_objects as go
        import pandas as pd
        _d = _fb_get_all()

        # ── Anlık + günlük metrikler ───────────────────────────────────────
        st.markdown('<div class="section-title">Anlık & Günlük Enerji</div>', unsafe_allow_html=True)
        _em1, _em2, _em3, _em4, _em5, _em6 = st.columns(6)
        _cur = _d.get("energy_current") or {}
        _em1.metric("Anlık Güç",    f'{_cur.get("energy_kw") or 0:.1f} kW')
        _em2.metric("Hava Debisi",  f'{_cur.get("air_flow")  or 0:.1f} m³/h')
        _tod = _d.get("energy_today") or {}
        _em3.metric("Günlük kWh",   f'{_tod.get("kwh_total")    or 0:.1f}')
        _em4.metric("Günlük m³",    f'{_tod.get("nm3_total")    or 0:.1f}')
        _em5.metric("kWh/Lastik",   f'{_tod.get("kwh_per_tire") or 0:.3f}')
        _em6.metric("m³/Lastik",    f'{_tod.get("nm3_per_tire") or 0:.4f}')

        # ── Vardiya özeti ──────────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">Vardiya Özeti</div>', unsafe_allow_html=True)
        _sv = _d.get("shift_summary") or []
        if _sv and isinstance(_sv, list):
            _sdf = pd.DataFrame(_sv)
            _cols = [c for c in ["shift","kwh_total","nm3_total","running_pct"] if c in _sdf.columns]
            if _cols:
                _sdf = _sdf[_cols]
                _sdf.columns = ["Vardiya","kWh","m³","Çalışma %"][:len(_cols)]
                st.dataframe(_sdf, hide_index=True)
        else:
            st.info("Vardiya verisi henüz yok.")

        # ── 24 saatlik trend ───────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">Enerji Trendi (Son 24 Saat)</div>', unsafe_allow_html=True)
        _et = _d.get("energy_trend") or []
        if _et and isinstance(_et, list):
            _hours = [r.get("hour","")          for r in _et]
            _kw    = [r.get("kw_mean",0)        for r in _et]
            _air   = [r.get("air_flow_mean",0)  for r in _et]
            _fig2  = go.Figure()
            _fig2.add_trace(go.Scatter(name="Güç (kW)", x=_hours, y=_kw,
                                       mode="lines", line=dict(color="#2196f3",width=2),
                                       fill="tozeroy", fillcolor="rgba(33,150,243,0.15)"))
            _fig2.add_trace(go.Scatter(name="Hava (m³/h)", x=_hours, y=_air,
                                       mode="lines", line=dict(color="#4caf50",width=2), yaxis="y2"))
            _fig2.update_layout(
                height=280, paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font=dict(color="#8ab8d8",size=11),
                xaxis=dict(gridcolor="#1e2a3a"),
                yaxis=dict(gridcolor="#1e2a3a", title="kW"),
                yaxis2=dict(overlaying="y",side="right",title="m³/h",showgrid=False),
                legend=dict(orientation="h",yanchor="bottom",y=1.02),
                margin=dict(l=50,r=50,t=10,b=40),
            )
            st.plotly_chart(_fig2, key="energy_trend_chart")
        else:
            st.info("Enerji trend verisi henüz yok (ilk 5 dk içinde gelir).")

        # ── Cycle bazlı tüketim ────────────────────────────────────────────
        st.divider()
        st.markdown('<div class="section-title">Cycle Bazlı Tüketim (Son 20)</div>', unsafe_allow_html=True)
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
                xaxis=dict(gridcolor="#1e2a3a",title="Cycle ID"),
                yaxis=dict(gridcolor="#1e2a3a"),
                legend=dict(orientation="h",yanchor="bottom",y=1.02),
                margin=dict(l=40,r=20,t=10,b=40),
            )
            st.plotly_chart(_fig3, key="cycle_energy_chart")
        else:
            st.info("Cycle enerji verisi henüz yok.")

    _energy_fragment()
