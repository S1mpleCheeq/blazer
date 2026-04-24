from pydantic import BaseModel
from typing import List, Optional
from enum import Enum


class ActionType(str, Enum):
    RUN = "run"
    TAKE_PHOTO = "take_photo"
    RETURN_TO_CHARGE = "return_to_charge"


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
    action_type: ActionType = ActionType.RUN
    location: Optional[str] = None
    x: Optional[float] = None
    y: Optional[float] = None
    z: Optional[float] = None
    status: NodeStatus = NodeStatus.PENDING
    agent_type: Optional[str] = None   # 分配的机器狗名称
    result: Optional[str] = None
    dependencies: List[str] = []


class Task(BaseModel):
    id: str
    title: str
    status: TaskStatus
    dag: List[TaskNode]
    current_node_index: int = 0
    completed_nodes: List[str] = []


class DogStatus(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    CHARGING = "charging"


class RobotDog(BaseModel):
    id: str
    name: str
    battery: float = 100.0
    status: DogStatus = DogStatus.IDLE
    charging_station: str
    current_location: Optional[str] = None
    current_task_id: Optional[str] = None


class AgentDescription(BaseModel):
    name: str
    capabilities: str
    embedding: Optional[List[float]] = None