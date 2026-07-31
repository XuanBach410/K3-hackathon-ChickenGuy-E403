import React, { useState, useEffect, useRef } from 'react';
import {
  Send, Bot, User, Settings, MessageSquare, BookOpen,
  Users, ListChecks, Layers, Lightbulb, ChevronRight,
  Sparkles, Trash2, Mic, ArrowRight, ExternalLink,
  CheckCircle2, Circle, CircleDot, Code2, Database,
  Server, Globe, Cpu, Shield, BarChart3
} from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import ApiKeyModal from './components/ApiKeyModal';
import TopicListView from './components/TopicListView';
import TeamSelectionView from './components/TeamSelectionView';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

// Navigation items for left sidebar
const NAV_ITEMS = [
  { id: 'chat', label: 'Chat', icon: MessageSquare, active: true },
  { id: 'topics', label: 'Đề tài của bạn', icon: BookOpen },
  { id: 'skills', label: 'Kỹ năng của nhóm', icon: Users },
  { id: 'topic-list', label: 'Danh sách đề tài', icon: ListChecks },
  { id: 'techstack', label: 'Tech Stack', icon: Layers },
  { id: 'suggest', label: 'Gợi ý tiếp theo', icon: Lightbulb },
];

// Progress steps
const PROGRESS_STEPS = [
  { id: 1, label: 'Nhập kỹ năng nhóm', done: false },
  { id: 2, label: 'Chọn/gợi ý đề tài', done: false },
  { id: 3, label: 'Tech stack & Lộ trình', done: false },
  { id: 4, label: 'Kế hoạch tiếp theo', done: false },
];

export default function DecisionWorkspace() {
  const [messages, setMessages] = useState(() => {
    try {
      return JSON.parse(localStorage.getItem('matchskill_chat_context') || '[]');
    } catch { return []; }
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState(localStorage.getItem('matchskill_api_key') || '');
  const [provider, setProvider] = useState(localStorage.getItem('matchskill_provider') || 'gemini');
  const [isApiKeyOpen, setIsApiKeyOpen] = useState(false);
  const [activeNav, setActiveNav] = useState('chat');

  // Context state
  const [teamMembers, setTeamMembers] = useState([]);
  const [mcdaResult, setMcdaResult] = useState(null);
  const [topicContext, setTopicContext] = useState(null);
  const [selectedTopic, setSelectedTopic] = useState(null);
  const [techStack, setTechStack] = useState(null);
  const [progressSteps, setProgressSteps] = useState(PROGRESS_STEPS);

  const scrollRef = useRef(null);
  const inputRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('matchskill_chat_context', JSON.stringify(messages));
    if (scrollRef.current) {
      scrollRef.current.scrollTo({ top: scrollRef.current.scrollHeight, behavior: 'smooth' });
    }
  }, [messages]);

  // Calculate progress percentage
  const completedSteps = progressSteps.filter(s => s.done).length;
  const progressPercent = Math.round((completedSteps / progressSteps.length) * 100);

  const handleSend = async (textOverride = null) => {
    const text = textOverride || input;
    if (!text.trim()) return;
    if (!apiKey) {
      setIsApiKeyOpen(true);
      return;
    }

    const newMessage = { role: 'user', content: text, time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }) };
    const currentHistory = [...messages, newMessage];
    setMessages(currentHistory);
    setInput('');
    setLoading(true);

    try {
      await processChatTurn(currentHistory, text);
    } catch (err) {
      setMessages(prev => [...prev, {
        role: 'assistant',
        content: 'Lỗi kết nối server: ' + err.message,
        time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' })
      }]);
    } finally {
      setLoading(false);
    }
  };

  const processChatTurn = async (history, currentText) => {
    let loopCount = 0;
    let currentHist = [...history];

    while (loopCount < 3) {
      loopCount++;
      const res = await fetch(`${API_BASE}/advisor/chat/`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: currentText,
          history: currentHist.slice(0, -1),
          team_members: teamMembers,
          api_key: apiKey,
          provider
        })
      });

      const data = await res.json();

      if (data.reply && data.reply.startsWith("Đang gọi công cụ:")) {
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply, isToolLoading: true }]);

        const toolRes = await fetch(`${API_BASE}/advisor/execute_tool/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data.tool_call_raw || {})
        });
        const toolData = await toolRes.json();

        if (toolData.result?.mcda_result) setMcdaResult(toolData.result.mcda_result);
        if (toolData.result?.latent_skills) {
          setTeamMembers([{ name: "Thành viên", proficiency: toolData.result.latent_skills }]);
          updateProgress(0, true);
        }

        const sysMsg = { role: 'system', content: `[Kết quả Tool]: ${JSON.stringify(toolData.result)}` };
        currentHist = [...currentHist, { role: 'assistant', content: data.reply }, sysMsg];
        currentText = "Vui lòng tiếp tục trả lời user dựa trên kết quả tool.";
        setMessages(prev => prev.filter(m => !m.isToolLoading));
      } else {
        const time = new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' });
        setMessages(prev => {
          const clean = prev.filter(m => !m.isToolLoading);
          return [...clean, {
            role: 'assistant',
            content: data.reply,
            suggestions: data.suggested_questions,
            topicCards: data.topic_cards,
            quickActions: data.quick_actions,
            time
          }];
        });
        if (data.mcda_snapshot) setMcdaResult(data.mcda_snapshot);
        if (data.topic_context) {
          setTopicContext(data.topic_context);
          setSelectedTopic(data.topic_context);
          updateProgress(1, true);
        }
        if (data.tech_stack) {
          setTechStack(data.tech_stack);
          updateProgress(2, true);
        }
        break;
      }
    }
  };

  const updateProgress = (index, done) => {
    setProgressSteps(prev => prev.map((s, i) => i === index ? { ...s, done } : s));
  };

  const clearChat = () => {
    setMessages([]);
    localStorage.removeItem('matchskill_chat_context');
  };

  // Initial greeting message
  const greeting = {
    role: 'assistant',
    content: 'Xin chào! 👋\nMình là TopicAI, mình sẽ giúp nhóm bạn chọn đề tài phù hợp nhất với kỹ năng, sở thích và mục tiêu. Bắt đầu nào nhé!',
    time: new Date().toLocaleTimeString('vi-VN', { hour: '2-digit', minute: '2-digit' }),
    quickActions: [
      { label: 'Chọn từ danh sách đề tài', icon: ListChecks },
      { label: '+ Gợi ý cho nhóm', icon: Sparkles },
    ]
  };

  const displayMessages = messages.length === 0 ? [greeting] : messages;

  return (
    <div className="flex h-screen bg-white font-sans">
      {/* ═══════════════ LEFT SIDEBAR ═══════════════ */}
      <aside className="w-64 bg-gradient-to-b from-violet-50 to-white border-r border-violet-100 flex flex-col">
        {/* Logo */}
        <div className="p-5 border-b border-violet-100">
          <div className="flex items-center gap-3">
            <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-lg shadow-violet-200">
              <Bot size={22} />
            </div>
            <div>
              <h1 className="font-bold text-base text-violet-900">TopicAI</h1>
              <p className="text-[11px] text-violet-500">AI Topic Advisor</p>
            </div>
          </div>
        </div>

        {/* Navigation */}
        <nav className="flex-1 p-3 space-y-1">
          {NAV_ITEMS.map(item => (
            <button
              key={item.id}
              onClick={() => setActiveNav(item.id)}
              className={`w-full flex items-center gap-3 px-4 py-2.5 rounded-xl text-sm font-medium transition-all duration-200 cursor-pointer ${
                activeNav === item.id
                  ? 'bg-violet-600 text-white shadow-md shadow-violet-200'
                  : 'text-violet-700 hover:bg-violet-100'
              }`}
            >
              <item.icon size={18} />
              {item.label}
            </button>
          ))}
        </nav>

        {/* Progress Tracker */}
        <div className="mx-4 mb-4 p-4 bg-white rounded-2xl border border-violet-100 shadow-sm">
          <div className="flex items-center justify-center mb-4">
            <div className="relative w-20 h-20">
              <svg viewBox="0 0 36 36" className="w-full h-full -rotate-90">
                <circle cx="18" cy="18" r="15" fill="none" stroke="#EDE9FE" strokeWidth="3" />
                <circle
                  cx="18" cy="18" r="15" fill="none"
                  stroke="#7C3AED" strokeWidth="3"
                  strokeDasharray={`${progressPercent * 0.94} 100`}
                  strokeLinecap="round"
                  className="transition-all duration-700"
                />
              </svg>
              <div className="absolute inset-0 flex flex-col items-center justify-center">
                <span className="text-lg font-bold text-violet-700">{progressPercent}%</span>
                <span className="text-[10px] text-violet-400">Hoàn tất</span>
              </div>
            </div>
          </div>
          <ul className="space-y-2 text-xs">
            {progressSteps.map(step => (
              <li key={step.id} className="flex items-center gap-2">
                {step.done ? (
                  <CheckCircle2 size={14} className="text-emerald-500 shrink-0" />
                ) : (
                  <Circle size={14} className="text-violet-300 shrink-0" />
                )}
                <span className={step.done ? 'text-emerald-600 font-medium' : 'text-violet-500'}>
                  {step.label}
                </span>
              </li>
            ))}
          </ul>
        </div>

        {/* User Profile */}
        <div className="p-4 border-t border-violet-100">
          <div className="flex items-center gap-3">
            <div className="w-9 h-9 rounded-full bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white text-sm font-bold shadow">
              D
            </div>
            <div className="flex-1 min-w-0">
              <div className="text-sm font-semibold text-violet-900 truncate">Đinh Hoài Nam</div>
              <div className="text-[11px] text-violet-500 truncate">nhóm-ai-innovators</div>
            </div>
          </div>
        </div>
      </aside>

      {/* ═══════════════ CENTER CHAT ═══════════════ */}
      <main className="flex-1 flex flex-col min-w-0">
        {/* Header */}
        <header className="h-16 flex items-center justify-between px-6 border-b bg-white/90 backdrop-blur-md sticky top-0 z-10">
          <div>
            <h2 className="text-lg font-bold text-slate-900">
              {activeNav === 'topic-list' ? 'Danh sách đề tài' :
               activeNav === 'skills' ? 'Thiết lập nhóm' : 'Chatbot hỗ trợ chọn đề tài'}
            </h2>
            <p className="text-xs text-slate-500">
              {activeNav === 'topic-list' ? 'Khám phá tất cả các đề tài dự án' : 
               activeNav === 'skills' ? 'Thêm thành viên vào nhóm của bạn từ dữ liệu mô phỏng' : 'Dựa trên kỹ năng nhóm, danh sách đề tài và định hướng phát triển'}
            </p>
          </div>
          {activeNav === 'chat' && (
            <div className="flex items-center gap-2">
              <Button variant="outline" size="sm" onClick={clearChat} className="text-xs gap-1.5 rounded-lg cursor-pointer">
                <Trash2 size={14} /> Xóa hội thoại
              </Button>
            </div>
          )}
        </header>

        {activeNav === 'topic-list' ? (
          <div className="flex-1 overflow-y-auto px-6 py-6 bg-slate-50">
            <TopicListView onSelectTopic={(topic) => {
              setSelectedTopic(topic);
              setActiveNav('chat');
              handleSend(`Xem chi tiết đề tài: ${topic.title}`);
            }} />
          </div>
        ) : activeNav === 'skills' ? (
          <div className="flex-1 overflow-y-auto px-6 py-6 bg-slate-50">
            <TeamSelectionView 
              currentTeam={teamMembers}
              onSaveTeam={(newTeam) => {
                setTeamMembers(newTeam);
                setActiveNav('chat');
                const names = newTeam.map(t => t.name).join(', ');
                handleSend(`Tôi đã cập nhật kỹ năng nhóm với ${newTeam.length} thành viên (${names}). Hãy đánh giá và tư vấn đề tài phù hợp cho chúng tôi.`);
              }} 
            />
          </div>
        ) : (
          <>
            {/* Messages */}
            <div className="flex-1 overflow-y-auto px-6 py-6" ref={scrollRef}>
          <div className="max-w-3xl mx-auto flex flex-col gap-5">
            {displayMessages.filter(m => m.role !== 'system').map((msg, i) => (
              <div key={i} className={`flex gap-3 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                {/* Avatar */}
                {msg.role !== 'user' && (
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white shadow-sm shrink-0">
                    <Bot size={18} />
                  </div>
                )}
                {msg.role === 'user' && (
                  <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-violet-600 to-indigo-600 flex items-center justify-center text-white shadow-sm shrink-0">
                    <User size={16} />
                  </div>
                )}

                {/* Message Bubble */}
                <div className={`max-w-[85%] ${msg.role === 'user' ? '' : ''}`}>
                  <div className={`rounded-2xl px-4 py-3 ${
                    msg.role === 'user'
                      ? 'bg-violet-600 text-white rounded-tr-md'
                      : 'bg-slate-50 border border-slate-200 text-slate-700 rounded-tl-md'
                  } ${msg.isToolLoading ? 'animate-pulse bg-violet-50 border-violet-200' : ''}`}>
                    <div className="whitespace-pre-wrap leading-relaxed text-[14px]">{msg.content}</div>
                  </div>

                  {/* Quick Actions */}
                  {msg.quickActions?.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {msg.quickActions.map((action, idx) => (
                        <button
                          key={idx}
                          onClick={() => handleSend(action.label)}
                          className="flex items-center gap-2 px-4 py-2 bg-white border border-violet-200 rounded-full text-sm text-violet-700 hover:bg-violet-50 hover:border-violet-300 transition-all cursor-pointer shadow-sm"
                        >
                          {action.icon && <action.icon size={14} />}
                          {action.label}
                        </button>
                      ))}
                    </div>
                  )}

                  {/* Topic Cards */}
                  {msg.topicCards?.length > 0 && (
                    <div className="grid grid-cols-1 md:grid-cols-3 gap-3 mt-4">
                      {msg.topicCards.map((card, idx) => (
                        <div
                          key={idx}
                          onClick={() => {
                            setSelectedTopic(card);
                            handleSend(`Xem chi tiết đề tài: ${card.title}`);
                          }}
                          className="bg-white border border-slate-200 rounded-xl p-4 hover:border-violet-300 hover:shadow-md transition-all cursor-pointer group"
                        >
                          <div className="flex items-center gap-2 mb-2">
                            <span className="w-6 h-6 rounded-full bg-violet-100 text-violet-700 flex items-center justify-center text-xs font-bold">{idx + 1}</span>
                            <h4 className="font-semibold text-sm text-slate-800 group-hover:text-violet-700 transition-colors">{card.title}</h4>
                          </div>
                          <p className="text-xs text-slate-500 mb-3 line-clamp-2">{card.description}</p>
                          {card.tags?.length > 0 && (
                            <div className="flex flex-wrap gap-1 mb-3">
                              {card.tags.map((tag, ti) => (
                                <span key={ti} className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded-md text-[10px] font-medium">{tag}</span>
                              ))}
                            </div>
                          )}
                          <div className="flex items-center text-violet-600 text-xs font-medium gap-1 group-hover:gap-2 transition-all">
                            Xem chi tiết <ArrowRight size={12} />
                          </div>
                        </div>
                      ))}
                    </div>
                  )}

                  {/* Suggestion Badges */}
                  {msg.suggestions?.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-3">
                      {msg.suggestions.map((sug, idx) => (
                        <Badge
                          key={idx}
                          variant="secondary"
                          className="cursor-pointer hover:bg-violet-100 hover:text-violet-700 px-3 py-1.5 text-xs font-normal rounded-lg transition-colors"
                          onClick={() => handleSend(sug)}
                        >
                          {sug}
                        </Badge>
                      ))}
                    </div>
                  )}

                  {/* Timestamp */}
                  {msg.time && (
                    <div className={`text-[11px] mt-1.5 ${msg.role === 'user' ? 'text-right text-slate-400' : 'text-slate-400'}`}>
                      {msg.time}
                    </div>
                  )}
                </div>
              </div>
            ))}

            {/* Loading indicator */}
            {loading && (
              <div className="flex gap-3">
                <div className="w-9 h-9 rounded-xl bg-gradient-to-br from-emerald-400 to-teal-500 flex items-center justify-center text-white shadow-sm">
                  <Bot size={18} />
                </div>
                <div className="bg-slate-100 rounded-2xl rounded-tl-md px-5 py-4 flex gap-1.5 items-center">
                  <div className="w-2 h-2 rounded-full bg-violet-400 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-violet-400 animate-bounce [animation-delay:75ms]" />
                  <div className="w-2 h-2 rounded-full bg-violet-400 animate-bounce [animation-delay:150ms]" />
                </div>
              </div>
            )}
          </div>
        </div>

        {/* Input Bar */}
        <div className="px-6 py-4 bg-white border-t">
          <form
            onSubmit={e => { e.preventDefault(); handleSend(); }}
            className="max-w-3xl mx-auto flex items-center gap-3 bg-slate-50 rounded-2xl border border-slate-200 p-1.5 focus-within:ring-2 focus-within:ring-violet-500/20 focus-within:border-violet-300 transition-all"
          >
            <button type="button" className="p-2 text-slate-400 hover:text-violet-600 transition-colors cursor-pointer">
              <Mic size={18} />
            </button>
            <Input
              ref={inputRef}
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Nhập tin nhắn của bạn..."
              className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0 text-sm px-2"
            />
            <Button
              type="submit"
              disabled={!input.trim() || loading}
              className="rounded-xl w-10 h-10 p-0 bg-violet-600 hover:bg-violet-700 disabled:opacity-40 shadow-md shadow-violet-200 transition-all cursor-pointer"
            >
              <Send size={16} />
            </Button>
          </form>
        </div>
          </>
        )}
      </main>

      {/* ═══════════════ RIGHT CONTEXT PANEL ═══════════════ */}
      <aside className="w-80 bg-slate-50 border-l border-slate-200 flex-col hidden lg:flex overflow-y-auto pt-2">
        {/* Selected Topic Card */}
        <div className="p-5">
          <h3 className="font-bold text-sm text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <BookOpen size={14} />
            Đề tài bạn đang chọn
          </h3>

          {selectedTopic ? (
            <Card className="p-4 bg-white border-violet-200 shadow-sm">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 rounded-xl bg-gradient-to-br from-violet-500 to-indigo-500 flex items-center justify-center text-white shrink-0">
                  <Sparkles size={18} />
                </div>
                <div>
                  <h4 className="font-bold text-sm text-slate-800">{selectedTopic.title || selectedTopic.name}</h4>
                  {selectedTopic.match_score && (
                    <span className="text-xs text-emerald-600 font-medium">Độ phù hợp: {selectedTopic.match_score}%</span>
                  )}
                </div>
              </div>
              <Button variant="outline" size="sm" className="w-full text-xs text-violet-600 border-violet-200 hover:bg-violet-50 cursor-pointer">
                <ExternalLink size={12} className="mr-1.5" /> Xem chi tiết đề tài
              </Button>
            </Card>
          ) : (
            <div className="text-sm text-slate-400 text-center py-8 border border-dashed border-slate-300 rounded-xl bg-white">
              Chưa chọn đề tài nào
            </div>
          )}
        </div>

        {/* Tech Stack */}
        <div className="px-5 pb-5">
          <h3 className="font-bold text-sm text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Layers size={14} />
            Tech Stack đề xuất
          </h3>

          {techStack ? (
            <div className="space-y-3">
              {Object.entries(techStack).map(([category, items]) => (
                <div key={category} className="flex items-start gap-3 bg-white p-3 rounded-xl border border-slate-100">
                  <div className="w-8 h-8 rounded-lg bg-violet-100 flex items-center justify-center text-violet-600 shrink-0">
                    {category.toLowerCase().includes('backend') ? <Server size={16} /> :
                     category.toLowerCase().includes('frontend') ? <Globe size={16} /> :
                     category.toLowerCase().includes('database') ? <Database size={16} /> :
                     category.toLowerCase().includes('ml') || category.toLowerCase().includes('ai') ? <Cpu size={16} /> :
                     category.toLowerCase().includes('devops') ? <Shield size={16} /> :
                     <Code2 size={16} />}
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-700">{category}</div>
                    <div className="text-[11px] text-slate-500">{Array.isArray(items) ? items.join(', ') : items}</div>
                  </div>
                </div>
              ))}
              <Button variant="outline" size="sm" className="w-full text-xs text-violet-600 cursor-pointer">
                Xem tất cả tech stack
              </Button>
            </div>
          ) : (
            <div className="space-y-3">
              {[
                { icon: Server, label: 'Backend', desc: 'Chưa có dữ liệu' },
                { icon: Globe, label: 'Frontend', desc: 'Chưa có dữ liệu' },
                { icon: Database, label: 'Database', desc: 'Chưa có dữ liệu' },
              ].map((item, i) => (
                <div key={i} className="flex items-start gap-3 bg-white p-3 rounded-xl border border-slate-100 opacity-50">
                  <div className="w-8 h-8 rounded-lg bg-slate-100 flex items-center justify-center text-slate-400 shrink-0">
                    <item.icon size={16} />
                  </div>
                  <div>
                    <div className="text-xs font-bold text-slate-500">{item.label}</div>
                    <div className="text-[11px] text-slate-400">{item.desc}</div>
                  </div>
                </div>
              ))}
            </div>
          )}
        </div>

        {/* Suggestions */}
        <div className="px-5 pb-5">
          <h3 className="font-bold text-sm text-slate-500 uppercase tracking-wider mb-4 flex items-center gap-2">
            <Lightbulb size={14} />
            Gợi ý tiếp theo
          </h3>
          <div className="space-y-2">
            {[
              'Phân tích yêu cầu chi tiết',
              'Lập kế hoạch phát triển (Roadmap)',
              'Tìm tài liệu & nguồn tham khảo',
              'Gợi ý ý tưởng mở rộng',
            ].map((sug, i) => (
              <button
                key={i}
                onClick={() => handleSend(sug)}
                className="w-full flex items-center justify-between p-3 bg-white border border-slate-100 rounded-xl text-sm text-slate-700 hover:border-violet-300 hover:bg-violet-50 hover:text-violet-700 transition-all cursor-pointer group"
              >
                <span>{sug}</span>
                <ChevronRight size={14} className="text-slate-300 group-hover:text-violet-500 transition-colors" />
              </button>
            ))}
          </div>
        </div>

        {/* MCDA Result Card */}
        {mcdaResult && (
          <div className="px-5 pb-5">
            <Card className="p-4 bg-white border-t-4 border-t-emerald-500 shadow-sm">
              <h3 className="font-bold text-xs text-slate-500 uppercase mb-3 flex items-center gap-2">
                <BarChart3 size={14} /> Kết quả MCDA
              </h3>
              <div className="text-3xl font-black text-violet-600 mb-1">{mcdaResult.score || mcdaResult.finalScore}%</div>
              <Badge className="bg-violet-100 text-violet-700 text-xs">{mcdaResult.fit_state || mcdaResult.fitState || 'Đang đánh giá'}</Badge>
            </Card>
          </div>
        )}
      </aside>

      {/* API Key Modal */}
      <ApiKeyModal
        isOpen={isApiKeyOpen}
        onClose={() => setIsApiKeyOpen(false)}
        onSave={(p, k) => { 
          setProvider(p); 
          setApiKey(k); 
          localStorage.setItem('matchskill_provider', p);
          localStorage.setItem('matchskill_api_key', k);
          setIsApiKeyOpen(false); 
        }}
        currentKey={apiKey}
      />
    </div>
  );
}
