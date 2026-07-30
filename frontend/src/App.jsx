import React, { useState, useEffect } from 'react';
import { Users, Library, Zap, Key, Plus, X, ArrowLeft, ArrowRight, ShieldAlert, CheckCircle, AlertTriangle, Sliders, ShieldCheck } from 'lucide-react';
import ApiKeyModal from './components/ApiKeyModal';
import DeepEvalQuiz from './components/DeepEvalQuiz';
import RoadmapView from './components/RoadmapView';
import RiskMatrixCard from './components/RiskMatrixCard';
import WhatIfSimulatorModal from './components/WhatIfSimulatorModal';
import SkillVerifierModal from './components/SkillVerifierModal';

const API_BASE = 'http://localhost:8000/api';

export default function App() {
  const [step, setStep] = useState(1);
  const [topics, setTopics] = useState([]);
  const [mockProfiles, setMockProfiles] = useState([]);
  const [teamMembers, setTeamMembers] = useState([]);
  const [selectedCodes, setSelectedCodes] = useState(new Set());
  const [matchingResults, setMatchingResults] = useState([]);
  
  // Modals & Agent Tools State
  const [isApiKeyModalOpen, setIsApiKeyModalOpen] = useState(false);
  const [isVerifierModalOpen, setIsVerifierModalOpen] = useState(false);
  const [isWhatIfModalOpen, setIsWhatIfModalOpen] = useState(false);
  const [whatIfTopic, setWhatIfTopic] = useState(null);

  const [provider, setProvider] = useState(localStorage.getItem('matchskill_provider') || 'gemini');
  const [apiKey, setApiKey] = useState(localStorage.getItem('matchskill_api_key') || '');

  // Deep Quiz & Evaluation State
  const [activeDeepTopic, setActiveDeepTopic] = useState(null);
  const [quizData, setQuizData] = useState(null);
  const [quizAnswers, setQuizAnswers] = useState({});
  const [finalEvaluation, setFinalEvaluation] = useState(null);
  const [evalLoading, setEvalLoading] = useState(false);

  // Search & Filter State
  const [searchTerm, setSearchTerm] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('ALL');

  useEffect(() => {
    fetchTopics();
    fetchProfiles();
  }, []);

  const fetchTopics = async () => {
    try {
      const res = await fetch(`${API_BASE}/topics/`);
      const data = await res.json();
      setTopics(data.topics || []);
    } catch (err) {
      console.error('Error fetching topics:', err);
    }
  };

  const fetchProfiles = async () => {
    try {
      const res = await fetch(`${API_BASE}/profiles/`);
      const data = await res.json();
      setMockProfiles(data.profiles || []);
    } catch (err) {
      console.error('Error fetching profiles:', err);
    }
  };

  const handleSaveApiKey = () => {
    localStorage.setItem('matchskill_provider', provider);
    localStorage.setItem('matchskill_api_key', apiKey);
    setIsApiKeyModalOpen(false);
    alert(apiKey ? `✅ Đã lưu API Key (${provider.toUpperCase()}) thành công!` : `ℹ️ Đã chuyển về Offline Fallback Engine.`);
  };

  const loadPresetTeam = (presetKey) => {
    if (presetKey.startsWith('mock-team-')) {
      const idx = parseInt(presetKey.replace('mock-team-', ''));
      const chunk = mockProfiles.slice(idx * 4, (idx + 1) * 4);
      setTeamMembers(chunk.map(p => ({
        ...p,
        name: `${p.name} (${p.desired_roles?.[0] || 'Dev'})`,
        skills: p.proficiency ? Object.entries(p.proficiency).map(([k, v]) => `${k}:${v}`).join(', ') : 'Python:3'
      })));
    }
  };

  const toggleTopicSelection = (code) => {
    const next = new Set(selectedCodes);
    if (next.has(code)) next.delete(code);
    else next.add(code);
    setSelectedCodes(next);
  };

  const runPreliminaryMatching = async () => {
    if (selectedCodes.size === 0 || teamMembers.length === 0) return;
    try {
      const res = await fetch(`${API_BASE}/evaluate/preliminary/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          team_members: teamMembers,
          selected_codes: Array.from(selectedCodes)
        })
      });
      const data = await res.json();
      setMatchingResults(data.results || []);
      setStep(3);
    } catch (err) {
      console.error('Error running MCDA:', err);
    }
  };

  const handleOpenDeepEval = async (code) => {
    setActiveDeepTopic(code);
    setFinalEvaluation(null);
    try {
      const res = await fetch(`${API_BASE}/evaluate/deep-quiz/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ topic_code: code })
      });
      const data = await res.json();
      setQuizData(data);
      setQuizAnswers({ 3: 3 });
    } catch (err) {
      console.error('Error loading deep quiz:', err);
    }
  };

  const handleFinalEvaluationSubmit = async () => {
    setEvalLoading(true);
    try {
      const res = await fetch(`${API_BASE}/evaluate/final/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          topic_code: activeDeepTopic,
          team_members: teamMembers,
          quiz_answers: quizAnswers,
          provider,
          api_key: apiKey
        })
      });
      const data = await res.json();
      setFinalEvaluation(data.evaluation);
    } catch (err) {
      console.error('Error running final evaluation:', err);
    } finally {
      setEvalLoading(false);
    }
  };

  const filteredTopics = topics.filter(t => {
    const matchesCategory = categoryFilter === 'ALL' || t.category === categoryFilter;
    const matchesSearch = !searchTerm || `${t.code} ${t.title}`.toLowerCase().includes(searchTerm.toLowerCase());
    return matchesCategory && matchesSearch;
  });

  const categories = ['ALL', ...Array.from(new Set(topics.map(t => t.category).filter(Boolean)))];

  return (
    <div style={{ minHeight: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* NAVBAR */}
      <nav style={{ background: 'var(--surface-primary)', borderBottom: '1px solid var(--border-color)', height: '56px' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 24px', height: '100%', display: 'flex', alignItems: 'center', justifyContent: 'space-between' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '12px' }}>
            <div style={{ width: '32px', height: '32px', background: 'var(--signal-red)', color: '#FFF', fontWeight: 700, borderRadius: '4px', display: 'flex', alignItems: 'center', justifyCenter: 'center' }}>M</div>
            <span style={{ fontWeight: 700, fontSize: '1.1rem' }}>MatchSkill AI</span>
            <span style={{ fontSize: '12px', border: '1px solid var(--border-color)', padding: '2px 8px', borderRadius: '4px', color: 'var(--text-secondary)' }}>Django + React.js</span>
          </div>

          <div style={{ display: 'flex', alignItems: 'center', gap: '16px' }}>
            <button
              onClick={() => setIsApiKeyModalOpen(true)}
              style={{ background: 'var(--surface-secondary)', border: '1px solid var(--border-color)', padding: '6px 12px', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px' }}
            >
              <Key size={14} color="var(--signal-red)" /> API Key Config
            </button>
          </div>
        </div>
      </nav>

      {/* API KEY MODAL */}
      <ApiKeyModal
        isOpen={isApiKeyModalOpen}
        onClose={() => setIsApiKeyModalOpen(false)}
        provider={provider}
        setProvider={setProvider}
        apiKey={apiKey}
        setApiKey={setApiKey}
        onSave={handleSaveApiKey}
      />

      {/* HERO SAAS BANNER */}
      <div style={{ background: 'var(--surface-primary)', borderBottom: '1px solid var(--border-color)', padding: '40px 0' }}>
        <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '0 24px', display: 'grid', gridTemplateColumns: '5fr 3fr', gap: '32px', alignItems: 'end' }}>
          <div>
            <div style={{ fontSize: '12px', fontWeight: 700, textTransform: 'uppercase', letterSpacing: '0.06em', color: 'var(--signal-red)', marginBottom: '8px' }}>
              SaaS AI Matchmaking Platform &middot; Mini Hackathon AI Batch 03
            </div>
            <h1 style={{ fontSize: '2.5rem', fontWeight: 700, lineHeight: 1.15, letterSpacing: '-0.02em', marginBottom: '16px' }}>
              Match <span style={{ color: 'var(--signal-red)' }}>Skill</span> to Topic.
            </h1>
            <p style={{ fontSize: '1.05rem', color: 'var(--text-secondary)', maxWidth: '56ch', lineHeight: 1.6 }}>
              Nền tảng SaaS phân tích đa tiêu chí (MCDA), đối soát kỹ năng ẩn từ hồ sơ nhóm với kho 360 đề tài thực tế. 
              Ước tính rủi ro vỡ tiến độ, đánh giá khả thi trong 6 tuần và sinh lộ trình chi tiết bằng AI.
            </p>
          </div>
          <div style={{ display: 'flex', flexDirection: 'column', gap: '16px' }}>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
              <span className="mono" style={{ fontSize: '2.2rem', fontWeight: 700, color: 'var(--signal-red)' }}>360</span>
              <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Kho Đề Tài Đồ Án Khoá Học</span>
            </div>
            <div style={{ display: 'flex', itemsAlign: 'baseline', gap: '12px' }}>
              <span className="mono" style={{ fontSize: '2.2rem', fontWeight: 700, color: 'var(--deep-blue)' }}>100</span>
              <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>Hồ Sơ Học Viên Sẵn Có (Mockdata)</span>
            </div>
            <div style={{ display: 'flex', alignItems: 'baseline', gap: '12px' }}>
              <span className="mono" style={{ fontSize: '2.2rem', fontWeight: 700, color: 'var(--success)' }}>MCDA</span>
              <span style={{ fontSize: '14px', color: 'var(--text-secondary)' }}>4 Tiêu Chí C1-C4 (criteria.md)</span>
            </div>
          </div>
        </div>
      </div>

      {/* MAIN CONTAINER */}
      <div style={{ maxWidth: '1280px', margin: '0 auto', padding: '24px', flex: 1, width: '100%' }}>
        {/* STEPPER */}
        <div style={{ display: 'flex', gap: '16px', marginBottom: '24px', alignItems: 'center' }}>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: step === 1 ? 700 : 400, color: step === 1 ? 'var(--signal-red)' : 'var(--text-secondary)' }}>
            <span style={{ width: '28px', height: '28px', borderRadius: '50%', background: step === 1 ? 'var(--signal-red)' : 'var(--surface-primary)', color: step === 1 ? '#FFF' : 'var(--text-secondary)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyCenter: 'center', fontSize: '12px', fontWeight: 700 }}>1</span>
            Team Profile
          </div>
          <div style={{ width: '40px', height: '2px', background: 'var(--border-color)' }}></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: step === 2 ? 700 : 400, color: step === 2 ? 'var(--signal-red)' : 'var(--text-secondary)' }}>
            <span style={{ width: '28px', height: '28px', borderRadius: '50%', background: step === 2 ? 'var(--signal-red)' : 'var(--surface-primary)', color: step === 2 ? '#FFF' : 'var(--text-secondary)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyCenter: 'center', fontSize: '12px', fontWeight: 700 }}>2</span>
            Topic Multi-Select
          </div>
          <div style={{ width: '40px', height: '2px', background: 'var(--border-color)' }}></div>
          <div style={{ display: 'flex', alignItems: 'center', gap: '8px', fontWeight: step === 3 ? 700 : 400, color: step === 3 ? 'var(--signal-red)' : 'var(--text-secondary)' }}>
            <span style={{ width: '28px', height: '28px', borderRadius: '50%', background: step === 3 ? 'var(--signal-red)' : 'var(--surface-primary)', color: step === 3 ? '#FFF' : 'var(--text-secondary)', border: '1px solid var(--border-color)', display: 'flex', alignItems: 'center', justifyCenter: 'center', fontSize: '12px', fontWeight: 700 }}>3</span>
            Results & Analysis
          </div>
        </div>

        {/* STEP 1: TEAM PROFILE */}
        {step === 1 && (
          <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '24px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Users size={20} /> Hồ Sơ Nhóm & Kỹ Năng Thành Viên
            </h3>

            <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
              Chọn Nhóm Mockdata (từ mork_data/mock_profiles.json)
            </label>
            <select
              onChange={(e) => loadPresetTeam(e.target.value)}
              style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)', marginBottom: '24px' }}
            >
              <option value="">-- Chọn nhóm mockdata --</option>
              {Array.from({ length: Math.min(5, Math.floor(mockProfiles.length / 4)) }).map((_, idx) => (
                <option key={idx} value={`mock-team-${idx}`}>
                  🎯 Nhóm {idx + 1} ({mockProfiles.slice(idx * 4, (idx + 1) * 4).map(p => p.name).join(', ')})
                </option>
              ))}
            </select>

            <div style={{ borderTop: '1px solid var(--border-subtle)', paddingTop: '16px' }}>
              <h4 style={{ fontSize: '14px', fontWeight: 600, marginBottom: '12px' }}>Danh Sách Thành Viên & Skill Level (1-5)</h4>
              {teamMembers.map((m, idx) => (
                <div key={idx} style={{ background: 'var(--surface-secondary)', padding: '12px 16px', borderRadius: '6px', marginBottom: '8px', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                  <div>
                    <div style={{ fontWeight: 600 }}>{m.name}</div>
                    <div className="mono" style={{ fontSize: '12px', color: 'var(--deep-blue)' }}>{m.skills}</div>
                  </div>
                  <button onClick={() => setTeamMembers(teamMembers.filter((_, i) => i !== idx))} style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'var(--cool-grey)' }}>
                    <X size={16} />
                  </button>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
              <button
                onClick={() => setIsVerifierModalOpen(true)}
                disabled={teamMembers.length === 0}
                style={{ padding: '10px 16px', background: 'var(--surface-secondary)', border: '1px solid var(--border-color)', borderRadius: '4px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontSize: '13px', opacity: teamMembers.length === 0 ? 0.5 : 1 }}
              >
                <ShieldCheck size={16} color="var(--success)" /> Kích Hoạt Skill Verifier Agent Tool
              </button>

              <button
                onClick={() => setStep(2)}
                disabled={teamMembers.length === 0}
                style={{ padding: '12px 24px', background: 'var(--signal-red)', color: '#FFF', border: 'none', borderRadius: '4px', fontWeight: 700, cursor: 'pointer', opacity: teamMembers.length === 0 ? 0.5 : 1 }}
              >
                Tiếp Theo: Chọn Đề Tài <ArrowRight size={16} style={{ display: 'inline', marginLeft: '6px' }} />
              </button>
            </div>
          </div>
        )}

        {/* STEP 2: TOPIC MULTI-SELECT */}
        {step === 2 && (
          <div style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '24px' }}>
            <h3 style={{ fontSize: '1.2rem', marginBottom: '16px', display: 'flex', alignItems: 'center', gap: '8px' }}>
              <Library size={20} /> Kho 360 Đề Tài & Chọn Multi-Selection
            </h3>

            <div style={{ display: 'flex', gap: '12px', marginBottom: '16px' }}>
              <input
                type="text"
                placeholder="Tìm đề tài theo tên hoặc mã (e.g. EDU-01)..."
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
                style={{ flex: 1, padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
              />
              <select
                value={categoryFilter}
                onChange={(e) => setCategoryFilter(e.target.value)}
                style={{ width: '220px', padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)' }}
              >
                {categories.map((cat) => (
                  <option key={cat} value={cat}>{cat === 'ALL' ? 'Tất cả các Khối' : cat}</option>
                ))}
              </select>
            </div>

            {/* Topic List */}
            <div style={{ maxHeight: '440px', overflowY: 'auto', border: '1px solid var(--border-subtle)', borderRadius: '6px' }}>
              {filteredTopics.slice(0, 80).map((t) => (
                <div
                  key={t.code}
                  onClick={() => toggleTopicSelection(t.code)}
                  style={{
                    display: 'grid', gridTemplateColumns: '40px 90px 1fr 140px', gap: '12px', padding: '12px 16px',
                    borderBottom: '1px solid var(--border-subtle)', cursor: 'pointer',
                    background: selectedCodes.has(t.code) ? '#EBF5FF' : 'transparent'
                  }}
                >
                  <input type="checkbox" checked={selectedCodes.has(t.code)} readOnly />
                  <span className="mono" style={{ fontWeight: 700, color: 'var(--signal-red)' }}>{t.code}</span>
                  <span style={{ fontSize: '14px', whiteSpace: 'nowrap', overflow: 'hidden', textOverflow: 'ellipsis' }}>{t.title}</span>
                  <span style={{ fontSize: '12px', color: 'var(--text-secondary)', textAlign: 'right' }}>{t.category}</span>
                </div>
              ))}
            </div>

            <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginTop: '24px' }}>
              <button onClick={() => setStep(1)} style={{ padding: '10px 20px', background: 'var(--surface-primary)', border: '1px solid var(--border-color)', borderRadius: '4px', cursor: 'pointer' }}>
                <ArrowLeft size={16} style={{ display: 'inline', marginRight: '6px' }} /> Quay Lại
              </button>
              <button
                onClick={runPreliminaryMatching}
                disabled={selectedCodes.size === 0}
                style={{ padding: '12px 24px', background: 'var(--signal-red)', color: '#FFF', border: 'none', borderRadius: '4px', fontWeight: 700, cursor: 'pointer', opacity: selectedCodes.size === 0 ? 0.5 : 1 }}
              >
                <Zap size={16} style={{ display: 'inline', marginRight: '6px' }} /> Phân Tích Matching Sơ Bộ ({selectedCodes.size} Đề Tài)
              </button>
            </div>
          </div>
        )}

        {/* STEP 3: RESULTS */}
        {step === 3 && (
          <div>
            <div style={{ display: 'flex', justifyCenter: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
              <h2>Kết Quả Fitting Sơ Bộ ({matchingResults.length} Đề Tài)</h2>
              <button onClick={() => setStep(2)} style={{ padding: '8px 16px', background: 'var(--surface-primary)', border: '1px solid var(--border-color)', borderRadius: '4px', cursor: 'pointer' }}>
                <ArrowLeft size={16} style={{ display: 'inline', marginRight: '6px' }} /> Chọn Đề Tài Khác
              </button>
            </div>

            {matchingResults.map((r) => (
              <div key={r.code} style={{ background: 'var(--surface-primary)', border: '1px solid var(--border-subtle)', borderRadius: '8px', padding: '20px', marginBottom: '16px' }}>
                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '12px' }}>
                  <div>
                    <span className="mono" style={{ background: 'var(--danger-bg)', color: 'var(--signal-red)', padding: '2px 8px', borderRadius: '4px', fontSize: '12px', fontWeight: 700, marginRight: '8px' }}>{r.code}</span>
                    <span style={{ fontSize: '12px', color: 'var(--text-secondary)' }}>{r.category}</span>
                    <h3 style={{ fontSize: '1.1rem', marginTop: '6px' }}>{r.title}</h3>
                  </div>
                  <div style={{ textAlign: 'center', padding: '8px 16px', border: '1px solid var(--border-color)', borderRadius: '8px' }}>
                    <div className="mono" style={{ fontSize: '1.4rem', fontWeight: 700, color: 'var(--signal-red)' }}>{r.finalScore}%</div>
                    <div style={{ fontSize: '10px', textTransform: 'uppercase', color: 'var(--text-secondary)' }}>Overall Score</div>
                  </div>
                </div>

                <p style={{ fontSize: '14px', color: 'var(--text-secondary)', marginBottom: '12px' }}>{r.description}</p>

                {/* Risk Matrix Card */}
                <RiskMatrixCard riskMatrix={r.riskMatrix} missingTechs={r.missingTechs} />

                <div style={{ display: 'flex', gap: '10px', marginTop: '16px' }}>
                  <button
                    onClick={() => handleOpenDeepEval(r.code)}
                    style={{ flex: 1, padding: '10px 16px', background: 'var(--deep-blue)', color: '#FFF', border: 'none', borderRadius: '4px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', justifyContent: 'center', gap: '6px' }}
                  >
                    <ShieldAlert size={16} /> Xem Đánh Giá Sâu & Lộ Trình
                  </button>

                  <button
                    onClick={() => {
                      setWhatIfTopic(r);
                      setIsWhatIfModalOpen(true);
                    }}
                    style={{ padding: '10px 16px', background: '#F8FAFC', border: '1px solid #CBD5E1', color: '#1E293B', borderRadius: '4px', fontWeight: 600, cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px' }}
                  >
                    <Sliders size={16} color="var(--signal-red)" /> Mô Phỏng What-If
                  </button>
                </div>
              </div>
            ))}

            {/* DEEP EVAL QUIZ & ROADMAP VIEW */}
            {activeDeepTopic && (
              <div>
                <DeepEvalQuiz
                  topicCode={activeDeepTopic}
                  quizData={quizData}
                  quizAnswers={quizAnswers}
                  setQuizAnswers={setQuizAnswers}
                  onSubmit={handleFinalEvaluationSubmit}
                  loading={evalLoading}
                />

                <RoadmapView evaluation={finalEvaluation} />
              </div>
            )}
          </div>
        )}
      </div>

      {/* AGENT TOOL MODALS */}
      <SkillVerifierModal
        isOpen={isVerifierModalOpen}
        onClose={() => setIsVerifierModalOpen(false)}
        teamMembers={teamMembers}
        apiBase={API_BASE}
      />

      <WhatIfSimulatorModal
        isOpen={isWhatIfModalOpen}
        onClose={() => setIsWhatIfModalOpen(false)}
        topicCode={whatIfTopic?.code}
        topicTitle={whatIfTopic?.title}
        missingTechs={whatIfTopic?.missingTechs}
        teamMembers={teamMembers}
        apiBase={API_BASE}
      />
    </div>
  );
}
