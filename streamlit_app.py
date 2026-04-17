"""
Streamlit chat UI for the tire curing press AI chatbot.
Connects to the FastAPI backend.
"""

import json
import os
import sys

import requests
import streamlit as st
import streamlit.components.v1 as _st_components

BACKEND_URL = os.environ.get("BACKEND_URL", "http://localhost:8000")

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import config as _cfg
from backend.report_service import ReportService as _ReportService
from frontend.auth import check_credentials, load_machines as _load_machines

_T = _cfg.thresholds  # threshold kısayolu

_DB_PATH = os.path.join(_cfg.data_dir, "cycles.db")


@st.cache_data(ttl=60, show_spinner=False)
def _cached_energy_excel(start: str, end: str) -> bytes | None:
    """Enerji Excel raporunu üret ve 60 sn cache'le."""
    try:
        from backend.energy_service import EnergyService as _ES
        return _ES(_DB_PATH).export_excel(start, end)
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def _cached_energy_pdf(start: str, end: str, lang: str) -> bytes | None:
    """Enerji PDF raporunu üret ve 60 sn cache'le."""
    try:
        from backend.energy_service import EnergyService as _ES
        return _ES(_DB_PATH).export_pdf(start, end, lang)
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def _cached_pdf(start: str, end: str, lang: str) -> bytes | None:
    """PDF raporunu üret ve 60 sn cache'le."""
    try:
        return _ReportService(_DB_PATH).export_pdf(start, end, lang)
    except Exception:
        return None


@st.cache_data(ttl=60, show_spinner=False)
def _cached_excel(start: str, end: str) -> bytes | None:
    """Excel raporunu üret ve 60 sn cache'le."""
    try:
        return _ReportService(_DB_PATH).export_excel(start, end)
    except Exception:
        return None


def _out_of_range(v: float, lo: float, hi: float) -> bool:
    return v < lo or v > hi

_BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_LOGO_PATH = os.path.join(_BASE_DIR, "data", "logo.png")

# ─── UI string'leri (TR / EN) ──────────────────────────────────────────────────

_UI: dict[str, dict[str, str]] = {
    "tr": {
        "header_title":      "Curing Pres — AI Asistan",
        "header_sub":        "Siemens S7-1500 &nbsp;|&nbsp; ABB ACS580 &nbsp;|&nbsp; PILZ Güvenlik",
        "quick_label":       "Hızlı Sorular",
        "btn_pressures":     "📊 Basınçlar",
        "btn_temperatures":  "🌡️ Sıcaklıklar",
        "btn_alarms":        "⚠️ Alarmlar",
        "q_pressures":       "Şu anki tüm basınç değerlerini göster",
        "q_temperatures":    "Şu anki tüm sıcaklık değerlerini göster",
        "q_alarms":          "Aktif alarmlar var mı? Varsa açıkla",
        "chat_placeholder":  "Sorunuzu yazın...",
        "clear_btn":         "🗑️ Sohbeti Temizle",
        "err_backend":       "❌ Backend sunucusuna bağlanılamadı. `python -m backend.main` komutunu çalıştırın.",
        "sec_alarms":        "Alarmlar",
        "sec_status":        "Makine Durumu",
        "sec_pressures":     "Basınçlar",
        "sec_temperatures":  "Sıcaklıklar",
        "sec_positions":     "LVDT Pozisyonlar",
        "alarm_none":        "✔ Alarm Yok",
        "alarm_active":      "Aktif Alarm",
        "backend_warn":      "Backend bağlantısı yok",
        "metric_mode":       "Mod",
        "metric_curing":     "Pişirme",
        "curing_active":     "✅ Aktif",
        "curing_inactive":   "⏸ Pasif",
        "metric_oil":        "HPU Yağ Sev.",
        "metric_loader":     "Loader In-Out Süre",
        "metric_unloader":   "Unloader In-Out Süre",
        "notif_btn":         "🔔 Bildirim Ayarları",
        "notif_title":       "Bildirim Ayarları",
        "notif_contacts":    "Kayıtlı Kişiler",
        "notif_add":         "Yeni Kişi Ekle",
        "notif_name":        "Ad Soyad",
        "notif_phone":       "Telefon (+905XXXXXXXXX)",
        "notif_email":       "E-posta",
        "notif_add_btn":     "Ekle",
        "notif_no_contacts": "Henüz kayıtlı kişi yok.",
        "notif_added":       "Kişi eklendi.",
        "notif_deleted":     "Kişi silindi.",
        "notif_err":         "Hata: telefon veya e-posta girilmeli.",
        "notif_col_name":    "Ad Soyad",
        "notif_col_phone":   "Telefon",
        "notif_col_email":   "E-posta",
        "notif_col_active":  "Aktif",
        "notif_col_del":     "Sil",
        "sec_anomaly":       "Anomali İzleme",
        "anomaly_no_data":   "Yeterli veri yok (min 10 cycle)",
        "anomaly_ok":        "Son cycle normal",
        "anomaly_warn":      "Anomali tespit edildi!",
        "anomaly_cycles":    "Kayıtlı cycle",
        # Alarm notifications tab
        "tab_contacts":      "📋 Kişiler",
        "tab_alarms":        "🔔 Alarm Bildirimleri",
        "alarm_notif_title": "Hangi alarmlar bildirim göndersin?",
        "alarm_notif_save":  "💾 Kaydet",
        "alarm_notif_saved": "Ayarlar kaydedildi.",
        "alarm_col_code":    "Kod",
        "alarm_col_name":    "Alarm Adı",
        "alarm_col_sev":     "Ciddiyet",
        "alarm_col_notif":   "Bildirim",
        # Anomaly config dialog
        "anomaly_btn":        "⚙️ Anomali Ayarları",
        "anomaly_dlg_title":  "Anomali İzleme Ayarları",
        "sim_mode_label":     "Simülasyon Modu",
        "sim_mode_help":      "Aktif edilince gerçek PLC yerine simüle edilmiş veri kullanılır",
        "cycle_notify_label": "Döngü Anomali Bildirimleri",
        "cycle_notify_help":  "Her döngü sonunda istatistiksel anomali (basınç sapması, zamanlama vb.) tespitinde mail gönder",
        "sim_anom_label":     "Simülasyon Anomalileri",
        "sim_anom_help":      "Aktif edilince sim modunda her 5/7 cycle'da kasıtlı anomali üretilir (test amaçlıdır)",
        "monitor_values":     "İzlenen Değerler",
        "add_value":          "Değer Ekle",
        "col_value":          "Değer",
        "col_min":            "Min Eşik",
        "col_max":            "Max Eşik",
        "col_unit":           "Birim",
        "col_enabled":        "Etkin",
        "col_notify":         "Bildirim",
        "col_del":            "Sil",
        "no_values":          "İzlenen değer yok. Aşağıdan ekleyin.",
        "select_tag":         "PLC Etiketi Seç",
        "btn_add_value":      "Ekle",
        "btn_save":           "💾 Kaydet",
        "saved_ok":           "Ayarlar kaydedildi.",
        # Dashboard
        "tab_chat":           "💬 Asistan",
        "tab_dashboard":      "📊 Alarm-Anomali",
        "dash_today":         "Bugün",
        "dash_yesterday":     "Dün",
        "dash_week":          "Bu Hafta",
        "dash_custom":        "Özel Aralık",
        "dash_refresh":       "🔄",
        "dash_cycles":        "Cycle Sayısı",
        "dash_alarms":        "Alarm Sayısı",
        "dash_anomaly_rate":  "Anomali Oranı",
        "dash_avg_duration":  "Ort. Süre (s)",
        "dash_daily_trend":   "Günlük Cycle & Anomali Trendi",
        "dash_pressure_trend":"Basınç Trendi (Ort.)",
        "dash_anomaly_dist":  "Anomali Dağılımı",
        "dash_top_alarms":    "En Çok Tekrar Eden Alarmlar",
        "dash_no_data":       "Bu tarih için veri yok.",
        "dash_excel":         "📥 Excel İndir",
        "dash_pdf":           "📥 PDF İndir",
        "dash_export_range":  "Export Tarih Aralığı",
        "dash_anomaly_names": {
            "pressure_drift":  "Basınç Kayması",
            "loader_timing":   "Loader Zamanlama",
            "unloader_timing": "Unloader Zamanlama",
            "press_close":     "Pres Kapanma",
        },
        # Bildirim ayarları dialog — sekmeler
        "tab_telegram":            "📱 Telegram",
        # Ayarlar sekmesi
        "tab_settings":            "⚙️ Ayarlar",
        "set_threshold_title":     "Eşik Değerleri",
        "set_threshold_save":      "💾 Kaydet",
        "set_threshold_saved":     "Eşik değerleri kaydedildi.",
        "set_telegram_title":      "Telegram Bildirimleri",
        "set_telegram_token":      "Bot Token",
        "set_telegram_chat":       "Chat ID",
        "set_telegram_save":       "💾 Kaydet",
        "set_telegram_saved":      "Telegram ayarları kaydedildi.",
        "set_telegram_test":       "📨 Test Mesajı Gönder",
        "set_pres_section":        "**Basınç (bar)**",
        "set_sqz_min":             "Sıkıştırma Min",
        "set_sqz_max":             "Sıkıştırma Max",
        "set_oil_section":         "**Yağ Seviyesi (mm)**",
        "set_oil_min":             "HPU Yağ Seviyesi Min",
        "set_oil_max":             "HPU Yağ Seviyesi Max",
        "set_cyc_section":         "**Cycle Süresi**",
        "set_cyc_max":             "Max Cycle Süresi (s)",
        "set_temp_section":        "**Sıcaklıklar (°C)**",
        "set_seg_min":             "Segment Min",
        "set_seg_max":             "Segment Max",
        "set_upl_min":             "Üst Platen Min",
        "set_upl_max":             "Üst Platen Max",
        "set_lpl_min":             "Alt Platen Min",
        "set_lpl_max":             "Alt Platen Max",
        "set_con_min":             "Konteyner Min",
        "set_con_max":             "Konteyner Max",
        "set_no_backend":          "Backend bağlantısı yok — eşik değerleri yüklenemedi.",
        "dash_cycle_duration":     "Son 20 Cycle Süresi (s)",
        # Enerji sekmesi
        "tab_energy":         "⚡ Enerji Tüketimi",
        "ene_live_kw":        "Anlık Güç",
        "ene_daily_kwh":      "Günlük Enerji",
        "ene_air_flow":       "Hava Debisi",
        "ene_daily_nm3":      "Günlük Hava",
        "ene_per_tire_kwh":   "kWh/Lastik",
        "ene_per_tire_nm3":   "m³/Lastik",
        "ene_elec_trend":     "Elektrik Trendi (Son 24 Saat)",
        "ene_air_trend":      "Hava Trendi (Son 24 Saat)",
        "ene_shift_title":    "Vardiya Özeti",
        "ene_cycle_title":    "Cycle Bazlı Tüketim (Son 20)",
        "ene_records_title":  "Detay Kayıtlar (Son 8 Saat)",
        "ene_shift_col_shift":"Vardiya",
        "ene_shift_col_kwh":  "kWh",
        "ene_shift_col_nm3":  "m³",
        "ene_shift_col_run":  "Çalışma %",
        "ene_alerts_title":   "Enerji Uyarıları",
        "ene_no_alerts":      "Son 24 saatte enerji uyarısı yok.",
        "ene_no_data":        "Veri yok — EnergyMonitor'ı başlatın.",
        "ene_export_range":   "Rapor Tarih Aralığı",
        "ene_excel":          "📥 Excel İndir",
        "ene_pdf":            "📥 PDF İndir",
        "dash_email":         "📧 E-posta Gönder",
        "ene_email":          "📧 E-posta Gönder",
        "btn_energy":         "⚡ Anlık Enerji",
        "q_energy":           "Anlık güç tüketimi ve hava debisi kaç?",
    },
    "en": {
        "header_title":      "Curing Press — AI Assistant",
        "header_sub":        "Siemens S7-1500 &nbsp;|&nbsp; ABB ACS580 &nbsp;|&nbsp; PILZ Safety",
        "quick_label":       "Quick Questions",
        "btn_pressures":     "📊 Pressures",
        "btn_temperatures":  "🌡️ Temperatures",
        "btn_alarms":        "⚠️ Alarms",
        "q_pressures":       "Show all current pressure values",
        "q_temperatures":    "Show all current temperature values",
        "q_alarms":          "Are there any active alarms? Explain if any",
        "chat_placeholder":  "Type your question...",
        "clear_btn":         "🗑️ Clear Chat",
        "err_backend":       "❌ Cannot connect to backend. Run `python -m backend.main`.",
        "sec_alarms":        "Alarms",
        "sec_status":        "Machine Status",
        "sec_pressures":     "Pressures",
        "sec_temperatures":  "Temperatures",
        "sec_positions":     "LVDT Positions",
        "alarm_none":        "✔ No Alarms",
        "alarm_active":      "Active Alarm",
        "backend_warn":      "No backend connection",
        "metric_mode":       "Mode",
        "metric_curing":     "Curing",
        "curing_active":     "✅ Active",
        "curing_inactive":   "⏸ Inactive",
        "metric_oil":        "HPU Oil Level",
        "metric_loader":     "Loader In-Out Time",
        "metric_unloader":   "Unloader In-Out Time",
        "notif_btn":         "🔔 Notification Settings",
        "notif_title":       "Notification Settings",
        "notif_contacts":    "Registered Contacts",
        "notif_add":         "Add New Contact",
        "notif_name":        "Full Name",
        "notif_phone":       "Phone (+905XXXXXXXXX)",
        "notif_email":       "E-mail",
        "notif_add_btn":     "Add",
        "notif_no_contacts": "No contacts registered yet.",
        "notif_added":       "Contact added.",
        "notif_deleted":     "Contact deleted.",
        "notif_err":         "Error: phone or e-mail required.",
        "notif_col_name":    "Full Name",
        "notif_col_phone":   "Phone",
        "notif_col_email":   "E-mail",
        "notif_col_active":  "Active",
        "notif_col_del":     "Delete",
        "sec_anomaly":       "Anomaly Monitor",
        "anomaly_no_data":   "Not enough data (min 10 cycles)",
        "anomaly_ok":        "Last cycle normal",
        "anomaly_warn":      "Anomaly detected!",
        "anomaly_cycles":    "Recorded cycles",
        # Alarm notifications tab
        "tab_contacts":      "📋 Contacts",
        "tab_alarms":        "🔔 Alarm Notifications",
        "alarm_notif_title": "Which alarms should send notifications?",
        "alarm_notif_save":  "💾 Save",
        "alarm_notif_saved": "Settings saved.",
        "alarm_col_code":    "Code",
        "alarm_col_name":    "Alarm Name",
        "alarm_col_sev":     "Severity",
        "alarm_col_notif":   "Notify",
        # Anomaly config dialog
        "anomaly_btn":        "⚙️ Anomaly Settings",
        "anomaly_dlg_title":  "Anomaly Monitoring Settings",
        "sim_mode_label":     "Simulation Mode",
        "sim_mode_help":      "When enabled, simulated data is used instead of the real PLC",
        "cycle_notify_label": "Cycle Anomaly Notifications",
        "cycle_notify_help":  "Send email when statistical anomaly is detected at end of each cycle (pressure drift, timing, etc.)",
        "sim_anom_label":     "Simulation Anomalies",
        "sim_anom_help":      "When enabled, simulation mode generates intentional anomalies every 5/7 cycles (for testing only)",
        "monitor_values":     "Monitored Values",
        "add_value":          "Add Value",
        "col_value":          "Value",
        "col_min":            "Min Threshold",
        "col_max":            "Max Threshold",
        "col_unit":           "Unit",
        "col_enabled":        "Enabled",
        "col_notify":         "Notify",
        "col_del":            "Del",
        "no_values":          "No monitored values. Add one below.",
        "select_tag":         "Select PLC Tag",
        "btn_add_value":      "Add",
        "btn_save":           "💾 Save",
        "saved_ok":           "Settings saved.",
        # Dashboard
        "tab_chat":           "💬 Assistant",
        "tab_dashboard":      "📊 Alarm-Anomaly",
        "dash_today":         "Today",
        "dash_yesterday":     "Yesterday",
        "dash_week":          "This Week",
        "dash_custom":        "Custom Range",
        "dash_refresh":       "🔄",
        "dash_cycles":        "Cycles",
        "dash_alarms":        "Alarms",
        "dash_anomaly_rate":  "Anomaly Rate",
        "dash_avg_duration":  "Avg Duration (s)",
        "dash_daily_trend":   "Daily Cycle & Anomaly Trend",
        "dash_pressure_trend":"Pressure Trend (Avg)",
        "dash_anomaly_dist":  "Anomaly Distribution",
        "dash_top_alarms":    "Most Frequent Alarms",
        "dash_no_data":       "No data for this period.",
        "dash_excel":         "📥 Download Excel",
        "dash_pdf":           "📥 Download PDF",
        "dash_export_range":  "Export Date Range",
        "dash_anomaly_names": {
            "pressure_drift":  "Pressure Drift",
            "loader_timing":   "Loader Timing",
            "unloader_timing": "Unloader Timing",
            "press_close":     "Press Closure",
        },
        # Notification dialog — tabs
        "tab_telegram":            "📱 Telegram",
        # Settings tab
        "tab_settings":            "⚙️ Settings",
        "set_threshold_title":     "Threshold Values",
        "set_threshold_save":      "💾 Save",
        "set_threshold_saved":     "Threshold values saved.",
        "set_telegram_title":      "Telegram Notifications",
        "set_telegram_token":      "Bot Token",
        "set_telegram_chat":       "Chat ID",
        "set_telegram_save":       "💾 Save",
        "set_telegram_saved":      "Telegram settings saved.",
        "set_telegram_test":       "📨 Send Test Message",
        "set_pres_section":        "**Pressure (bar)**",
        "set_sqz_min":             "Squeezing Min",
        "set_sqz_max":             "Squeezing Max",
        "set_oil_section":         "**Oil Level (mm)**",
        "set_oil_min":             "HPU Oil Level Min",
        "set_oil_max":             "HPU Oil Level Max",
        "set_cyc_section":         "**Cycle Duration**",
        "set_cyc_max":             "Max Cycle Duration (s)",
        "set_temp_section":        "**Temperatures (°C)**",
        "set_seg_min":             "Segment Min",
        "set_seg_max":             "Segment Max",
        "set_upl_min":             "Upper Platen Min",
        "set_upl_max":             "Upper Platen Max",
        "set_lpl_min":             "Lower Platen Min",
        "set_lpl_max":             "Lower Platen Max",
        "set_con_min":             "Container Min",
        "set_con_max":             "Container Max",
        "set_no_backend":          "No backend connection — threshold values could not be loaded.",
        "dash_cycle_duration":     "Last 20 Cycle Durations (s)",
        # Energy tab
        "tab_energy":         "⚡ Energy Consumption",
        "ene_live_kw":        "Live Power",
        "ene_daily_kwh":      "Daily Energy",
        "ene_air_flow":       "Air Flow",
        "ene_daily_nm3":      "Daily Air",
        "ene_per_tire_kwh":   "kWh/Tire",
        "ene_per_tire_nm3":   "m³/Tire",
        "ene_elec_trend":     "Electricity Trend (Last 24h)",
        "ene_air_trend":      "Air Trend (Last 24h)",
        "ene_shift_title":    "Shift Summary",
        "ene_cycle_title":    "Cycle Energy (Last 20)",
        "ene_records_title":  "Detail Records (Last 8h)",
        "ene_shift_col_shift":"Shift",
        "ene_shift_col_kwh":  "kWh",
        "ene_shift_col_nm3":  "m³",
        "ene_shift_col_run":  "Running %",
        "ene_alerts_title":   "Energy Alerts",
        "ene_no_alerts":      "No energy alerts in the last 24 hours.",
        "ene_no_data":        "No data — start EnergyMonitor.",
        "ene_export_range":   "Report Date Range",
        "ene_excel":          "📥 Download Excel",
        "ene_pdf":            "📥 Download PDF",
        "dash_email":         "📧 Send Email",
        "ene_email":          "📧 Send Email",
        "btn_energy":         "⚡ Live Energy",
        "q_energy":           "What is the current power consumption and air flow?",
    },
}

# ─── Page config ───────────────────────────────────────────────────────────────

st.set_page_config(
    page_title="Curing Pres AI",
    page_icon=_LOGO_PATH if os.path.exists(_LOGO_PATH) else "🔧",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Pencereyi maximize et
_st_components.html("""
<script>
try {
    window.moveTo(0, 0);
    window.resizeTo(screen.availWidth, screen.availHeight);
} catch(e) {}
</script>
""", height=0)

# ─── Custom CSS ────────────────────────────────────────────────────────────────

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=Inter:wght@400;500;600&display=swap');

/* Streamlit deploy/hamburger menüsü ve header'ı tamamen gizle */
[data-testid="stToolbar"],
[data-testid="stDecoration"],
[data-testid="stHeader"],
#MainMenu {
    display: none !important;
    height: 0 !important;
    min-height: 0 !important;
}

/* Üst boşluğu kaldır */
.block-container {
    padding-top: 0.5rem !important;
}
[data-testid="stAppViewContainer"] > .main > .block-container {
    padding-top: 0.5rem !important;
}

/* Minimum pencere boyutu */
html, body {
    min-width: 1280px !important;
    min-height: 720px !important;
}

/* Genel arka plan */
[data-testid="stAppViewContainer"] {
    background-color: #0f1117;
}
[data-testid="stSidebar"] {
    background-color: #161b27;
    border-right: 1px solid #1e2a3a;
}

/* Header kartı */
.header-card {
    background: linear-gradient(135deg, #1a2035 0%, #0d1520 100%);
    border: 1px solid #1e3a5f;
    border-radius: 12px;
    padding: 18px 24px;
    display: flex;
    align-items: center;
    gap: 20px;
    margin-bottom: 8px;
    box-shadow: 0 4px 20px rgba(0,0,0,0.4);
}
.header-title {
    font-size: 1.7rem;
    font-weight: 700;
    color: #e8f4ff;
    margin: 0;
    line-height: 1.2;
}
.header-sub {
    font-size: 0.78rem;
    color: #4a7fa5;
    margin-top: 4px;
    letter-spacing: 0.5px;
}

/* Sidebar section başlıkları */
.sidebar-section {
    font-size: 1rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #5a9ec8;
    padding: 6px 0 4px 0;
    border-bottom: 1px solid #1e2a3a;
    margin-bottom: 8px;
}

/* Metric kartları daha kompakt */
[data-testid="stMetric"] {
    background-color: #1a2235;
    border: 1px solid #1e2e42;
    border-radius: 8px;
    padding: 8px 12px !important;
}
[data-testid="stMetricLabel"] {
    font-size: 0.7rem !important;
    color: #5a8aaa !important;
}
[data-testid="stMetricValue"] {
    font-size: 1rem !important;
    color: #c8e6ff !important;
}

/* Hızlı soru butonları */
[data-testid="stButton"] > button {
    background-color: #1a2a3f;
    border: 1px solid #1e3a5a;
    border-radius: 8px;
    color: #8ab8d8;
    font-size: 0.82rem;
    font-weight: 500;
    transition: all 0.2s;
    padding: 10px 16px;
}
[data-testid="stButton"] > button:hover {
    background-color: #1e3555;
    border-color: #2a5a8a;
    color: #c8e6ff;
    transform: translateY(-1px);
    box-shadow: 0 4px 12px rgba(0,80,150,0.3);
}

/* Chat mesaj alanı */
[data-testid="stChatMessage"] {
    border-radius: 10px;
    margin-bottom: 4px;
}

/* Chat input */
[data-testid="stChatInput"] textarea {
    background-color: #1a2235 !important;
    border: 1px solid #1e3a5f !important;
    border-radius: 10px !important;
    color: #c8e6ff !important;
    font-size: 0.9rem !important;
}

/* Divider */
hr {
    border-color: #1e2a3a !important;
    margin: 8px 0 !important;
}

/* Section label (Hızlı Sorular) */
.section-label {
    font-size: 0.72rem;
    font-weight: 700;
    text-transform: uppercase;
    letter-spacing: 1.2px;
    color: #3a6b8a;
    margin-bottom: 8px;
}

/* Sidebar caption yazıları okunabilir */
[data-testid="stSidebar"] [data-testid="stCaptionContainer"] p,
[data-testid="stSidebar"] .stCaption p {
    color: #8ab8d8 !important;
    font-size: 0.72rem !important;
    line-height: 1.5 !important;
}

/* Sidebar her zaman görünür — collapse/expand butonları gizli */
[data-testid="stSidebar"] {
    transform: none !important;
    visibility: visible !important;
    display: block !important;
    min-width: 300px !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="stSidebarNavCollapseButton"],
[data-testid="stBaseButton-headerNoPadding"],
[data-testid="collapsedControl"] {
    display: none !important;
}

/* Alarm badge */
.alarm-none {
    background: linear-gradient(90deg, #0d2a1a, #112a1a);
    border: 1px solid #1a4a2a;
    border-radius: 8px;
    padding: 8px 14px;
    color: #4caf7a;
    font-size: 0.82rem;
    font-weight: 600;
}
.alarm-active {
    background: linear-gradient(90deg, #2a0d0d, #2a1010);
    border: 1px solid #6a1a1a;
    border-radius: 8px;
    padding: 8px 14px;
    color: #ff6b6b;
    font-size: 0.82rem;
    font-weight: 600;
}
</style>
""", unsafe_allow_html=True)

# ─── Header ────────────────────────────────────────────────────────────────────

logo_html = ""
if os.path.exists(_LOGO_PATH):
    import base64
    with open(_LOGO_PATH, "rb") as f:
        logo_b64 = base64.b64encode(f.read()).decode()
    logo_html = f'<img src="data:image/png;base64,{logo_b64}" style="width:60px;height:60px;object-fit:contain;border-radius:8px;" />'

# ─── Session state ─────────────────────────────────────────────────────────────

if "messages" not in st.session_state:
    st.session_state.messages = []
if "api_history" not in st.session_state:
    st.session_state.api_history = []
if "lang" not in st.session_state:
    st.session_state.lang = "tr"
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "machine_selected" not in st.session_state:
    st.session_state.machine_selected = False

# ─── Giriş ekranı ──────────────────────────────────────────────────────────────

def _show_login():
    """Kullanıcı adı / şifre giriş ekranı."""
    _lcol1, _lcol2, _lcol3 = st.columns([1, 2, 1])
    with _lcol2:
        if os.path.exists(_LOGO_PATH):
            st.image(_LOGO_PATH, width=180)
        st.markdown("## Lastik Pişirme Presi")
        st.markdown("**Hydraulic Tire Curing Press**")
        st.divider()
        _login_user = st.text_input("Kullanıcı Adı", key="login_user")
        _login_pass = st.text_input("Şifre", type="password", key="login_pass")
        if st.button("Giriş Yap", type="primary", key="login_btn"):
            _user = check_credentials(_login_user, _login_pass)
            if _user:
                st.session_state.authenticated = True
                st.session_state.current_user  = _user
                st.rerun()
            else:
                st.error("Kullanıcı adı veya şifre hatalı.")


def _show_machine_select():
    """Makina seçim ekranı."""
    _mcol1, _mcol2, _mcol3 = st.columns([1, 2, 1])
    with _mcol2:
        if os.path.exists(_LOGO_PATH):
            st.image(_LOGO_PATH, width=120)
        _display = st.session_state.get("current_user", {}).get("display_name", "")
        st.markdown(f"### Hoş geldiniz, {_display}!")
        st.markdown("Lütfen çalışacağınız makineyi seçin:")
        st.divider()
        _machines = _load_machines()
        if not _machines:
            st.warning("Tanımlı makina bulunamadı. `data/machines.json` dosyasını kontrol edin.")
        for _m in _machines:
            _mlabel = f"**{_m['name']}** — {_m['model']}  \n📍 {_m.get('location', '')}"
            if st.button(_mlabel, key=f"mach_{_m['id']}"):
                st.session_state.machine_selected = True
                st.session_state.selected_machine  = _m
                st.rerun()
        st.divider()
        if st.button("Çıkış Yap", key="machine_logout_btn"):
            st.session_state.authenticated    = False
            st.session_state.machine_selected = False
            st.rerun()


# ─── Auth kapısı ───────────────────────────────────────────────────────────────

if not st.session_state.authenticated:
    _show_login()
    st.stop()

if not st.session_state.machine_selected:
    _show_machine_select()
    st.stop()

# ─── Header + dil butonu ───────────────────────────────────────────────────────

_col_title, _col_lang = st.columns([6, 1])
with _col_title:
    _u = _UI[st.session_state.lang]
    st.markdown(f"""
<div class="header-card">
    {logo_html}
    <div>
        <div class="header-title">{_u["header_title"]}</div>
        <div class="header-sub">{_u["header_sub"]}</div>
    </div>
</div>
""", unsafe_allow_html=True)
with _col_lang:
    _selected = st.selectbox(
        "Language",
        ["TR", "EN"],
        index=0 if st.session_state.lang == "tr" else 1,
        key="lang_select",
        label_visibility="hidden",
    )
    st.session_state.lang = _selected.lower()
# ─── Notification settings dialog ─────────────────────────────────────────────

@st.dialog("🔔 Bildirim Ayarları", width="large")
def _notification_dialog():
    _u = _UI[st.session_state.get("lang", "tr")]
    tab_contacts, tab_alarms, tab_telegram = st.tabs([
        _u["tab_contacts"], _u["tab_alarms"], _u["tab_telegram"]
    ])

    # ── Sekme 1: Kayıtlı kişiler ────────────────────────────────────────────
    with tab_contacts:
        st.subheader(_u["notif_contacts"])
        try:
            r = requests.get(f"{BACKEND_URL}/api/contacts", timeout=5)
            contacts = r.json().get("contacts", []) if r.ok else []
        except Exception:
            contacts = []
            st.warning(_u["backend_warn"])

        if contacts:
            header = st.columns([2, 2, 3, 1, 1])
            header[0].markdown(f"**{_u['notif_col_name']}**")
            header[1].markdown(f"**{_u['notif_col_phone']}**")
            header[2].markdown(f"**{_u['notif_col_email']}**")
            header[3].markdown(f"**{_u['notif_col_active']}**")
            header[4].markdown(f"**{_u['notif_col_del']}**")
            st.divider()

            for c in contacts:
                cols = st.columns([2, 2, 3, 1, 1])
                cols[0].write(c.get("name", ""))
                cols[1].write(c.get("phone", "—"))
                cols[2].write(c.get("email", "—"))

                is_active = c.get("active", True)
                if cols[3].checkbox("Aktif", value=is_active, key=f"active_{c['id']}",
                                    label_visibility="collapsed"):
                    if not is_active:
                        try:
                            requests.put(f"{BACKEND_URL}/api/contacts/{c['id']}",
                                         json={"active": True}, timeout=5)
                            st.rerun()
                        except Exception:
                            pass
                else:
                    if is_active:
                        try:
                            requests.put(f"{BACKEND_URL}/api/contacts/{c['id']}",
                                         json={"active": False}, timeout=5)
                            st.rerun()
                        except Exception:
                            pass

                if cols[4].button("🗑️", key=f"del_{c['id']}"):
                    try:
                        requests.delete(f"{BACKEND_URL}/api/contacts/{c['id']}", timeout=5)
                        st.rerun()
                    except Exception:
                        pass
        else:
            st.info(_u["notif_no_contacts"])

        st.divider()
        st.subheader(_u["notif_add"])
        with st.form("add_contact_form", clear_on_submit=True):
            name  = st.text_input(_u["notif_name"])
            col_p, col_e = st.columns(2)
            phone = col_p.text_input(_u["notif_phone"])
            email = col_e.text_input(_u["notif_email"])
            submitted = st.form_submit_button(_u["notif_add_btn"], width="stretch")

        if submitted:
            if not phone and not email:
                st.error(_u["notif_err"])
            elif not name:
                st.error(_u["notif_name"] + (" boş bırakılamaz." if st.session_state.get("lang") == "tr"
                         else " cannot be empty."))
            else:
                try:
                    resp = requests.post(
                        f"{BACKEND_URL}/api/contacts",
                        json={"name": name, "phone": phone, "email": email},
                        timeout=5,
                    )
                    if resp.ok:
                        st.success(_u["notif_added"])
                        st.rerun()
                    else:
                        st.error(resp.json().get("detail", "Hata"))
                except Exception as exc:
                    st.error(str(exc))

        st.divider()
        test_label = "📧 Test Bildirimi Gönder" if st.session_state.get("lang") == "tr" else "📧 Send Test Notification"
        if st.button(test_label, width="stretch"):
            try:
                r = requests.post(f"{BACKEND_URL}/api/contacts/test-notification", timeout=15)
                if r.ok:
                    results = r.json().get("results", [])
                    for res in results:
                        email_status = res.get("email")
                        sms_status   = res.get("sms")
                        if email_status == "ok":
                            st.success(f"✅ {res['name']} — e-posta gönderildi")
                        elif email_status:
                            st.error(f"❌ {res['name']} e-posta hatası: {email_status}")
                        if sms_status == "ok":
                            st.success(f"✅ {res['name']} — SMS gönderildi")
                        elif sms_status:
                            st.error(f"❌ {res['name']} SMS hatası: {sms_status}")
                else:
                    st.error(r.json().get("detail", "Test başarısız"))
            except Exception as exc:
                st.error(str(exc))

    # ── Sekme 3: Telegram ───────────────────────────────────────────────────
    with tab_telegram:
        st.markdown(f"**{_u['set_telegram_title']}**")
        st.caption("Bot oluşturmak için @BotFather'a yazın. Chat ID için @userinfobot'u kullanın.")
        with st.form("telegram_config_form"):
            _tg_token = st.text_input(
                _u["set_telegram_token"],
                type="password",
                placeholder="123456789:ABCdefGhIJKlmNoPQRsTUVwxyZ",
                help="@BotFather'dan alınan token",
            )
            _tg_chat = st.text_input(
                _u["set_telegram_chat"],
                placeholder="-100123456789 veya @kanal_adi",
                help="Mesajın gönderileceği chat/grup/kanal ID'si",
            )
            _tg_submit = st.form_submit_button(_u["set_telegram_save"], width="stretch")

        if _tg_submit:
            if not _tg_token or not _tg_chat:
                st.error("Token ve Chat ID boş bırakılamaz.")
            else:
                try:
                    _r = requests.put(
                        f"{BACKEND_URL}/api/telegram-config",
                        json={"telegram_bot_token": _tg_token, "telegram_chat_id": _tg_chat},
                        timeout=5,
                    )
                    if _r.ok:
                        st.success(_u["set_telegram_saved"])
                    else:
                        st.error(f"Hata: {_r.text}")
                except Exception as _e:
                    st.error(str(_e))

        st.divider()
        _test_label = "📨 Test Mesajı Gönder" if st.session_state.get("lang") == "tr" else "📨 Send Test Message"
        if st.button(_test_label, width="stretch"):
            try:
                _r = requests.post(f"{BACKEND_URL}/api/contacts/test-notification", timeout=15)
                if _r.ok:
                    _res = _r.json()
                    _tg_res = _res.get("telegram")
                    if _tg_res == "ok":
                        st.success("✅ Telegram mesajı gönderildi")
                    elif _tg_res:
                        st.error(f"❌ Telegram hatası: {_tg_res}")
                    else:
                        st.warning("Telegram yapılandırılmamış veya token/chat_id eksik.")
                    for _cr in _res.get("results", []):
                        if _cr.get("email") == "ok":
                            st.success(f"✅ {_cr['name']} — e-posta gönderildi")
                        elif _cr.get("email"):
                            st.error(f"❌ {_cr['name']} e-posta hatası: {_cr['email']}")
                else:
                    st.error(f"Hata: {_r.json().get('detail', 'Bilinmeyen hata')}")
            except Exception as _e:
                st.error(str(_e))

    # ── Sekme 2: Alarm bildirimleri ─────────────────────────────────────────
    with tab_alarms:
        st.subheader(_u["alarm_notif_title"])
        try:
            r_an = requests.get(f"{BACKEND_URL}/api/alarm-notifications", timeout=5)
            r_al = requests.get(f"{BACKEND_URL}/api/alarms", timeout=3)
            notif_map = r_an.json() if r_an.ok else {}
            alarm_info_r = requests.get(f"{BACKEND_URL}/api/contacts", timeout=3)  # reuse backend data
        except Exception:
            notif_map = {}
            st.warning(_u["backend_warn"])

        # Load alarm definitions from knowledge base via a helper endpoint
        # We'll read them from the already-fetched alarm-notifications plus local alarm names
        # by fetching the full alarm list via a dedicated endpoint we add, or use the
        # notification map keys paired with names from a second call.
        # Since we don't have a dedicated alarm-list endpoint, we'll show code + toggle only.
        sev_icons = {"critical": "🚨", "high": "⚠️", "medium": "⚡", "low": "ℹ️"}

        # Fetch alarm details for display
        try:
            r_details = requests.get(f"{BACKEND_URL}/api/alarm-details", timeout=5)
            alarm_details = r_details.json() if r_details.ok else {}
        except Exception:
            alarm_details = {}

        header_cols = st.columns([1, 3, 1, 1])
        header_cols[0].markdown(f"**{_u['alarm_col_code']}**")
        header_cols[1].markdown(f"**{_u['alarm_col_name']}**")
        header_cols[2].markdown(f"**{_u['alarm_col_sev']}**")
        header_cols[3].markdown(f"**{_u['alarm_col_notif']}**")
        st.divider()

        new_notif = {}
        for code, current_val in sorted(notif_map.items()):
            detail = alarm_details.get(code, {})
            name = detail.get("name", code)
            sev  = detail.get("severity", "")
            cols = st.columns([1, 3, 1, 1])
            cols[0].write(f"`{code}`")
            cols[1].write(name)
            cols[2].write(f"{sev_icons.get(sev, '')} {sev}")
            new_val = cols[3].checkbox(
                "notify", value=bool(current_val),
                key=f"alarm_notif_{code}", label_visibility="collapsed"
            )
            new_notif[code] = new_val

        st.divider()
        if st.button(_u["alarm_notif_save"], width="stretch"):
            try:
                resp = requests.put(f"{BACKEND_URL}/api/alarm-notifications",
                                    json=new_notif, timeout=5)
                if resp.ok:
                    st.success(_u["alarm_notif_saved"])
                else:
                    st.error("Kayıt hatası")
            except Exception as exc:
                st.error(str(exc))


# ─── PLC tag catalog (for anomaly config dropdown) ────────────────────────────

_PLC_TAGS: list[dict] = [
    {"id": "ISP_HP",               "label_tr": "İç Buhar Basıncı (HP)",      "label_en": "Internal Steam Pressure (HP)",   "unit": "bar"},
    {"id": "ISP_LP",               "label_tr": "İç Buhar Basıncı (LP)",      "label_en": "Internal Steam Pressure (LP)",   "unit": "bar"},
    {"id": "SQZ",                  "label_tr": "Sıkıştırma Basıncı",         "label_en": "Squeeze Pressure",               "unit": "bar"},
    {"id": "RTD_EST_T",            "label_tr": "Dış Buhar Sıcaklığı Üst",   "label_en": "Ext. Steam Temp Top",            "unit": "°C"},
    {"id": "RTD_EST_B",            "label_tr": "Dış Buhar Sıcaklığı Alt",   "label_en": "Ext. Steam Temp Bottom",         "unit": "°C"},
    {"id": "RTD_EST_C",            "label_tr": "Dış Buhar Sıcaklığı Konteynır", "label_en": "Ext. Steam Temp Container", "unit": "°C"},
    {"id": "RTD_IST",              "label_tr": "Segment/Kont. Kondensasyon", "label_en": "Seg/Cont Condensate Temp",       "unit": "°C"},
    {"id": "RTD_SGT",              "label_tr": "Segment Sıcaklığı",          "label_en": "Segment Temperature",            "unit": "°C"},
    {"id": "RTD_BLD",              "label_tr": "Balon Sızıntı Sıcaklığı",   "label_en": "Bladder Leakage Temp",           "unit": "°C"},
    {"id": "RTD_EST_Trap",         "label_tr": "Kondensasyon Tuzağı",        "label_en": "Condensate Trap Temp",           "unit": "°C"},
    {"id": "RTD_TB",               "label_tr": "Kabin Sıcaklığı",            "label_en": "Cabinet Temperature",            "unit": "°C"},
    {"id": "HPU_Oiltemp",          "label_tr": "Hidrolik Yağ Sıcaklığı",    "label_en": "HPU Oil Temperature",            "unit": "°C"},
    {"id": "HPU_Oillevel",         "label_tr": "Hidrolik Yağ Seviyesi",      "label_en": "HPU Oil Level",                  "unit": "mm"},
    {"id": "LVTD_PR",              "label_tr": "Pres LVDT Pozisyonu",        "label_en": "Press LVDT Position",            "unit": "mm"},
    {"id": "LVTD_LO",              "label_tr": "Loader LVDT Pozisyonu",      "label_en": "Loader LVDT Position",           "unit": "mm"},
    {"id": "LVTD_UN",              "label_tr": "Unloader LVDT Pozisyonu",    "label_en": "Unloader LVDT Position",         "unit": "mm"},
    {"id": "LVTD_TR",              "label_tr": "Üst Halka LVDT",             "label_en": "Top Clamp Ring LVDT",            "unit": "mm"},
    {"id": "LVTD_SMO",             "label_tr": "Segment LVDT",               "label_en": "Segment LVDT",                   "unit": "mm"},
    {"id": "Loader_In_Out_Time",   "label_tr": "Loader In-Out Süresi",       "label_en": "Loader In/Out Time",             "unit": "s"},
    {"id": "Unloader_In_Out_Time", "label_tr": "Unloader In-Out Süresi",     "label_en": "Unloader In/Out Time",           "unit": "s"},
]
_TAG_BY_ID = {t["id"]: t for t in _PLC_TAGS}


# ─── Anomaly config dialog ─────────────────────────────────────────────────────

@st.dialog("⚙️ Anomali Ayarları", width="large")
def _anomaly_config_dialog():
    _u = _UI[st.session_state.get("lang", "tr")]
    lang = st.session_state.get("lang", "tr")
    label_key = "label_tr" if lang == "tr" else "label_en"

    if "anom_cfg" not in st.session_state:
        try:
            r = requests.get(f"{BACKEND_URL}/api/anomaly-config", timeout=5)
            st.session_state["anom_cfg"] = r.json() if r.ok else {"simulation_mode_override": False, "monitored_values": []}
        except Exception:
            st.session_state["anom_cfg"] = {"simulation_mode_override": False, "monitored_values": []}
            st.warning(_u["backend_warn"])
    cfg = st.session_state["anom_cfg"]

    # ── Simülasyon modu toggle ──────────────────────────────────────────────
    sim_override = st.checkbox(
        _u["sim_mode_label"],
        value=cfg.get("simulation_mode_override", False),
        help=_u["sim_mode_help"],
        key="anom_sim_override",
    )
    cfg["simulation_mode_override"] = sim_override

    cycle_notify = st.checkbox(
        _u["cycle_notify_label"],
        value=cfg.get("cycle_anomaly_notify", True),
        help=_u["cycle_notify_help"],
        key="anom_cycle_notify",
    )
    cfg["cycle_anomaly_notify"] = cycle_notify

    sim_anom = st.checkbox(
        _u["sim_anom_label"],
        value=cfg.get("sim_anomaly_enabled", False),
        help=_u["sim_anom_help"],
        key="anom_sim_anom",
    )
    cfg["sim_anomaly_enabled"] = sim_anom

    st.divider()

    # ── Cycle anomali kontrolleri ───────────────────────────────────────────
    st.subheader("İstatistiksel Cycle Anomali Kontrolleri" if st.session_state.get("lang") == "tr" else "Statistical Cycle Anomaly Checks")
    _cycle_checks = cfg.get("cycle_anomaly_checks", [])
    _label_key_cc = "label_tr" if st.session_state.get("lang") == "tr" else "label_en"
    for _cc in _cycle_checks:
        _cc["enabled"] = st.checkbox(
            _cc.get(_label_key_cc, _cc["id"]),
            value=_cc.get("enabled", True),
            key=f"cc_{_cc['id']}",
        )
    cfg["cycle_anomaly_checks"] = _cycle_checks

    st.divider()

    # ── İzlenen değerler tablosu ────────────────────────────────────────────
    st.subheader(_u["monitor_values"])
    monitored = cfg.get("monitored_values", [])

    if not monitored:
        st.info(_u["no_values"])
    else:
        header = st.columns([3, 1.5, 1.5, 1, 1, 1, 0.7])
        for col, label in zip(header, [
            _u["col_value"], _u["col_min"], _u["col_max"],
            _u["col_unit"], _u["col_enabled"], _u["col_notify"], _u["col_del"]
        ]):
            col.markdown(f"**{label}**")
        st.divider()

        to_delete = []
        for i, mv in enumerate(monitored):
            tag_info = _TAG_BY_ID.get(mv["id"], {})
            display_name = tag_info.get(label_key, mv["id"])
            cols = st.columns([3, 1.5, 1.5, 1, 1, 1, 0.7])
            cols[0].write(f"{display_name}  \n`{mv['id']}`")

            th_min = cols[1].number_input(
                "min", value=float(mv["threshold_min"]) if mv.get("threshold_min") is not None else 0.0,
                key=f"tmin_{mv['id']}", label_visibility="collapsed", step=0.5
            )
            th_max = cols[2].number_input(
                "max", value=float(mv["threshold_max"]) if mv.get("threshold_max") is not None else 0.0,
                key=f"tmax_{mv['id']}", label_visibility="collapsed", step=0.5
            )
            cols[3].write(mv.get("unit", ""))
            mv["enabled"] = cols[4].checkbox("e", value=mv.get("enabled", True),
                                              key=f"en_{mv['id']}", label_visibility="collapsed")
            mv["notify"]  = cols[5].checkbox("n", value=mv.get("notify", False),
                                              key=f"nt_{mv['id']}", label_visibility="collapsed")
            if cols[6].button("🗑️", key=f"delmv_{mv['id']}"):
                to_delete.append(i)

            mv["threshold_min"] = th_min if th_min != 0.0 else None
            mv["threshold_max"] = th_max if th_max != 0.0 else None

        for idx in reversed(to_delete):
            monitored.pop(idx)
        if to_delete:
            cfg["monitored_values"] = monitored
            st.session_state["anom_cfg"] = cfg

    st.divider()

    # ── Değer ekle ──────────────────────────────────────────────────────────
    st.subheader(_u["add_value"])
    existing_ids = {mv["id"] for mv in monitored}
    available = [t for t in _PLC_TAGS if t["id"] not in existing_ids]
    if available:
        tag_labels = [f"{t[label_key]}  ({t['id']})" for t in available]
        sel_idx = st.selectbox(_u["select_tag"], range(len(tag_labels)),
                               format_func=lambda i: tag_labels[i], label_visibility="collapsed")
        col_add_min, col_add_max, col_add_btn = st.columns([2, 2, 1])
        new_min = col_add_min.number_input("Min", value=0.0, step=0.5, key="new_min")
        new_max = col_add_max.number_input("Max", value=0.0, step=0.5, key="new_max")
        if col_add_btn.button(_u["btn_add_value"], width="stretch"):
            chosen = available[sel_idx]
            monitored.append({
                "id":             chosen["id"],
                "label_tr":       chosen["label_tr"],
                "label_en":       chosen["label_en"],
                "unit":           chosen["unit"],
                "threshold_min":  new_min if new_min != 0.0 else None,
                "threshold_max":  new_max if new_max != 0.0 else None,
                "enabled":        True,
                "notify":         False,
            })
            cfg["monitored_values"] = monitored
            st.session_state["anom_cfg"] = cfg

    st.divider()

    # ── Kaydet ─────────────────────────────────────────────────────────────
    cfg["monitored_values"] = monitored
    if st.button(_u["btn_save"], width="stretch"):
        try:
            resp = requests.put(f"{BACKEND_URL}/api/anomaly-config", json=cfg, timeout=5)
            if resp.ok:
                st.session_state.pop("anom_cfg", None)
                st.success(_u["saved_ok"])
            else:
                st.error("Kayıt hatası")
        except Exception as exc:
            st.error(str(exc))


# ─── Sidebar: Live machine data ────────────────────────────────────────────────

@st.fragment(run_every="1s")
def sidebar_data():
    _u = _UI[st.session_state.get("lang", "tr")]

    # ── Alarmlar ────────────────────────────────────────────────────────────────
    try:
        r = requests.get(f"{BACKEND_URL}/api/alarms", timeout=3)
        if r.ok:
            alarm_data = r.json()
            count = alarm_data.get("active_alarm_count", 0)
            st.markdown(f'<div class="sidebar-section">{_u["sec_alarms"]}</div>', unsafe_allow_html=True)
            if count > 0:
                st.markdown(f'<div class="alarm-active">⚠️ {count} {_u["alarm_active"]}</div>', unsafe_allow_html=True)
                for a in alarm_data.get("active_alarms", []):
                    st.error(f"{a['code']}: {a['name']}")
            else:
                st.markdown(f'<div class="alarm-none">{_u["alarm_none"]}</div>', unsafe_allow_html=True)
    except Exception:
        pass

    st.divider()

    # ── Makine Durumu ───────────────────────────────────────────────────────────
    try:
        r = requests.get(f"{BACKEND_URL}/api/status", timeout=3)
        if r.ok:
            s = r.json()
            st.markdown(f'<div class="sidebar-section">{_u["sec_status"]}</div>', unsafe_allow_html=True)
            mod = s.get("mod", "?")
            mod_icons = {"OTOMATİK": "🟢", "MANUEL": "🟡", "KALIP DEĞİŞİM": "🔵"}
            st.metric(_u["metric_mode"], f"{mod_icons.get(mod, '⚪')} {mod}")
            pisirme = _u["curing_active"] if s.get("pisirme_aktif") else _u["curing_inactive"]
            st.metric(_u["metric_curing"], pisirme)
            seviye = s.get("hpu_yag_seviyesi_lt")
            if seviye is not None:
                oil_label = _u["metric_oil"]
                label = f"{oil_label} ❗" if _out_of_range(seviye, _T.oil_level_min, _T.oil_level_max) else oil_label
                st.metric(label, f"{seviye:.0f} lt")
            _loader_t = s.get("loader_sure_s")
            _unloader_t = s.get("unloader_sure_s")
    except Exception:
        st.warning(_u["backend_warn"])
        _loader_t = None
        _unloader_t = None

    st.divider()

    # ── Basınçlar ───────────────────────────────────────────────────────────────
    _PRESS_THRESH = {
        "Squeeze Pressure": (_T.sqz_min, _T.sqz_max),
    }
    try:
        r = requests.get(f"{BACKEND_URL}/api/pressures", timeout=3)
        if r.ok:
            p = r.json()
            st.markdown(f'<div class="sidebar-section">{_u["sec_pressures"]}</div>', unsafe_allow_html=True)
            for val in p.values():
                if isinstance(val, dict) and "value" in val:
                    v = val["value"]
                    if v is not None:
                        desc = val.get("desc", "")
                        lims = _PRESS_THRESH.get(desc)
                        if lims and _out_of_range(v, lims[0], lims[1]):
                            st.metric(f"{desc} ❗", f"{v:.1f} {val.get('unit', '')}")
                        else:
                            st.metric(desc, f"{v:.1f} {val.get('unit', '')}")
    except Exception:
        pass

    st.divider()

    # ── Sıcaklıklar ────────────────────────────────────────────────────────────
    _TEMP_THRESH = {
        "Segment temperature":      (_T.segment_temp_min,    _T.segment_temp_max),
        "External steam Top":       (_T.upper_platen_min,    _T.upper_platen_max),
        "External steam Bottom":    (_T.lower_platen_min,    _T.lower_platen_max),
        "External steam Container": (_T.container_temp_min,  _T.container_temp_max),
        "Condensate trap":          (_T.trap_temp_min,       _T.trap_temp_max),
    }
    try:
        r = requests.get(f"{BACKEND_URL}/api/temperatures", timeout=3)
        if r.ok:
            t = r.json()
            st.markdown(f'<div class="sidebar-section">{_u["sec_temperatures"]}</div>', unsafe_allow_html=True)
            for val in t.values():
                if isinstance(val, dict) and "value" in val:
                    v = val["value"]
                    if v is not None:
                        desc = val.get("desc", "")
                        lims = _TEMP_THRESH.get(desc)
                        if lims and _out_of_range(v, lims[0], lims[1]):
                            st.metric(f"{desc} ❗", f"{v:.1f} {val.get('unit', '')}")
                        else:
                            st.metric(desc, f"{v:.1f} {val.get('unit', '')}")
    except Exception:
        pass

    st.divider()

    # ── Pozisyonlar ─────────────────────────────────────────────────────────────
    try:
        r = requests.get(f"{BACKEND_URL}/api/positions", timeout=3)
        if r.ok:
            pos = r.json()
            st.markdown(f'<div class="sidebar-section">{_u["sec_positions"]}</div>', unsafe_allow_html=True)
            for val in pos.values():
                if isinstance(val, dict) and "value" in val:
                    v = val["value"]
                    if v is not None:
                        st.metric(val.get("desc", ""), f"{v:.1f} {val.get('unit', '')}")
    except Exception:
        pass

    st.divider()

    # ── Loader / Unloader Süre ──────────────────────────────────────────────────
    try:
        if _loader_t is not None:
            st.metric(_u["metric_loader"], f"{_loader_t:.1f} s")
        if _unloader_t is not None:
            st.metric(_u["metric_unloader"], f"{_unloader_t:.1f} s")
    except Exception:
        pass

    st.divider()

    # ── Anomali İzleme ──────────────────────────────────────────────────────────
    try:
        ar = requests.get(f"{BACKEND_URL}/api/anomalies/latest", timeout=2)
        if ar.ok:
            anom = ar.json()
            st.markdown(
                f'<div class="sidebar-section">{_u["sec_anomaly"]}</div>',
                unsafe_allow_html=True,
            )
            if anom is None:
                st.caption(_u["anomaly_no_data"])
            elif not anom.get("enough_data"):
                total = anom.get("total_cycles", 0)
                st.caption(f'{_u["anomaly_no_data"]} ({total}/10)')
            elif not anom.get("has_anomaly"):
                st.success(_u["anomaly_ok"], icon="✅")
            else:
                st.warning(_u["anomaly_warn"], icon="⚠️")
                for line in anom.get("detail_lines", []):
                    st.caption(f"• {line}")
            if anom is not None:
                st.caption(f'{_u["anomaly_cycles"]}: {anom.get("total_cycles", 0)}')
    except Exception:
        pass

    st.divider()

    # ── Anlık Enerji ────────────────────────────────────────────────────────────
    st.markdown('<div class="sidebar-section">⚡ Enerji</div>', unsafe_allow_html=True)
    try:
        _ene_r = requests.get(f"{BACKEND_URL}/api/energy/current", timeout=2)
        if _ene_r.ok:
            _ene = _ene_r.json()
            _ec1, _ec2 = st.columns(2)
            _ec1.metric("Güç", f'{_ene.get("energy_kw") or 0:.1f} kW')
            _ec2.metric("Hava", f'{_ene.get("air_flow") or 0:.1f} m³/h')
    except Exception:
        pass


with st.sidebar:
    sidebar_data()
    _u_side = _UI[st.session_state.get("lang", "tr")]
    _btn_col1, _btn_col2 = st.columns(2)
    with _btn_col1:
        if st.button(_u_side["notif_btn"], width="stretch"):
            _notification_dialog()
    with _btn_col2:
        if st.button(_u_side["anomaly_btn"], width="stretch"):
            _anomaly_config_dialog()
    st.divider()
    if st.button("🚪 Çıkış", width="stretch", key="sidebar_logout_btn"):
        st.session_state.authenticated    = False
        st.session_state.machine_selected = False
        st.rerun()

# ─── Sekmeler ──────────────────────────────────────────────────────────────────

_u = _UI[st.session_state.lang]
_tab_chat, _tab_dash, _tab_energy, _tab_settings = st.tabs([
    _u["tab_chat"], _u["tab_dashboard"], _u["tab_energy"], _u["tab_settings"]
])

# ─── Dashboard sekmesi ─────────────────────────────────────────────────────────

with _tab_dash:
    import plotly.graph_objects as go
    from datetime import date as _date, timedelta as _timedelta

    # ── Tarih filtresi ──────────────────────────────────────────────────────
    _today = _date.today()
    _fcol1, _fcol2, _fcol3, _fcol4, _fcol5 = st.columns([1, 1, 1, 2, 0.4])
    if _fcol1.button(_u["dash_today"],     width="stretch", key="df_today"):
        st.session_state["dash_start"] = _today.isoformat()
        st.session_state["dash_end"]   = _today.isoformat()
        st.session_state["dash_mode"]  = "daily"
    if _fcol2.button(_u["dash_yesterday"], width="stretch", key="df_yesterday"):
        _yest = (_today - _timedelta(days=1)).isoformat()
        st.session_state["dash_start"] = _yest
        st.session_state["dash_end"]   = _yest
        st.session_state["dash_mode"]  = "daily"
    if _fcol3.button(_u["dash_week"],      width="stretch", key="df_week"):
        st.session_state["dash_start"] = (_today - _timedelta(days=6)).isoformat()
        st.session_state["dash_end"]   = _today.isoformat()
        st.session_state["dash_mode"]  = "trend"
    with _fcol4:
        _dr = st.date_input("Tarih aralığı", value=(_today, _today), key="dash_date_range",
                            label_visibility="collapsed")
        if isinstance(_dr, (list, tuple)) and len(_dr) == 2:
            st.session_state["dash_start"] = _dr[0].isoformat()
            st.session_state["dash_end"]   = _dr[1].isoformat()
            _days_diff = (_dr[1] - _dr[0]).days
            st.session_state["dash_mode"] = "trend" if _days_diff > 0 else "daily"
    if _fcol5.button(_u["dash_refresh"], width="stretch", key="df_refresh"):
        st.rerun()

    _dash_start = st.session_state.get("dash_start", _today.isoformat())
    _dash_end   = st.session_state.get("dash_end",   _today.isoformat())
    _dash_mode  = st.session_state.get("dash_mode",  "daily")

    # ── Veri çek ────────────────────────────────────────────────────────────
    try:
        _daily_r = requests.get(
            f"{BACKEND_URL}/api/report/daily", params={"date": _dash_start}, timeout=5
        )
        _daily = _daily_r.json() if _daily_r.ok else {}
        _trend_days = max(7, (_date.fromisoformat(_dash_end) - _date.fromisoformat(_dash_start)).days + 1)
        _trend_r = requests.get(
            f"{BACKEND_URL}/api/report/trend", params={"days": min(_trend_days, 30)}, timeout=5
        )
        _trend = _trend_r.json() if _trend_r.ok else []
    except Exception:
        _daily, _trend = {}, []
        st.warning(_u["backend_warn"])

    _cs = _daily.get("cycles", {})
    _as = _daily.get("alarms", {})

    # ── KPI Kartları ────────────────────────────────────────────────────────
    st.divider()
    _k1, _k2, _k3, _k4 = st.columns(4)
    _k1.metric(_u["dash_cycles"],       _cs.get("count", 0))
    _k2.metric(_u["dash_alarms"],       _as.get("count", 0))
    _k3.metric(_u["dash_anomaly_rate"], f"{_cs.get('anomaly_rate', 0)}%")
    _k4.metric(_u["dash_avg_duration"], f"{_cs.get('avg_duration', 0)} s")

    st.divider()

    # ── Grafikler ───────────────────────────────────────────────────────────
    _gc1, _gc2 = st.columns(2)

    with _gc1:
        st.markdown(f"**{_u['dash_daily_trend']}**")
        if _trend:
            _dates   = [d["date"] for d in _trend]
            _c_cnts  = [d["cycle_count"] for d in _trend]
            _a_cnts  = [d["anomaly_count"] for d in _trend]
            _fig1 = go.Figure()
            _fig1.add_bar(x=_dates, y=_c_cnts, name="Cycle", marker_color="#2a5a8a")
            _fig1.add_bar(x=_dates, y=_a_cnts, name="Anomali", marker_color="#d94f4f")
            _fig1.update_layout(
                barmode="overlay", paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font_color="#8ab8d8", margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(bgcolor="rgba(0,0,0,0)"), height=260,
                xaxis=dict(gridcolor="#1e2a3a"), yaxis=dict(gridcolor="#1e2a3a"),
            )
            st.plotly_chart(_fig1)
        else:
            st.info(_u["dash_no_data"])

    with _gc2:
        st.markdown(f"**{_u['dash_pressure_trend']}**")
        if _trend and any(d.get("avg_duration") for d in _trend):
            # Günlük basınç verisini daily endpoint'ten alamıyoruz; süre trendini göster
            _dur = [d["avg_duration"] for d in _trend]
            _al  = [d["alarm_count"]  for d in _trend]
            _fig2 = go.Figure()
            _fig2.add_scatter(x=_dates, y=_dur, mode="lines+markers",
                              name="Ort. Süre (s)", line=dict(color="#4a9ec8", width=2))
            _fig2.add_scatter(x=_dates, y=_al, mode="lines+markers",
                              name="Alarm", line=dict(color="#e8a44a", width=2), yaxis="y2")
            _fig2.update_layout(
                paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
                font_color="#8ab8d8", margin=dict(l=0, r=0, t=10, b=0),
                legend=dict(bgcolor="rgba(0,0,0,0)"), height=260,
                xaxis=dict(gridcolor="#1e2a3a"),
                yaxis=dict(gridcolor="#1e2a3a", title="Süre (s)"),
                yaxis2=dict(overlaying="y", side="right", title="Alarm"),
            )
            st.plotly_chart(_fig2)
        else:
            st.info(_u["dash_no_data"])

    # ── Cycle süresi trendi ─────────────────────────────────────────────────
    st.markdown(f"**{_u['dash_cycle_duration']}**")
    try:
        _cyc_hist_r = requests.get(f"{BACKEND_URL}/api/cycles/history", params={"n": 20}, timeout=5)
        _cyc_hist   = _cyc_hist_r.json() if _cyc_hist_r.ok else []
        _thr_r      = requests.get(f"{BACKEND_URL}/api/thresholds", timeout=5)
        _thr_data   = _thr_r.json() if _thr_r.ok else {}
        _dur_max    = _thr_data.get("cycle_duration_max_s", 1200.0)
    except Exception:
        _cyc_hist, _dur_max = [], 1200.0
    if _cyc_hist:
        _cdlbls = [f"#{r['id']}" for r in reversed(_cyc_hist)]
        _cddurs = [r.get("duration_s") or 0 for r in reversed(_cyc_hist)]
        _fig_d  = go.Figure()
        _fig_d.add_trace(go.Bar(
            x=_cdlbls, y=_cddurs, name="Süre (s)",
            marker_color=["#d94f4f" if d > _dur_max else "#5a8a4a" for d in _cddurs],
        ))
        _fig_d.add_hline(
            y=_dur_max, line_dash="dot", line_color="#e8a44a",
            annotation_text=f"Eşik {_dur_max:.0f}s", annotation_position="top right",
        )
        _fig_d.update_layout(
            paper_bgcolor="#0f1117", plot_bgcolor="#0f1117",
            font_color="#8ab8d8", margin=dict(l=0, r=0, t=20, b=40),
            height=220, showlegend=False,
            xaxis=dict(gridcolor="#1e2a3a", tickangle=-45),
            yaxis=dict(gridcolor="#1e2a3a", title="Saniye"),
        )
        st.plotly_chart(_fig_d, key="dash_cycle_dur_chart")
    else:
        st.info(_u["dash_no_data"])

    # ── Tablolar ────────────────────────────────────────────────────────────
    _tc1, _tc2 = st.columns(2)

    with _tc1:
        st.markdown(f"**{_u['dash_anomaly_dist']}**")
        _anames = _u.get("dash_anomaly_names", {})
        _abreak = _daily.get("anomaly_breakdown", {})
        if _abreak:
            _adf = [
                {"Tip": _anames.get(k, k), "Sayı": v}
                for k, v in _abreak.items()
            ]
            st.dataframe(_adf, hide_index=True)
        else:
            st.info(_u["dash_no_data"])

    with _tc2:
        st.markdown(f"**{_u['dash_top_alarms']}**")
        _top = _as.get("top_codes", [])
        if _top:
            _tdf = [{"Kod": a["code"], "Ad": a["name"], "Sayı": a["count"]} for a in _top]
            st.dataframe(_tdf, hide_index=True)
        else:
            st.info(_u["dash_no_data"])

    # ── Export ──────────────────────────────────────────────────────────────
    st.divider()
    st.markdown(f"**{_u['dash_export_range']}**")
    _ex1, _ex2, _ex3, _ex4 = st.columns([2, 1, 1, 1])
    with _ex1:
        _exp_dr = st.date_input("Export aralığı", value=(_today, _today), key="export_range",
                                label_visibility="collapsed")
        _exp_start = _exp_dr[0].isoformat() if isinstance(_exp_dr, (list, tuple)) else _today.isoformat()
        _exp_end   = _exp_dr[1].isoformat() if isinstance(_exp_dr, (list, tuple)) and len(_exp_dr) == 2 else _exp_start

    with _ex2:
        _excel_bytes = _cached_excel(_exp_start, _exp_end)
        if _excel_bytes:
            st.download_button(
                _u["dash_excel"],
                data=_excel_bytes,
                file_name=f"uretim_{_exp_start}_{_exp_end}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        else:
            st.button(_u["dash_excel"], disabled=True, width="stretch",
                      help="openpyxl yüklü değil")

    with _ex3:
        _pdf_bytes = _cached_pdf(_dash_start, _dash_end, st.session_state.lang)
        if _pdf_bytes:
            st.download_button(
                _u["dash_pdf"],
                data=_pdf_bytes,
                file_name=f"uretim_{_dash_start}_{_dash_end}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        else:
            st.button(_u["dash_pdf"], disabled=True, width="stretch",
                      help="fpdf2 yüklü değil")

    with _ex4:
        if st.button(_u["dash_email"], width="stretch", key="dash_send_email"):
            try:
                _er = requests.post(
                    f"{BACKEND_URL}/api/report/send-email",
                    params={"format": "pdf", "start": _exp_start, "end": _exp_end},
                    timeout=30,
                )
                if _er.ok:
                    st.toast("📧 E-posta gönderildi")
                else:
                    st.toast(f"❌ Hata: {_er.text}")
            except Exception as _email_exc:
                st.toast(f"❌ {_email_exc}")

# ─── Enerji sekmesi ────────────────────────────────────────────────────────────

import plotly.graph_objects as _go2

_BASE_URL = "http://localhost:8000"

@st.cache_data(ttl=1)
def _ene_current():
    try:
        return requests.get(f"{_BASE_URL}/api/energy/current", timeout=3).json()
    except Exception:
        return {}

@st.cache_data(ttl=25)
def _ene_today():
    try:
        return requests.get(f"{_BASE_URL}/api/energy/today", timeout=3).json()
    except Exception:
        return {}

@st.cache_data(ttl=25)
def _ene_trend(hours=24):
    try:
        return requests.get(f"{_BASE_URL}/api/energy/trend?hours={hours}", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=25)
def _ene_shift():
    try:
        return requests.get(f"{_BASE_URL}/api/energy/shift-summary", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=25)
def _ene_cycles(n=20):
    try:
        return requests.get(f"{_BASE_URL}/api/energy/cycles?n={n}", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=25)
def _ene_alerts(hours=24):
    try:
        return requests.get(f"{_BASE_URL}/api/energy/alerts?hours={hours}", timeout=5).json()
    except Exception:
        return []

@st.cache_data(ttl=25)
def _ene_records(hours=8):
    try:
        return requests.get(f"{_BASE_URL}/api/energy/records?hours={hours}", timeout=5).json()
    except Exception:
        return []

@st.fragment(run_every="1s")
def _energy_live():
    """Sadece anlık güç ve hava debisi — 1 saniyede bir güncellenir."""
    _u   = _UI[st.session_state.get("lang", "tr")]
    _cur = _ene_current()
    _kc1, _kc2 = st.columns(2)
    _kc1.metric(_u["ene_live_kw"],  f'{_cur.get("energy_kw") or 0:.1f} kW')
    _kc2.metric(_u["ene_air_flow"], f'{_cur.get("air_flow")  or 0:.1f} m³/h')

@st.fragment(run_every="30s")
def _energy_tab():
    _u = _UI[st.session_state.get("lang", "tr")]
    _etod    = _ene_today()
    _trend   = _ene_trend(24)
    _shift   = _ene_shift()
    _cycles  = _ene_cycles(20)
    _ealerts = _ene_alerts(24)
    _erecs   = _ene_records(8)

    # ── Günlük + lastik başı KPI'lar ────────────────────────────────────────
    _kc2, _kc4, _kc5, _kc6 = st.columns(4)
    _kc2.metric(_u["ene_daily_kwh"],    f'{_etod.get("kwh_total")    or 0:.2f} kWh')
    _kc4.metric(_u["ene_daily_nm3"],    f'{_etod.get("nm3_total")    or 0:.3f} m³')
    _kc5.metric(_u["ene_per_tire_kwh"], f'{_etod.get("kwh_per_tire") or 0:.3f}')
    _kc6.metric(_u["ene_per_tire_nm3"], f'{_etod.get("nm3_per_tire") or 0:.4f}')

    st.divider()

    # ── Trend grafikleri ─────────────────────────────────────────────────
    _gcol1, _gcol2 = st.columns(2)

    with _gcol1:
        st.markdown(f'<div class="section-label">{_u["ene_elec_trend"]}</div>', unsafe_allow_html=True)
        if _trend:
            _hours_lbl = [r["hour"] for r in _trend]
            _kw_vals   = [r["kw_mean"] for r in _trend]
            _fig_e = _go2.Figure()
            _fig_e.add_trace(_go2.Scatter(
                x=_hours_lbl, y=_kw_vals, name="kW",
                mode="lines+markers", fill="tozeroy",
                line=dict(color="#2a5a8a", width=2),
                fillcolor="rgba(42,90,138,0.15)",
                marker=dict(size=4),
            ))
            _fig_e.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8d6e5",
                height=280,
                margin=dict(l=10, r=10, t=20, b=40),
                showlegend=False,
                yaxis=dict(title="kW", gridcolor="#1e2a3a"),
                xaxis=dict(gridcolor="#1e2a3a"),
            )
            st.plotly_chart(_fig_e, key="ene_elec_chart")
        else:
            st.caption(_u["ene_no_data"])

    with _gcol2:
        st.markdown(f'<div class="section-label">{_u["ene_air_trend"]}</div>', unsafe_allow_html=True)
        if _trend:
            _air_vals = [r["air_flow_mean"] for r in _trend]
            _fig_a = _go2.Figure()
            _fig_a.add_trace(_go2.Scatter(
                x=_hours_lbl, y=_air_vals, name="m³/h",
                mode="lines+markers", fill="tozeroy",
                line=dict(color="#2a7a5a", width=2),
                fillcolor="rgba(42,122,90,0.15)",
                marker=dict(size=4),
            ))
            _fig_a.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8d6e5",
                height=280,
                margin=dict(l=10, r=10, t=20, b=40),
                showlegend=False,
                yaxis=dict(title="m³/h", gridcolor="#1e2a3a"),
                xaxis=dict(gridcolor="#1e2a3a"),
            )
            st.plotly_chart(_fig_a, key="ene_air_chart")
        else:
            st.caption(_u["ene_no_data"])

    st.divider()

    # ── Alt bölüm ────────────────────────────────────────────────────────
    _bcol1, _bcol2 = st.columns([1, 2])

    with _bcol1:
        st.markdown(f'<div class="section-label">{_u["ene_shift_title"]}</div>', unsafe_allow_html=True)
        if _shift:
            import pandas as _pd2
            _sdf = _pd2.DataFrame(_shift)
            _sdf = _sdf.rename(columns={
                "shift":       _u["ene_shift_col_shift"],
                "kwh_total":   _u["ene_shift_col_kwh"],
                "nm3_total":   _u["ene_shift_col_nm3"],
                "running_pct": _u["ene_shift_col_run"],
            })[[ _u["ene_shift_col_shift"], _u["ene_shift_col_kwh"],
                 _u["ene_shift_col_nm3"],   _u["ene_shift_col_run"] ]]
            st.dataframe(_sdf, hide_index=True)
        else:
            st.caption(_u["ene_no_data"])

        st.divider()

        st.markdown(f'<div class="section-label">{_u["ene_alerts_title"]}</div>', unsafe_allow_html=True)
        if _ealerts:
            for _ea in _ealerts[:10]:
                _sev  = _ea.get("severity", "")
                _icon = "🔴" if _sev == "high" else ("🟡" if _sev == "medium" else "🔵")
                _ts   = str(_ea.get("timestamp", ""))[:16]
                st.markdown(f"{_icon} **{_ea.get('name','')}** — {_ts}")
        else:
            st.success(_u["ene_no_alerts"])

    with _bcol2:
        st.markdown(f'<div class="section-label">{_u["ene_cycle_title"]}</div>', unsafe_allow_html=True)

        # ── Son cycle vs son 10 cycle ortalaması ─────────────────────────────
        if len(_cycles) >= 2:
            _last    = _cycles[-1]
            _n_avg   = min(len(_cycles), 10)
            _avg_kwh = sum(c["kwh_cycle"] for c in _cycles[-10:]) / _n_avg
            _avg_nm3 = sum(c["nm3_cycle"] for c in _cycles[-10:]) / _n_avg
            _cmp1, _cmp2 = st.columns(2)
            _cmp1.metric(
                "Son Cycle kWh",
                f'{_last["kwh_cycle"]:.3f}',
                delta=f'{_last["kwh_cycle"] - _avg_kwh:+.3f} vs ort.',
                delta_color="inverse",
            )
            _cmp2.metric(
                "Son Cycle m³",
                f'{_last["nm3_cycle"]:.4f}',
                delta=f'{_last["nm3_cycle"] - _avg_nm3:+.4f} vs ort.',
                delta_color="inverse",
            )

        if _cycles:
            _clabels = [f"#{r['cycle_id']}" for r in _cycles]
            _ckwh    = [r["kwh_cycle"] for r in _cycles]
            _cnm3    = [r["nm3_cycle"] for r in _cycles]
            _fig_c = _go2.Figure()
            _fig_c.add_trace(_go2.Bar(
                name="kWh", x=_clabels, y=_ckwh,
                marker_color="#2a5a8a",
            ))
            _fig_c.add_trace(_go2.Bar(
                name="m³", x=_clabels, y=_cnm3,
                marker_color="#2a7a5a",
                yaxis="y2",
            ))
            _fig_c.update_layout(
                paper_bgcolor="rgba(0,0,0,0)",
                plot_bgcolor="rgba(0,0,0,0)",
                font_color="#c8d6e5",
                height=220,
                margin=dict(l=10, r=10, t=10, b=40),
                legend=dict(orientation="h", y=-0.3),
                barmode="group",
                yaxis=dict(title="kWh", gridcolor="#1e2a3a"),
                yaxis2=dict(title="m³", overlaying="y", side="right", showgrid=False),
                xaxis=dict(gridcolor="#1e2a3a", tickangle=-45),
            )
            st.plotly_chart(_fig_c, key="ene_cycle_chart")
        else:
            st.caption(_u["ene_no_data"])

        st.markdown(f'<div class="section-label">{_u["ene_records_title"]}</div>', unsafe_allow_html=True)
        if _erecs:
            import pandas as _pd3
            _rdf = _pd3.DataFrame(_erecs)
            if "ts" in _rdf.columns:
                _rdf["ts"] = _rdf["ts"].str[:19].str.replace("T", " ", regex=False)
            st.dataframe(_rdf, hide_index=True, height=200)
        else:
            st.caption(_u["ene_no_data"])

with _tab_energy:
    _energy_live()
    _energy_tab()

    # ── Enerji rapor export ──────────────────────────────────────────────────
    from datetime import date as _date_e, timedelta as _td_e
    _today_e = _date_e.today()
    st.divider()
    st.markdown(f"**{_u['ene_export_range']}**")
    _eex1, _eex2, _eex3, _eex4 = st.columns([2, 1, 1, 1])
    with _eex1:
        _ene_exp_dr = st.date_input(
            "Enerji rapor aralığı",
            value=(_today_e - _td_e(days=6), _today_e),
            key="ene_export_range",
            label_visibility="collapsed",
        )
        _ene_exp_start = _ene_exp_dr[0].isoformat() if isinstance(_ene_exp_dr, (list, tuple)) else _today_e.isoformat()
        _ene_exp_end   = _ene_exp_dr[1].isoformat() if isinstance(_ene_exp_dr, (list, tuple)) and len(_ene_exp_dr) == 2 else _ene_exp_start
    with _eex2:
        _ene_excel_bytes = _cached_energy_excel(_ene_exp_start, _ene_exp_end)
        if _ene_excel_bytes:
            st.download_button(
                _u["ene_excel"],
                data=_ene_excel_bytes,
                file_name=f"enerji_{_ene_exp_start}_{_ene_exp_end}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                width="stretch",
            )
        else:
            st.button(_u["ene_excel"], disabled=True, width="stretch", help="openpyxl yüklü değil")
    with _eex3:
        _ene_pdf_bytes = _cached_energy_pdf(_ene_exp_start, _ene_exp_end, st.session_state.lang)
        if _ene_pdf_bytes:
            st.download_button(
                _u["ene_pdf"],
                data=_ene_pdf_bytes,
                file_name=f"enerji_{_ene_exp_start}_{_ene_exp_end}.pdf",
                mime="application/pdf",
                width="stretch",
            )
        else:
            st.button(_u["ene_pdf"], disabled=True, width="stretch", help="fpdf2 yüklü değil")
    with _eex4:
        if st.button(_u["ene_email"], width="stretch", key="ene_send_email"):
            try:
                _er = requests.post(
                    f"{BACKEND_URL}/api/energy/send-email",
                    params={"format": "pdf", "start": _ene_exp_start, "end": _ene_exp_end},
                    timeout=30,
                )
                if _er.ok:
                    st.toast("📧 E-posta gönderildi")
                else:
                    st.toast(f"❌ Hata: {_er.text}")
            except Exception as _email_exc:
                st.toast(f"❌ {_email_exc}")

# ─── Ayarlar sekmesi ───────────────────────────────────────────────────────────

with _tab_settings:
    import requests as _req_s
    _u_s = _UI[st.session_state.get("lang", "tr")]

    # ── Eşik değerleri editörü ───────────────────────────────────────────────
    st.markdown(f'<div class="section-label">{_u_s["set_threshold_title"]}</div>', unsafe_allow_html=True)
    try:
        _thr_cur = _req_s.get(f"{_BASE_URL}/api/thresholds", timeout=5).json()
    except Exception:
        _thr_cur = {}

    if _thr_cur:
        with st.form("threshold_form"):
            _sc1, _sc2 = st.columns(2)
            with _sc1:
                st.markdown(_u_s["set_pres_section"])
                _f_sqz_min = st.number_input(_u_s["set_sqz_min"], value=float(_thr_cur.get("sqz_min", 100.0)),           step=1.0, key="t_sqz_min")
                _f_sqz_max = st.number_input(_u_s["set_sqz_max"], value=float(_thr_cur.get("sqz_max", 120.0)),           step=1.0, key="t_sqz_max")
                st.markdown(_u_s["set_oil_section"])
                _f_oil_min = st.number_input(_u_s["set_oil_min"], value=float(_thr_cur.get("oil_level_min", 160.0)),    step=1.0, key="t_oil_min")
                _f_oil_max = st.number_input(_u_s["set_oil_max"], value=float(_thr_cur.get("oil_level_max", 180.0)),    step=1.0, key="t_oil_max")
                st.markdown(_u_s["set_cyc_section"])
                _f_cyc_max = st.number_input(_u_s["set_cyc_max"], value=float(_thr_cur.get("cycle_duration_max_s", 1200.0)), step=60.0, key="t_cyc_max")
            with _sc2:
                st.markdown(_u_s["set_temp_section"])
                _f_seg_min  = st.number_input(_u_s["set_seg_min"], value=float(_thr_cur.get("segment_temp_min", 160.0)),    step=1.0, key="t_seg_min")
                _f_seg_max  = st.number_input(_u_s["set_seg_max"], value=float(_thr_cur.get("segment_temp_max", 165.0)),    step=1.0, key="t_seg_max")
                _f_upl_min  = st.number_input(_u_s["set_upl_min"], value=float(_thr_cur.get("upper_platen_min", 180.0)),    step=1.0, key="t_upl_min")
                _f_upl_max  = st.number_input(_u_s["set_upl_max"], value=float(_thr_cur.get("upper_platen_max", 190.0)),    step=1.0, key="t_upl_max")
                _f_lpl_min  = st.number_input(_u_s["set_lpl_min"], value=float(_thr_cur.get("lower_platen_min", 180.0)),    step=1.0, key="t_lpl_min")
                _f_lpl_max  = st.number_input(_u_s["set_lpl_max"], value=float(_thr_cur.get("lower_platen_max", 190.0)),    step=1.0, key="t_lpl_max")
                _f_con_min  = st.number_input(_u_s["set_con_min"], value=float(_thr_cur.get("container_temp_min", 160.0)),  step=1.0, key="t_con_min")
                _f_con_max  = st.number_input(_u_s["set_con_max"], value=float(_thr_cur.get("container_temp_max", 165.0)),  step=1.0, key="t_con_max")

            if st.form_submit_button(_u_s["set_threshold_save"], width="stretch"):
                _payload = {
                    "sqz_min": _f_sqz_min, "sqz_max": _f_sqz_max,
                    "oil_level_min": _f_oil_min, "oil_level_max": _f_oil_max,
                    "segment_temp_min": _f_seg_min, "segment_temp_max": _f_seg_max,
                    "upper_platen_min": _f_upl_min, "upper_platen_max": _f_upl_max,
                    "lower_platen_min": _f_lpl_min, "lower_platen_max": _f_lpl_max,
                    "container_temp_min": _f_con_min, "container_temp_max": _f_con_max,
                    "cycle_duration_max_s": _f_cyc_max,
                }
                try:
                    _r = _req_s.put(f"{_BASE_URL}/api/thresholds", json=_payload, timeout=5)
                    if _r.ok:
                        st.success(_u_s["set_threshold_saved"])
                    else:
                        st.error(f"Hata: {_r.text}")
                except Exception as _e:
                    st.error(str(_e))
    else:
        st.warning(_u_s["set_no_backend"])

    #st.caption("Telegram bildirimleri için 🔔 Bildirim Ayarları → Telegram sekmesini kullanın.")

# ─── Chat sekmesi ──────────────────────────────────────────────────────────────

with _tab_chat:

    st.markdown(f'<div class="section-label">{_u["quick_label"]}</div>', unsafe_allow_html=True)
    cols = st.columns(4)
    quick_questions = [
        (_u["btn_pressures"],    _u["q_pressures"]),
        (_u["btn_temperatures"], _u["q_temperatures"]),
        (_u["btn_alarms"],       _u["q_alarms"]),
        (_u["btn_energy"],       _u["q_energy"]),
    ]
    for col, (label, question) in zip(cols, quick_questions):
        with col:
            if st.button(label, width="stretch"):
                st.session_state["pending_message"] = question

    # ─── Chat display ──────────────────────────────────────────────────────

    st.divider()
    chat_container = st.container(height=420, border=False)

    with chat_container:
        for msg in st.session_state.messages:
            role = msg["role"]
            content = msg["content"]
            with st.chat_message(role, avatar="👤" if role == "user" else "🤖"):
                st.markdown(content)

    # ─── Chat input ────────────────────────────────────────────────────────

    pending = st.session_state.pop("pending_message", None)
    user_input = st.chat_input(_u["chat_placeholder"]) or pending

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})
        with chat_container:
            with st.chat_message("user", avatar="👤"):
                st.markdown(user_input)

        with chat_container:
            with st.chat_message("assistant", avatar="🤖"):
                placeholder = st.empty()
                full_response = ""

                try:
                    payload = {
                        "message": user_input,
                        "history": st.session_state.api_history,
                        "lang":    st.session_state.lang,
                    }
                    with requests.post(
                        f"{BACKEND_URL}/api/chat/stream",
                        json=payload,
                        stream=True,
                        timeout=120,
                    ) as resp:
                        for line in resp.iter_lines():
                            if line:
                                line = line.decode("utf-8")
                                if line.startswith("data: "):
                                    data_str = line[6:]
                                    if data_str == "[DONE]":
                                        break
                                    try:
                                        data = json.loads(data_str)
                                        if "chunk" in data:
                                            full_response += data["chunk"]
                                            placeholder.markdown(full_response + "▌")
                                        elif "__drawing__" in data:
                                            st.session_state["pending_drawing"] = data["__drawing__"]
                                            st.session_state["pending_valve"] = data.get("__valve__", "")
                                        elif "__flow__" in data:
                                            st.session_state["pending_flow"] = data["__flow__"]
                                        elif "__issue__" in data:
                                            st.session_state["pending_issue"] = data["__issue__"]
                                        elif "error" in data:
                                            full_response = f"❌ Hata: {data['error']}"
                                            break
                                    except json.JSONDecodeError:
                                        pass

                    placeholder.markdown(full_response)

                    if "pending_drawing" in st.session_state:
                        dk = st.session_state.pop("pending_drawing")
                        valve_id = st.session_state.pop("pending_valve", "")
                        try:
                            url = f"{BACKEND_URL}/api/drawing/{dk}"
                            if valve_id:
                                url += f"?valve={valve_id}"
                            drawing_r = requests.get(url, timeout=10)
                            if drawing_r.ok:
                                ct = drawing_r.headers.get("content-type", "")
                                if "text/html" in ct:
                                    import streamlit.components.v1 as _components
                                    _components.html(drawing_r.text, height=520, scrolling=True)
                                else:
                                    st.image(drawing_r.content)
                        except Exception:
                            pass

                    history_response = full_response
                    if "pending_flow" in st.session_state:
                        flow_state = st.session_state.pop("pending_flow")
                        history_response = full_response + f"\n[flow:{flow_state}]"
                    if "pending_issue" in st.session_state:
                        issue_key = st.session_state.pop("pending_issue")
                        history_response += f"\n[issue:{issue_key}]"

                    st.session_state.api_history.append({"role": "user", "content": user_input})
                    st.session_state.api_history.append({"role": "assistant", "content": history_response})
                    if len(st.session_state.api_history) > 40:
                        st.session_state.api_history = st.session_state.api_history[-40:]

                except requests.exceptions.ConnectionError:
                    full_response = _u["err_backend"]
                    placeholder.markdown(full_response)
                except Exception as exc:
                    full_response = f"❌ Hata: {str(exc)}"
                    placeholder.markdown(full_response)

        import re as _re
        display_response = _re.sub(r'\s*\[flow:[^\]]+\]', '', full_response)
        display_response = _re.sub(r'\s*\[issue:[^\]]+\]', '', display_response).strip()
        st.session_state.messages.append({"role": "assistant", "content": display_response})

