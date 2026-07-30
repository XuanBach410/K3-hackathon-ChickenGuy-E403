import React, { useState } from 'react';
import { Sliders, Zap, ArrowRight, CheckCircle2, AlertTriangle, X } from 'lucide-react';

export default function WhatIfSimulatorModal({ isOpen, onClose, topicCode, topicTitle, missingTechs, teamMembers, apiBase }) {
  const [selectedSkill, setSelectedSkill] = useState('');
  const [simulationResult, setSimulationResult] = useState(null);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const missingList = (missingTechs || []).map(m => (typeof m === 'object' ? m.tech : m));

  const handleSimulate = async () => {
    if (!selectedSkill) return;
    setLoading(true);
    try {
      const res = await fetch(`${apiBase}/evaluate/what-if/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic_code: topicCode,
          team_members: teamMembers,
          target_skill: selectedSkill
        })
      });
      const data = await res.json();
      setSimulationResult(data);
    } catch (err) {
      console.error('Error running What-If simulation:', err);
    } finally {
      setLoading(false);
    }
  };

  return (
    <div style={{
      position: 'fixed', inset: 0, background: 'rgba(15, 23, 42, 0.65)', backdropFilter: 'blur(4px)',
      display: 'flex', alignItems: 'center', justifyContent: 'center', zIndex: 1000, padding: '20px'
    }}>
      <div style={{
        background: '#FFF', borderRadius: '12px', width: '100%', maxWidth: '600px',
        border: '1px solid var(--border-color)', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', overflow: 'hidden'
      }}>
        {/* Modal Header */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F8FAFC' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <Sliders size={20} color="var(--signal-red)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>What-If Analysis Simulator — [{topicCode}]</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B' }}>
            <X size={20} />
          </button>
        </div>

        {/* Modal Body */}
        <div style={{ padding: '24px' }}>
          <p style={{ fontSize: '14px', color: '#475569', marginBottom: '16px' }}>
            Giả lập kịch bản: <strong>Nếu 1 thành viên trong nhóm học thêm kỹ năng mới</strong>, điểm phù hợp (Matching Score) và Ma trận Rủi ro sẽ thay đổi ra sao?
          </p>

          <label style={{ display: 'block', fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', color: '#64748B', marginBottom: '8px' }}>
            Chọn Kỹ Năng Muốn Giả Lập Học Thêm:
          </label>
          <div style={{ display: 'flex', gap: '10px', marginBottom: '20px' }}>
            <select
              value={selectedSkill}
              onChange={(e) => setSelectedSkill(e.target.value)}
              style={{ flex: 1, padding: '10px', borderRadius: '6px', border: '1px solid #CBD5E1', fontSize: '14px' }}
            >
              <option value="">-- Chọn từ kỹ năng nhóm đang thiếu --</option>
              {missingList.map((sk, idx) => (
                <option key={idx} value={sk}>⚡ {sk}</option>
              ))}
              <option value="Docker">Docker</option>
              <option value="PyTorch">PyTorch</option>
              <option value="FastAPI">FastAPI</option>
              <option value="React">React</option>
            </select>
            <button
              onClick={handleSimulate}
              disabled={!selectedSkill || loading}
              style={{
                padding: '10px 20px', background: 'var(--signal-red)', color: '#FFF', border: 'none',
                borderRadius: '6px', fontWeight: 700, cursor: 'pointer', opacity: (!selectedSkill || loading) ? 0.6 : 1
              }}
            >
              {loading ? 'Đang Mô Phỏng...' : 'Mô Phỏng Ngay'}
            </button>
          </div>

          {/* Simulation Results Comparison */}
          {simulationResult && (
            <div style={{ background: '#F0FDF4', border: '1px solid #BBF0C8', borderRadius: '8px', padding: '16px', marginTop: '16px' }}>
              <div style={{ fontSize: '14px', fontWeight: 700, color: '#166534', marginBottom: '12px', display: 'flex', alignItems: 'center', gap: '6px' }}>
                <Zap size={18} color="#166534" /> Kịch bản nếu nhóm học thành công: "{simulationResult.target_skill}"
              </div>

              <div style={{ display: 'grid', gridTemplateColumns: '1fr 40px 1fr', alignItems: 'center', textAlign: 'center', gap: '8px', marginBottom: '16px' }}>
                <div style={{ background: '#FFF', padding: '12px', borderRadius: '6px', border: '1px solid #CBD5E1' }}>
                  <div style={{ fontSize: '11px', color: '#64748B', textTransform: 'uppercase' }}>Điểm Hiện Tại</div>
                  <div className="mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#475569' }}>
                    {simulationResult.baseline.score}%
                  </div>
                </div>

                <ArrowRight size={24} color="#166534" style={{ margin: '0 auto' }} />

                <div style={{ background: '#FFF', padding: '12px', borderRadius: '6px', border: '1px solid #86EFAC' }}>
                  <div style={{ fontSize: '11px', color: '#166534', textTransform: 'uppercase' }}>Điểm Sau Mô Phỏng</div>
                  <div className="mono" style={{ fontSize: '1.6rem', fontWeight: 800, color: '#16A34A' }}>
                    {simulationResult.what_if.score}%
                  </div>
                </div>
              </div>

              <div style={{ fontSize: '13px', color: '#14532D', background: '#FFF', padding: '10px', borderRadius: '6px', border: '1px solid #DCFCE7' }}>
                🚀 <strong>Tăng trưởng:</strong> +{simulationResult.score_improvement}% điểm phù hợp!
                <br />
                🛡️ <strong>Rủi ro Skill Risk:</strong> Chuyển từ <span style={{ fontWeight: 700 }}>{simulationResult.baseline.riskMatrix?.skill_risk}</span> → <span style={{ fontWeight: 700, color: '#16A34A' }}>{simulationResult.what_if.riskMatrix?.skill_risk}</span>
              </div>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
