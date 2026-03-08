import streamlit as st
import lancedb
from datetime import datetime
from collections import Counter

# Config
DB_PATH = "/Users/yu-tsehsiao/.openclaw/memory/lancedb-pro"

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
    .stButton>button { width: 100%; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 LanceDB 記憶監控")

# Session state for edit mode
if "edit_record" not in st.session_state:
    st.session_state.edit_record = None
if "delete_record" not in st.session_state:
    st.session_state.delete_record = None

# Get data
@st.cache_data
def get_data():
    try:
        db = lancedb.connect(DB_PATH)
        tables = db.table_names()
        
        all_data = {"tables": {}}
        
        for table_name in tables:
            table = db.open_table(table_name)
            df = table.to_pandas()
            # Add row index as ID
            df = df.reset_index(drop=True)
            df['_row_id'] = df.index
            all_data["tables"][table_name] = {
                "count": len(df),
                "records": df.to_dict('records')
            }
        
        return all_data
    except Exception as e:
        return {"error": str(e)}

# Save function
def save_record(table_name, row_id, new_text, new_category, new_importance):
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(table_name)
        df = table.to_pandas()
        
        # Update the record
        df.loc[row_id, 'text'] = new_text
        df.loc[row_id, 'category'] = new_category
        df.loc[row_id, 'importance'] = new_importance
        
        # Write back
        table.update(df)
        db.close()
        return True, "✅ 更新成功！"
    except Exception as e:
        return False, f"❌ 錯誤: {str(e)}"

# Delete function
def delete_record(table_name, row_id):
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(table_name)
        df = table.to_pandas()
        
        # Delete the row
        df = df.drop(row_id).reset_index(drop=True)
        
        # Write back
        table.update(df)
        db.close()
        return True, "✅ 刪除成功！"
    except Exception as e:
        return False, f"❌ 錯誤: {str(e)}"

# Handle delete
if st.session_state.delete_record:
    success, msg = delete_record(
        st.session_state.delete_record["table"],
        st.session_state.delete_record["row_id"]
    )
    st.session_state.delete_record = None
    st.rerun()

# Handle edit save
if st.session_state.edit_record:
    record = st.session_state.edit_record
    st.subheader("✏️ 編輯記憶")
    
    new_text = st.text_area("內容", record["text"], height=150)
    new_category = st.selectbox("分類", ["fact", "decision", "preference", "entity", "other"], 
                                index=["fact", "decision", "preference", "entity", "other"].index(record["category"]))
    new_importance = st.slider("重要性", 0.0, 1.0, record["importance"])
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("💾 儲存"):
            success, msg = save_record(record["table"], record["row_id"], new_text, new_category, new_importance)
            st.session_state.edit_record = None
            st.rerun()
    with col2:
        if st.button("❌ 取消"):
            st.session_state.edit_record = None
            st.rerun()
    
    st.divider()

# Load data
data = get_data()

if "error" in data:
    st.error(f"連接錯誤: {data['error']}")
else:
    # Stats
    total = sum(t["count"] for t in data["tables"].values())
    
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 總記憶數", total)
    col2.metric("📅 現在時間", datetime.now().strftime("%Y-%m-%d %H:%M"))
    col3.metric("🔖 表格數", len(data["tables"]))
    
    st.divider()
    
    # Category stats
    st.subheader("📈 分類統計")
    
    all_categories = []
    for table_name, table_data in data["tables"].items():
        for record in table_data["records"]:
            if "category" in record:
                all_categories.append(record["category"])
    
    if all_categories:
        cat_counts = Counter(all_categories)
        
        cols = st.columns(len(cat_counts))
        for i, (cat, count) in enumerate(cat_counts.items()):
            cols[i].metric(cat.upper(), count)
        
        st.bar_chart(cat_counts)
    
    st.divider()
    
    # Filter
    st.subheader("🔍 搜尋與篩選")
    
    col_search, col_cat = st.columns(2)
    
    with col_search:
        search = st.text_input("🔎 關鍵字搜尋", placeholder="輸入關鍵字...")
    
    with col_cat:
        cats = list(cat_counts.keys()) if cat_counts else []
        category_filter = st.selectbox("📂 分類篩選", ["全部"] + cats)
    
    st.divider()
    
    # Results
    st.subheader("📝 記憶列表")
    
    results = []
    for table_name, table_data in data["tables"].items():
        for record in table_data["records"]:
            text = record.get("text", "")
            category = record.get("category", "N/A")
            
            if category_filter != "全部" and category != category_filter:
                continue
            if search and search.lower() not in text.lower():
                continue
                
            results.append({
                "table": table_name,
                "row_id": record.get("_row_id"),
                "分類": category,
                "內容": text[:200] + "..." if len(text) > 200 else text,
                "完整內容": text,
                "重要性": record.get("importance", 0.5),
                "時間": str(record.get("created_at", ""))[:10] if "created_at" in record else "N/A"
            })
    
    st.write(f"共 {len(results)} 筆記錄")
    
    # Show with edit/delete buttons
    for r in results[:20]:
        with st.expander(f"[#{r['row_id']}] [{r['分類']}] {r['內容'][:80]}..."):
            col1, col2 = st.columns([3, 1])
            with col1:
                st.write(f"**分類**: {r['分類']}")
                st.write(f"**重要性**: {r['重要性']}")
                st.write(f"**時間**: {r['時間']}")
                st.write(f"**完整內容**: {r['完整內容']}")
            with col2:
                st.write("")  # spacing
                if st.button("✏️ 編輯", key=f"edit_{r['table']}_{r['row_id']}"):
                    st.session_state.edit_record = {
                        "table": r["table"],
                        "row_id": r["row_id"],
                        "text": r["完整內容"],
                        "category": r["分類"],
                        "importance": r["重要性"]
                    }
                    st.rerun()
                if st.button("🗑️ 刪除", key=f"delete_{r['table']}_{r['row_id']}"):
                    st.session_state.delete_record = {
                        "table": r["table"],
                        "row_id": r["row_id"]
                    }
                    st.rerun()
    
    st.divider()
    st.caption("🧸 LanceDB Monitor v3.0 - 小熊抱出品")
