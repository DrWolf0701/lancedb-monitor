import streamlit as st
import json
from collections import Counter

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")

# Custom CSS
st.markdown("""
<style>
    .big-font { font-size:24px !important; }
    .stMetric { background-color: #f0f2f6; padding: 10px; border-radius: 10px; }
</style>
""", unsafe_allow_html=True)

st.title("🧠 LanceDB 記憶監控")

# Load data
try:
    with open("lancedb_export.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    # Stats
    total = sum(t["count"] for t in data["tables"].values())
    
    # Header metrics
    col1, col2, col3 = st.columns(3)
    col1.metric("📊 總記憶數", total)
    col2.metric("📅 匯出時間", data["export_time"][:16].replace("T", " "))
    col3.metric("🔖 表格數", len(data["tables"]))
    
    st.divider()
    
    # Category stats
    st.subheader("📈 分類統計")
    
    all_categories = []
    all_texts = []
    for table_name, table_data in data["tables"].items():
        for record in table_data["records"]:
            if "category" in record:
                all_categories.append(record["category"])
            if "text" in record:
                all_texts.append(record["text"])
    
    if all_categories:
        cat_counts = Counter(all_categories)
        
        # Show as columns
        cols = st.columns(len(cat_counts))
        for i, (cat, count) in enumerate(cat_counts.items()):
            cols[i].metric(cat.upper(), count)
        
        # Bar chart
        st.bar_chart(cat_counts)
    
    st.divider()
    
    # Filter by category
    st.subheader("🔍 搜尋與篩選")
    
    col_search, col_cat = st.columns(2)
    
    with col_search:
        search = st.text_input("🔎 關鍵字搜尋", placeholder="輸入關鍵字...")
    
    with col_cat:
        category_filter = st.selectbox("📂 分類篩選", ["全部"] + list(cat_counts.keys()))
    
    st.divider()
    
    # Results
    st.subheader("📝 記憶列表")
    
    results = []
    for table_name, table_data in data["tables"].items():
        for record in table_data["records"]:
            text = record.get("text", "")
            category = record.get("category", "N/A")
            
            # Filter
            if category_filter != "全部" and category != category_filter:
                continue
            if search and search.lower() not in text.lower():
                continue
                
            results.append({
                "分類": category,
                "內容": text[:200] + "..." if len(text) > 200 else text,
                "重要性": record.get("importance", "N/A"),
                "建立時間": record.get("created_at", "")[:10] if record.get("created_at") else "N/A"
            })
    
    st.write(f"共 {len(results)} 筆記錄")
    
    if results:
        # Convert to DataFrame for display
        import pandas as pd
        df_results = pd.DataFrame(results)
        
        # Display with custom styling
        for i, row in df_results.iterrows():
            with st.expander(f"[{row['分類']}] {row['內容'][:80]}..."):
                st.write(f"**分類**: {row['分類']}")
                st.write(f"**重要性**: {row['重要性']}")
                st.write(f"**時間**: {row['建立時間']}")
                st.write(f"**內容**: {row['內容']}")
    
    st.divider()
    st.caption("🧸 LanceDB Monitor v2.0 - 小熊抱出品")
    
except Exception as e:
    st.error(f"載入失敗: {e}")
    st.write("請確保 lancedb_export.json 存在於相同目錄")
