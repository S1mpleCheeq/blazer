import asyncio
import json
import os
from typing import List

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agents.host_agent import HostAgent
from agents.router import DogRouter
from agents.execution_agents import execute_node_async, execute_return_to_charge
from models import Task, TaskNode, TaskStatus, NodeStatus, ActionType, RobotDog, DogStatus
from config_loader import config

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ── 全局状态 ──────────────────────────────────────────────
host_agent = HostAgent()
dog_router = DogRouter()

# 3只机器狗
dogs: List[RobotDog] = [
    RobotDog(id="dog1", name="Dog1", charging_station="充电桩A"),
    RobotDog(id="dog2", name="Dog2", charging_station="充电桩B"),
    RobotDog(id="dog3", name="Dog3", charging_station="充电桩C"),
]

task_stack: List[Task] = []
completed_tasks: List[Task] = []
active_connections: List[WebSocket] = []


def get_dog(name: str) -> RobotDog:
    return next(d for d in dogs if d.name == name)


# ── WebSocket 广播 ────────────────────────────────────────
async def broadcast(message: dict):
    disconnected = []
    for ws in active_connections:
        try:
            await ws.send_json(message)
        except Exception:
            disconnected.append(ws)
    for ws in disconnected:
        active_connections.remove(ws)


async def broadcast_state(task: Task = None):
    msg = {
        "type": "state_update",
        "task_stack": [t.dict() for t in task_stack],
        "completed_tasks": [t.dict() for t in completed_tasks],
        "dogs": [d.dict() for d in dogs],
    }
    if task:
        msg["task"] = task.dict()
    await broadcast(msg)


# ── 任务执行 ──────────────────────────────────────────────
async def execute_task(task: Task, dog: RobotDog):
    dog.status = DogStatus.WORKING
    dog.current_task_id = task.id
    await broadcast_state(task)

    completed = set(n.id for n in task.dag if n.status == NodeStatus.COMPLETED)

    while len(completed) < len(task.dag):
        # 找到下一个可执行节点（线性序列，依赖都满足）
        ready = [
            n for n in task.dag
            if n.id not in completed
            and n.status == NodeStatus.PENDING
            and all(dep in completed for dep in n.dependencies)
        ]
        if not ready:
            break

        node = ready[0]

        # 电量检查：不足则先回充电桩
        drain = config.drain_run if node.action_type == ActionType.RUN else config.drain_photo
        if dog.battery - drain < config.battery_threshold:
            await _recharge(task, dog)

        # 执行节点
        node.status = NodeStatus.RUNNING
        node.agent_type = dog.name
        dog.current_location = node.location
        await broadcast_state(task)

        result = await execute_node_async(dog.name, node)

        node.status = NodeStatus.COMPLETED
        node.result = result
        dog.battery = max(0.0, dog.battery - drain)
        completed.add(node.id)
        task.completed_nodes = list(completed)
        await broadcast_state(task)

    # 完成
    task.status = TaskStatus.COMPLETED
    if task in task_stack:
        task_stack.remove(task)
    completed_tasks.insert(0, task)

    dog.status = DogStatus.IDLE
    dog.current_location = None
    dog.current_task_id = None
    await broadcast_state(task)


async def _recharge(task: Task, dog: RobotDog):
    """插入充电节点：回桩、等待充电、恢复满电"""
    charge_node = TaskNode(
        id=f"charge_{len(task.dag)}",
        description=f"🔋 电量不足({dog.battery:.0f}%)，返回{dog.charging_station}充电",
        action_type=ActionType.RETURN_TO_CHARGE,
        location=dog.charging_station,
        status=NodeStatus.RUNNING,
        agent_type=dog.name,
    )
    task.dag.append(charge_node)
    dog.status = DogStatus.CHARGING
    dog.current_location = dog.charging_station
    await broadcast_state(task)

    await execute_return_to_charge(dog.name, config.charging_seconds)

    charge_node.status = NodeStatus.COMPLETED
    charge_node.result = f"充电完成，电量恢复至100%"
    dog.battery = 100.0
    dog.status = DogStatus.WORKING
    await broadcast_state(task)


# ── API ───────────────────────────────────────────────────
class TaskSubmitRequest(BaseModel):
    prompt: str


@app.post("/api/task/submit")
async def submit_task(request: TaskSubmitRequest):
    task = host_agent.decompose_task(request.prompt)

    dog = dog_router.assign_dog(dogs)
    if dog is None:
        return {"error": "所有机器狗均忙碌，请稍后再试", "status": "busy"}

    task_stack.append(task)
    await broadcast_state(task)

    asyncio.create_task(execute_task(task, dog))

    sequence = [
        {"step": i + 1, "action": n.action_type, "location": n.location,
         "description": n.description, "result": n.result,
         "x": n.x, "y": n.y, "z": n.z}
        for i, n in enumerate(task.dag)
    ]
    return {"task_id": task.id, "robot": dog.name, "status": "started", "sequence": sequence}


@app.get("/api/task/stack")
async def get_task_stack():
    return {
        "task_stack": [t.dict() for t in task_stack],
        "completed_tasks": [t.dict() for t in completed_tasks],
    }


@app.get("/api/task/{task_id}/sequence")
async def get_task_sequence(task_id: str):
    """输出带坐标的任务序列 JSON，供机器狗平台消费"""
    all_tasks = task_stack + completed_tasks
    task = next((t for t in all_tasks if t.id == task_id), None)
    if not task:
        return {"error": "Task not found"}

    dog_name = task.dag[0].agent_type if task.dag else None
    sequence = [
        {"step": i + 1, "action": n.action_type, "location": n.location,
         "description": n.description, "result": n.result,
         "x": n.x, "y": n.y, "z": n.z, "status": n.status}
        for i, n in enumerate(task.dag)
        if n.action_type != ActionType.RETURN_TO_CHARGE
    ]
    return {"task_id": task_id, "robot": dog_name, "sequence": sequence}


@app.get("/api/robots")
async def get_robots():
    return {"dogs": [d.dict() for d in dogs]}


@app.get("/api/locations")
async def get_locations():
    path = os.path.join(os.path.dirname(__file__), '..', 'map_data', '标注.json')
    with open(path, 'r', encoding='utf-8') as f:
        return {"locations": json.load(f)}


@app.websocket("/ws/execution")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        await asyncio.sleep(0.1)
        await websocket.send_json({
            "type": "state_update",
            "task_stack": [t.dict() for t in task_stack],
            "completed_tasks": [t.dict() for t in completed_tasks],
            "dogs": [d.dict() for d in dogs],
        })
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        if websocket in active_connections:
            active_connections.remove(websocket)
