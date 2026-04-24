from pydantic import BaseModel
from typing import List, Optional
from enum import Enum

class Priority(str, Enum):
    HIGH = "HIGH"
    NORMAL = "NORMAL"

class NodeStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    COMPLETED = "completed"

class TaskStatus(str, Enum):
    RUNNING = "running"
    SUSPENDED = "suspended"
    COMPLETED = "completed"

class TaskNode(BaseModel):
    id: str
    description: str
    status: NodeStatus = NodeStatus.PENDING
    agent_type: Optional[str] = None
    result: Optional[str] = None
    dependencies: List[str] = []  # 依赖的节点ID列表

class Task(BaseModel):
    id: str
    title: str
    priority: Priority
    status: TaskStatus
    dag: List[TaskNode]
    current_node_index: int = 0
    completed_nodes: List[str] = []

class AgentDescription(BaseModel):
    name: str
    capabilities: str
    embedding: Optional[List[float]] = None
