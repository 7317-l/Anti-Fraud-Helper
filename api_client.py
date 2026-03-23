import requests
import json

# ============ 基础配置（保留成功文件的配置）============
BASE_URL = "https://hiagent.zcmu.edu.cn:32300/api/proxy/api/v1"
API_KEY = "d6tslb6lvndc72p0sqlg"
USER_ID = "d6r42tmlvndc72p0mkg0"

headers = {
    "Apikey": API_KEY,
    "Content-Type": "application/json"
}

# 反诈助手系统指令
SYSTEM_INSTRUCTION = """你是反诈智能助手，专门帮助用户识别和防范各类电信诈骗。
请用简洁易懂的语言回答问题，特别关注老年人群体的理解能力。
如果检测到诈骗风险，请明确告知风险等级（安全/中风险/高风险）。"""

def call_ai_api(user_message):
    """
    调用 AI API（保留成功文件的两步调用逻辑）
    返回格式：{"success": True/False, "reply": "回复内容" 或 "error": "错误信息"}
    """
    # ==========================================
    # 步骤 1：创建会话
    # ==========================================
    create_url = f"{BASE_URL}/create_conversation"
    create_data = {"UserID": USER_ID}
    
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
    # 步骤 2：发送消息并获取回复
    # ==========================================
    chat_url = f"{BASE_URL}/chat_query_v2"
    
    # 融合系统指令和用户消息
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
        
        answer = chat_result.get("answer", "未获取到回答内容")
        return {"success": True, "reply": answer}
        
    except Exception as e:
        return {"success": False, "error": f"发送消息请求异常：{str(e)}"}

def analyze_risk_with_ai(text, image_description=""):
    """AI 风险分析"""
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
    """本地规则分析（API 失败时的备用方案）"""
    risk_keywords_high = ["转账", "汇款", "安全账户", "验证码", "刷单", "返利", "垫付", "中奖", "退款"]
    risk_keywords_medium = ["贷款", "征信", "额度", "解冻", "兼职", "投资"]
    
    if any(k in text for k in risk_keywords_high):
        return {"success": True, "risk_level": "高风险", "analysis": "🔴 **高风险**：检测到敏感词汇，疑似诈骗！请立即停止操作并核实对方身份。", "fallback": True}
    elif any(k in text for k in risk_keywords_medium):
        return {"success": True, "risk_level": "中风险", "analysis": "🟠 **中风险**：检测到潜在风险词汇，请谨慎操作，建议通过官方渠道核实。", "fallback": True}
    else:
        return {"success": True, "risk_level": "安全", "analysis": "🟢 **安全**：未检测到明显风险，但仍请保持警惕。", "fallback": True}

def get_smart_response(user_message, uploaded_img=None, uploaded_audio=None):
    """主入口函数（app.py 调用这个）"""
    image_desc = "[用户上传了一张图片]" if uploaded_img else ""
    analysis_result = analyze_risk_with_ai(user_message, image_desc)
    
    if analysis_result["success"]:
        risk_level = analysis_result["risk_level"]
        ai_analysis = analysis_result["analysis"]
        popup_msg = None
        if risk_level == "高风险":
            popup_msg = f"🚨 诈骗风险检测！检测到高风险内容！{ai_analysis[:150]}... 请立即停止任何资金操作！"
        return {
            "risk_level": risk_level,
            "content": ai_analysis,
            "popup_msg": popup_msg,
            "is_fallback": analysis_result.get("fallback", False)
        }
    else:
        return {"risk_level": "安全", "content": "⚠️ 智能分析暂时不可用", "popup_msg": None, "error": True}

# 测试运行
if __name__ == "__main__":
    print("开始测试反诈接口...")
    test_msg = "你好，我是公安局的，请你把钱转到安全账户验证一下。"
    result = get_smart_response(test_msg)
    print(f"风险等级：{result['risk_level']}")
    print(f"分析内容：{result['content']}")
    if result.get('popup_msg'):
        print(f"弹窗警告：{result['popup_msg']}")
