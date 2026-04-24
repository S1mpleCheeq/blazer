import asyncio
from models import TaskNode, ActionType

# 3只狗，对应3个充电桩
DOGS = {
    "Dog1": {"charging_station": "充电桩A"},
    "Dog2": {"charging_station": "充电桩B"},
    "Dog3": {"charging_station": "充电桩C"},
}


async def execute_node_async(dog_name: str, task_node: TaskNode) -> str:
    if task_node.action_type == ActionType.RUN:
        await asyncio.sleep(2)
        coords = ""
        if task_node.x is not None:
            coords = f" ({task_node.x:.1f}, {task_node.y:.1f}, {task_node.z:.1f})"
        return f"已导航至 {task_node.location}{coords}"

    elif task_node.action_type == ActionType.TAKE_PHOTO:
        await asyncio.sleep(1)
        return f"已完成 {task_node.location} 拍照存档"

    elif task_node.action_type == ActionType.RETURN_TO_CHARGE:
        await asyncio.sleep(5)
        station = DOGS.get(dog_name, {}).get("charging_station", "充电桩")
        return f"已返回{station}，充电完成"

    return "未知动作"


async def execute_return_to_charge(dog_name: str, charging_seconds: int = 5) -> str:
    await asyncio.sleep(charging_seconds)
    station = DOGS.get(dog_name, {}).get("charging_station", "充电桩")
    return f"已返回{station}，充电完成"
