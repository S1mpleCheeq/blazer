from typing import List
import uuid
import json
from models import Task, TaskNode, Priority, TaskStatus, NodeStatus
from services.llm_service import call_qwen
from config_loader import config

class HostAgent:
    def detect_priority(self, prompt: str) -> Priority:
        """检测任务优先级"""
        high_keywords = config.priority_keywords['HIGH']
        if any(kw in prompt for kw in high_keywords):
            return Priority.HIGH
        return Priority.NORMAL

    def decompose_task(self, user_prompt: str) -> Task:
        """任务拆解"""
        priority = self.detect_priority(user_prompt)

        decompose_prompt = f"""请将以下任务拆解为具体的执行步骤，以JSON格式返回，支持步骤间的依赖关系。

任务: {user_prompt}

返回格式（只返回JSON，不要其他内容）：
{{
  "nodes": [
    {{"id": "node_0", "description": "步骤1描述", "dependencies": []}},
    {{"id": "node_1", "description": "步骤2描述", "dependencies": ["node_0"]}},
    {{"id": "node_2", "description": "步骤3描述", "dependencies": ["node_0", "node_1"]}}
  ]
}}

说明：
- dependencies为空表示可以立即执行
- dependencies包含其他节点ID表示需要等待这些节点完成
- 限制：最多{config.max_nodes}个节点"""

        response = call_qwen(decompose_prompt)

        try:
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                data = json.loads(json_str)
                nodes_data = data.get('nodes', [])
                dag = [
                    TaskNode(
                        id=node['id'],
                        description=node['description'],
                        status=NodeStatus.PENDING,
                        dependencies=node.get('dependencies', [])
                    )
                    for node in nodes_data[:config.max_nodes]
                ]
            else:
                raise ValueError("No JSON found")
        except:
            steps = [line.strip() for line in response.split('\n') if line.strip() and not line.strip().startswith('#')]
            dag = [
                TaskNode(id=f"node_{i}", description=step, status=NodeStatus.PENDING, dependencies=[])
                for i, step in enumerate(steps[:config.max_nodes])
            ]

        task_id = str(uuid.uuid4())[:8]
        title = user_prompt[:50] + "..." if len(user_prompt) > 50 else user_prompt

        return Task(
            id=task_id,
            title=title,
            priority=priority,
            status=TaskStatus.RUNNING,
            dag=dag
        )

    def should_preempt(self, new_task: Task, current_task: Task) -> bool:
        """判断是否需要抢占"""
        priority_order = {Priority.HIGH: 2, Priority.NORMAL: 1}
        return priority_order[new_task.priority] > priority_order[current_task.priority]
