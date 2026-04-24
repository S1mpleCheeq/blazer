# 多智能体调度系统

支持任务中断、优先级抢占和上下文恢复的多智能体任务调度系统。

## 核心功能

- 任务拆解与DAG生成
- 优先级抢占（HIGH > NORMAL）
- 任务挂起与断点恢复
- 语义路由（向量相似度匹配）
- 实时WebSocket通信
- 任务栈可视化

## 快速启动

### 后端

```bash
cd backend
pip install -r requirements.txt
cp .env.example .env  # 填入DASHSCOPE_API_KEY
uvicorn main:app --reload --port 8000
```

### 前端

```bash
cd frontend
npm install
npm run dev  # 访问 http://localhost:5173
```

## 演示场景

### 场景1：启动常规巡检（Task A）
```
请对变电站执行一次例行巡检：依次完成1号主变区、GIS区和控制楼巡检
```

### 场景2：注入突发任务（Task B - 会中断Task A）
```
突发告警：2号主变区检测到高温异常，请立即进行复核，优先级高于当前任务
```

### 场景3：观察恢复
Task B完成后，系统自动从断点恢复Task A（不是从头开始）

## 技术栈

**后端:** FastAPI + Qwen API + WebSocket
**前端:** React + ReactFlow + Vite

## API端点

- `POST /api/task/submit` - 提交任务
- `GET /api/task/stack` - 获取任务栈
- `GET /api/task/{task_id}/status` - 获取任务状态
- `WS /ws/execution` - WebSocket实时更新
