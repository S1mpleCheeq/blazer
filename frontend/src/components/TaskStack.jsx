import React from 'react';

function TaskCard({ task, isSelected, onSelect }) {
  const completedCount = task.dag ? task.dag.filter(n => n.status === 'completed').length : 0;
  const totalCount = task.dag ? task.dag.length : 0;
  const progress = totalCount > 0 ? Math.round(completedCount / totalCount * 100) : 0;

  return (
    <div
      onClick={() => onSelect(task)}
      style={{
        margin: '8px 0',
        padding: '12px',
        backgroundColor: isSelected ? '#e8f4fd' :
                         task.status === 'running' ? '#fff3cd' :
                         task.status === 'suspended' ? '#f0f0f0' : '#f6fff6',
        border: `2px solid ${isSelected ? '#007bff' :
                              task.status === 'running' ? '#ffc107' :
                              task.status === 'suspended' ? '#aaa' : '#4ade80'}`,
        borderRadius: '6px',
        cursor: 'pointer',
      }}
    >
      <div style={{ display: 'flex', justifyContent: 'space-between', marginBottom: '6px' }}>
        <span style={{ fontWeight: 'bold', fontSize: 13 }}>
          {task.status === 'running' ? '🔴 执行中' :
           task.status === 'suspended' ? '⏸️ 已挂起' : '✅ 已完成'}
        </span>
        <span style={{
          padding: '2px 8px',
          backgroundColor: task.priority === 'HIGH' ? '#dc3545' : '#6c757d',
          color: 'white', borderRadius: '3px', fontSize: '11px'
        }}>
          {task.priority}
        </span>
      </div>
      <div style={{ fontSize: 12, marginBottom: '6px', color: '#333' }}>{task.title}</div>
      <div style={{ fontSize: 11, color: '#666' }}>
        进度: {completedCount}/{totalCount} 节点
        {task.status === 'suspended' && ` （断点 ${progress}%）`}
      </div>
      <div style={{ marginTop: 6, height: 4, backgroundColor: '#ddd', borderRadius: 2 }}>
        <div style={{
          height: '100%', width: `${progress}%`,
          backgroundColor: task.status === 'running' ? '#ffc107' :
                           task.status === 'suspended' ? '#aaa' : '#4ade80',
          borderRadius: 2, transition: 'width 0.3s'
        }} />
      </div>
    </div>
  );
}

function TaskStack({ tasks, completedTasks = [], selectedId, onSelect }) {
  const activeTasks = [...tasks].reverse();

  return (
    <div style={{ padding: '20px', backgroundColor: '#f5f5f5' }}>
      <h3 style={{ margin: '0 0 8px 0' }}>活跃任务</h3>
      {activeTasks.length === 0 && <p style={{ color: '#999', fontSize: 13 }}>暂无活跃任务</p>}
      {activeTasks.map(task => (
        <TaskCard key={task.id} task={task} isSelected={task.id === selectedId} onSelect={onSelect} />
      ))}

      {completedTasks.length > 0 && (
        <>
          <h3 style={{ margin: '16px 0 8px 0', color: '#666' }}>已完成</h3>
          {completedTasks.map(task => (
            <TaskCard key={task.id} task={task} isSelected={task.id === selectedId} onSelect={onSelect} />
          ))}
        </>
      )}
    </div>
  );
}

export default TaskStack;
