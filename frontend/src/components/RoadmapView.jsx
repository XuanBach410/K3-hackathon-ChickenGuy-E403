import React from 'react';
import { Route, CheckCircle, AlertOctagon, BookOpen, Clock } from 'lucide-react';

export default function RoadmapView({ evaluation }) {
  if (!evaluation) return null;

  const { fitState, verdictTitle, transparentJustification, feasibilityIndex, riskLevel, weeklyRoadmap, requiredSkillSummary } = evaluation;

  const isFit = fitState === 'PERFECT_FIT';
  const isAble = fitState === 'ABLE_TO_LEARN';
  const color = isFit ? 'var(--success)' : isAble ? 'var(--warning)' : 'var(--signal-red)';

  return (
    <div style={{ marginTop: '32px', borderTop: '1px solid var(--border-subtle)', paddingTop: '24px' }}>
      {/* Header Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px' }}>Kết Luận</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 700, color }}>{fitState}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>{verdictTitle}</div>
        </div>

        <div style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px' }}>Chỉ Số Khả Thi</div>
          <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 700, color: 'var(--deep-blue)' }}>{feasibilityIndex} / 5.0</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>Mức Rủi Ro: {riskLevel}</div>
        </div>

        <div style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px' }}>Kỹ Năng Thiếu</div>
          <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 700, color: requiredSkillSummary?.toLearn?.length ? 'var(--signal-red)' : 'var(--success)' }}>
            {requiredSkillSummary?.toLearn?.length || 0} Skills
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>Thời gian học ~2 tuần</div>
        </div>
      </div>

      {/* Justification Box */}
      <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '20px', marginBottom: '24px' }}>
        <h4 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <CheckCircle size={18} color="var(--deep-blue)" /> Phân Tích & Giải Thích Minh Bạch (Transparent Evidence)
        </h4>
        <ul style={{ paddingLeft: '20px', fontSize: '14px', color: 'var(--text-primary)' }}>
          {transparentJustification?.map((j, idx) => (
            <li key={idx} style={{ marginBottom: '6px' }}>{j}</li>
          ))}
        </ul>
      </div>

      {/* 6-Week Roadmap */}
      <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '20px' }}>
        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px' }}>
          <Route size={20} color="var(--deep-blue)" /> Lộ Trình Thực Hiện 6 Tuần (6-Week Roadmap)
        </h4>

        {weeklyRoadmap?.map((w) => (
          <div key={w.week} style={{ display: 'grid', gridTemplateColumns: '80px 1fr', gap: '16px', marginBottom: '16px' }}>
            <div className="mono" style={{ fontWeight: 700, color: 'var(--deep-blue)', fontSize: '14px', paddingTop: '4px' }}>
              Tuần {w.week}
            </div>
            <div style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', padding: '14px', borderRadius: '6px', fontSize: '14px' }}>
              <strong style={{ display: 'block', marginBottom: '4px' }}>{w.title}</strong>
              <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)' }}>
                {w.tasks?.map((t, idx) => (
                  <li key={idx}>{t}</li>
                ))}
              </ul>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
}
