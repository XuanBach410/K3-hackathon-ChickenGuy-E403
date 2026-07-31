import React, { useState, useEffect, useMemo } from 'react';
import { BookOpen, Users, ArrowRight, Search, Filter } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function TopicListView({ onSelectTopic }) {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');
  const [selectedCategory, setSelectedCategory] = useState('');

  useEffect(() => {
    fetch(`${API_BASE}/topics/`)
      .then(res => res.json())
      .then(data => {
        setTopics(data.topics || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Lỗi khi tải danh sách đề tài:", err);
        setLoading(false);
      });
  }, []);

  const categories = useMemo(() => {
    const cats = new Set();
    topics.forEach(t => {
      if (t.category) cats.add(t.category);
    });
    return Array.from(cats).sort();
  }, [topics]);

  const filteredTopics = topics.filter(t => {
    const matchesSearch = t.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
                          t.code.toLowerCase().includes(searchTerm.toLowerCase());
    const matchesCategory = selectedCategory ? t.category === selectedCategory : true;
    return matchesSearch && matchesCategory;
  });

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-8 h-8 rounded-full bg-violet-400 mb-4" />
          <div className="text-slate-500 font-medium text-sm">Đang tải danh sách đề tài...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="flex flex-col md:flex-row md:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight flex items-center gap-2">
            <span className="aurora-text-gradient">Danh sách đề tài dự án</span>
          </h2>
          <p className="text-sm text-slate-500">Tìm kiếm và lọc đề tài phù hợp ({filteredTopics.length} kết quả)</p>
        </div>
        <div className="flex flex-col sm:flex-row gap-3">
          <div className="relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <input
              type="text"
              placeholder="Tìm kiếm tên, mã..."
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
              className="pl-9 pr-4 py-2 border border-slate-200/80 rounded-xl text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-[#0080FF]/30 focus:border-[#0080FF] bg-white/80 backdrop-blur-sm transition-all"
            />
          </div>
          <div className="relative">
            <Filter className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="pl-9 pr-4 py-2 border border-slate-200/80 rounded-xl text-sm w-full sm:w-48 focus:outline-none focus:ring-2 focus:ring-[#0080FF]/30 focus:border-[#0080FF] bg-white/80 backdrop-blur-sm transition-all appearance-none"
            >
              <option value="">Tất cả chuyên ngành</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredTopics.map((topic, idx) => (
          <Card key={idx} className="p-5 flex flex-col border-slate-200/80 bg-white/90 backdrop-blur-sm aurora-card-hover rounded-xl shadow-sm hover:border-[#0080FF]/40 transition-all">
            <div className="flex justify-between items-start mb-2">
              <Badge variant="outline" className="bg-[#0080FF]/10 text-[#0080FF] border-[#0080FF]/30 text-xs font-semibold">
                {topic.code}
              </Badge>
              <Badge variant="secondary" className="text-[10px] flex items-center gap-1 bg-slate-100/80 text-slate-600 font-medium">
                <Users size={12} /> Tối đa {topic.max_team || 2} người
              </Badge>
            </div>
            <h3 className="font-bold text-slate-800 text-base mb-2 line-clamp-2" title={topic.title}>{topic.title}</h3>
            
            <p className="text-slate-500 text-xs line-clamp-3 mb-4 flex-1 whitespace-pre-wrap leading-relaxed">
              {topic.description}
            </p>
            
            <div className="mt-auto border-t border-slate-100 pt-3 flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1 truncate max-w-[65%]">
                <BookOpen size={12} className="shrink-0 text-[#0080FF]" /> {topic.category}
              </span>
              <button 
                onClick={() => onSelectTopic && onSelectTopic(topic)}
                className="text-[11px] font-semibold text-white bg-gradient-to-r from-[#0080FF] to-[#7C3AED] hover:from-[#0060DF] hover:to-[#6D28D9] shadow-sm flex items-center gap-1.5 transition-all px-3 py-1.5 rounded-lg cursor-pointer active:scale-95"
              >
                Phân tích <ArrowRight size={12} />
              </button>
            </div>
          </Card>
        ))}
        {filteredTopics.length === 0 && (
          <div className="col-span-1 md:col-span-2 text-center py-12 text-slate-500 text-sm bg-white/50 rounded-xl border border-dashed border-slate-300">
            Không tìm thấy đề tài nào phù hợp với bộ lọc.
          </div>
        )}
      </div>
    </div>
  );
}
