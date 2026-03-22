import requests
import time

# ============ API 配置 ============
API_ID = "d6r42tmlvndc72p0mkg0"
API_KEY = "d6tslb6lvndc72p0sqlg"
API_URL = "https://hiagent.zcmu.edu.cn:32300/api/proxy/api/v1"

def call_ai_api(user_message, context=None):
    headers = {
        "Content-Type": "application/json",
        "X-API-ID": API_ID,
        "X-API-KEY": API_KEY
    }
    payload = {
        "model": "default",
        "messages": [
            {
                "role": "system",
                "content": "你是反诈智能助手，专门帮助用户识别和防范各类电信诈骗。请用简洁易懂的语言回答问题，特别关注老年人群体的理解能力。如果检测到诈骗风险，请明确告知风险等级（安全/中风险/高风险）。"
            },
            {
                "role": "user",
                "content": user_message
            }
        ],
        "temperature": 0.3,
        "max_tokens": 800,
        "stream": False
    }
    try:
        response = requests.post(API_URL, headers=headers, json=payload, timeout=30)
        response.raise_for_status()
        result = response.json()
        if "choices" in result and result["choices"]:
            reply = result["choices"][0]["message"]["content"]
        elif "data" in result and "reply" in result["data"]:
            reply = result["data"]["reply"]
        elif "result" in result:
            reply = result["result"]
        else:
            reply = str(result)
        return {"success": True, "reply": reply}
    except Exception as e:
        return {"success": False, "error": str(e)}

def analyze_risk_with_ai(text, image_description=""):
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
        return fallback_risk_analysis(text)

def fallback_risk_analysis(text):
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
