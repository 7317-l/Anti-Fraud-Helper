import requests
import json
import time

# ============ API 配置 (使用文件 2 的成功配置) ============
# 请确保填入文件 2 中那个有效的 API_KEY
BASE_URL = "https://hiagent.zcmu.edu.cn:32300/api/proxy/api/v1"
API_KEY = "d6tslb6lvndc72p0sqlg"  # ⚠️ 注意保密，不要泄露
USER_ID = "d6r42tmlvndc72p0mkg0"  # 自定义用户标识

# 成功的请求头配置
headers = {
    "Apikey": API_KEY,
    "Content-Type": "application/json"
}

# 文件 1 原有的系统指令 (反诈助手人设)
SYSTEM_INSTRUCTION = """
你是反诈智能助手，专门帮助用户识别和防范各类电信诈骗。
请用简洁易懂的语言回答问题，特别关注老年人群体的理解能力。
如果检测到诈骗风险，请明确告知风险等级（安全/中风险/高风险）。
"""

def call_ai_api(user_message, context=None):
    """
    使用文件 2 的成功网络配置来调用 API
    保留了文件 1 的返回格式 {"success": True, "reply": ...}
    """
    # ==========================================
    # 步骤 1：创建会话 (复用文件 2 的逻辑)
    # ==========================================
    create_url = f"{BASE_URL}/create_conversation"
    create_data = {
        "UserID": USER_ID
    }
    
    app_conversation_id = None
    try:
        create_resp = requests.post(create_url, headers=headers, json=create_data, timeout=30)
        create_resp.raise_for_status()
        create_result = create_resp.json()
        app_conversation_id = create_result.get("Conversation", {}).get("AppConversationID")
        
        if not app_conversation_id:
            return {"success": False, "error": "创建会话失败，未获取到 AppConversationID"}
            
    except Exception as e:
        return {"success": False, "error": f"创建会话请求异常：{str(e)}"}

    # ==========================================
    # 步骤 2：发送消息 (融合文件 1 的系统指令)
    # ==========================================
    chat_url = f"{BASE_URL}/chat_query_v2"
    
    # 因为新接口只支持 Query 字符串，我们将系统指令和用户消息合并
    full_query = f"{SYSTEM_INSTRUCTION}\n\n用户输入：{user_message}"
    
    chat_data = {
        "UserID": USER_ID,
        "AppConversationID": app_conversation_id,
        "Query": full_query,
        "ResponseMode": "blocking"
    }
    
    try:
        chat_resp = requests.post(chat_url, headers=headers, json=chat_data, timeout=30)
        chat_resp.raise_for_status()
        chat_result = chat_resp.json()
        
        # 适配文件 2 的返回格式
        reply = chat_result.get("answer", "未获取到回答内容")
        return {"success": True, "reply": reply}
        
    except Exception as e:
        return {"success": False, "error": f"发送消息请求异常：{str(e)}"}

def analyze_risk_with_ai(text, image_description=""):
    # 文件 1 原有的业务逻辑保持不变
    risk_prompt = f"""
    请分析以下内容是否存在诈骗风险，严格按以下格式回答：

    文本内容：{text}
    图片描述：{image_description}

    请按以下格式回答：
    风险等级：安全/中风险/高风险
    分析理由：...
    建议：...

    注意：如果提到转账、汇款、安全账户、验证码、刷单、返利、垫付等，通常是高风险。
    """
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
        # 如果 API 调用失败，进入降级方案
        return fallback_risk_analysis(text)

def fallback_risk_analysis(text):
    # 文件 1 原有的降级逻辑保持不变
    risk_keywords_high = ["转账", "汇款", "安全账户", "验证码", "刷单", "返利", "垫付", "中奖", "退款"]
    risk_keywords_medium = ["贷款", "征信", "额度", "解冻", "兼职", "投资"]
    text_lower = text.lower()
    if any(k in text_lower for k in risk_keywords_high):
        return {"success": True, "risk_level": "高风险", "analysis": "🔴 **高风险**：检测到敏感词汇，疑似诈骗！请立即停止操作并核实对方身份。", "fallback": True}
    elif any(k in text_lower for k in risk_keywords_medium):
        return {"success": True, "risk_level": "中风险", "analysis": "🟠 **中风险**：检测到潜在风险词汇，请谨慎操作，建议通过官方渠道核实。", "fallback": True}
    else:
        return {"success": True, "risk_level": "安全", "analysis": "🟢 **安全**：未检测到明显风险，但仍请保持警惕。", "fallback": True}

def get_smart_response(user_message, uploaded_img=None, uploaded_audio=None):
    # 文件 1 原有的入口逻辑保持不变
    image_desc = "[用户上传了一张图片]" if uploaded_img else ""
    analysis_result = analyze_risk_with_ai(user_message, image_desc)
    if analysis_result["success"]:
        risk_level = analysis_result["risk_level"]
        ai_analysis = analysis_result["analysis"]
        popup_msg = None
        if risk_level == "高风险":
            popup_msg = f"🚨 诈骗风险检测！<br><strong>检测到高风险内容！</strong><br>{ai_analysis[:150]}...<br><strong>请立即停止任何资金操作！</strong>"
        return {"risk_level": risk_level, "content": ai_analysis, "popup_msg": popup_msg, "is_fallback": analysis_result.get("fallback", False)}
    else:
        return {"risk_level": "安全", "content": "⚠️ 智能分析暂时不可用，请稍后再试。", "popup_msg": None, "error": True}

# 测试入口
if __name__ == "__main__":
    print("开始测试反诈接口...")
    test_msg = "你好，我是公安局的，请你把钱转到安全账户验证一下。"
    result = get_smart_response(test_msg)
    print(f"风险等级：{result['risk_level']}")
    print(f"分析内容：{result['content']}")
    if result.get('popup_msg'):
        print(f"弹窗警告：{result['popup_msg']}")
