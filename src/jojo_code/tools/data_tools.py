"""JSON/YAML 处理工具"""

from typing import Any

from langchain_core.tools import tool


@tool("validate_json")
def validate_json(content: str) -> dict[str, Any]:
    """验证 JSON 格式

    Args:
        content: JSON 字符串

    Returns:
        验证结果
    """
    import json

    try:
        data = json.loads(content)
        return {
            "valid": True,
            "type": type(data).__name__,
            "keys": list(data.keys()) if isinstance(data, dict) else None,
        }
    except json.JSONDecodeError as e:
        return {
            "valid": False,
            "error": str(e),
            "position": e.pos,
        }


@tool("format_json")
def format_json(content: str, indent: int = 2) -> str:
    """格式化 JSON

    Args:
        content: JSON 字符串
        indent: 缩进空格数

    Returns:
        格式化后的 JSON
    """
    import json

    try:
        data = json.loads(content)
        return json.dumps(data, indent=indent, ensure_ascii=False)
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {str(e)}"


@tool("minify_json")
def minify_json(content: str) -> str:
    """压缩 JSON (去除空白)

    Args:
        content: JSON 字符串

    Returns:
        压缩后的 JSON
    """
    import json

    try:
        data = json.loads(content)
        return json.dumps(data, separators=(",", ":"))
    except json.JSONDecodeError as e:
        return f"JSON 解析失败: {str(e)}"


@tool("yaml_to_json")
def yaml_to_json(yaml_str: str) -> str:
    """YAML 转 JSON

    Args:
        yaml_str: YAML 字符串

    Returns:
        JSON 字符串
    """
    try:
        import json

        import yaml

        data = yaml.safe_load(yaml_str)
        return json.dumps(data, indent=2, ensure_ascii=False)
    except ImportError:
        return "需要安装 pyyaml: pip install pyyaml"
    except Exception as e:
        return f"转换失败: {str(e)}"


@tool("json_to_yaml")
def json_to_yaml(json_str: str) -> str:
    """JSON 转 YAML

    Args:
        json_str: JSON 字符串

    Returns:
        YAML 字符串
    """
    try:
        import json

        import yaml

        data = json.loads(json_str)
        return yaml.dump(data, allow_unicode=True, default_flow_style=False)
    except ImportError:
        return "需要安装 pyyaml: pip install pyyaml"
    except Exception as e:
        return f"转换失败: {str(e)}"


@tool("diff_json")
def diff_json(json1: str, json2: str) -> dict[str, Any]:
    """比较两个 JSON 的差异

    Args:
        json1: 第一个 JSON
        json2: 第二个 JSON

    Returns:
        差异结果
    """
    import json

    try:
        data1 = json.loads(json1)
        data2 = json.loads(json2)

        diff = _deep_diff(data1, data2)
        return {"different": len(diff) > 0, "diffs": diff}
    except Exception as e:
        return {"error": str(e)}


def _deep_diff(obj1: Any, obj2: Any, path: str = "") -> list[dict[str, Any]]:
    """深度比较两个对象"""
    diffs = []

    if type(obj1) is not type(obj2):
        diffs.append(
            {
                "path": path,
                "type": "type_changed",
                "from": type(obj1).__name__,
                "to": type(obj2).__name__,
            }
        )
        return diffs

    if isinstance(obj1, dict):
        all_keys = set(obj1.keys()) | set(obj2.keys())
        for key in all_keys:
            new_path = f"{path}.{key}" if path else key
            if key not in obj1:
                diffs.append({"path": new_path, "type": "added", "value": obj2[key]})
            elif key not in obj2:
                diffs.append({"path": new_path, "type": "removed", "value": obj1[key]})
            else:
                diffs.extend(_deep_diff(obj1[key], obj2[key], new_path))

    elif isinstance(obj1, list):
        if obj1 != obj2:
            diffs.append({"path": path, "type": "list_changed", "from": obj1, "to": obj2})

    else:
        if obj1 != obj2:
            diffs.append({"path": path, "type": "value_changed", "from": obj1, "to": obj2})

    return diffs


__all__ = [
    "validate_json",
    "format_json",
    "minify_json",
    "yaml_to_json",
    "json_to_yaml",
    "diff_json",
]
