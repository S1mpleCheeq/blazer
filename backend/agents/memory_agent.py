from typing import Dict, Optional
from models import Task, TaskStatus, NodeStatus

class MemoryAgent:
    def __init__(self):
        self.task_states: Dict[str, Task] = {}

    def save_task(self, task: Task):
        """保存任务状态"""
        self.task_states[task.id] = task

    def suspend_task(self, task_id: str):
        """挂起任务"""
        if task_id in self.task_states:
            self.task_states[task_id].status = TaskStatus.SUSPENDED

    def resume_task(self, task_id: str) -> Optional[dict]:
        """恢复任务，返回断点信息"""
        if task_id not in self.task_states:
            return None
        task = self.task_states[task_id]
        task.status = TaskStatus.RUNNING
        return {
            "current_node_index": task.current_node_index,
            "completed_nodes": task.completed_nodes,
            "remaining_nodes": len(task.dag) - task.current_node_index
        }

    def get_task(self, task_id: str) -> Optional[Task]:
        """获取任务"""
        return self.task_states.get(task_id)

    def update_node_status(self, task_id: str, node_id: str, result: str):
        """更新节点状态"""
        if task_id in self.task_states:
            task = self.task_states[task_id]
            for node in task.dag:
                if node.id == node_id:
                    node.result = result
                    node.status = NodeStatus.COMPLETED
                    if node_id not in task.completed_nodes:
                        task.completed_nodes.append(node_id)
