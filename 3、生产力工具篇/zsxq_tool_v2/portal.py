import streamlit as st
from pathlib import Path

# 页面配置
st.set_page_config(
    page_title="工具集成门户",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 工具配置 - 现在直接使用页面文件名
TOOLS_CONFIG = [
    {
        "name": "Markdown图片本地化",
        "description": "下载Markdown文件中的远程图片到本地",
        "icon": "📸",
        "page": "01_Markdown图片本地化",  # 对应pages目录下的文件名
        "category": "文档处理",
        "color": "#4B8BBE"
    },
    {
        "name": "Markdown转HTML",
        "description": "将Markdown转换为美观的HTML文档",
        "icon": "📄",
        "page": "02_Markdown转HTML",  # 对应pages目录下的文件名
        "category": "文档处理",
        "color": "#306998"
    },
    {
        "name": "Markdown转HTML(带水印)",
        "description": "将Markdown转换为带水印的HTML文档",
        "icon": "🖼️",
        "page": "03_Markdown转HTML_带水印",  # 对应pages目录下的文件名
        "category": "文档处理",
        "color": "#4CAF50"
    },
    {
        "name": "PNG加水印",
        "description": "PNG加水印",
        "icon": "📚",
        "page": "04_PNG加水印",
        "category": "文档处理",
        "color": "#646464"
    },
    {
        "name": "示例工具3",
        "description": "数据转换工具示例",
        "icon": "📊",
        "page": "数据转换工具",
        "category": "数据转换",
        "color": "#FF6B6B"
    },
    {
        "name": "示例工具4",
        "description": "开发辅助工具",
        "icon": "💻",
        "page": "开发工具",
        "category": "开发工具",
        "color": "#51A3A3"
    }
]

def main():
    """主门户页面"""
    # 标题区域
    st.title("🔧 工具集成门户")
    st.markdown("一站式工具平台，点击下方工具卡片开始使用")
    
    # 创建搜索和筛选区域
    col1, col2 = st.columns([3, 1])
    
    with col1:
        search_query = st.text_input("🔍 搜索工具...", placeholder="输入工具名称或描述")
    
    with col2:
        # 分类筛选
        categories = ["所有分类"] + sorted(set([tool["category"] for tool in TOOLS_CONFIG]))
        selected_category = st.selectbox("📁 分类", categories)
    
    # 过滤工具
    filtered_tools = TOOLS_CONFIG
    
    if search_query:
        filtered_tools = [
            tool for tool in filtered_tools 
            if search_query.lower() in tool["name"].lower() 
            or search_query.lower() in tool["description"].lower()
        ]
    
    if selected_category != "所有分类":
        filtered_tools = [tool for tool in filtered_tools if tool["category"] == selected_category]
    
    # 显示工具数量
    if not filtered_tools:
        st.info("没有找到匹配的工具")
        return
    
    st.markdown(f"### 📋 找到 {len(filtered_tools)} 个工具")
    
    # 创建卡片网格 - 使用Streamlit原生组件
    cols_per_row = 3
    tool_count = len(filtered_tools)
    
    for i in range(0, tool_count, cols_per_row):
        cols = st.columns(cols_per_row)
        row_tools = filtered_tools[i:i + cols_per_row]
        
        for j, tool in enumerate(row_tools):
            with cols[j]:
                display_tool_card(tool)

def display_tool_card(tool):
    """显示工具卡片 - 使用Streamlit原生组件"""
    # 创建卡片容器
    with st.container():
        # 卡片样式通过markdown实现
        card_html = f"""
        <div style="
            background: linear-gradient(135deg, {tool['color']}20, {tool['color']}10);
            border: 1px solid {tool['color']}30;
            border-radius: 12px;
            padding: 1.5rem;
            margin: 0.5rem 0;
            height: 200px;
            display: flex;
            flex-direction: column;
            justify-content: space-between;
        ">
            <div>
                <div style="font-size: 2rem; margin-bottom: 0.5rem;">
                    {tool['icon']}
                </div>
                <h3 style="color: {tool['color']}; margin: 0.5rem 0;">
                    {tool['name']}
                </h3>
                <p style="color: #666; font-size: 0.9rem; line-height: 1.4;">
                    {tool['description']}
                </p>
            </div>
            <div style="
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin-top: 1rem;
                padding-top: 0.8rem;
                border-top: 1px solid {tool['color']}20;
            ">
                <span style="
                    background: {tool['color']}15;
                    color: {tool['color']};
                    padding: 0.2rem 0.8rem;
                    border-radius: 20px;
                    font-size: 0.8rem;
                ">
                    {tool['category']}
                </span>
                <span style="color: #888; font-size: 0.9rem;">→</span>
            </div>
        </div>
        """
        
        st.markdown(card_html, unsafe_allow_html=True)
        
        # 使用按钮进行导航
        if st.button(f"使用{tool['icon']}{tool['name']}", 
                    key=f"use_{tool['page']}",
                    use_container_width=True,
                    type="primary"):
            # 导航到对应页面
            st.switch_page(f"pages/{tool['page']}.py")

if __name__ == "__main__":
    main()