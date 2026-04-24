import os
from typing import List
from dashscope import Generation, TextEmbedding
from http import HTTPStatus
from dotenv import load_dotenv
from config_loader import config

load_dotenv()
api_key = os.getenv("DASHSCOPE_API_KEY")

def call_qwen(prompt: str) -> str:
    """调用通义千问生成文本"""
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

def generate_embedding(text: str) -> List[float]:
    """使用Qwen生成文本向量"""
    response = TextEmbedding.call(
        api_key=api_key,
        model=config.embedding_model,
        input=text
    )
    if response.status_code == HTTPStatus.OK:
        return response.output['embeddings'][0]['embedding']
    raise Exception(f"向量化失败: {response.message}")
