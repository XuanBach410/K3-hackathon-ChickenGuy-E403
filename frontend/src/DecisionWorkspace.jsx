import React, { useState, useEffect, useRef } from 'react';
import { Send, Bot, User, Settings, ShieldAlert, Cpu } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { Avatar, AvatarFallback, AvatarImage } from '@/components/ui/avatar';
import { ScrollArea } from '@/components/ui/scroll-area';
import { Badge } from '@/components/ui/badge';
import ApiKeyModal from './components/ApiKeyModal';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function DecisionWorkspace() {
  const [messages, setMessages] = useState(() => {
    try {
      const saved = JSON.parse(localStorage.getItem('matchskill_chat_context') || '[]');
      return saved;
    } catch { return []; }
  });
  const [input, setInput] = useState('');
  const [loading, setLoading] = useState(false);
  const [apiKey, setApiKey] = useState(localStorage.getItem('matchskill_api_key') || '');
  const [isApiKeyOpen, setIsApiKeyOpen] = useState(false);
  
  // Side panel state (dynamic based on tools)
  const [teamMembers, setTeamMembers] = useState([]);
  const [mcdaResult, setMcdaResult] = useState(null);
  const [topicContext, setTopicContext] = useState(null);

  const scrollRef = useRef(null);

  useEffect(() => {
    localStorage.setItem('matchskill_chat_context', JSON.stringify(messages));
    if (scrollRef.current) {
      scrollRef.current.scrollTo(0, scrollRef.current.scrollHeight);
    }
  }, [messages]);

  const handleSend = async (textOverride = null) => {
    const text = textOverride || input;
    if (!text.trim()) return;
    if (!apiKey) {
      setIsApiKeyOpen(true);
      return;
    }

    const newMessage = { role: 'user', content: text };
    const currentHistory = [...messages, newMessage];
    setMessages(currentHistory);
    setInput('');
    setLoading(true);

    try {
      await processChatTurn(currentHistory, text);
    } catch (err) {
      setMessages(prev => [...prev, { role: 'assistant', content: 'Lỗi kết nối server: ' + err.message }]);
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
          history: currentHist.slice(0, -1), // Everything before currentText is history
          team_members: teamMembers,
          api_key: apiKey,
          provider: localStorage.getItem('matchskill_provider') || 'gemini'
        })
      });

      const data = await res.json();

      if (data.reply && data.reply.startsWith("Đang gọi công cụ:")) {
        // AI returned a tool call
        setMessages(prev => [...prev, { role: 'assistant', content: data.reply, isToolLoading: true }]);
        
        // Execute tool
        const toolRes = await fetch(`${API_BASE}/advisor/execute_tool/`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify(data.tool_call_raw || {}) // need backend to pass raw tool call
        });
        const toolData = await toolRes.json();
        
        // Update Side Panel context if applicable
        if (toolData.result?.mcda_result) setMcdaResult(toolData.result.mcda_result);
        if (toolData.result?.latent_skills) {
          // just mock saving team
          setTeamMembers([{name: "Thành viên", proficiency: toolData.result.latent_skills}]);
        }

        // Add tool result as system message and loop
        const sysMsg = { role: 'system', content: `[Kết quả Tool]: ${JSON.stringify(toolData.result)}` };
        currentHist = [...currentHist, { role: 'assistant', content: data.reply }, sysMsg];
        currentText = "Vui lòng tiếp tục trả lời user dựa trên kết quả tool.";
        
        // Remove loading state from previous message
        setMessages(prev => prev.filter(m => !m.isToolLoading));
      } else {
        // Final reply
        setMessages(prev => {
           const clean = prev.filter(m => !m.isToolLoading);
           return [...clean, { role: 'assistant', content: data.reply, suggestions: data.suggested_questions }];
        });
        if (data.mcda_snapshot) setMcdaResult(data.mcda_snapshot);
        if (data.topic_context) setTopicContext(data.topic_context);
        break;
      }
    }
  };

  return (
    <div className="flex h-screen bg-slate-50 text-slate-900 font-sans">
      {/* Left Main Chat */}
      <div className="flex-1 flex flex-col max-w-4xl mx-auto border-r bg-white shadow-xl">
        <header className="h-16 flex items-center justify-between px-6 border-b bg-white/80 backdrop-blur-md sticky top-0 z-10">
          <div className="flex items-center gap-3">
            <div className="w-8 h-8 rounded-full bg-blue-600 flex items-center justify-center text-white">
              <Bot size={20} />
            </div>
            <div>
              <h1 className="font-bold text-lg">MatchSkill Advisor</h1>
              <p className="text-xs text-slate-500">AI-First DSS Framework</p>
            </div>
          </div>
          <Button variant="ghost" size="icon" onClick={() => setIsApiKeyOpen(true)}>
            <Settings size={20} />
          </Button>
        </header>

        <ScrollArea className="flex-1 p-6" ref={scrollRef}>
          <div className="flex flex-col gap-6">
            {messages.length === 0 && (
              <div className="text-center py-20 opacity-60">
                <Bot size={48} className="mx-auto mb-4 text-blue-500" />
                <h2 className="text-xl font-medium mb-2">Xin chào! Tôi là AI Advisor.</h2>
                <p>Hãy bắt đầu bằng cách mô tả kỹ năng của nhóm bạn, hoặc hỏi về một đề tài bất kỳ (vd: RAV-10).</p>
              </div>
            )}
            
            {messages.filter(m => m.role !== 'system').map((msg, i) => (
              <div key={i} className={`flex gap-4 ${msg.role === 'user' ? 'flex-row-reverse' : ''}`}>
                <Avatar className="w-10 h-10 border shadow-sm">
                  <AvatarFallback className={msg.role === 'user' ? 'bg-slate-800 text-white' : 'bg-blue-100 text-blue-700'}>
                    {msg.role === 'user' ? <User size={18} /> : <Bot size={18} />}
                  </AvatarFallback>
                </Avatar>
                <div className={`max-w-[80%] rounded-2xl px-5 py-3 shadow-sm ${
                  msg.role === 'user' 
                    ? 'bg-slate-800 text-white rounded-tr-none' 
                    : 'bg-white border rounded-tl-none text-slate-700'
                } ${msg.isToolLoading ? 'animate-pulse bg-blue-50 border-blue-200' : ''}`}>
                  <div className="whitespace-pre-wrap leading-relaxed">{msg.content}</div>
                  
                  {msg.suggestions?.length > 0 && (
                    <div className="flex flex-wrap gap-2 mt-4 pt-3 border-t border-slate-100">
                      {msg.suggestions.map((sug, idx) => (
                        <Badge 
                          key={idx} 
                          variant="secondary" 
                          className="cursor-pointer hover:bg-blue-100 px-3 py-1 text-xs font-normal"
                          onClick={() => handleSend(sug)}
                        >
                          {sug}
                        </Badge>
                      ))}
                    </div>
                  )}
                </div>
              </div>
            ))}
            {loading && (
              <div className="flex gap-4">
                <Avatar className="w-10 h-10 border bg-blue-100"><Bot size={18} className="text-blue-700 m-auto" /></Avatar>
                <div className="bg-slate-100 rounded-2xl rounded-tl-none px-5 py-4 w-20 flex gap-1 items-center">
                  <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce" />
                  <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce delay-75" />
                  <div className="w-2 h-2 rounded-full bg-slate-400 animate-bounce delay-150" />
                </div>
              </div>
            )}
          </div>
        </ScrollArea>

        <div className="p-4 bg-white border-t">
          <form 
            onSubmit={e => { e.preventDefault(); handleSend(); }}
            className="flex gap-2 p-1 bg-slate-100 rounded-full border shadow-inner focus-within:ring-2 focus-within:ring-blue-500/20 transition-all"
          >
            <Input 
              value={input}
              onChange={e => setInput(e.target.value)}
              placeholder="Hỏi về đề tài, phân tích kỹ năng, hoặc nhờ so sánh..." 
              className="flex-1 border-0 bg-transparent shadow-none focus-visible:ring-0 px-5"
            />
            <Button type="submit" disabled={!input.trim() || loading} className="rounded-full w-12 h-12 p-0 bg-blue-600 hover:bg-blue-700">
              <Send size={18} />
            </Button>
          </form>
        </div>
      </div>

      {/* Right Side Panel (Dynamic Widgets) */}
      <div className="w-[400px] bg-slate-50 p-6 overflow-y-auto hidden lg:block">
        <h2 className="font-bold text-slate-800 mb-6 flex items-center gap-2">
          <Cpu size={18} /> Dynamic Context
        </h2>

        {!mcdaResult && !topicContext && teamMembers.length === 0 && (
          <div className="text-sm text-slate-500 text-center py-10 border border-dashed rounded-xl">
            Panel sẽ hiển thị Dashboard, Biểu đồ Radar và Radar Matrix khi AI phân tích.
          </div>
        )}

        {mcdaResult && (
          <Card className="p-5 mb-6 shadow-md border-t-4 border-t-blue-500">
            <h3 className="font-bold text-sm text-slate-500 uppercase mb-4">Kết quả MCDA</h3>
            <div className="text-4xl font-black text-blue-600 mb-1">{mcdaResult.score || mcdaResult.finalScore}%</div>
            <div className="text-sm font-medium mb-4 text-slate-600">Trạng thái: <Badge>{mcdaResult.fit_state || mcdaResult.fitState}</Badge></div>
            
            {mcdaResult.risk_matrix && (
               <div className="grid grid-cols-2 gap-3 text-xs">
                 <div className="bg-slate-100 p-2 rounded">
                   <div className="text-slate-500">Skill Risk</div>
                   <div className="font-bold">{mcdaResult.risk_matrix.skill_risk}</div>
                 </div>
                 <div className="bg-slate-100 p-2 rounded">
                   <div className="text-slate-500">Time Risk</div>
                   <div className="font-bold">{mcdaResult.risk_matrix.time_risk}</div>
                 </div>
               </div>
            )}
          </Card>
        )}

        {topicContext && (
          <Card className="p-5 mb-6 shadow-md border-t-4 border-t-purple-500">
            <h3 className="font-bold text-sm text-slate-500 uppercase mb-3">Topic Constraints</h3>
            <ul className="text-sm space-y-2">
              {topicContext.constraints?.slice(0,3).map((c, i) => (
                <li key={i} className="flex gap-2 items-start"><ShieldAlert size={14} className="mt-1 text-amber-500 shrink-0"/> {c}</li>
              ))}
            </ul>
          </Card>
        )}
      </div>

      <ApiKeyModal isOpen={isApiKeyOpen} onClose={() => setIsApiKeyOpen(false)} onSave={(provider, key) => {
        setProvider(provider);
        setApiKey(key);
      }} currentKey={apiKey} />
    </div>
  );
}
