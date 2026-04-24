import asyncio
from services.llm_service import call_qwen
from models import TaskNode

AGENTS = {
    # 巡检执行类
    "Aerial":      "你是无人机巡检Agent，负责对变电站进行空中热成像扫描、高空设备外观检查、输电线路巡视",
    "Ground":      "你是机器狗地面巡检Agent，负责对变电站设备进行地面近距离检查、声音异常检测、外观复核",
    "Indoor":      "你是室内巡检Agent，负责控制楼、继电保护室、通信机房等室内设备的运行状态检查",
    # 专项检测类
    "Thermal":     "你是热成像检测Agent，负责对变压器、开关柜、电缆接头等设备进行红外测温，识别过热异常点",
    "Electrical":  "你是电气检测Agent，负责对电气设备进行绝缘电阻、接地电阻、电流电压等参数的检测和记录",
    "Oil":         "你是油务检测Agent，负责对主变压器、油浸式互感器进行油位检查、油色谱分析和渗漏油检测",
    # 应急处置类
    "Emergency":   "你是应急响应Agent，负责处理突发告警、设备异常、火情、SF6泄漏等紧急情况的第一响应",
    "Maintenance": "你是抢修处置Agent，负责根据故障诊断结果制定抢修方案、协调抢修资源、指导现场处置",
    # 数据分析类
    "Diagnosis":   "你是故障诊断Agent，负责对采集到的巡检数据进行综合分析，定位故障原因并给出处置建议",
    "Report":      "你是报告汇总Agent，负责整合所有巡检结果，生成标准化巡检报告并提交缺陷工单",
}

async def execute_node_async(agent_name: str, task_node: TaskNode) -> str:
    """异步执行节点，避免阻塞事件循环"""
    agent_prompt = AGENTS.get(agent_name, "你是通用巡检Agent")
    full_prompt = f"{agent_prompt}\n\n任务: {task_node.description}\n\n请执行该任务并返回简短结果（100字以内）。"
    print(f"[LLM] 调用中: {agent_name} - {task_node.description[:30]}...")
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(None, lambda: call_qwen(full_prompt))
    print(f"[LLM] 返回: {result[:50]}...")
    return result
