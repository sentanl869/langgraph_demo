#!/usr/bin/env python3
"""
Agent客户端
部署在内网另一台电脑上，连接MCP服务器
运行命令: python agent_client.py
"""

import json
import requests
import sys


class MCPAgentClient:
    """MCP Agent客户端"""

    def __init__(self, server_url):
        """
        初始化客户端

        Args:
            server_url: MCP服务器的URL，如 http://192.168.1.100:8000
        """
        self.server_url = server_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})

        # 测试连接
        self._test_connection()

    def _test_connection(self):
        """测试服务器连接"""
        try:
            response = self.session.get(f"{self.server_url}/health", timeout=5)
            if response.status_code == 200:
                print(f"✓ 成功连接到MCP服务器: {self.server_url}")
                return True
            else:
                print(f"✗ 服务器返回错误: {response.status_code}")
                return False
        except requests.exceptions.ConnectionError:
            print(f"✗ 无法连接到服务器: {self.server_url}")
            print("  请检查:")
            print("  1. 服务器是否正在运行")
            print("  2. 网络是否连通")
            print("  3. IP地址和端口是否正确")
            print("  4. 防火墙是否允许该端口")
            return False
        except Exception as e:
            print(f"✗ 连接测试失败: {e}")
            return False

    def send_request(self, method, params=None, request_id=1):
        """
        发送JSON-RPC请求到MCP服务器

        Args:
            method: 方法名，如 "initialize", "tools/list", "tools/call"
            params: 参数对象
            request_id: 请求ID

        Returns:
            响应数据的字典
        """
        request = {
            "jsonrpc": "2.0",
            "method": method,
            "id": request_id
        }

        if params:
            request["params"] = params

        try:
            print(f"发送请求: {method} (ID: {request_id})")
            response = self.session.post(
                self.server_url,
                json=request,
                timeout=10
            )

            if response.status_code != 200:
                print(f"请求失败，状态码: {response.status_code}")
                return {"error": f"HTTP {response.status_code}"}

            return response.json()

        except requests.exceptions.Timeout:
            print("请求超时")
            return {"error": "请求超时"}
        except requests.exceptions.RequestException as e:
            print(f"网络错误: {e}")
            return {"error": f"网络错误: {e}"}
        except json.JSONDecodeError:
            print("响应不是有效的JSON")
            return {"error": "无效的JSON响应"}

    def initialize(self):
        """初始化MCP连接"""
        print("\n" + "=" * 50)
        print("步骤1: 初始化连接")
        print("=" * 50)

        response = self.send_request("initialize", {
            "protocolVersion": "0.1.0",
            "clientInfo": {
                "name": "MCP Agent Client",
                "version": "1.0.0"
            }
        }, request_id=1)

        if "result" in response:
            print("✓ 初始化成功")
            return True
        else:
            print(f"✗ 初始化失败: {response.get('error', '未知错误')}")
            return False

    def list_tools(self):
        """获取可用工具列表"""
        print("\n" + "=" * 50)
        print("步骤2: 获取工具列表")
        print("=" * 50)

        response = self.send_request("tools/list", request_id=2)

        if "result" in response:
            tools = response["result"].get("tools", [])
            print(f"✓ 获取到 {len(tools)} 个工具:")
            for tool in tools:
                print(f"  - {tool['name']}: {tool['description']}")
            return tools
        else:
            print(f"✗ 获取工具列表失败: {response.get('error', '未知错误')}")
            return []

    def call_tool(self, tool_name, arguments=None):
        """调用MCP工具"""
        print("\n" + "=" * 50)
        print(f"步骤3: 调用工具 '{tool_name}'")
        print("=" * 50)

        response = self.send_request("tools/call", {
            "name": tool_name,
            "arguments": arguments or {}
        }, request_id=3)

        if "result" in response:
            print("✓ 工具调用成功")

            # 提取并显示结果
            content = response["result"].get("content", [])
            for item in content:
                if item.get("type") == "text":
                    try:
                        result_data = json.loads(item["text"])
                        print("返回结果:")
                        print(json.dumps(result_data, indent=2, ensure_ascii=False))
                    except:
                        print(f"文本结果: {item['text']}")
            return response["result"]
        else:
            print(f"✗ 工具调用失败: {response.get('error', '未知错误')}")
            return None


def main():
    """主函数"""
    print("MCP Agent 客户端")
    print("=" * 60)

    # 获取服务器地址
    if len(sys.argv) > 1:
        server_url = sys.argv[1]
    else:
        # 默认地址，请根据实际情况修改
        server_url = "http://172.24.10.25:8000"
        print(f"未指定服务器地址，使用默认: {server_url}")
        print("如需指定，请使用: python agent_client.py <服务器地址>")
        print("例如: python agent_client.py http://172.24.10.25:8000")

    print(f"目标服务器: {server_url}")
    print("=" * 60)

    # 创建客户端
    client = MCPAgentClient(server_url)

    # 执行MCP流程
    if not client.initialize():
        return

    tools = client.list_tools()
    if not tools:
        print("没有可用的工具，退出")
        return

    # 调用每个工具
    for tool in tools:
        client.call_tool(tool["name"], {"name": "测试用户", "test": True})

    print("\n" + "=" * 60)
    print("MCP测试完成!")
    print("=" * 60)


if __name__ == "__main__":
    main()