import re


def clean_code(code: str) -> str:
    if "```python" in code:
        code = re.sub(r"(?s).*?```python\s*(.*?)\s*```.*", r"\1", code)
    elif "```" in code:
        code = re.sub(r"(?s).*?```\s*(.*?)\s*```.*", r"\1", code)

    invisible_chars = (
        "\u200b\u200c\u200d\u200e\u200f"
        "\ufeff\u00a0\u00ad"
        "\u202a\u202b\u202c\u202d\u202e"
    )
    code = code.translate({ord(ch): None for ch in invisible_chars})
    code = "".join(c for c in code if c.isprintable() or c in "\n\t")
    code = code.replace("\r\n", "\n").replace("\r", "\n").strip()
    return code


def clean_python_list(list_str) -> list:
    if isinstance(list_str, list):
        return list_str

    if "```python" in list_str:
        list_str = re.sub(r"(?s).*?```python(.*?)```", r"\1", list_str)

    list_str = re.sub(r"[\u200b\u200e\u200f\ufeff\u00a0\u00ad]", "", list_str)
    list_str = list_str.encode("utf-8", errors="ignore").decode("utf-8").strip()

    import ast
    try:
        parsed = ast.literal_eval(list_str)
        if not isinstance(parsed, list):
            raise ValueError("Result is not a list")
        return parsed
    except Exception as e:
        raise ValueError(f"Invalid list: {e}")
