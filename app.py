import streamlit as st
import json
import os
from datetime import datetime
from collections import Counter

# Cloud version - read from JSON
EXPORT_FILE = "/mount/src/lancedb-monitor/memories_export.json"
LOG_FILE = "/mount/src/lancedb-monitor/operations.log"

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

st.title("🧠 LanceDB 記憶監控（雲端版）")

# Log function
def log_operation(bear_name, action, record_id, details=""):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{bear_name}] {action}: {record_id} - {details}\n"
    try:
        with open(LOG_FILE, "a") as f:
            f.write(log_entry)
    except:
        pass

# Get data from JSON
def get_data():
    try:
        if os.path.exists(EXPORT_FILE):
            with open(EXPORT_FILE, "r", encoding="utf-8") as f:
                records = json.load(f)
            
            # Add row_id
            for i, r in enumerate(records):
                r['_row_id'] = i
            
            return {"records": records, "count": len(records)}
        else:
            return {"records": [], "count": 0, "error": "找不到匯出檔案"}
    except Exception as e:
        return {"error": str(e), "trace": ""}

# Get logs
def get_logs():
    try:
        if os.path.exists(LOG_FILE):
            with open(LOG_FILE, "r") as f:
                lines = f.readlines()
                return lines[-30:]
    except:
        pass
    return []

data = get_data()

if "error" in data:
    st.error(f"連接錯誤: {data['error']}")
else:
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
    
    # Logs section
    st.subheader("📜 操作日誌")
    logs = get_logs()
    if logs:
        for log in reversed(logs):
            st.text(log.strip())
    else:
        st.info("尚無操作日誌")
    
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
            
            st.info("💡 雲端版本僅供查看，請使用本地版本編輯")
    
    st.divider()
    st.caption("🧸 LanceDB Monitor 雲端版 - 小熊抱出品")
