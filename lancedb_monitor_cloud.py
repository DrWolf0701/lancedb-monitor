import streamlit as st
import lancedb
from datetime import datetime
from collections import Counter

# Config - use the directory, not the .lance file
DB_PATH = "/mount/src/lancedb-monitor/memories"

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

st.title("🧠 LanceDB 記憶監控")

# Get data 
@st.cache_data
def get_data():
    try:
        # Connect to the directory (not the .lance file)
        db = lancedb.connect(DB_PATH)
        result = db.list_tables()
        tables = result.tables
        
        all_data = {"tables": {}, "count": 0}
        
        for table_name in tables:
            table = db.open_table(table_name)
            df = table.to_pandas()
            
            # Convert problematic columns
            for col in df.columns:
                df[col] = df[col].apply(lambda x: str(x) if isinstance(x, (tuple, list)) else x)
            
            # Add row index
            df = df.reset_index(drop=True)
            df['_row_id'] = df.index
            
            all_data["tables"][table_name] = df.to_dict('records')
            all_data["count"] += len(df)
        
        return all_data
    except Exception as e:
        import traceback
        return {"error": str(e), "trace": traceback.format_exc()}

# Save function
def save_record(table_name, row_id, new_text, new_category, new_importance):
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(table_name)
        df = table.to_pandas()
        
        # Update
        df.loc[row_id, 'text'] = new_text
        df.loc[row_id, 'category'] = new_category
        df.loc[row_id, 'importance'] = float(new_importance)
        
        table.update(df)
        return True, "✅ 更新成功！"
    except Exception as e:
        return False, f"❌ 錯誤: {str(e)}"

# Delete function
def delete_record(table_name, row_id):
    try:
        db = lancedb.connect(DB_PATH)
        table = db.open_table(table_name)
        df = table.to_pandas()
        
        df = df.drop(row_id).reset_index(drop=True)
        table.update(df)
        return True, "✅ 刪除成功！"
    except Exception as e:
        return False, f"❌ 錯誤: {str(e)}"

# Load data
data = get_data()

if "error" in data:
    st.error(f"連接錯誤: {data['error']}")
    st.code(data.get("trace", ""))
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
    
    # Filter
    st.subheader("🔍 搜尋與篩選")
    search = st.text_input("🔎 關鍵字搜尋", placeholder="輸入關鍵字...", key="search_input")
    
    # Build results
    results = []
    for table_name, records in data["tables"].items():
        for r in records:
            text = str(r.get("text", ""))
            category = str(r.get("category", "N/A"))
            
            if search and search.lower() not in text.lower():
                continue
                
            results.append({
                "table": table_name,
                "row_id": r.get("_row_id"),
                "分類": category,
                "內容": text[:200] + "..." if len(text) > 200 else text,
                "完整內容": text,
                "重要性": float(r.get("importance", 0.5)),
            })
    
    st.subheader(f"📝 記憶列表（共 {len(results)} 筆記錄）")
    
    if results:
        options = [f"#{r['row_id']} [{r['分類']}] {r['內容'][:50]}..." for r in results]
        selected = st.selectbox("選擇要編輯/刪除的記錄", range(len(options)), format_func=lambda i: options[i])
        
        if selected is not None:
            r = results[selected]
            with st.expander("📄 完整內容", expanded=True):
                st.write(f"**分類**: {r['分類']}")
                st.write(f"**重要性**: {r['重要性']}")
                st.text(r["完整內容"])
            
            st.subheader("✏️ 編輯")
            new_text = st.text_area("內容", r["完整內容"], height=150, key="edit_text")
            new_category = st.selectbox("分類", ["fact", "decision", "preference", "entity", "other"], 
                                        index=["fact", "decision", "preference", "entity", "other"].index(r["分類"]),
                                        key="edit_cat")
            new_importance = st.slider("重要性", 0.0, 1.0, r["重要性"], key="edit_imp")
            
            col1, col2 = st.columns(2)
            with col1:
                if st.button("💾 儲存變更", key="save_btn"):
                    success, msg = save_record(r["table"], r["row_id"], new_text, new_category, new_importance)
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
            with col2:
                if st.button("🗑️ 刪除此記錄", key="delete_btn"):
                    success, msg = delete_record(r["table"], r["row_id"])
                    if success:
                        st.success(msg)
                        st.rerun()
                    else:
                        st.error(msg)
    
    st.divider()
    st.caption("🧸 LanceDB Monitor v7.0 - 小熊抱出品")
