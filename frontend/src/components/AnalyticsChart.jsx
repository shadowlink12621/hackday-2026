import React from 'react';
import { PieChart, Pie, Cell, Tooltip, ResponsiveContainer, Legend } from 'recharts';

const COLORS = ['#00ffb3', '#00a3ff', '#ffd166', '#ff4d4d', '#a0b2b5'];

export default function AnalyticsChart({ items }) {
  if (!items || items.length === 0) return null;

  // Aggregate by category
  const dataMap = {};
  items.forEach(item => {
    const cat = item.category || 'misc';
    dataMap[cat] = (dataMap[cat] || 0) + item.amount;
  });

  const data = Object.keys(dataMap).map(key => ({
    name: key,
    value: dataMap[key]
  }));

  return (
    <div style={{ width: '100%', height: 200, marginTop: '20px' }}>
      <ResponsiveContainer>
        <PieChart>
          <Pie
            data={data}
            cx="50%"
            cy="50%"
            innerRadius={40}
            outerRadius={70}
            paddingAngle={5}
            dataKey="value"
          >
            {data.map((entry, index) => (
              <Cell key={`cell-${index}`} fill={COLORS[index % COLORS.length]} />
            ))}
          </Pie>
          <Tooltip 
            contentStyle={{ backgroundColor: 'rgba(5, 10, 13, 0.9)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px' }}
            itemStyle={{ color: '#fff' }}
          />
          <Legend wrapperStyle={{ fontSize: '11px', fontFamily: 'monospace' }} />
        </PieChart>
      </ResponsiveContainer>
    </div>
  );
}
