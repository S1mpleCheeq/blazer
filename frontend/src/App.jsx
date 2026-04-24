import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import TaskStack from './components/TaskStack';
import DAGView from './components/DAGView';
import AgentStatus from './components/AgentStatus';

const API_BASE = 'http://localhost:8000';

function App() {
  const [taskStack, setTaskStack] = useState([]);        // 活跃任务栈
  const [completedTasks, setCompletedTasks] = useState([]); // 已完成任务历史
  const [viewingTask, setViewingTask] = useState(null);
  const [autoFollow, setAutoFollow] = useState(true);
  const [prompt, setPrompt] = useState('');
  const [agentStatus, setAgentStatus] = useState({
    Aerial: null, Ground: null, Indoor: null,
    Thermal: null, Electrical: null, Oil: null,
    Emergency: null, Maintenance: null, Diagnosis: null, Report: null
  });
  const taskCacheRef = useRef({});

  const updateAgentStatus = (task) => {
    const newStatus = {
      Aerial: null, Ground: null, Indoor: null,
      Thermal: null, Electrical: null, Oil: null,
      Emergency: null, Maintenance: null, Diagnosis: null, Report: null
    };
    if (task?.dag) {
      task.dag.forEach(node => {
        if (node.status === 'running' && node.agent_type) {
          newStatus[node.agent_type] = node.description;
        }
      });
    }
    setAgentStatus(newStatus);
  };

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/execution');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);
      console.log('[WS]', update.type);

      // 更新任务缓存
      if (update.task) {
        taskCacheRef.current[update.task.id] = update.task;
      }

      // 更新任务栈
      if (update.task_stack !== undefined) {
        setTaskStack(update.task_stack);
        update.task_stack.forEach(t => { taskCacheRef.current[t.id] = t; });
      }

      // 任务完成：移入历史
      if (update.type === 'task_completed' && update.task) {
        const done = update.task;
        taskCacheRef.current[done.id] = done;
        setCompletedTasks(prev => {
          const exists = prev.find(t => t.id === done.id);
          return exists ? prev.map(t => t.id === done.id ? done : t) : [done, ...prev];
        });
        if (autoFollow) {
          setViewingTask(done);
          updateAgentStatus(done);
        }
        return;
      }

      // 普通task更新
      if (update.task) {
        const incoming = update.task;
        setViewingTask(prev => {
          if (autoFollow) { updateAgentStatus(incoming); return incoming; }
          if (prev?.id === incoming.id) { updateAgentStatus(incoming); return incoming; }
          return prev;
        });
      }

      // 任务恢复
      if (update.type === 'task_resumed' && update.task) {
        taskCacheRef.current[update.task.id] = update.task;
        if (autoFollow) { setViewingTask(update.task); updateAgentStatus(update.task); }
      }
    };

    ws.onerror = (e) => console.error('[WS] 错误:', e);

    // 初始化获取任务栈
    axios.get(`${API_BASE}/api/task/stack`).then(res => {
      setTaskStack(res.data.task_stack);
    });

    return () => ws.close();
  }, [autoFollow]);

  const handleSelectTask = (task) => {
    setAutoFollow(false);
    // 从缓存获取最新状态
    const latest = taskCacheRef.current[task.id] || task;
    setViewingTask(latest);
    updateAgentStatus(latest);
  };

  const submitTask = async () => {
    if (!prompt.trim()) return;
    try {
      const res = await axios.post(`${API_BASE}/api/task/submit`, { prompt });
      setPrompt('');
      setAutoFollow(true);  // 提交新任务后自动跟随
    } catch (error) {
      console.error('提交失败:', error);
    }
  };

  const agents = Object.entries(agentStatus).map(([name, task]) => ({ name, current_task: task }));

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'Arial, sans-serif' }}>
      {/* 左侧面板 */}
      <div style={{ width: '30%', borderRight: '1px solid #ccc', overflow: 'auto', display: 'flex', flexDirection: 'column' }}>
        <div style={{ padding: '20px', borderBottom: '1px solid #eee' }}>
          <h2 style={{ margin: '0 0 10px 0' }}>任务输入</h2>
          <textarea
            value={prompt}
            onChange={(e) => setPrompt(e.target.value)}
            placeholder="输入任务描述..."
            style={{ width: '100%', height: '100px', marginBottom: '10px', padding: '10px', boxSizing: 'border-box', resize: 'vertical' }}
          />
          <button
            onClick={submitTask}
            style={{ width: '100%', padding: '10px', backgroundColor: '#007bff', color: 'white', border: 'none', borderRadius: '5px', cursor: 'pointer' }}
          >
            提交任务
          </button>
        </div>
        <div style={{ flex: 1, overflow: 'auto' }}>
          <TaskStack
            tasks={taskStack}
            completedTasks={completedTasks}
            selectedId={viewingTask?.id}
            onSelect={handleSelectTask}
          />
          {!autoFollow && (
            <div style={{ padding: '0 20px 10px' }}>
              <button
                onClick={() => setAutoFollow(true)}
                style={{ width: '100%', padding: '6px', backgroundColor: '#28a745', color: 'white', border: 'none', borderRadius: '4px', cursor: 'pointer', fontSize: 12 }}
              >
                🔄 恢复自动跟随
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 右侧面板 */}
      <div style={{ width: '70%', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ flex: 1, padding: '20px', overflow: 'hidden' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 10 }}>
            <h2 style={{ margin: 0 }}>DAG执行视图</h2>
            {viewingTask && (
              <span style={{ fontSize: 12, color: '#666', backgroundColor: '#f0f0f0', padding: '2px 8px', borderRadius: 10 }}>
                {viewingTask.title}
              </span>
            )}
            {!autoFollow && (
              <span style={{ fontSize: 11, color: '#e67e22' }}>（手动模式）</span>
            )}
          </div>
          <DAGView task={viewingTask} />
        </div>
        <AgentStatus agents={agents} />
      </div>
    </div>
  );
}

export default App;
