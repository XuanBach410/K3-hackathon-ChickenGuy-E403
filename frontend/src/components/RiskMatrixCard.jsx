import React from 'react';
import { ShieldAlert, Clock, AlertTriangle, Users, Compass } from 'lucide-react';

export default function RiskMatrixCard({ riskMatrix, missingTechs }) {
  if (!riskMatrix) return null;

  const { skill_risk, time_risk, team_risk, domain_risk, total_learning_hours, critical_missing_count } = riskMatrix;

  const getRiskColor = (level) => {
    if (level === 'High') return { bg: '#FEE2E2', text: '#DC2626', border: '#FCA5A5' };
    if (level === 'Medium') return { bg: '#FEF3C7', text: '#D97706', border: '#FCD34D' };
    return { bg: '#E8F5ED', text: '#16A34A', border: '#86EFAC' };
  };

  const risks = [
    { label: 'Skill Risk', value: skill_risk, icon: ShieldAlert, desc: critical_missing_count > 0 ? `${critical_missing_count} skill Critical` : 'Phủ đủ skill chính' },
    { label: 'Time Risk', value: time_risk, icon: Clock, desc: `Cần ~${total_learning_hours || 0}h học` },
    { label: 'Team Risk', value: team_risk, icon: Users, desc: team_risk === 'High' ? 'Vượt sĩ số' : 'Sĩ số chuẩn' },
    { label: 'Domain Risk', value: domain_risk, icon: Compass, desc: domain_risk === 'High' ? 'Lệch domain' : 'Chuẩn domain' }
  ];

  const criticals = (missingTechs || []).filter(m => (typeof m === 'object' ? m.criticality : 'Major') === 'Critical');
  const majors = (missingTechs || []).filter(m => (typeof m === 'object' ? m.criticality : 'Major') === 'Major');
  const minors = (missingTechs || []).filter(m => (typeof m === 'object' ? m.criticality : 'Major') === 'Minor');

  return (
    <div style={{
      background: 'var(--surface-primary)',
      border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius)',
      padding: '16px',
      marginTop: '16px'
    }}>
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '12px' }}>
        <h4 style={{ fontSize: '13px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.04em', color: 'var(--text-secondary)', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <ShieldAlert size={16} color="var(--signal-red)" /> Decision Support System: Risk Assessment Matrix
        </h4>
        <span style={{ fontSize: '11px', background: '#F1F5F9', padding: '2px 8px', borderRadius: '4px', color: '#475569', fontWeight: 600 }}>
          4 Dạng Rủi Ro Định Lượng
        </span>
      </div>

      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '10px', marginBottom: '14px' }}>
        {risks.map((r, i) => {
          const style = getRiskColor(r.value);
          const Icon = r.icon;
          return (
            <div key={i} style={{ background: style.bg, border: `1px solid ${style.border}`, borderRadius: '6px', padding: '10px 12px' }}>
              <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'space-between', marginBottom: '4px' }}>
                <span style={{ fontSize: '11px', fontWeight: 700, color: '#334155' }}>{r.label}</span>
                <Icon size={14} color={style.text} />
              </div>
              <div style={{ fontSize: '15px', fontWeight: 800, color: style.text }}>{r.value}</div>
              <div style={{ fontSize: '10px', color: '#64748B', marginTop: '2px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{r.desc}</div>
            </div>
          );
        })}
      </div>

      <div style={{ fontSize: '12px', background: '#F8FAFC', border: '1px solid #E2E8F0', padding: '12px', borderRadius: '6px' }}>
        <div style={{ fontWeight: 700, marginBottom: '8px', color: '#1E293B', display: 'flex', alignItems: 'center', gap: '6px' }}>
          <AlertTriangle size={14} color="#D97706" /> Phân Tích Khoảng Trống Kỹ Năng (Skill Gap Breakdown):
        </div>
        
        <div style={{ display: 'flex', flexWrap: 'wrap', gap: '6px' }}>
          {criticals.map((m, i) => {
            const name = typeof m === 'object' ? m.tech : m;
            const hours = typeof m === 'object' ? m.cost_hours : 20;
            return (
              <span key={`crit_${i}`} style={{ background: '#FEE2E2', color: '#991B1B', border: '#FCA5A5 1px solid', padding: '2px 8px', borderRadius: '4px', fontWeight: 700, fontSize: '11px' }}>
                🔴 CRITICAL: {name} (~{hours}h)
              </span>
            );
          })}
          {majors.map((m, i) => {
            const name = typeof m === 'object' ? m.tech : m;
            const hours = typeof m === 'object' ? m.cost_hours : 20;
            return (
              <span key={`maj_${i}`} style={{ background: '#FEF3C7', color: '#92400E', border: '#FCD34D 1px solid', padding: '2px 8px', borderRadius: '4px', fontWeight: 600, fontSize: '11px' }}>
                🟠 MAJOR: {name} (~{hours}h)
              </span>
            );
          })}
          {minors.map((m, i) => {
            const name = typeof m === 'object' ? m.tech : m;
            const hours = typeof m === 'object' ? m.cost_hours : 20;
            return (
              <span key={`min_${i}`} style={{ background: '#F1F5F9', color: '#475569', border: '#CBD5E1 1px solid', padding: '2px 8px', borderRadius: '4px', fontWeight: 500, fontSize: '11px' }}>
                🟡 MINOR: {name} (~{hours}h)
              </span>
            );
          })}
          {missingTechs?.length === 0 && (
            <span style={{ color: '#16A34A', fontWeight: 600 }}>✓ Nhóm không thiếu kỹ năng nào!</span>
          )}
        </div>
      </div>
    </div>
  );
}
