import React from 'react';
import { BrainCircuit, CheckCircle2, Clock3, Send } from 'lucide-react';

export default function DeepEvaluationChatCell({ topicCode, quizData, quizAnswers, setQuizAnswers, onSubmit, loading }) {
  if (!quizData?.questions?.length) return null;

  const answeredCount = quizData.questions.filter((question) => {
    const answer = quizAnswers[question.id];
    return answer !== undefined && answer !== '' && answer !== null;
  }).length;

  return (
    <section className="deep-chat-cell" aria-label={`Đánh giá sâu cho ${topicCode}`}>
      <div className="deep-chat-intro">
        <span className="assistant-avatar"><BrainCircuit size={18} /></span>
        <div>
          <strong>Đánh Giá Sâu Khả Thi & Lộ Trình 6 Tuần</strong>
          <p>{topicCode} · Trả lời ngay trong hội thoại để Agent tổng hợp evidence và roadmap.</p>
        </div>
      </div>

      <div className="deep-question-list">
        {quizData.questions.map((question, index) => (
          <article className="deep-question" key={question.id}>
            <div className="question-number">{index + 1}</div>
            <div className="question-content">
              <p>{question.question}</p>
              {question.type === 'scale' && (
                <div className="deep-scale-options">
                  {[1, 2, 3, 4, 5].map((value) => (
                    <button
                      type="button"
                      className={quizAnswers[question.id] === value ? 'selected' : ''}
                      key={value}
                      onClick={() => setQuizAnswers({ ...quizAnswers, [question.id]: value })}
                    >
                      {value}
                    </button>
                  ))}
                </div>
              )}
              {question.type === 'choice' && (
                <div className="deep-choice-options">
                  {question.options.map((option) => (
                    <button
                      type="button"
                      className={quizAnswers[question.id] === option ? 'selected' : ''}
                      key={option}
                      onClick={() => setQuizAnswers({ ...quizAnswers, [question.id]: option })}
                    >
                      <CheckCircle2 size={14} />{option}
                    </button>
                  ))}
                </div>
              )}
              {question.type === 'number' && (
                <label className="deep-number-input">
                  <Clock3 size={15} />
                  <input
                    type="number"
                    min="1"
                    max="12"
                    value={quizAnswers[question.id] ?? question.default ?? 3}
                    onChange={(event) => setQuizAnswers({ ...quizAnswers, [question.id]: Number(event.target.value) })}
                  />
                  <span>giờ/ngày</span>
                </label>
              )}
              {question.type === 'text' && (
                <textarea
                  value={quizAnswers[question.id] || ''}
                  placeholder={question.placeholder || 'Nhập câu trả lời của nhóm...'}
                  onChange={(event) => setQuizAnswers({ ...quizAnswers, [question.id]: event.target.value })}
                />
              )}
            </div>
          </article>
        ))}
      </div>

      <div className="deep-chat-footer">
        <span>{answeredCount}/{quizData.questions.length} câu đã trả lời</span>
        <button type="button" onClick={onSubmit} disabled={loading || answeredCount < quizData.questions.length}>
          <Send size={15} />{loading ? 'Đang tổng hợp...' : 'Sinh kết luận & roadmap'}
        </button>
      </div>
    </section>
  );
}
