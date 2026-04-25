import os
from http import HTTPStatus

from dashscope import Generation
from dotenv import load_dotenv

from config_loader import config

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")


def call_qwen(prompt: str) -> str:
    messages = [{'role': 'user', 'content': prompt}]
    response = Generation.call(
        api_key=api_key,
        model=config.llm_model,
        messages=messages,
        result_format="message"
    )
    if response.status_code == HTTPStatus.OK:
        return response.output.choices[0].message.content
    raise Exception(f"API调用失败: {response.message}")
