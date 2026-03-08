import streamlit as st
import requests
from datetime import datetime
from collections import Counter

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")
st.title("🧠 LanceDB 記憶監控")

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
