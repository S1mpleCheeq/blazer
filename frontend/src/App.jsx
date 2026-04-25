import React, { useState, useEffect, useRef } from 'react';
import axios from 'axios';
import TaskStack from './components/TaskStack';
import DAGView from './components/DAGView';
import RobotStatus from './components/RobotStatus';

const API_BASE = 'http://localhost:8000';

function App() {
  const [taskStack, setTaskStack] = useState([]);
  const [completedTasks, setCompletedTasks] = useState([]);
  const [dogs, setDogs] = useState([]);
  const [viewingTask, setViewingTask] = useState(null);
  const [autoFollow, setAutoFollow] = useState(true);
  const [prompt, setPrompt] = useState('');
  const [submitting, setSubmitting] = useState(false);
  const [errorMsg, setErrorMsg] = useState('');
  const taskCacheRef = useRef({});

  useEffect(() => {
    const ws = new WebSocket('ws://localhost:8000/ws/execution');

    ws.onmessage = (event) => {
      const update = JSON.parse(event.data);

      if (update.dogs) setDogs(update.dogs);

      if (update.task_stack !== undefined) {
        setTaskStack(update.task_stack);
        update.task_stack.forEach(t => { taskCacheRef.current[t.id] = t; });
      }

      if (update.completed_tasks !== undefined) {
        setCompletedTasks(update.completed_tasks);
        update.completed_tasks.forEach(t => { taskCacheRef.current[t.id] = t; });
      }

      if (update.task) {
        const incoming = update.task;
        taskCacheRef.current[incoming.id] = incoming;
        if (autoFollow) setViewingTask(incoming);
        else if (viewingTask?.id === incoming.id) setViewingTask(incoming);
      }
    };

    ws.onerror = () => console.error('[WS] 连接错误');

    axios.get(`${API_BASE}/api/task/stack`).then(res => {
      setTaskStack(res.data.task_stack || []);
      setCompletedTasks(res.data.completed_tasks || []);
    });

    axios.get(`${API_BASE}/api/robots`).then(res => {
      setDogs(res.data.dogs || []);
    });

    return () => ws.close();
  }, []);

  // autoFollow 变化时同步更新 task 视图
  useEffect(() => {
    if (autoFollow) {
      const active = taskStack[taskStack.length - 1];
      if (active) setViewingTask(taskCacheRef.current[active.id] || active);
    }
  }, [autoFollow, taskStack]);

  const handleSelectTask = (task) => {
    setAutoFollow(false);
    setViewingTask(taskCacheRef.current[task.id] || task);
  };

  const submitTask = async () => {
    if (!prompt.trim()) return;
    setSubmitting(true);
    setErrorMsg('');
    try {
      await axios.post(`${API_BASE}/api/task/submit`, { prompt });
      setPrompt('');
      setAutoFollow(true);
    } catch (err) {
      const msg = err.response?.data?.error || err.message;
      setErrorMsg(msg);
    } finally {
      setSubmitting(false);
    }
  };

  const handleKeyDown = (e) => {
    if (e.key === 'Enter' && (e.ctrlKey || e.metaKey)) submitTask();
  };

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'system-ui, sans-serif', background: '#f0f2f5' }}>
      {/* 左侧面板 */}
      <div style={{ width: '30%', background: '#fff', borderRight: '1px solid #e8e8e8', display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ padding: '16px 20px', borderBottom: '1px solid #e8e8e8' }}>
          <h2 style={{ margin: '0 0 12px', fontSize: 16, color: '#1a1a1a' }}>🐕 巡检任务调度</h2>
          <textarea
            value={prompt}
            onChange={e => setPrompt(e.target.value)}
            onKeyDown={handleKeyDown}
            placeholder={'输入巡检任务，例如：\n"巡检货物存放区A、B和办公区C"'}
            style={{
              width: '100%', height: 90, padding: '8px 10px', boxSizing: 'border-box',
              border: '1px solid #d9d9d9', borderRadius: 6, fontSize: 13,
              resize: 'vertical', fontFamily: 'inherit',
            }}
          />
          <button
            onClick={submitTask}
            disabled={submitting || !prompt.trim()}
            style={{
              width: '100%', marginTop: 8, padding: '9px 0',
              background: submitting ? '#6c757d' : '#1890ff',
              color: '#fff', border: 'none', borderRadius: 6,
              fontSize: 14, cursor: submitting ? 'not-allowed' : 'pointer',
            }}
          >
            {submitting ? '拆解中...' : '提交任务 (Ctrl+Enter)'}
          </button>
          {errorMsg && (
            <div style={{ marginTop: 8, fontSize: 12, color: '#dc3545', background: '#fff5f5', padding: '6px 10px', borderRadius: 4 }}>
              ⚠ {errorMsg}
            </div>
          )}
        </div>

        <div style={{ flex: 1, overflowY: 'auto' }}>
          <TaskStack
            tasks={taskStack}
            completedTasks={completedTasks}
            selectedId={viewingTask?.id}
            onSelect={handleSelectTask}
          />
          {!autoFollow && (
            <div style={{ padding: '0 16px 12px' }}>
              <button
                onClick={() => setAutoFollow(true)}
                style={{ width: '100%', padding: '6px', background: '#52c41a', color: '#fff', border: 'none', borderRadius: 4, fontSize: 12, cursor: 'pointer' }}
              >
                ↩ 恢复自动跟随
              </button>
            </div>
          )}
        </div>
      </div>

      {/* 右侧面板 */}
      <div style={{ flex: 1, display: 'flex', flexDirection: 'column', overflow: 'hidden' }}>
        <div style={{ flex: 1, padding: '16px 20px', overflow: 'hidden', background: '#fff', margin: '12px 12px 0', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,.08)' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: 10, marginBottom: 12 }}>
            <h2 style={{ margin: 0, fontSize: 16 }}>任务执行序列</h2>
            {viewingTask && (
              <span style={{ fontSize: 12, color: '#666', background: '#f0f0f0', padding: '2px 8px', borderRadius: 10 }}>
                {viewingTask.title}
              </span>
            )}
            {!autoFollow && (
              <span style={{ fontSize: 11, color: '#fa8c16' }}>（手动浏览）</span>
            )}
          </div>
          <DAGView task={viewingTask} />
        </div>

        <div style={{ background: '#fff', margin: '8px 12px 12px', borderRadius: 8, boxShadow: '0 1px 3px rgba(0,0,0,.08)' }}>
          <RobotStatus dogs={dogs} />
        </div>
      </div>
    </div>
  );
}

export default App;
