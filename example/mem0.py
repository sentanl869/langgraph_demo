import requests
import json
 
# 配置你的 Server 地址 (请根据实际情况修改端口，默认通常是 8000)
MEM0_SERVER_URL = "http://localhost:8888"
# 如果你在部署时设置了 API Key，请填入；如果没有设置，可以留空
API_KEY = "your-api-key"
 
headers = {
    "Content-Type": "application/json",
    "Authorization": f"Token {API_KEY}" if API_KEY else ""
}
 
def add_memory(content, user_id):
    """向 Server 添加记忆"""
    url = f"{MEM0_SERVER_URL}/memories/"
    payload = {
        "messages": [
            {"role": "user", "content": content}
        ],
        "user_id": user_id
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
 
def search_memories(query, user_id):
    """从 Server 搜索记忆"""
    url = f"{MEM0_SERVER_URL}/search/"
    payload = {
        "query": query,
        "user_id": user_id
    }
    response = requests.post(url, json=payload, headers=headers)
    return response.json()
 
# --- 测试调用 ---
try:
    uid = "test_user_001"
     
    # 1. 存储记忆
    print("正在存入记忆...")
    save_res = add_memory("我喜欢在周五晚上吃火锅", uid)
    print("存储结果:", json.dumps(save_res, indent=2, ensure_ascii=False))
 
    # 2. 查询记忆
    print("\n正在查询记忆...")
    search_res = search_memories("用户周五晚上喜欢做什么？", uid)
    print("查询结果:", json.dumps(search_res, indent=2, ensure_ascii=False))
 
except Exception as e:
    print(f"调用失败: {e}")
