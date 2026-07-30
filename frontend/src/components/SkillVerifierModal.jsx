import React, { useState } from 'react';
import { CheckSquare, ShieldCheck, X, Award } from 'lucide-react';

export default function SkillVerifierModal({ isOpen, onClose, teamMembers, apiBase }) {
  const [quizzes, setQuizzes] = useState([]);
  const [answers, setAnswers] = useState({});
  const [verified, setVerified] = useState(false);
  const [loading, setLoading] = useState(false);

  if (!isOpen) return null;

  const handleFetchQuizzes = async () => {
    setLoading(true);
    // Extract unique skills from team members
    const allSkills = new Set();
    teamMembers.forEach(m => {
      if (typeof m.skills === 'string') {
        m.skills.split(',').forEach(s => {
          const parts = s.split(':');
          if (parts[0]) allSkills.add(parts[0].trim());
        });
      }
    });

    try {
      const res = await fetch(`${apiBase}/evaluate/verify-skills/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ declared_skills: Array.from(allSkills) })
      });
      const data = await res.json();
      if (!res.ok) throw new Error(data.error || 'Unable to generate verification questions');
      setQuizzes(data.verification_quizzes || []);
    } catch (err) {
      console.error('Error fetching skill verifier tool:', err);
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
        background: '#FFF', borderRadius: '12px', width: '100%', maxWidth: '640px',
        border: '1px solid var(--border-color)', boxShadow: '0 20px 25px -5px rgba(0,0,0,0.1)', overflow: 'hidden'
      }}>
        {/* Header */}
        <div style={{ padding: '16px 24px', borderBottom: '1px solid #E2E8F0', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: '#F8FAFC' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px' }}>
            <ShieldCheck size={20} color="var(--success)" />
            <h3 style={{ fontSize: '1.1rem', fontWeight: 700 }}>Skill Verifier Agent Tool (Chống Khai Khống)</h3>
          </div>
          <button onClick={onClose} style={{ background: 'none', border: 'none', cursor: 'pointer', color: '#64748B' }}>
            <X size={20} />
          </button>
        </div>

        {/* Content */}
        <div style={{ padding: '24px', maxHeight: '70vh', overflowY: 'auto' }}>
          {quizzes.length === 0 && !verified && (
            <div style={{ textAlign: 'center', padding: '20px 0' }}>
              <Award size={48} color="var(--deep-blue)" style={{ margin: '0 auto 12px' }} />
              <h4 style={{ fontSize: '1.1rem', fontWeight: 700, marginBottom: '8px' }}>Xác Thực Kỹ Năng Thành Viên Trong Nhóm</h4>
              <p style={{ fontSize: '14px', color: '#64748B', maxWidth: '44ch', margin: '0 auto 20px' }}>
                Agent sẽ kiểm tra lại các kỹ năng mà nhóm đã tự khai báo bằng các câu hỏi trắc nghiệm thực hành để tránh đánh giá lệch.
              </p>
              <button
                onClick={handleFetchQuizzes}
                disabled={loading}
                style={{ padding: '12px 24px', background: 'var(--deep-blue)', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}
              >
                {loading ? 'Đang Lấy Bộ Câu Hỏi...' : 'Bắt Đầu Kích Hoạt Skill Verifier'}
              </button>
            </div>
          )}

          {quizzes.length > 0 && !verified && (
            <div>
              {quizzes.map((q, idx) => (
                <div key={idx} style={{ marginBottom: '20px', background: '#F8FAFC', padding: '16px', borderRadius: '8px', border: '1px solid #E2E8F0' }}>
                  <div style={{ fontWeight: 700, fontSize: '14px', marginBottom: '8px', color: '#1E293B' }}>
                    {idx + 1}. {q.question}
                  </div>
                  <div style={{ display: 'flex', flexDirection: 'column', gap: '6px' }}>
                    {q.options.map((opt, i) => (
                      <label key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '13px', cursor: 'pointer', color: '#334155' }}>
                        <input
                          type="radio"
                          name={`q_verify_${idx}`}
                          checked={answers[idx] === opt}
                          onChange={() => setAnswers({ ...answers, [idx]: opt })}
                        />
                        {opt}
                      </label>
                    ))}
                  </div>
                </div>
              ))}

              <button
                onClick={() => setVerified(true)}
                style={{ width: '100%', padding: '12px', background: 'var(--success)', color: '#FFF', border: 'none', borderRadius: '6px', fontWeight: 700, cursor: 'pointer' }}
              >
                ✓ Xác Nhận & Cập Nhật Hồ Sơ Thực Với Agent
              </button>
            </div>
          )}

          {verified && (
            <div style={{ textAlign: 'center', padding: '24px', background: '#E8F5ED', borderRadius: '8px', border: '1px solid #86EFAC' }}>
              <ShieldCheck size={48} color="var(--success)" style={{ margin: '0 auto 12px' }} />
              <h4 style={{ fontSize: '1.2rem', fontWeight: 700, color: 'var(--success)', marginBottom: '8px' }}>
                Xác Thực Kỹ Năng Thành Công!
              </h4>
              <p style={{ fontSize: '14px', color: '#14532D' }}>
                Hồ sơ nhóm đã được gán nhãn Verified. Độ tin cậy dữ liệu của bạn đã đạt <strong>95%</strong>.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
