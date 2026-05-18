"""HTTP 请求工具"""

from typing import Any

from langchain_core.tools import tool


@tool("http_get")
def http_get(url: str, headers: dict[str, str] | None = None) -> dict[str, Any]:
    """发送 GET 请求

    Args:
        url: 请求 URL
        headers: 请求头

    Returns:
        响应结果
    """
    import httpx

    try:
        response = httpx.get(url, headers=headers or {}, timeout=10)
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:5000],
        }
    except Exception as e:
        return {"error": str(e)}


@tool("http_post")
def http_post(
    url: str,
    data: dict[str, Any] | None = None,
    json_data: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """发送 POST 请求

    Args:
        url: 请求 URL
        data: 表单数据
        json_data: JSON 数据

    Returns:
        响应结果
    """
    import httpx

    try:
        response = httpx.post(url, data=data, json=json_data, timeout=10)
        return {
            "status": response.status_code,
            "headers": dict(response.headers),
            "content": response.text[:5000],
        }
    except Exception as e:
        return {"error": str(e)}


@tool("curl")
def curl(url: str, method: str = "GET", data: str = "", headers: str = "") -> str:
    """模拟 curl 命令

    Args:
        url: 请求 URL
        method: HTTP 方法
        data: 请求体
        headers: 请求头 (格式: "Key: Value\nKey: Value")

    Returns:
        curl 风格输出
    """
    import httpx

    try:
        header_dict = {}
        if headers:
            for line in headers.split("\n"):
                if ":" in line:
                    k, v = line.split(":", 1)
                    header_dict[k.strip()] = v.strip()

        if method == "GET":
            response = httpx.get(url, headers=header_dict, timeout=10)
        elif method == "POST":
            response = httpx.post(url, content=data, headers=header_dict, timeout=10)
        elif method == "PUT":
            response = httpx.put(url, content=data, headers=header_dict, timeout=10)
        elif method == "DELETE":
            response = httpx.delete(url, headers=header_dict, timeout=10)
        else:
            return f"不支持的方法: {method}"

        output = f"""< HTTP/1.1 {response.status_code}
{chr(10).join(f"{k}: {v}" for k, v in response.headers.items())}

{response.text[:2000]}"""
        return output

    except Exception as e:
        return f"请求失败: {str(e)}"


__all__ = ["http_get", "http_post", "curl"]
