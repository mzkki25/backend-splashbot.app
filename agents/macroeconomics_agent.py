from typing import Optional
from prompt.web_prompt import handle_web_prompt
from prompt.file_prompt import handle_file_pdf, handle_file_image


def build_macro_prompt(last_response: str | None, prompt: str, snippets: str) -> str:
    return handle_web_prompt(last_response, prompt, snippets)


def build_file_prompt(prompt: str, file_obj, last_response: str | None) -> str:
    if hasattr(file_obj, "name"):
        return handle_file_pdf(prompt, file_obj, last_response)
    else:
        return handle_file_image(file_obj, prompt, last_response)
