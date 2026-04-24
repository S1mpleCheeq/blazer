import React from 'react';

const STATUS_LABEL = { idle: '空闲', working: '执行中', charging: '充电中' };
const STATUS_COLOR = { idle: '#6c757d', working: '#007bff', charging: '#fd7e14' };

function BatteryBar({ value }) {
  const color = value > 50 ? '#28a745' : value > 20 ? '#ffc107' : '#dc3545';
  return (
    <div style={{ display: 'flex', alignItems: 'center', gap: 6, marginTop: 4 }}>
      <div style={{ flex: 1, height: 8, background: '#e9ecef', borderRadius: 4, overflow: 'hidden' }}>
        <div style={{ width: `${value}%`, height: '100%', background: color, borderRadius: 4, transition: 'width 0.5s, background 0.5s' }} />
      </div>
      <span style={{ fontSize: 11, color, fontWeight: 'bold', minWidth: 32 }}>{value.toFixed(0)}%</span>
    </div>
  );
}

function RobotStatus({ dogs }) {
  return (
    <div style={{ padding: '12px 20px', borderTop: '1px solid #eee' }}>
      <h3 style={{ margin: '0 0 10px 0', fontSize: 14 }}>机器狗状态</h3>
      <div style={{ display: 'flex', gap: 10, flexWrap: 'wrap' }}>
        {dogs.map(dog => {
          const statusColor = STATUS_COLOR[dog.status] || '#6c757d';
          return (
            <div key={dog.id} style={{
              padding: '10px 14px',
              border: `2px solid ${statusColor}`,
              borderRadius: 8,
              backgroundColor: dog.status === 'working' ? '#e8f4fd' : dog.status === 'charging' ? '#fff3e0' : '#f8f9fa',
              minWidth: 150,
            }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontWeight: 'bold', fontSize: 13 }}>🐕 {dog.name}</span>
                <span style={{
                  fontSize: 11, padding: '1px 6px', borderRadius: 10,
                  background: statusColor, color: '#fff',
                }}>
                  {STATUS_LABEL[dog.status] || dog.status}
                </span>
              </div>
              <div style={{ fontSize: 11, color: '#666', marginTop: 4 }}>
                归属：{dog.charging_station}
              </div>
              {dog.current_location && (
                <div style={{ fontSize: 11, color: '#333', marginTop: 2 }}>
                  位置：{dog.current_location}
                </div>
              )}
              <BatteryBar value={dog.battery} />
            </div>
          );
        })}
      </div>
    </div>
  );
}

export default RobotStatus;
