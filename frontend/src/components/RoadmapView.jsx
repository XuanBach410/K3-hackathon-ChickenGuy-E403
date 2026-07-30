import React, { useEffect, useRef } from 'react';
import { Route, CheckCircle, AlertOctagon, BookOpen, Clock, ShieldAlert } from 'lucide-react';

export default function RoadmapView({ evaluation }) {
  const containerRef = useRef(null);

  useEffect(() => {
    if (evaluation && containerRef.current) {
      containerRef.current.scrollIntoView({ behavior: 'smooth' });
    }
  }, [evaluation]);

  if (!evaluation) return null;

  // Defensive parsing if evaluation is a string
  let evalObj = evaluation;
  if (typeof evaluation === 'string') {
    try {
      evalObj = JSON.parse(evaluation);
    } catch (e) {
      evalObj = { verdictTitle: evaluation };
    }
  }

  const fitState = evalObj.fitState || 'ABLE_TO_LEARN';
  const verdictTitle = evalObj.verdictTitle || 'Đánh giá từ AI Advisor';
  const feasibilityIndex = evalObj.feasibilityIndex || 3.5;
  const riskLevel = evalObj.riskLevel || 'Medium';

  // Defensive Array Conversions
  const justifications = Array.isArray(evalObj.transparentJustification)
    ? evalObj.transparentJustification
    : evalObj.transparentJustification ? [String(evalObj.transparentJustification)] : ['Đánh giá dựa trên năng lực và tiêu chí MCDA.'];

  const weeklyRoadmap = Array.isArray(evalObj.weeklyRoadmap) ? evalObj.weeklyRoadmap : [];

  const coveredSkills = Array.isArray(evalObj.requiredSkillSummary?.covered) ? evalObj.requiredSkillSummary.covered : [];
  const toLearnSkills = Array.isArray(evalObj.requiredSkillSummary?.toLearn) ? evalObj.requiredSkillSummary.toLearn : [];

  const isFit = fitState === 'PERFECT_FIT';
  const isAble = fitState === 'ABLE_TO_LEARN';
  const color = isFit ? 'var(--success)' : isAble ? 'var(--warning)' : 'var(--signal-red)';

  return (
    <div ref={containerRef} style={{ marginTop: '32px', borderTop: '2px solid var(--border-subtle)', paddingTop: '24px' }}>
      <h3 style={{ fontSize: '1.3rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', color: 'var(--deep-blue)' }}>
        <ShieldAlert size={24} /> Báo Cáo Đánh Giá Khả Thi & Lộ Trình 6 Tuần
      </h3>

      {/* Header Metric Cards */}
      <div style={{ display: 'grid', gridTemplateColumns: 'repeat(3, 1fr)', gap: '16px', marginBottom: '24px' }}>
        <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>Kết Luận Agent</div>
          <div style={{ fontSize: '1.2rem', fontWeight: 800, color }}>{fitState}</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>{verdictTitle}</div>
        </div>

        <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>Chỉ Số Khả Thi</div>
          <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: 'var(--deep-blue)' }}>{feasibilityIndex} / 5.0</div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>Mức Rủi Ro: <strong>{riskLevel}</strong></div>
        </div>

        <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', padding: '16px', borderRadius: '8px', textAlign: 'center', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' }}>
          <div style={{ fontSize: '11px', textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '4px', fontWeight: 600 }}>Kỹ Năng Cần Bù Đắp</div>
          <div className="mono" style={{ fontSize: '1.5rem', fontWeight: 800, color: toLearnSkills.length > 0 ? 'var(--signal-red)' : 'var(--success)' }}>
            {toLearnSkills.length} Skills
          </div>
          <div style={{ fontSize: '12px', color: 'var(--text-secondary)', marginTop: '2px' }}>Đã đáp ứng: {coveredSkills.length} skills</div>
        </div>
      </div>

      {/* Justification Box */}
      <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '20px', marginBottom: '24px', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' }}>
        <h4 style={{ fontSize: '15px', fontWeight: 700, marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '8px', color: '#1E293B' }}>
          <CheckCircle size={18} color="var(--deep-blue)" /> Phân Tích & Giải Thích Minh Bạch (Transparent Evidence)
        </h4>
        <ul style={{ paddingLeft: '20px', fontSize: '14px', color: 'var(--text-primary)', lineHeight: 1.7 }}>
          {justifications.map((j, idx) => (
            <li key={idx} style={{ marginBottom: '6px' }}>{j}</li>
          ))}
        </ul>
      </div>

      {/* Required Skills Breakdown */}
      {(toLearnSkills.length > 0 || coveredSkills.length > 0) && (
        <div style={{ background: '#F8FAFC', border: '1px solid #E2E8F0', borderRadius: '8px', padding: '16px', marginBottom: '24px' }}>
          <h4 style={{ fontSize: '14px', fontWeight: 700, marginBottom: '10px', color: '#334155', display: 'flex', alignItems: 'center', gap: '6px' }}>
            <BookOpen size={16} color="var(--deep-blue)" /> Phân Tóm Tắt Kỹ Năng (Skill Summary):
          </h4>
          <div style={{ display: 'flex', gap: '16px', flexWrap: 'wrap' }}>
            {toLearnSkills.length > 0 && (
              <div>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#991B1B', display: 'block', marginBottom: '4px' }}>Cần học thêm:</span>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {toLearnSkills.map((sk, i) => (
                    <span key={i} style={{ background: '#FEE2E2', color: '#991B1B', border: '1px solid #FCA5A5', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                      ⚡ {typeof sk === 'object' ? JSON.stringify(sk) : sk}
                    </span>
                  ))}
                </div>
              </div>
            )}
            {coveredSkills.length > 0 && (
              <div>
                <span style={{ fontSize: '12px', fontWeight: 700, color: '#166534', display: 'block', marginBottom: '4px' }}>Đã làm chủ:</span>
                <div style={{ display: 'flex', gap: '6px', flexWrap: 'wrap' }}>
                  {coveredSkills.map((sk, i) => (
                    <span key={i} style={{ background: '#DCFCE7', color: '#166534', border: '1px solid #86EFAC', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 600 }}>
                      ✓ {typeof sk === 'object' ? JSON.stringify(sk) : sk}
                    </span>
                  ))}
                </div>
              </div>
            )}
          </div>
        </div>
      )}

      {/* 6-Week Roadmap */}
      <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '20px', boxShadow: '0 2px 4px rgba(0,0,0,0.04)' }}>
        <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '20px', display: 'flex', alignItems: 'center', gap: '8px', color: '#0F172A' }}>
          <Route size={20} color="var(--deep-blue)" /> Lộ Trình Thực Hiện 6 Tuần Chi Tiết (6-Week Learning & Execution Roadmap)
        </h4>

        {weeklyRoadmap.map((w, index) => {
          const weekNum = w.week || (index + 1);
          const tasks = Array.isArray(w.tasks) ? w.tasks : w.tasks ? [String(w.tasks)] : [];

          return (
            <div key={weekNum} style={{ display: 'grid', gridTemplateColumns: '90px 1fr', gap: '16px', marginBottom: '16px' }}>
              <div className="mono" style={{ fontWeight: 700, color: 'var(--deep-blue)', fontSize: '14px', paddingTop: '4px' }}>
                Tuần {weekNum}
              </div>
              <div style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-subtle)', padding: '14px', borderRadius: '6px', fontSize: '14px' }}>
                <strong style={{ display: 'block', marginBottom: '6px', color: '#1E293B' }}>{w.title || `Tuần ${weekNum}`}</strong>
                <ul style={{ paddingLeft: '20px', color: 'var(--text-secondary)', lineHeight: 1.6 }}>
                  {tasks.map((t, idx) => (
                    <li key={idx}>{typeof t === 'object' ? JSON.stringify(t) : t}</li>
                  ))}
                </ul>
              </div>
            </div>
          );
        })}

        {weeklyRoadmap.length === 0 && (
          <div style={{ padding: '16px', textAlign: 'center', color: '#64748B', fontSize: '14px' }}>
            Không có thông tin lộ trình tuần chi tiết.
          </div>
        )}
      </div>
    </div>
  );
}
