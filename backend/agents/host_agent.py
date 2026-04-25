import json
import os
import uuid
from typing import List, Dict, Optional
from models import Task, TaskNode, TaskStatus, NodeStatus, ActionType
from services.llm_service import call_qwen
from config_loader import config


def _load_locations() -> List[Dict]:
    path = os.path.join(os.path.dirname(__file__), '..', '..', 'map_data', '标注.json')
    with open(path, 'r', encoding='utf-8') as f:
        return json.load(f)


def _build_location_map(locations: List[Dict]) -> Dict[str, Dict]:
    return {loc['name']: loc for loc in locations}


class HostAgent:
    def __init__(self):
        self.locations = _load_locations()
        self.location_map = _build_location_map(self.locations)
        self.location_names = [loc['name'] for loc in self.locations]

    def decompose_task(self, user_prompt: str) -> Task:
        location_list = '\n'.join(f"- {name}" for name in self.location_names)

        prompt = f"""你是一个机器狗巡检调度系统。请将以下巡检任务拆解为机器狗的动作序列。

可用地点列表：
{location_list}

任务：{user_prompt}

规则：
1. 每到一个地点，必须先 run（导航前往），再 take_photo（拍照巡检）
2. 地点名称必须与上方列表完全一致
3. 只返回 JSON，不要其他内容

返回格式：
{{
  "sequence": [
    {{"action": "run", "location": "货物存放区A"}},
    {{"action": "take_photo", "location": "货物存放区A"}},
    {{"action": "run", "location": "办公区B"}},
    {{"action": "take_photo", "location": "办公区B"}}
  ]
}}"""

        response = call_qwen(prompt)

        try:
            start = response.find('{')
            end = response.rfind('}') + 1
            data = json.loads(response[start:end])
            sequence = data.get('sequence', [])
        except Exception:
            sequence = []

        nodes: List[TaskNode] = []
        for i, step in enumerate(sequence[:config.max_nodes]):
            action_str = step.get('action', 'run')
            location = step.get('location', '')
            coords = self.location_map.get(location, {})

            action_type = ActionType.RUN if action_str == 'run' else ActionType.TAKE_PHOTO

            label = f"前往{location}" if action_type == ActionType.RUN else f"拍照巡检{location}"
            # 线性序列：每个节点依赖前一个
            deps = [f"node_{i-1}"] if i > 0 else []

            nodes.append(TaskNode(
                id=f"node_{i}",
                description=label,
                action_type=action_type,
                location=location,
                x=coords.get('x'),
                y=coords.get('y'),
                z=coords.get('z'),
                status=NodeStatus.PENDING,
                dependencies=deps,
            ))

        task_id = str(uuid.uuid4())[:8]
        title = user_prompt[:50] + ('...' if len(user_prompt) > 50 else '')
        return Task(id=task_id, title=title, status=TaskStatus.RUNNING, dag=nodes)
