import re
import ast

def clean_code(code: str) -> str:
    code = re.sub(r"(?s).*?```python(.*?)```", r"\1", code) if '```python' in code else code
    code = re.sub(r"(?s).*?python(.*?)```", r"\1", code) if 'python' in code else code

    invisible_chars = (
        '\u200b\u200c\u200d\u200e\u200f'  
        '\ufeff\u00a0\u00ad'              
        '\u202a\u202b\u202c\u202d\u202e'  
    )
    code = code.translate({ord(ch): None for ch in invisible_chars})
    code = ''.join(c for c in code if c.isprintable() or c in '\n\t')
    code = code.replace('\r\n', '\n').replace('\r', '\n').strip()

    return code

def clean_python_list(list_str) -> list:
    if isinstance(list_str, list):
        return list_str

    if '```python' in list_str:
        list_str = re.sub(r"(?s).*?```python(.*?)```", r"\1", list_str)
    elif 'python' in list_str:
        list_str = re.sub(r"(?s).*?python(.*?)```", r"\1", list_str)

    list_str = re.sub(r"[\u200b\u200e\u200f\ufeff\u00a0\u00ad]", '', list_str)
    list_str = list_str.encode('utf-8', errors='ignore').decode('utf-8').strip()

    try:
        parsed = ast.literal_eval(list_str)
        if not isinstance(parsed, list):
            raise ValueError("Hasil bukan list")
        return parsed

    except Exception as e:
        raise ValueError(f"List tidak valid: {e}")

def save_code(code: str, filename: str):
    with open(filename, 'w') as f:
        f.write(code)
    print(f"Code saved to {filename}")

def read_clean_python_file(filepath):
    try:
        with open(filepath, "r", encoding="utf-8") as f:
            code = f.read()

        code = code.replace('\r\n', '\n').strip()
        ast.parse(code)
        code = code.encode('utf-8', errors='ignore').decode('utf-8')

        return code

    except SyntaxError as e:
        raise SyntaxError(f"File Python tidak valid: {e}")

    except Exception as e:
        raise RuntimeError(f"Gagal membaca file: {e}")