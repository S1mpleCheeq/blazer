from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import List, Optional
import asyncio
import json

from agents.host_agent import HostAgent
from agents.memory_agent import MemoryAgent
from agents.router import SemanticRouter
from agents.execution_agents import execute_node_async
from models import Task, AgentDescription, NodeStatus, TaskStatus

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 全局状态
host_agent = HostAgent()
memory_agent = MemoryAgent()
task_stack: List[Task] = []
active_connections: List[WebSocket] = []
# task_id -> asyncio.Event，用于中断任务
cancel_events: dict = {}

# 初始化Agent描述（与execution_agents.py保持一致）
agents = [
    AgentDescription(name="Aerial",      capabilities="无人机，空中巡检，热成像，高空检测，输电线路，外观检查"),
    AgentDescription(name="Ground",      capabilities="机器狗，地面巡检，近距离检查，设备复核，声音检测"),
    AgentDescription(name="Indoor",      capabilities="室内巡检，控制楼，继电保护，通信机房，室内设备"),
    AgentDescription(name="Thermal",     capabilities="红外测温，热成像，过热检测，变压器，开关柜，电缆接头"),
    AgentDescription(name="Electrical",  capabilities="电气检测，绝缘电阻，接地电阻，电流电压，参数记录"),
    AgentDescription(name="Oil",         capabilities="油务检测，变压器油位，油色谱，渗漏油，油浸设备"),
    AgentDescription(name="Emergency",   capabilities="应急响应，突发告警，异常处理，高温，SF6泄漏，火情"),
    AgentDescription(name="Maintenance", capabilities="抢修处置，故障维修，抢修方案，现场处置，资源协调"),
    AgentDescription(name="Diagnosis",   capabilities="故障诊断，数据分析，缺陷定位，原因分析，处置建议"),
    AgentDescription(name="Report",      capabilities="报告汇总，巡检报告，缺陷工单，结果整合，数据归档"),
]
router = SemanticRouter(agents)

class TaskSubmitRequest(BaseModel):
    prompt: str

async def broadcast_update(message: dict):
    """广播更新到所有WebSocket连接"""
    disconnected = []
    for connection in active_connections:
        try:
            await connection.send_json(message)
        except:
            disconnected.append(connection)
    for c in disconnected:
        active_connections.remove(c)

async def broadcast_task(task: Task):
    """广播完整任务状态和任务栈"""
    await broadcast_update({
        "type": "task_update",
        "task": task.dict(),
        "task_stack": [t.dict() for t in task_stack]
    })

async def execute_node_with_broadcast(task: Task, node, agent_name: str, agent_locks: dict, cancel_event: asyncio.Event):
    """执行单个节点，支持取消"""
    if agent_name not in agent_locks:
        agent_locks[agent_name] = asyncio.Lock()

    async with agent_locks[agent_name]:
        # 执行前检查是否已被取消
        if cancel_event.is_set():
            print(f"[取消] 节点 {node.id} 跳过（任务已挂起）")
            node.status = NodeStatus.PENDING
            return node.id

        result = await execute_node_async(agent_name, node)
        print(f"[完成] 节点 {node.id}")
        node.status = NodeStatus.COMPLETED
        node.result = result
        memory_agent.update_node_status(task.id, node.id, result)
        await broadcast_task(task)
    return node.id

async def execute_task(task: Task):
    """执行任务（支持依赖关系，同层并发，同agent串行，支持中断）"""
    print(f"[执行] 开始执行任务 {task.id}, 共 {len(task.dag)} 个节点")

    # 注册取消事件
    cancel_event = asyncio.Event()
    cancel_events[task.id] = cancel_event

    # 从断点恢复：已完成的节点加入completed集合
    completed = set(node.id for node in task.dag if node.status == NodeStatus.COMPLETED)
    agent_locks = {}

    while len(completed) < len(task.dag):
        # 检查是否被中断
        if cancel_event.is_set():
            print(f"[中断] 任务 {task.id} 已挂起，停止执行")
            break

        ready_nodes = [
            (i, node) for i, node in enumerate(task.dag)
            if node.id not in completed
            and node.status != NodeStatus.RUNNING
            and all(dep in completed for dep in node.dependencies)
        ]

        if not ready_nodes:
            print(f"[警告] 无可执行节点，可能存在循环依赖")
            break

        # 路由所有ready节点
        for i, node in ready_nodes:
            node.status = NodeStatus.RUNNING
            task.current_node_index = i
            agent_name = router.route_task_node(node)
            node.agent_type = agent_name
            print(f"[路由] 节点 {node.id} → {agent_name}")

        await broadcast_task(task)

        # 并发执行
        results = await asyncio.gather(*[
            execute_node_with_broadcast(task, node, node.agent_type, agent_locks, cancel_event)
            for _, node in ready_nodes
        ])
        completed.update(results)

    # 只有未被中断时才标记完成
    if not cancel_event.is_set():
        task.status = TaskStatus.COMPLETED
        print(f"[完成] 任务 {task.id} 全部执行完成")
        await broadcast_task(task)

    cancel_events.pop(task.id, None)

@app.post("/api/task/submit")
async def submit_task(request: TaskSubmitRequest):
    """提交任务"""
    new_task = host_agent.decompose_task(request.prompt)
    memory_agent.save_task(new_task)

    if task_stack and task_stack[-1].status == TaskStatus.RUNNING:
        current_task = task_stack[-1]
        if host_agent.should_preempt(new_task, current_task):
            # 触发取消事件，中断正在执行的任务
            if current_task.id in cancel_events:
                cancel_events[current_task.id].set()
                print(f"[中断] 发送中断信号给任务 {current_task.id}")
            memory_agent.suspend_task(current_task.id)
            current_task.status = TaskStatus.SUSPENDED
            # 将running节点重置为pending（断点保留已完成的）
            for node in current_task.dag:
                if node.status == NodeStatus.RUNNING:
                    node.status = NodeStatus.PENDING

    task_stack.append(new_task)
    await broadcast_update({
        "type": "task_started",
        "task_id": new_task.id,
        "task_stack": [t.dict() for t in task_stack],
        "task": new_task.dict()
    })

    asyncio.create_task(execute_task_with_resume(new_task))
    return {"task_id": new_task.id, "status": "started"}

async def finish_task(task: Task):
    """任务完成后的收尾：移出栈、广播、恢复下一个挂起任务"""
    print(f"[收尾] 开始处理任务 {task.id}，当前栈: {[t.id for t in task_stack]}")

    if task in task_stack:
        task_stack.remove(task)
        print(f"[收尾] 任务 {task.id} 移出栈，剩余: {[t.id for t in task_stack]}")

    await broadcast_update({
        "type": "task_completed",
        "task_stack": [t.dict() for t in task_stack],
        "task": task.dict()
    })

    # 恢复栈顶的挂起任务
    if task_stack:
        suspended_task = task_stack[-1]
        print(f"[收尾] 栈顶任务 {suspended_task.id} 状态: {suspended_task.status}")
        if suspended_task.status == TaskStatus.SUSPENDED:
            memory_agent.resume_task(suspended_task.id)
            print(f"[恢复] 任务 {suspended_task.id} 状态改为: {suspended_task.status}")
            await broadcast_update({
                "type": "task_resumed",
                "task_id": suspended_task.id,
                "task_stack": [t.dict() for t in task_stack],
                "task": suspended_task.dict()
            })
            await execute_task_with_resume(suspended_task)
    else:
        print(f"[收尾] 任务栈已空")

async def execute_task_with_resume(task: Task):
    """执行任务入口"""
    await execute_task(task)

    # 被中断挂起的任务不走收尾流程，由紧急任务完成后负责恢复
    if task.status == TaskStatus.SUSPENDED:
        print(f"[跳过收尾] 任务 {task.id} 被挂起，等待恢复")
        return

    await finish_task(task)

@app.get("/api/task/stack")
async def get_task_stack():
    return {"task_stack": [t.dict() for t in task_stack]}

@app.get("/api/task/{task_id}/status")
async def get_task_status(task_id: str):
    task = memory_agent.get_task(task_id)
    if not task:
        return {"error": "Task not found"}
    return task.dict()

@app.websocket("/ws/execution")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    active_connections.append(websocket)
    try:
        # 等一个tick再推送，确保客户端已就绪
        await asyncio.sleep(0.1)
        await websocket.send_json({
            "type": "task_stack_update",
            "task_stack": [t.dict() for t in task_stack]
        })
        while True:
            await websocket.receive_text()
    except (WebSocketDisconnect, Exception):
        if websocket in active_connections:
            active_connections.remove(websocket)
