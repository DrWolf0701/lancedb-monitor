import streamlit as st
import lancedb
from datetime import datetime
from collections import Counter
import traceback
import os
import subprocess

# Config
DB_PATH = "/mount/src/lancedb-monitor/memories"
LOG_FILE = "/mount/src/lancedb-monitor/operations.log"
EXPORT_DIR = "/mount/src/lancedb-monitor"

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

st.title("🧠 LanceDB 記憶監控")

# Log function - shared by all bears
def log_operation(bear_name, action, record_id, details=""):
    """
    Call this to log any memory operation
    Usage: log_operation("小熊抱", "STORE", "record_id", "category=fact")
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{bear_name}] {action}: {record_id} - {details}\n"
    with open(LOG_FILE, "a") as f:
        f.write(log_entry)

# Get data - no caching
def get_data():
    try:
        db = lancedb.connect(DB_PATH)
        result = db.list_tables()
        tables = result.tables
        
        all_data = {"tables": {}, "count": 0}
        
        for table_name in tables:
            table = db.open_table(table_name)
            df = table.to_pandas()
            
            for col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (tuple, list)) else x)
            
            df = df.reset_index(drop=True)
            df['_row_id'] = df.index
            
            all_data["tables"][table_name] = df.to_dict('records')
            all_data["count"] += len(df)
        
        return all_data
    except Exception as e:
        return {"error": str(e), "trace": traceback.format_exc()}

def save_record(table_name, record_id, new_text, new_category, new_importance):
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(table_name)
        
        table.update(
            where=f"id = '{record_id}'",
            values={
                "text": new_text,
                "category": new_category,
                "importance": float(new_importance)
            }
        )
        log_operation("Chris(網頁)", "UPDATE", record_id, f"category={new_category}, text={new_text[:50]}...")
        
        # Auto export
        export_ok, export_msg = auto_export()
        
        return True, f"✅ 更新成功！ {export_msg}"
    except Exception as e:
        return False, f"❌ 錯誤: {str(e)}\n{traceback.format_exc()[:200]}"

def delete_record(table_name, record_id, original_text):
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(table_name)
        
        table.delete(f"id = '{record_id}'")
        log_operation("Chris(網頁)", "DELETE", record_id, f"text={original_text[:30]}... (已刪除)")
        
        # Auto export
        export_ok, export_msg = auto_export()
        
        return True, f"✅ 刪除成功！ {export_msg}"
    except Exception as e:
        return False, f"❌ 錯誤: {str(e)}\n{traceback.format_exc()[:200]}"

# Get logs
def get_logs():
    if os.path.exists(LOG_FILE):
        with open(LOG_FILE, "r") as f:
            lines = f.readlines()
            return lines[-30:]  # Last 30 lines
    return []

# Auto export to GitHub
def auto_export():
    """儲存/刪除後自動 Export 並 Push 到 GitHub"""
    try:
        # Export to JSON
        db = lancedb.connect(DB_PATH)
        table = db.open_table("memories")
        df = table.to_pandas()
        
        # Convert problematic columns
        for col in df.columns:
            df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (tuple, list)) else x)
        
        # Save to export directory
        os.makedirs(EXPORT_DIR, exist_ok=True)
        export_file = os.path.join(EXPORT_DIR, "memories_export.json")
        df.to_json(export_file, orient="records", force_ascii=False, indent=2)
        
        # Git add, commit, push
        os.chdir(EXPORT_DIR)
        subprocess.run(["git", "add", "memories_export.json"], capture_output=True)
        subprocess.run(["git", "commit", "-m", "auto: export memories"], capture_output=True)
        subprocess.run(["git", "push"], capture_output=True)
        
        return True, "✅ 已自動同步到 GitHub！"
    except Exception as e:
        return False, f"⚠️ 自動同步失敗: {str(e)}"

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
    
    categories = []
    for table_name, records in data["tables"].items():
        for r in records:
            if "category" in r:
                categories.append(r["category"])
    
    if categories:
        cat_counts = Counter(categories)
        cols = st.columns(len(cat_counts))
        for i, (cat, count) in enumerate(cat_counts.items()):
            cols[i].metric(cat.upper(), count)
        st.bar_chart(cat_counts)
    
    st.divider()
    
    # Logs section
    st.subheader("📜 操作日誌（谁改的看这里）")
    logs = get_logs()
    if logs:
        for log in reversed(logs):
            st.text(log.strip())
    else:
        st.info("尚無操作日誌")
    
    st.divider()
    
    # Build results
    results = []
    for table_name, records in data["tables"].items():
        for r in records:
            text = str(r.get("text", ""))
            category = str(r.get("category", "N/A"))
            
            results.append({
                "table": table_name,
                "row_id": r.get("_row_id"),
                "id": r.get("id"),
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
            st.write(f"**ID**: {r['id'][:20]}...")
            st.write(f"**時間**: {r['時間']}")
            st.write(f"**重要性**: {r['重要性']}")
            st.text(r["完整內容"])
            
            col1, col2 = st.columns(2)
            with col1:
                new_text = st.text_area("編輯內容", r["完整內容"], height=100, key=f"text_{r['row_id']}")
            with col2:
                new_category = st.selectbox("分類", ["fact", "decision", "preference", "entity", "other"], 
                                          index=["fact", "decision", "preference", "entity", "other"].index(r["分類"]),
                                          key=f"cat_{r['row_id']}")
                new_importance = st.slider("重要性", 0.0, 1.0, r["重要性"], key=f"imp_{r['row_id']}")
            
            c1, c2 = st.columns(2)
            with c1:
                if st.button(f"💾 儲存 #{r['row_id']}", key=f"save_{r['row_id']}"):
                    success, msg = save_record(r["table"], r["id"], new_text, new_category, new_importance)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with c2:
                if st.button(f"🗑️ 刪除 #{r['row_id']}", key=f"del_{r['row_id']}"):
                    success, msg = delete_record(r["table"], r["id"], r["完整內容"])
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    st.divider()
    st.caption("🧸 LanceDB Monitor v12.0 - 小熊抱出品")

# ============================================================================
# 小熊們用的日志函數 - 複製到各小熊使用！
# ============================================================================
BEAR_LOG_FILE = "/mount/src/lancedb-monitor/operations.log"

def bear_log(bear_name, action, details=""):
    """小熊們存記憶時呼叫這個函數"""
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_entry = f"[{timestamp}] [{bear_name}] {action}: - {details}\n"
    with open(BEAR_LOG_FILE, "a") as f:
        f.write(log_entry)

# 使用範例：
# bear_log("投資小熊", "STORE", "category=fact, importance=0.9")
# bear_log("影片小熊", "UPDATE", "record_id=xxx, category=decision")
# bear_log("管家小熊", "DELETE", "record_id=xxx")
