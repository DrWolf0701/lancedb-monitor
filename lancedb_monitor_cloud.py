import streamlit as st
import json

st.set_page_config(page_title="LanceDB Monitor", page_icon="🧠", layout="wide")
st.title("🧠 LanceDB 記憶監控")

# Load exported data
try:
    with open("lancedb_export.json", "r", encoding="utf-8") as f:
        data = json.load(f)
    
    total = sum(t["count"] for t in data["tables"].values())
    
    col1, col2 = st.columns(2)
    col1.metric("📊 總記憶數", total)
    col2.metric("📋 表格數", len(data["tables"]))
    
    st.write(f"📅 匯出時間: {data['export_time']}")
    
    st.divider()
    
    # Search
    st.subheader("🔍 搜尋記憶")
    search = st.text_input("輸入關鍵字")
    
    if search:
        results = []
        for table_name, table_data in data["tables"].items():
            for record in table_data["records"]:
                if search.lower() in record.get("text", "").lower():
                    results.append({**record, "table": table_name})
        
        st.write(f"找到 {len(results)} 筆:")
        for r in results[:10]:
            st.write(f"- [{r.get('category', 'N/A')}] {r.get('text', '')[:100]}...")
    
    st.divider()
    
    # Recent memories
    st.subheader("📝 記憶列表")
    for table_name, table_data in data["tables"].items():
        with st.expander(f"{table_name} ({table_data['count']}筆)"):
            for r in table_data["records"][:10]:
                st.write(f"**{r.get('category', '')}** - {r.get('text', '')[:150]}...")
                
except Exception as e:
    st.error(f"載入失敗: {e}")

st.caption("🧸 LanceDB Monitor - Cloud Version")
