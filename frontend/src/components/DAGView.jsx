import React from 'react';

const ACTION_ICON = { run: '🚶', take_photo: '📷', return_to_charge: '🔋' };
const ACTION_LABEL = { run: '前往', take_photo: '拍照', return_to_charge: '充电' };

function StepNode({ node, index }) {
  const { action_type, location, status, result } = node;
  const bg = status === 'completed' ? '#d4edda'
           : status === 'running'   ? '#fff3cd'
           : '#f8f9fa';
  const border = status === 'completed' ? '#28a745'
               : status === 'running'   ? '#ffc107'
               : '#dee2e6';
  const icon = ACTION_ICON[action_type] || '▶';
  const label = ACTION_LABEL[action_type] || action_type;

  return (
    <div style={{ display: 'flex', alignItems: 'flex-start', gap: 8 }}>
      {/* 步骤序号 + 竖线 */}
      <div style={{ display: 'flex', flexDirection: 'column', alignItems: 'center', flexShrink: 0 }}>
        <div style={{
          width: 28, height: 28, borderRadius: '50%',
          background: border, color: status === 'pending' ? '#6c757d' : '#fff',
          display: 'flex', alignItems: 'center', justifyContent: 'center',
          fontSize: 12, fontWeight: 'bold',
        }}>
          {status === 'completed' ? '✓' : status === 'running' ? '●' : index + 1}
        </div>
        <div style={{ width: 2, flex: 1, background: '#dee2e6', minHeight: 16 }} />
      </div>

      {/* 内容卡片 */}
      <div style={{
        flex: 1, marginBottom: 8, padding: '8px 12px',
        background: bg, border: `1px solid ${border}`,
        borderRadius: 6, fontSize: 13,
      }}>
        <div style={{ fontWeight: 'bold' }}>
          {icon} {label}({location || node.description})
        </div>
        {node.x != null && (
          <div style={{ fontSize: 11, color: '#6c757d', marginTop: 2 }}>
            坐标：({node.x.toFixed(2)}, {node.y.toFixed(2)}, {node.z.toFixed(2)})
          </div>
        )}
        {result && (
          <div style={{ fontSize: 11, color: '#155724', marginTop: 4 }}>✓ {result}</div>
        )}
        {status === 'running' && !result && (
          <div style={{ fontSize: 11, color: '#856404', marginTop: 4 }}>执行中...</div>
        )}
      </div>
    </div>
  );
}

function DAGView({ task }) {
  if (!task) {
    return (
      <div style={{ padding: 30, color: '#999', textAlign: 'center' }}>
        暂无任务，请在左侧输入巡检指令
      </div>
    );
  }

  const completed = task.dag.filter(n => n.status === 'completed').length;
  const total = task.dag.length;
  const progress = total > 0 ? Math.round(completed / total * 100) : 0;

  return (
    <div style={{ height: 'calc(100vh - 200px)', overflowY: 'auto', padding: '0 4px' }}>
      {/* 进度条 */}
      <div style={{ marginBottom: 16 }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', fontSize: 12, color: '#666', marginBottom: 4 }}>
          <span>执行进度</span>
          <span>{completed}/{total} 步</span>
        </div>
        <div style={{ height: 6, background: '#e9ecef', borderRadius: 3, overflow: 'hidden' }}>
          <div style={{
            height: '100%', width: `${progress}%`,
            background: task.status === 'completed' ? '#28a745' : '#007bff',
            borderRadius: 3, transition: 'width 0.4s',
          }} />
        </div>
      </div>

      {/* 步骤列表 */}
      {task.dag.map((node, i) => (
        <StepNode key={node.id} node={node} index={i} />
      ))}

      {task.dag.length === 0 && (
        <div style={{ color: '#999', fontSize: 13 }}>任务序列为空</div>
      )}
    </div>
  );
}

export default DAGView;
