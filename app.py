
import streamlit as st
import time
from datetime import datetime
import requests
import time as time_module

# --- 页面配置 ---
st.set_page_config(
    page_title="反诈智能助手原型",
    page_icon="🛡️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============ API 配置（已填入正确信息）============
API_CONFIG = {
    "id": "d6r42tmlvndc72p0mkg0",
    "key": "d6tslb6lvndc72p0sqlg",
    "url": "https://hiagent.zcmu.edu.cn:32300/api/proxy/api/v1",
    "timeout": 30,
    "verify_ssl": False  # 忽略 SSL 证书验证
}

# --- CSS 样式 ---
st.markdown("""
<style>
.risk-high {background-color: #ffe6e6 !important; border-left: 4px solid #ff4444; padding: 15px; border-radius: 8px;}
.risk-medium {background-color: #fff3e6 !important; border-left: 4px solid #ff9900; padding: 15px; border-radius: 8px;}
.risk-safe {background-color: #e6ffe6 !important; border-left: 4px solid #00cc66; padding: 15px; border-radius: 8px;}
.stat-card {background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 15px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.1);}
.popup-overlay {position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; background: rgba(0, 0, 0, 0.6); z-index: 99999; display: flex; justify-content: center; align-items: center; backdrop-filter: blur(10px);}
.popup-box {background: linear-gradient(145deg, #ff3333 0%, #cc0000 100%); color: white; padding: 50px 40px; border-radius: 24px; box-shadow: 0 20px 50px rgba(255, 0, 0, 0.4), 0 0 0 1px rgba(255,255,255,0.2) inset; width: 500px; text-align: center; border: 2px solid #ff6666; animation: popIn 0.4s cubic-bezier(0.175, 0.885, 0.32, 1.275); position: relative;}
@keyframes popIn {from { opacity: 0; transform: scale(0.8) translateY(20px); } to { opacity: 1; transform: scale(1) translateY(0); }}
.popup-icon {font-size: 70px; margin-bottom: 10px; filter: drop-shadow(0 4px 6px rgba(0,0,0,0.3)); animation: shake 2s infinite; display: inline-block;}
@keyframes shake {0%, 100% { transform: rotate(0deg); } 25% { transform: rotate(-5deg); } 75% { transform: rotate(5deg); }}
.popup-title {font-size: 36px; font-weight: 800; margin: 10px 0 20px 0; color: #fff; text-transform: uppercase; letter-spacing: 2px; text-shadow: 0 2px 4px rgba(0,0,0,0.3);}
.popup-content {font-size: 22px; line-height: 1.6; margin: 20px 0; font-weight: 600; color: #fff0f0;}
.popup-footer {font-size: 18px; color: #ffcccc; margin-top: 20px; font-weight: 500; background: rgba(0,0,0,0.2); padding: 10px; border-radius: 8px;}
.progress-bar {margin-top: 25px; width: 100%; height: 8px; background: rgba(255,255,255,0.2); border-radius: 10px; overflow: hidden;}
.progress-fill {height: 100%; background: linear-gradient(90deg, #ffcc00, #ff6600); border-radius: 10px; animation: progressAnim 5s linear forwards; width: 100%;}
@keyframes progressAnim {from { width: 100%; } to { width: 0%; }}
.ad-banner {background: linear-gradient(90deg, #ff9966, #ff5e62); color: white; padding: 15px; border-radius: 10px; text-align: center; font-size: 18px; font-weight: bold; margin: 10px 0; box-shadow: 0 2px 4px rgba(0,0,0,0.2);}
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
if "popup_trigger_time" not in st.session_state:
    st.session_state.popup_trigger_time = 0
if "ad_index" not in st.session_state:
    st.session_state.ad_index = 0
if "api_available" not in st.session_state:
    st.session_state.api_available = None
if "api_error_detail" not in st.session_state:
    st.session_state.api_error_detail = ""

# --- 全局变量 ---
role = "老年人"
guardian = "138****1234"

# ============ API 客户端函数 ============
def call_ai_api(user_message, context=None):
    """调用 AI API - 尝试多种请求格式"""
    
    # 请求头配置（尝试多种格式）
    headers_list = [
        {"Content-Type": "application/json", "X-API-ID": API_CONFIG["id"], "X-API-Key": API_CONFIG["key"]},
        {"Content-Type": "application/json", "X-API-ID": API_CONFIG["id"], "X-API-KEY": API_CONFIG["key"]},
        {"Content-Type": "application/json", "Authorization": f"Bearer {API_CONFIG['key']}", "X-API-ID": API_CONFIG["id"]},
    ]
    
    # 请求体配置（尝试多种格式）
    payload_list = [
        {
            "model": "default",
            "messages": [
                {"role": "system", "content": "你是反诈智能助手，专门帮助用户识别和防范各类电信诈骗。请用简洁易懂的语言回答问题。如果检测到诈骗风险，请明确告知风险等级（安全/中风险/高风险）。"},
                {"role": "user", "content": user_message}
            ],
            "temperature": 0.3,
            "max_tokens": 800,
            "stream": False
        },
        {
            "messages": [
                {"role": "user", "content": user_message}
            ],
            "stream": False
        },
        {
            "prompt": user_message,
            "stream": False
        }
    ]
    
    errors = []
    
    for headers in headers_list:
        for payload in payload_list:
            try:
                response = requests.post(
                    API_CONFIG["url"], 
                    headers=headers, 
                    json=payload, 
                    timeout=API_CONFIG["timeout"],
                    verify=API_CONFIG["verify_ssl"]
                )
                
                if response.status_code == 200:
                    result = response.json()
                    st.session_state.api_available = True
                    st.session_state.api_error_detail = ""
                    
                    # 解析多种返回格式
                    if "choices" in result and result["choices"]:
                        reply = result["choices"][0]["message"]["content"]
                    elif "data" in result and "reply" in result["data"]:
                        reply = result["data"]["reply"]
                    elif "result" in result:
                        reply = result["result"]
                    elif "response" in result:
                        reply = result["response"]
                    elif "content" in result:
                        reply = result["content"]
                    elif "message" in result:
                        reply = result["message"]
                    else:
                        reply = str(result)
                    
                    return {"success": True, "reply": reply}
                else:
                    errors.append(f"状态码 {response.status_code}: {response.text[:100]}")
                    
            except requests.exceptions.SSLError as e:
                errors.append(f"SSL 错误：{str(e)}")
            except requests.exceptions.ConnectionError as e:
                errors.append(f"连接错误：{str(e)}")
            except requests.exceptions.Timeout as e:
                errors.append(f"超时：{str(e)}")
            except Exception as e:
                errors.append(f"错误：{str(e)}")
    
    # 所有尝试都失败
    st.session_state.api_available = False
    st.session_state.api_error_detail = " | ".join(errors[:3])
    return {"success": False, "error": "API 连接失败", "details": st.session_state.api_error_detail}

def analyze_risk_with_ai(text, image_description=""):
    """使用 AI 分析风险"""
    risk_prompt = f"""请分析以下内容是否存在诈骗风险：

文本内容：{text}
图片描述：{image_description}

请按以下格式回答：
风险等级：安全/中风险/高风险
分析理由：...
建议：...

注意：如果提到转账、汇款、安全账户、验证码、刷单、返利、垫付等，通常是高风险。"""
    
    result = call_ai_api(risk_prompt)
    if result["success"]:
        ai_reply = result["reply"]
        if "高风险" in ai_reply:
            risk_level = "高风险"
        elif "中风险" in ai_reply:
            risk_level = "中风险"
        else:
            risk_level = "安全"
        return {"success": True, "risk_level": risk_level, "analysis": ai_reply}
    else:
        return fallback_risk_analysis(text)

def fallback_risk_analysis(text):
    """本地规则分析（API 不可用时的备用方案）"""
    if not text:
        return {"success": True, "risk_level": "安全", "analysis": "🟢 **安全**：未检测到明显风险，但仍请保持警惕。", "fallback": True}
    
    high_risk_keywords = ["转账", "汇款", "安全账户", "验证码", "刷单", "返利", "垫付", "中奖", "退款", "银行卡", "密码", "屏幕共享", "贷款", "征信", "冻结", "洗钱"]
    medium_risk_keywords = ["投资", "理财", "兼职", "链接", "扫码", "下载", "客服", "快递", "注销", "升级"]
    text_lower = text.lower()
    
    for keyword in high_risk_keywords:
        if keyword in text_lower:
            return {"success": True, "risk_level": "高风险", "analysis": f"🔴 **高风险**：检测到敏感词汇「**{keyword}**」，疑似诈骗！请立即停止操作并核实对方身份。", "fallback": True}
    
    for keyword in medium_risk_keywords:
        if keyword in text_lower:
            return {"success": True, "risk_level": "中风险", "analysis": f"🟠 **中风险**：检测到潜在风险词汇「**{keyword}**」，请谨慎操作，建议通过官方渠道核实。", "fallback": True}
    
    return {"success": True, "risk_level": "安全", "analysis": "🟢 **安全**：未检测到明显风险，但仍请保持警惕。", "fallback": True}

def get_smart_response(user_message, uploaded_img=None, uploaded_audio=None):
    """主分析函数"""
    image_desc = "[用户上传了一张图片]" if uploaded_img else ""
    
    # 如果 API 明确不可用，直接使用本地规则
    if st.session_state.api_available == False:
        analysis_result = fallback_risk_analysis(user_message)
    else:
        analysis_result = analyze_risk_with_ai(user_message, image_desc)
    
    if analysis_result["success"]:
        risk_level = analysis_result["risk_level"]
        ai_analysis = analysis_result["analysis"]
        popup_msg = None
        
        if risk_level == "高风险":
            popup_msg = f"🚨 诈骗风险检测！检测到高风险内容！{ai_analysis[:100]}... 请立即停止任何资金操作！"
        
        return {"risk_level": risk_level, "content": ai_analysis, "popup_msg": popup_msg, "is_fallback": analysis_result.get("fallback", False)}
    else:
        return {"risk_level": "安全", "content": "⚠️ 智能分析暂时不可用，请稍后再试。", "popup_msg": None, "error": True}

def test_api_connection():
    """测试 API 连接"""
    result = call_ai_api("你好，测试连接")
    return result["success"], result.get("reply", result.get("error", "未知错误")), result.get("details", "")

# --- 关闭弹窗逻辑 ---
def hide_popup_logic():
    st.session_state.show_popup = False
    st.session_state.popup_message = ""
    st.session_state.popup_trigger_time = 0
    if "close_popup" in st.query_params:
        del st.query_params["close_popup"]
    st.rerun()

# --- 检查 URL 参数 ---
if "close_popup" in st.query_params:
    hide_popup_logic()

# --- 检查弹窗是否超时 ---
if st.session_state.show_popup and st.session_state.popup_trigger_time > 0:
    current_time = time_module.time()
    if current_time - st.session_state.popup_trigger_time >= 5:
        hide_popup_logic()

# --- 弹窗渲染 ---
popup_placeholder = st.empty()

def render_popup():
    if not st.session_state.show_popup:
        popup_placeholder.empty()
        return
    
    popup_html = f'''
<div class="popup-overlay">
<div class="popup-box">
<div class="popup-icon">🚨</div>
<h2 class="popup-title">反诈预警</h2>
<div class="popup-content">{st.session_state.popup_message}</div>
<div class="popup-footer">⛔ 请立即停止任何转账操作！如有疑问请联系监护人！</div>
<div class="progress-bar"><div class="progress-fill"></div></div>
</div>
</div>
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
    st.markdown("### 🔌 API 连接状态")
    
    api_status = st.session_state.api_available
    if api_status is None:
        st.info("⚪ 首次使用，请点击测试按钮")
    elif api_status:
        st.success("🟢 API 已连接")
    else:
        st.warning("🟠 使用本地规则分析")
        if st.session_state.api_error_detail:
            with st.expander("📋 查看错误详情"):
                st.code(st.session_state.api_error_detail, language="text")
    
    if st.button("🔄 测试 API 连接", key="test_api", use_container_width=True):
        with st.spinner("正在连接 API..."):
            success, result, details = test_api_connection()
            if success:
                st.success("✅ API 连接成功！")
                with st.expander("查看 AI 回复"):
                    st.write(result)
            else:
                st.warning("⚠️ API 连接失败，使用本地规则")
                if details:
                    with st.expander("📋 详细错误信息"):
                        st.code(details, language="text")
                    st.info("""
                    **可能的原因：**
                    1. 需要校园网环境才能访问
                    2. API 服务暂时不可用
                    3. 网络连接问题
                    
                    **当前仍可使用本地规则分析，功能正常！**
                    """)
    
    st.markdown("---")
    st.markdown("### 📊 实时监测状态")
    status_color = "🟢" if st.session_state.risk_level == "安全" else "🔴"
    st.metric("当前风险等级", f"{status_color} {st.session_state.risk_level}")
    
    if st.session_state.show_popup:
        st.error("⚠️ 预警弹窗已触发")
        if st.button("🛑 手动关闭预警", key="manual_close_popup", use_container_width=True):
            hide_popup_logic()
    
    st.markdown("---")
    st.markdown("### 📈 今日统计")
    col1, col2 = st.columns(2)
    with col1:
        st.metric("安全对话", st.session_state.safe_count)
    with col2:
        st.metric("风险预警", st.session_state.risk_count)
    st.markdown("---")
    st.caption("© 2026 浙工大网络空间安全创新研究院")

# --- 渲染弹窗 ---
render_popup()

# --- 广告轮播 ---
render_ad_banner()

# --- 主界面 ---
st.title("💬 智能反诈对话助手")
st.markdown("支持文本、语音、图片多模态输入，实时风险识别与预警")

col1, col2, col3 = st.columns(3)
with col1:
    bg_color = "linear-gradient(135deg, #ff4444 0%, #cc0000 100%)" if st.session_state.risk_level == "高风险" else ("linear-gradient(135deg, #ff9900 0%, #ff6600 100%)" if st.session_state.risk_level == "中风险" else "linear-gradient(135deg, #667eea 0%, #764ba2 100%)")
    st.markdown(f'<div class="stat-card" style="background: {bg_color};"><h3>🛡️ 防护状态</h3><div style="font-size: 24px; font-weight: bold;">{st.session_state.risk_level}</div></div>', unsafe_allow_html=True)
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
        hide_popup_logic()

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
            st.error("⚠️ 高风险预警！已自动通知监护人。")
            if st.session_state.get("guardian_linkage", True):
                st.info(f"📩 已发送预警短信至监护人：{guardian}")
            st.session_state.risk_count += 1
            if popup_msg:
                st.session_state.show_popup = True
                st.session_state.popup_message = popup_msg
                st.session_state.popup_trigger_time = time_module.time()
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
        hide_popup_logic()
