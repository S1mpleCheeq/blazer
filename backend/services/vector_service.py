from typing import Dict, List
import numpy as np
from sklearn.metrics.pairwise import cosine_similarity

def compute_similarity(task_emb: List[float], agent_embs: Dict[str, List[float]]) -> Dict[str, float]:
    """计算余弦相似度"""
    task_vec = np.array(task_emb).reshape(1, -1)
    similarities = {}
    for name, emb in agent_embs.items():
        agent_vec = np.array(emb).reshape(1, -1)
        sim = cosine_similarity(task_vec, agent_vec)[0][0]
        similarities[name] = float(sim)
    return similarities

def select_top_k_agents(similarities: Dict[str, float], k: int = 3) -> List[str]:
    """返回Top-K候选Agent"""
    sorted_agents = sorted(similarities.items(), key=lambda x: x[1], reverse=True)
    return [name for name, _ in sorted_agents[:k]]
