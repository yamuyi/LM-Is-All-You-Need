import streamlit as st
import importlib.util
import sys
from pathlib import Path
import json

# 配置页面
st.set_page_config(
    page_title="工具集成平台",
    page_icon="🔧",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 工具配置
TOOLS_DIR = Path("tools")
TOOLS_CONFIG_FILE = Path("tools_config.json")

# 默认工具配置
DEFAULT_TOOLS_CONFIG = {
    "tools": [
        {
            "name": "Markdown图片本地化工具",
            "module": "markdown_image_localizer",
            "description": "将Markdown文件中的远程图片下载到本地",
            "icon": "📸",
            "author": "工具平台",
            "version": "1.0.0",
            "category": "文档处理"
        },
        {
            "name": "示例工具",
            "module": "example_tool",
            "description": "这是一个示例工具",
            "icon": "🔧",
            "author": "示例作者",
            "version": "1.0.0",
            "category": "示例"
        }
    ],
    "categories": ["文档处理", "图片处理", "数据转换", "开发工具", "示例"]
}

# 创建必要的目录
TOOLS_DIR.mkdir(exist_ok=True)

def load_tools_config():
    """加载工具配置"""
    if TOOLS_CONFIG_FILE.exists():
        try:
            with open(TOOLS_CONFIG_FILE, 'r', encoding='utf-8') as f:
                return json.load(f)
        except:
            return DEFAULT_TOOLS_CONFIG
    else:
        # 保存默认配置
        save_tools_config(DEFAULT_TOOLS_CONFIG)
        return DEFAULT_TOOLS_CONFIG

def save_tools_config(config):
    """保存工具配置"""
    with open(TOOLS_CONFIG_FILE, 'w', encoding='utf-8') as f:
        json.dump(config, f, ensure_ascii=False, indent=2)

def load_tool_module(tool_module_name):
    """动态加载工具模块"""
    try:
        # 构建模块路径
        module_path = TOOLS_DIR / f"{tool_module_name}.py"
        
        if not module_path.exists():
            st.error(f"工具模块不存在: {module_path}")
            return None
        
        # 动态加载模块
        spec = importlib.util.spec_from_file_location(tool_module_name, module_path)
        module = importlib.util.module_from_spec(spec)
        sys.modules[tool_module_name] = module
        spec.loader.exec_module(module)
        
        return module
    except Exception as e:
        st.error(f"加载工具模块失败: {str(e)}")
        return None

def main_dashboard():
    """主仪表板"""
    st.title("🔧 工具集成平台")
    st.markdown("""
    欢迎使用工具集成平台！这里汇集了各种实用工具，点击下方卡片开始使用。
    
    💡 **使用提示**：
    - 点击工具卡片进入工具界面
    - 在工具界面中可以完成相应操作
    - 使用侧边栏返回主页或切换工具
    """)
    
    # 加载工具配置
    config = load_tools_config()
    tools = config.get("tools", [])
    
    if not tools:
        st.warning("暂无可用工具")
        return
    
    # 按分类组织工具
    categories = {}
    for tool in tools:
        category = tool.get("category", "未分类")
        if category not in categories:
            categories[category] = []
        categories[category].append(tool)
    
    # 显示分类工具
    for category, category_tools in categories.items():
        st.subheader(f"📁 {category}")
        
        # 创建卡片网格
        cols = st.columns(3)
        for idx, tool in enumerate(category_tools):
            col_idx = idx % 3
            with cols[col_idx]:
                with st.container():
                    st.markdown(f"""
                    <div style='
                        padding: 1rem;
                        border-radius: 10px;
                        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                        color: white;
                        margin-bottom: 1rem;
                        height: 180px;
                    '>
                        <h3 style='color: white;'>{tool['icon']} {tool['name']}</h3>
                        <p style='color: rgba(255,255,255,0.9); font-size: 0.9rem;'>{tool['description']}</p>
                        <div style='margin-top: 1rem; font-size: 0.8rem;'>
                            <span>👤 {tool['author']}</span><br>
                            <span>🔖 {tool['version']}</span>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    if st.button(f"使用{tool['icon']}", key=f"use_{tool['module']}", use_container_width=True):
                        st.session_state.selected_tool = tool
                        st.rerun()

def tool_interface(tool_config):
    """工具界面"""
    # 显示返回按钮
    if st.sidebar.button("🏠 返回主页"):
        if "selected_tool" in st.session_state:
            del st.session_state.selected_tool
        st.rerun()
    
    # 显示工具信息
    st.sidebar.markdown(f"""
    ### {tool_config['icon']} {tool_config['name']}
    
    **描述**: {tool_config['description']}
    
    **作者**: {tool_config['author']}
    
    **版本**: {tool_config['version']}
    
    **分类**: {tool_config['category']}
    """)
    
    # 加载并运行工具
    st.title(f"{tool_config['icon']} {tool_config['name']}")
    
    with st.spinner(f"正在加载 {tool_config['name']}..."):
        tool_module = load_tool_module(tool_config["module"])
        
        if tool_module and hasattr(tool_module, 'main'):
            try:
                # 运行工具的主函数
                tool_module.main()
            except Exception as e:
                st.error(f"运行工具时出错: {str(e)}")
                st.exception(e)
        else:
            st.error(f"工具模块 {tool_config['module']} 没有找到 main() 函数")

def admin_panel():
    """管理面板"""
    st.title("⚙️ 工具管理")
    
    config = load_tools_config()
    tools = config.get("tools", [])
    
    tab1, tab2, tab3 = st.tabs(["工具列表", "添加工具", "配置管理"])
    
    with tab1:
        st.subheader("已安装工具")
        for i, tool in enumerate(tools):
            with st.expander(f"{tool['icon']} {tool['name']} - v{tool['version']}"):
                col1, col2 = st.columns([3, 1])
                with col1:
                    st.write(f"**模块名**: {tool['module']}")
                    st.write(f"**描述**: {tool['description']}")
                    st.write(f"**作者**: {tool['author']}")
                    st.write(f"**分类**: {tool['category']}")
                with col2:
                    if st.button("删除", key=f"del_{i}", type="secondary"):
                        tools.pop(i)
                        config["tools"] = tools
                        save_tools_config(config)
                        st.success("已删除工具")
                        st.rerun()
    
    with tab2:
        st.subheader("添加新工具")
        with st.form("add_tool_form"):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("工具名称*")
                module = st.text_input("模块名*（对应tools目录下的.py文件名）")
                description = st.text_area("工具描述*")
            with col2:
                icon = st.text_input("图标*", value="🔧")
                author = st.text_input("作者*", value="匿名")
                version = st.text_input("版本*", value="1.0.0")
                category = st.selectbox("分类", config.get("categories", []))
            
            if st.form_submit_button("添加工具", type="primary"):
                if name and module and description:
                    new_tool = {
                        "name": name,
                        "module": module,
                        "description": description,
                        "icon": icon,
                        "author": author,
                        "version": version,
                        "category": category
                    }
                    tools.append(new_tool)
                    config["tools"] = tools
                    save_tools_config(config)
                    st.success("工具添加成功！")
                    st.rerun()
                else:
                    st.error("请填写所有必填项（带*的字段）")
    
    with tab3:
        st.subheader("平台配置")
        
        # 管理分类
        st.write("**工具分类管理**")
        categories = config.get("categories", [])
        
        new_category = st.text_input("添加新分类")
        if st.button("添加分类"):
            if new_category and new_category not in categories:
                categories.append(new_category)
                config["categories"] = categories
                save_tools_config(config)
                st.success(f"已添加分类: {new_category}")
                st.rerun()
        
        # 显示现有分类
        for i, category in enumerate(categories):
            col1, col2 = st.columns([1, 3])
            with col1:
                if st.button("🗑️", key=f"del_cat_{i}"):
                    categories.pop(i)
                    config["categories"] = categories
                    save_tools_config(config)
                    st.success(f"已删除分类: {category}")
                    st.rerun()
            with col2:
                st.write(category)

def main():
    """主函数"""
    # 初始化session state
    if "selected_tool" not in st.session_state:
        st.session_state.selected_tool = None
    if "show_admin" not in st.session_state:
        st.session_state.show_admin = False
    
    # 侧边栏导航
    with st.sidebar:
        st.title("导航")
        
        if st.button("🏠 主页", use_container_width=True):
            if "selected_tool" in st.session_state:
                del st.session_state.selected_tool
            if "show_admin" in st.session_state:
                st.session_state.show_admin = False
            st.rerun()
        
        st.divider()
        
        # 显示可用工具
        config = load_tools_config()
        tools = config.get("tools", [])
        
        if tools:
            st.subheader("📋 工具列表")
            for tool in tools:
                if st.button(
                    f"{tool['icon']} {tool['name']}", 
                    key=f"nav_{tool['module']}",
                    use_container_width=True,
                    type="secondary"
                ):
                    st.session_state.selected_tool = tool
                    st.session_state.show_admin = False
                    st.rerun()
        
        st.divider()
        
        # 管理入口
        if st.button("⚙️ 管理面板", use_container_width=True):
            st.session_state.show_admin = True
            st.session_state.selected_tool = None
            st.rerun()
    
    # 主内容区
    if st.session_state.show_admin:
        admin_panel()
    elif st.session_state.selected_tool:
        tool_interface(st.session_state.selected_tool)
    else:
        main_dashboard()

if __name__ == "__main__":
    main()