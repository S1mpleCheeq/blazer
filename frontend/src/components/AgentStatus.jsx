import React from 'react';

function AgentStatus({ agents }) {
  return (
    <div style={{ padding: '12px 20px', borderTop: '1px solid #eee' }}>
      <h3 style={{ margin: '0 0 10px 0' }}>Agent状态</h3>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {agents.map(agent => (
          <div key={agent.name} style={{
            padding: '8px 12px',
            border: `2px solid ${agent.current_task ? '#fbbf24' : '#ddd'}`,
            borderRadius: 6,
            backgroundColor: agent.current_task ? '#fffbeb' : '#fafafa',
            minWidth: 120
          }}>
            <div style={{ fontWeight: 'bold', fontSize: 13 }}>{agent.name}</div>
            <div style={{ fontSize: 11, color: agent.current_task ? '#b45309' : '#999', marginTop: 2 }}>
              {agent.current_task
                ? `⚡ ${agent.current_task.substring(0, 20)}...`
                : '空闲'}
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}

export default AgentStatus;
