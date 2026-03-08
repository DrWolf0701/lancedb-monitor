import streamlit as st
import requests
from datetime import datetime, timedelta
from collections import Counter

# 密碼保護
if 'authenticated' not in st.session_state:
    st.session_state.authenticated = False

if not st.session_state.authenticated:
    st.title("🔒 請輸入密碼")
    password = st.text_input("密碼", type="password")
    if password == "s8824415":
        st.session_state.authenticated = True
        st.rerun()
    elif password:
        st.error("密碼錯誤")
    st.stop()

st.set_page_config(title="LanceDB Monitor", page_icon="🧠", layout="wide")
st.title("🧠 LanceDB 記憶監控")

# Fetch memories
try:
    url = "https://raw.githubusercontent.com/DrWolf0701/lancedb-monitor/main/memories_export.json"
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    records = response.json()
    count = len(records)
    
    st.success(f"✅ 成功載入 {count} 筆記錄")
    
    # Stats
    col1, col2 = st.columns(2)
    col1.metric("📊 總記憶數", count)
    col2.metric("📅 現在時間", datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    st.divider()
    
    # Categories
    categories = [r.get("category", "N/A") for r in records if "category" in r]
    if categories:
        st.subheader("📈 分類統計")
        cat_counts = Counter(categories)
        cols = st.columns(len(cat_counts))
        for i, (cat, c) in enumerate(cat_counts.items()):
            cols[i].metric(cat.upper(), c)
        st.bar_chart(cat_counts)
    
    st.divider()
    
    # Fetch logs from GitHub
    st.subheader("📜 操作日誌（最近3天）")
    try:
        log_url = "https://raw.githubusercontent.com/DrWolf0701/lancedb-monitor/main/operations.log"
        log_response = requests.get(log_url, timeout=10)
        if log_response.status_code == 200:
            lines = log_response.text.strip().split('\n')
            today = datetime.now().date()
            three_days_ago = today - timedelta(days=3)
            
            recent_logs = []
            for line in lines:
                try:
                    date_str = line[1:11]
                    log_date = datetime.strptime(date_str, "%Y-%m-%d").date()
                    if log_date >= three_days_ago:
                        recent_logs.append(line)
                except:
                    pass
            
            if recent_logs:
                for log in reversed(recent_logs[-20:]):
                    st.text(log)
            else:
                st.info("最近3天沒有操作日誌")
        else:
            st.info("尚無操作日誌")
    except:
        st.info("無法載入日誌")
    
    st.divider()
    
    # List
    st.subheader(f"📝 記憶列表（共 {count} 筆記錄）")
    
    for i, r in enumerate(records):
        text = str(r.get("text", ""))[:80] + "..."
        cat = r.get("category", "N/A")
        with st.expander(f"#{i} [{cat}] {text}"):
            st.write(f"**時間**: {str(r.get('timestamp',''))[:19]}")
            st.write(f"**重要性**: {r.get('importance', 'N/A')}")
            st.text(r.get("text", ""))

except Exception as e:
    st.error(f"❌ 錯誤: {str(e)}")

st.caption("🧸 LanceDB Monitor 雲端版")
