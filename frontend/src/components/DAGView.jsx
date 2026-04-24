import React, { useMemo } from 'react';
import ReactFlow, { Background, Controls, Handle, Position } from 'reactflow';
import 'reactflow/dist/style.css';

const NODE_WIDTH = 200;
const NODE_HEIGHT = 80;
const H_GAP = 100;
const V_GAP = 30;

// 固定高度的自定义节点
function TaskNodeComponent({ data }) {
  const { label, agent, result, status } = data;
  const bg = status === 'completed' ? '#4ade80' : status === 'running' ? '#fbbf24' : '#d1d5db';
  return (
    <div style={{
      width: NODE_WIDTH,
      height: NODE_HEIGHT,
      background: bg,
      borderRadius: 6,
      border: '1px solid #999',
      display: 'flex',
      flexDirection: 'column',
      justifyContent: 'center',
      padding: '0 10px',
      boxSizing: 'border-box',
      overflow: 'hidden'
    }}>
      <Handle type="target" position={Position.Left} style={{ background: '#555' }} />
      <div style={{ fontSize: 12, fontWeight: 'bold', lineHeight: 1.3, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>{label}</div>
      <div style={{ fontSize: 10, color: '#444', marginTop: 2 }}>{agent || '未分配'}</div>
      {result && (
        <div style={{ fontSize: 10, color: '#333', marginTop: 2, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          ✓ {result.substring(0, 40)}...
        </div>
      )}
      <Handle type="source" position={Position.Right} style={{ background: '#555' }} />
    </div>
  );
}

const nodeTypes = { taskNode: TaskNodeComponent };

function DAGView({ task }) {
  const { nodes, edges } = useMemo(() => {
    if (!task || !task.dag || task.dag.length === 0) return { nodes: [], edges: [] };

    // 计算层级
    const levels = {};
    const inDegree = {};
    const adjList = {};

    task.dag.forEach(node => {
      inDegree[node.id] = node.dependencies ? node.dependencies.length : 0;
      adjList[node.id] = [];
    });

    task.dag.forEach(node => {
      (node.dependencies || []).forEach(depId => {
        if (adjList[depId]) adjList[depId].push(node.id);
      });
    });

    const queue = task.dag.filter(n => inDegree[n.id] === 0).map(n => n.id);
    queue.forEach(id => { levels[id] = 0; });
    const bfsQueue = [...queue];
    while (bfsQueue.length > 0) {
      const cur = bfsQueue.shift();
      adjList[cur].forEach(next => {
        levels[next] = Math.max(levels[next] || 0, levels[cur] + 1);
        inDegree[next]--;
        if (inDegree[next] === 0) bfsQueue.push(next);
      });
    }

    // 按层分组
    const groups = {};
    task.dag.forEach(node => {
      const lv = levels[node.id] || 0;
      if (!groups[lv]) groups[lv] = [];
      groups[lv].push(node);
    });

    // 所有层中最多节点数
    const maxCount = Math.max(...Object.values(groups).map(g => g.length));
    const totalH = maxCount * NODE_HEIGHT + (maxCount - 1) * V_GAP;

    const nodes = task.dag.map(node => {
      const lv = levels[node.id] || 0;
      const groupNodes = groups[lv];
      const idx = groupNodes.indexOf(node);
      const groupH = groupNodes.length * NODE_HEIGHT + (groupNodes.length - 1) * V_GAP;
      // 垂直居中对齐
      const offsetY = (totalH - groupH) / 2;
      return {
        id: node.id,
        type: 'taskNode',
        position: {
          x: lv * (NODE_WIDTH + H_GAP),
          y: offsetY + idx * (NODE_HEIGHT + V_GAP)
        },
        data: {
          label: node.description,
          agent: node.agent_type,
          result: node.result,
          status: node.status
        }
      };
    });

    const edges = [];
    task.dag.forEach(node => {
      (node.dependencies || []).forEach(depId => {
        edges.push({
          id: `${depId}->${node.id}`,
          source: depId,
          target: node.id,
          type: 'smoothstep',
          animated: node.status === 'running'
        });
      });
    });

    return { nodes, edges };
  }, [task]);

  if (!task) return <div style={{ padding: 20, color: '#999' }}>暂无任务</div>;

  return (
    <div style={{ height: 'calc(100vh - 220px)', minHeight: 300, border: '1px solid #ccc', borderRadius: 4 }}>
      <ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView>
        <Background />
        <Controls />
      </ReactFlow>
    </div>
  );
}

export default DAGView;
