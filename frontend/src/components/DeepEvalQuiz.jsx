import React from 'react';
import { ShieldAlert, Info, BookOpen, CheckCircle, AlertTriangle } from 'lucide-react';

export default function DeepEvalQuiz({ topicCode, quizData, quizAnswers, setQuizAnswers, onSubmit, loading }) {
  if (!quizData) return null;

  return (
    <div style={{
      background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)',
      borderRadius: 'var(--radius)', padding: '24px', marginTop: '24px', boxShadow: 'var(--shadow-card)'
    }}>
      <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
        <ShieldAlert color="var(--deep-blue)" size={20} />
        Đánh Giá Sâu Khả Thi & Lộ Trình 6 Tuần — [{topicCode}]
      </h3>

      <div style={{ padding: '12px 16px', background: '#EBF5FF', border: '1px solid #93C5FD', borderRadius: '6px', fontSize: '14px', color: '#1E3A5F', marginBottom: '24px' }}>
        <Info size={16} style={{ display: 'inline', marginRight: '6px' }} />
        Vui lòng hoàn thành 4-5 câu hỏi ngắn bên dưới để Agent phân tích chính xác năng lực thực chiến, thời gian cam kết và sinh Lộ trình 6 tuần tối ưu.
      </div>

      {quizData.questions.map((q, idx) => (
        <div key={q.id} style={{ marginBottom: '24px' }}>
          <div style={{ fontWeight: 600, fontSize: '14px', marginBottom: '12px', display: 'flex', gap: '8px' }}>
            <span style={{ background: 'var(--deep-blue)', color: '#FFF', borderRadius: '50%', width: '22px', height: '22px', display: 'flex', alignItems: 'center', justifyContent: 'center', fontSize: '12px', flexShrink: 0 }}>
              {idx + 1}
            </span>
            <span>{q.question}</span>
          </div>

          {q.type === 'scale' && (
            <div style={{ display: 'flex', gap: '8px' }}>
              {[1, 2, 3, 4, 5].map((val) => (
                <button
                  key={val}
                  type="button"
                  onClick={() => setQuizAnswers({ ...quizAnswers, [q.id]: val })}
                  style={{
                    width: '44px', height: '44px', border: '1px solid var(--border-color)',
                    borderRadius: '4px', background: quizAnswers[q.id] === val ? 'var(--deep-blue)' : 'var(--surface-primary)',
                    color: quizAnswers[q.id] === val ? '#FFF' : 'var(--text-primary)',
                    fontWeight: 700, cursor: 'pointer'
                  }}
                >
                  {val}
                </button>
              ))}
            </div>
          )}

          {q.type === 'choice' && (
            <div style={{ display: 'flex', flexDirection: 'column', gap: '8px' }}>
              {q.options.map((opt, i) => (
                <label key={i} style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '14px', cursor: 'pointer' }}>
                  <input
                    type="radio"
                    name={`q_${q.id}`}
                    value={opt}
                    checked={quizAnswers[q.id] === opt}
                    onChange={() => setQuizAnswers({ ...quizAnswers, [q.id]: opt })}
                  />
                  {opt}
                </label>
              ))}
            </div>
          )}

          {q.type === 'number' && (
            <input
              type="number"
              min="1"
              max="12"
              value={quizAnswers[q.id] || 3}
              onChange={(e) => setQuizAnswers({ ...quizAnswers, [q.id]: parseInt(e.target.value) })}
              style={{ width: '100px', padding: '8px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
            />
          )}

          {q.type === 'text' && (
            <textarea
              placeholder={q.placeholder}
              value={quizAnswers[q.id] || ''}
              onChange={(e) => setQuizAnswers({ ...quizAnswers, [q.id]: e.target.value })}
              style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
            />
          )}
        </div>
      ))}

      <button
        onClick={onSubmit}
        disabled={loading}
        style={{
          width: '100%', padding: '14px', background: 'var(--deep-blue)', color: '#FFF',
          border: 'none', borderRadius: '4px', fontWeight: 700, cursor: 'pointer', opacity: loading ? 0.6 : 1
        }}
      >
        {loading ? 'Đang Gọi Agent Phân Tích...' : 'Hoàn Tất & Sinh Kết Luận Khả Thi + Lộ Trình 6 Tuần'}
      </button>
    </div>
  );
}
