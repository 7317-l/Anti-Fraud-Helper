import streamlit as st
import time
from datetime import datetime

from api_client import get_smart_response

st.set_page_config(page_title="反诈智能助手原型", page_icon="🛡️", layout="wide", initial_sidebar_state="expanded")

st.markdown("""
<style>
.risk-high {background-color: #ffe6e6 !important; border-left: 4px solid #ff4444; padding: 15px; border-radius: 8px;}
.risk-medium {background-color: #fff3e6 !important; border-left: 4px solid #ff9900; padding: 15px; border-radius: 8px;}
.risk-safe {background-color: #e6ffe6 !important; border-left: 4px solid #00cc66; padding: 15px; border-radius: 8px;}
.stat-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}

/* 弹窗样式 */
.popup-overlay {
    position: fixed; 
    top: 0; 
    left: 0; 
    width: 100vw; 
    height: 100vh; 
    background: rgba(0,0,0,0.85); 
    z-index: 99999; 
    display: flex; 
    justify-content: center; 
    align-items: center; 
    backdrop-filter: blur(8px);
}
.popup-box {
    background: linear-gradient(135deg, #ff4444 0%, #cc0000 100%); 
    color: white; 
    padding: 40px 50px; 
    border-radius: 20px; 
    box-shadow: 0 0 60px rgba(255,0,0,0.7); 
    width: 520px; 
    text-align: center; 
    border: 5px solid #ffcc00; 
    animation: popIn 0.5s cubic-bezier(0.175, 0.885, 0.32, 1.275); 
    position: relative;
}
@keyframes popIn {
    from { opacity: 0; transform: scale(0.7) translateY(30px); } 
    to { opacity: 1; transform: scale(1) translateY(0); }
}
.popup-title {
    font-size: 38px; 
    font-weight: bold; 
    margin: 0 0 20px 0; 
    color: #ffcc00; 
    text-shadow: 3px 3px 6px rgba(0,0,0,0.5);
}
.popup-content {
    font-size: 24px; 
    line-height: 1.7; 
    margin: 25px 0; 
    font-weight: 600;
    text-align: left;
    background: rgba(255,255,255,0.95);
    color: #333;
    padding: 25px;
    border-radius: 10px;
    max-height: 400px;
    overflow-y: auto;
}
.popup-footer {
    font-size: 20px; 
    color: #fff; 
    margin-top: 20px; 
    font-weight: bold;
}
.countdown-badge {
    display: inline-block; 
    background: rgba(255,255,255,0.25); 
    padding: 10px 25px; 
    border-radius: 25px; 
    font-size: 18px; 
    margin-top: 25px; 
    font-weight: bold; 
    border: 2px solid rgba(255,255,255,0.3);
}
.popup-icon {
    font-size: 80px; 
    margin-bottom: 15px; 
    animation: pulse 1s infinite;
}
@keyframes pulse {
    0%, 100% { transform: scale(1); } 
    50% { transform: scale(1.1); }
}

/* 叉号关闭按钮 */
.close-btn {
    position: absolute;
    top: 15px;
    right: 15px;
    width: 45px;
    height: 45px;
    background: rgba(255,255,255,0.9);
    border: none;
    border-radius: 50%;
    color: #cc0000;
    font-size: 28px;
    font-weight: bold;
    cursor: pointer;
    display: flex;
    align-items: center;
    justify-content: center;
    transition: all 0.3s ease;
    line-height: 1;
    z-index: 100;
}
.close-btn:hover {
    background: white;
    transform: scale(1.15);
    box-shadow: 0 0 15px rgba(255,255,255,0.8);
}

.ad-banner {
    background: linear-gradient(90deg, #ff9966, #ff5e62); 
    color: white; 
    padding: 15px; 
    border-radius: 10px; 
    text-align: center; 
    font-size: 18px; 
    font-weight: bold; 
    margin: 10px 0; 
    box-shadow: 0 2px 4px rgba(0,0,0,0.2);
}
</style>
""", unsafe_allow_html=True)

# --- Session State 初始化 ---
if "messages" not in st.session_state:
    st.session_state.messages = []
if "risk_level" not in st.session_state:
    st.session_state.risk_level = "安全"
if "risk_count" not in st.session_state:
    st.session_state.risk_count = 0
if "safe_count" not in st.session_state:
    st.session_state.safe_count = 0
if "show_popup" not in st.session_state:
    st.session_state.show_popup = False
if "popup_message" not in st.session_state:
    st.session_state.popup_message = ""
if "popup_remaining" not in st.session_state:
    st.session_state.popup_remaining = 0
if "ad_index" not in st.session_state:
    st.session_state.ad_index = 0

role = "老年人"
guardian = "138****1234"

# --- ✅ 弹窗渲染函数（修复版）---
popup_placeholder = st.empty()

def render_popup():
    if not st.session_state.show_popup:
        popup_placeholder.empty()
        return
    
    # ✅ 直接处理内容，不转义 HTML 标签
    content_lines = st.session_state.popup_message.split('\n')
    content_html = '<br>'.join([f'<div>{line}</div>' for line in content_lines if line.strip()])
    
    # ✅ 使用完整的 HTML + JS，确保叉号能关闭
    popup_html = f'''
    <div id="risk-popup-overlay" class="popup-overlay">
        <div class="popup-box">
            <!-- 叉号按钮 -->
            <button class="close-btn" onclick="closeRiskPopup()">×</button>
            
            <div class="popup-icon">🚨</div>
            <h2 class="popup-title">反诈预警</h2>
            <div class="popup-content">
                {content_html}
            </div>
            <div class="popup-footer">
                 请立即停止任何转账操作！<br>
                如有疑问请联系监护人！
            </div>
            <div class="countdown-badge" id="countdown-timer">
                ⏱️ 窗口将在 {st.session_state.popup_remaining} 秒后自动关闭
            </div>
        </div>
    </div>
    
    <script>
        // 关闭弹窗函数
        function closeRiskPopup() {{
            var popup = document.getElementById("risk-popup-overlay");
            if (popup) {{
                popup.style.display = "none";
            }}
            // 通知 Streamlit 弹窗已关闭（可选）
            if (window.parent) {{
                window.parent.postMessage({{type: "popup_closed"}}, "*");
            }}
        }}
        
        // 倒计时自动关闭
        var seconds = {st.session_state.popup_remaining};
        var countdownEl = document.getElementById("countdown-timer");
        var popupEl = document.getElementById("risk-popup-overlay");
        
        if (countdownEl && popupEl) {{
            var timer = setInterval(function() {{
                seconds--;
                if (seconds <= 0) {{
                    clearInterval(timer);
                    popupEl.style.display = "none";
                }} else {{
                    countdownEl.innerHTML = "⏱️ 窗口将在 " + seconds + " 秒后自动关闭";
                }}
            }}, 1000);
        }}
        
        // 点击遮罩层也可以关闭
        if (popupEl) {{
            popupEl.addEventListener('click', function(e) {{
                if (e.target === popupEl) {{
                    closeRiskPopup();
                }}
            }});
        }}
    </script>
    '''
    
    popup_placeholder.markdown(popup_html, unsafe_allow_html=True)

# --- 广告轮播 ---
ad_messages = [
    "📢 反诈小贴士：陌生来电要警惕，可疑链接莫点击！转账汇款先核实，守护您的钱袋子！",
    "📢 防骗口诀：不轻信、不透露、不转账，遇事先问家人或警察！",
    "📢 温馨提示：公检法不会电话办案，更不会索要银行卡信息！",
    "📢 紧急提醒：网络刷单、虚假投资都是诈骗，天上不会掉馅饼！"
]
ad_placeholder = st.empty()

def render_ad_banner():
    ad_text = ad_messages[st.session_state.ad_index]
    ad_placeholder.markdown(f'<div class="ad-banner">{ad_text}</div>', unsafe_allow_html=True)
    col_prev, col_next = st.columns([1, 1])
    with col_prev:
        if st.button("⬅️ 上一条", key="ad_prev"):
            st.session_state.ad_index = (st.session_state.ad_index - 1) % len(ad_messages)
            st.rerun()
    with col_next:
        if st.button("下一条 ➡️", key="ad_next"):
            st.session_state.ad_index = (st.session_state.ad_index + 1) % len(ad_messages)
            st.rerun()

# --- 侧边栏 ---
with st.sidebar:
    st.title("🛡️ 反诈智能助手")
    st.markdown("### 👤 用户画像设置")
    role = st.selectbox("身份角色", ["老年人", "青少年", "中青年", "财会人员"], index=0)
    guardian = st.text_input("监护人联系方式", value="138****1234")
    st.toggle("开启监护人联动", value=True, key="guardian_linkage")
    st.markdown("---")
    st.markdown("### 📊 实时监测状态")
    status_color = "🟢" if st.session_state.risk_level == "安全" else "🔴"
    st.metric("当前风险等级", f"{status_color} {st.session_state.risk_level}")
    st.markdown("---")
    st.markdown("### 📈 今日统计")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("安全对话", st.session_state.safe_count)
    with col2:
        st.metric("风险预警", st.session_state.risk_count)
    st.markdown("---")
    st.caption("© 2026 浙工大网络空间安全创新研究院")

# --- 先渲染弹窗 ---
render_popup()

# --- 广告轮播 ---
render_ad_banner()

# --- 主界面 ---
st.title("💬 智能反诈对话助手")
st.markdown("支持文本、语音、图片多模态输入，实时风险识别与预警")

col1, col2, col3 = st.columns(3)
with col1:
    bg_color = "linear-gradient(135deg, #ff4444 0%, #cc0000 100%)" if st.session_state.risk_level == "高风险" else ("linear-gradient(135deg, #ff9900 0%, #ff6600 100%)" if st.session_state.risk_level == "中风险" else "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
    st.markdown(f'<div class="stat-card" style="background: {bg_color};"><h3>️ 防护状态</h3><div style="font-size: 24px; font-weight: bold;">{st.session_state.risk_level}</div></div>', unsafe_allow_html=True)
with col2:
    st.markdown(f'<div class="stat-card" style="background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);"><h3>📊 今日检测</h3><div style="font-size: 24px; font-weight: bold;">{st.session_state.safe_count + st.session_state.risk_count} 次</div></div>', unsafe_allow_html=True)
with col3:
    st.markdown(f'<div class="stat-card" style="background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%);"><h3>👥 监护人</h3><div style="font-size: 20px; font-weight: bold;">{guardian}</div></div>', unsafe_allow_html=True)

st.markdown("---")

for message in st.session_state.messages:
    with st.chat_message(message["role"]):
        st.markdown(message["content"])
        if message["role"] == "assistant" and message.get("risk_level") == "高风险":
            st.error("⚠️ 高风险预警！已自动通知监护人。")
            if st.session_state.get("guardian_linkage", True):
                st.info(f"📩 已发送预警短信至监护人：{guardian}")

col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    uploaded_img = st.file_uploader("上传图片/截图", type=["png", "jpg", "jpeg"], key="img_uploader", label_visibility="collapsed")
with col2:
    uploaded_audio = st.file_uploader("上传语音", type=["wav", "mp3"], key="audio_uploader", label_visibility="collapsed")
with col3:
    if st.button("🗑️ 清空记录", key="clear1", use_container_width=True):
        st.session_state.messages = []
        st.session_state.risk_level = "安全"
        st.session_state.risk_count = 0
        st.session_state.safe_count = 0
        st.session_state.show_popup = False
        st.rerun()

# --- 聊天输入框 ---
prompt = st.chat_input("请输入内容或描述附件...")

if prompt or uploaded_img or uploaded_audio:
    with st.chat_message("user"):
        if prompt:
            st.markdown(prompt)
        if uploaded_img:
            st.image(uploaded_img, width=300, caption="📷 上传的图片")
        if uploaded_audio:
            st.audio(uploaded_audio, caption="🎤 上传的语音")
    user_content = prompt if prompt else "发送了一个附件"
    st.session_state.messages.append({"role": "user", "content": user_content, "image": uploaded_img, "audio": uploaded_audio})
    with st.chat_message("assistant"):
        message_placeholder = st.empty()
        message_placeholder.markdown("🤔 正在分析多模态数据...")
        time.sleep(0.8)
        ai_result = get_smart_response(prompt, uploaded_img, uploaded_audio)
        risk_level = ai_result["risk_level"]
        risk_content = ai_result["content"]
        popup_msg = ai_result.get("popup_msg")
        if ai_result.get("is_fallback"):
            risk_content += "\n\n<i>（当前使用本地规则分析，AI 服务暂不可用）</i>"
        risk_class_name = "risk-high" if risk_level == "高风险" else ("risk-medium" if risk_level == "中风险" else "risk-safe")
        message_placeholder.markdown(f'<div class="{risk_class_name}">{risk_content}</div>', unsafe_allow_html=True)
        if risk_level == "高风险":
            st.error("️ 高风险预警！已自动通知监护人。")
            if st.session_state.get("guardian_linkage", True):
                st.info(f"📩 已发送预警短信至监护人：{guardian}")
            st.session_state.risk_count += 1
            if popup_msg:
                st.session_state.show_popup = True
                st.session_state.popup_message = popup_msg
                st.session_state.popup_remaining = 5
                st.rerun()
        elif risk_level == "中风险":
            st.warning("⚠️ 中风险提醒！请谨慎操作。")
            st.session_state.risk_count += 1
        else:
            st.session_state.safe_count += 1
        st.session_state.risk_level = risk_level
        st.session_state.messages.append({"role": "assistant", "content": risk_content, "risk_level": risk_level})

st.markdown("---")
col1, col2, col3 = st.columns([3, 1, 1])
with col1:
    st.caption("🔒 当前会话已加密存储，用于个性化风险评估")
with col2:
    report_data = f"""反诈安全报告
生成时间：{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
风险等级：{st.session_state.risk_level}
安全对话：{st.session_state.safe_count} 次
风险预警：{st.session_state.risk_count} 次
监护人：{guardian}
用户角色：{role}
"""
    st.download_button(label="📥 下载安全报告", data=report_data, file_name=f"safety_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt", mime="text/plain", use_container_width=True)
with col3:
    if st.button("🗑️ 清空记录", key="clear2", use_container_width=True):
        st.session_state.messages = []
        st.session_state.risk_level = "安全"
        st.session_state.risk_count = 0
        st.session_state.safe_count = 0
        st.session_state.show_popup = False
        st.rerun()
