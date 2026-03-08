import streamlit as st
import lancedb
import os
from datetime import datetime
from collections import Counter

# Config
DB_PATH = "/Users/yu-tsehsiao/.openclaw/memory/lancedb-pro"

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 LanceDB 記憶監控")

# Get data without caching db connection
@st.cache_data
def get_data():
    try:
        db = lancedb.connect(DB_PATH)
        tables = db.table_names()
        
        all_data = {"tables": {}}
        
        for table_name in tables:
            table = db.open_table(table_name)
            df = table.to_pandas()
            all_data["tables"][table_name] = {
                "count": len(df),
                "records": df.to_dict('records')
            }
        
        # Close connection by returning only serializable data
        db.close()
            
        return all_data
    except Exception as e:
        return {"error": str(e)}

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
                "分類": category,
                "內容": text[:200] + "..." if len(text) > 200 else text,
                "重要性": record.get("importance", "N/A"),
                "時間": str(record.get("created_at", ""))[:10] if "created_at" in record else "N/A"
            })
    
    st.write(f"共 {len(results)} 筆記錄")
    
    for r in results[:20]:
        with st.expander(f"[{r['分類']}] {r['內容'][:80]}..."):
            st.write(f"**分類**: {r['分類']}")
            st.write(f"**重要性**: {r['重要性']}")
            st.write(f"**時間**: {r['時間']}")
            st.write(f"**內容**: {r['內容']}")
    
    st.divider()
    st.caption("🧸 LanceDB Monitor v2.0 - 小熊抱出品")
