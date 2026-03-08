import streamlit as st
import json
import urllib.request
from datetime import datetime
from collections import Counter

# Cloud version - fetch from GitHub
GITHUB_RAW_URL = "https://raw.githubusercontent.com/DrWolf0701/lancedb-monitor/main/memories_export.json"

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

st.title("🧠 LanceDB 記憶監控（雲端版）")

# Log function
def log_operation(bear_name, action, record_id, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    st.write(f"[{timestamp}] [{bear_name}] {action}: {record_id} - {details}")

# Get data from GitHub
@st.cache_data(ttl=300)  # Cache for 5 minutes
def get_data():
    try:
        st.info("🔄 正在從 GitHub 獲取資料...")
        
        with urllib.request.urlopen(GITHUB_RAW_URL, timeout=30) as response:
            records = json.loads(response.read().decode('utf-8'))
        
        # Add row_id
        for i, r in enumerate(records):
            r['_row_id'] = i
        
        st.success(f"✅ 成功載入 {len(records)} 筆記錄")
        return {"records": records, "count": len(records)}
    except Exception as e:
        st.error(f"❌ 獲取失敗: {str(e)}")
        return {"error": str(e), "count": 0}

data = get_data()

if data.get("count", 0) > 0:
    # Stats
    col1, col2 = st.columns(2)
    col1.metric("📊 總記憶數", data["count"])
    col2.metric("📅 現在時間", datetime.now().strftime("%Y-%m-%d %H:%M"))
    
    st.divider()
    
    # Category stats
    st.subheader("📈 分類統計")
    
    categories = [r.get("category", "N/A") for r in data["records"] if "category" in r]
    if categories:
        cat_counts = Counter(categories)
        cols = st.columns(len(cat_counts))
        for i, (cat, count) in enumerate(cat_counts.items()):
            cols[i].metric(cat.upper(), count)
        st.bar_chart(cat_counts)
    
    st.divider()
    
    # Build results
    results = []
    for r in data["records"]:
        text = str(r.get("text", ""))
        category = str(r.get("category", "N/A"))
        
        results.append({
            "row_id": r.get("_row_id"),
            "id": r.get("id", ""),
            "分類": category,
            "內容": text[:100] + "..." if len(text) > 100 else text,
            "完整內容": text,
            "重要性": float(r.get("importance", 0.5)),
            "時間": str(r.get("timestamp", ""))[:19] if r.get("timestamp") else "N/A"
        })
    
    st.subheader(f"📝 記憶列表（共 {len(results)} 筆記錄）")
    
    # Show all as expandable sections
    for r in results:
        with st.expander(f"#{r['row_id']} [{r['分類']}] {r['內容']}", expanded=False):
            st.write(f"**ID**: {str(r['id'])[:20]}...")
            st.write(f"**時間**: {r['時間']}")
            st.write(f"**重要性**: {r['重要性']}")
            st.text(r["完整內容"])
    
    st.divider()
    st.caption("🧸 LanceDB Monitor 雲端版 - 資料來源: GitHub")
else:
    st.warning("⚠️ 無法載入資料，請檢查網絡連接")
