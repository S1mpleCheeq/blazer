from typing import List
from models import TaskNode, AgentDescription
from services.llm_service import generate_embedding, call_qwen
from services.vector_service import compute_similarity, select_top_k_agents
from config_loader import config

class SemanticRouter:
    def __init__(self, agents: List[AgentDescription]):
        self.agents = agents
        self._initialize_embeddings()

    def _initialize_embeddings(self):
        """初始化Agent向量"""
        for agent in self.agents:
            if agent.embedding is None:
                agent.embedding = generate_embedding(agent.capabilities)

    def route_task_node(self, task_node: TaskNode) -> str:
        """路由任务节点到最合适的Agent"""
        strategy = config.router_strategy

        if strategy == "vector_similarity":
            return self._route_by_vector(task_node)
        elif strategy == "llm_selection":
            return self._route_by_llm(task_node)
        elif strategy == "hybrid":
            return self._route_hybrid(task_node)
        else:
            return self._route_by_vector(task_node)

    def _route_by_vector(self, task_node: TaskNode) -> str:
        """纯向量相似度匹配"""
        task_emb = generate_embedding(task_node.description)
        agent_embs = {agent.name: agent.embedding for agent in self.agents}
        similarities = compute_similarity(task_emb, agent_embs)
        top_agents = select_top_k_agents(similarities, k=1)
        return top_agents[0] if top_agents else self.agents[0].name

    def _route_by_llm(self, task_node: TaskNode) -> str:
        """LLM直接选择Agent"""
        agent_list = "\n".join([f"- {a.name}: {a.capabilities}" for a in self.agents])
        prompt = f"""请为以下任务选择最合适的Agent，只返回Agent名称。

任务: {task_node.description}

可用Agent:
{agent_list}

只返回Agent名称（如：Aerial）："""

        response = call_qwen(prompt).strip()
        for agent in self.agents:
            if agent.name in response:
                return agent.name
        return self.agents[0].name

    def _route_hybrid(self, task_node: TaskNode) -> str:
        """混合策略：向量筛选Top-K + LLM最终选择"""
        task_emb = generate_embedding(task_node.description)
        agent_embs = {agent.name: agent.embedding for agent in self.agents}
        similarities = compute_similarity(task_emb, agent_embs)
        top_k = config.router_top_k
        top_agent_names = select_top_k_agents(similarities, k=top_k)

        if len(top_agent_names) == 1:
            return top_agent_names[0]

        candidates = [a for a in self.agents if a.name in top_agent_names]
        agent_list = "\n".join([f"- {a.name}: {a.capabilities}" for a in candidates])

        prompt = f"""从以下候选Agent中选择最合适的执行任务，只返回Agent名称。

任务: {task_node.description}

候选Agent:
{agent_list}

只返回Agent名称："""

        response = call_qwen(prompt).strip()
        for agent in candidates:
            if agent.name in response:
                return agent.name
        return top_agent_names[0]
