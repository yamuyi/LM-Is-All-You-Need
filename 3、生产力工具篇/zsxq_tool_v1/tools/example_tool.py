import streamlit as st
import pandas as pd
import numpy as np

def main():
    """示例工具的主函数"""
    st.set_page_config(
        page_title="示例工具",
        page_icon="🔧",
        layout="wide"
    )
    
    st.title("🔧 示例工具")
    st.markdown("这是一个示例工具，展示如何集成新工具到平台中。")
    
    # 创建一些示例功能
    tab1, tab2, tab3 = st.tabs(["数据生成", "数据处理", "可视化"])
    
    with tab1:
        st.subheader("生成示例数据")
        num_rows = st.slider("数据行数", 10, 100, 20)
        
        if st.button("生成数据"):
            data = {
                'ID': range(1, num_rows + 1),
                'Value': np.random.randn(num_rows),
                'Category': np.random.choice(['A', 'B', 'C'], num_rows)
            }
            df = pd.DataFrame(data)
            st.session_state.example_data = df
            st.success(f"已生成 {num_rows} 行数据")
    
    with tab2:
        st.subheader("数据处理")
        if 'example_data' in st.session_state:
            df = st.session_state.example_data
            
            st.dataframe(df, use_container_width=True)
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("总行数", len(df))
            with col2:
                st.metric("唯一类别数", df['Category'].nunique())
        else:
            st.info("请先在'数据生成'标签页生成数据")
    
    with tab3:
        st.subheader("数据可视化")
        if 'example_data' in st.session_state:
            df = st.session_state.example_data
            
            chart_type = st.selectbox("选择图表类型", ["折线图", "柱状图", "散点图"])
            
            if chart_type == "折线图":
                st.line_chart(df.set_index('ID')['Value'])
            elif chart_type == "柱状图":
                st.bar_chart(df['Category'].value_counts())
            else:
                st.scatter_chart(df[['ID', 'Value']])
        else:
            st.info("请先在'数据生成'标签页生成数据")

# 如果单独运行这个工具
if __name__ == "__main__":
    main()