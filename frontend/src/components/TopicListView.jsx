import React, { useState, useEffect } from 'react';
import { BookOpen, Users, ArrowRight, Search } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function TopicListView({ onSelectTopic }) {
  const [topics, setTopics] = useState([]);
  const [loading, setLoading] = useState(true);
  const [searchTerm, setSearchTerm] = useState('');

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

  const filteredTopics = topics.filter(t => 
    t.title.toLowerCase().includes(searchTerm.toLowerCase()) || 
    t.code.toLowerCase().includes(searchTerm.toLowerCase())
  );

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
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900">Danh sách đề tài dự án</h2>
          <p className="text-sm text-slate-500">Tìm kiếm và khám phá các đề tài phù hợp với kỹ năng của nhóm</p>
        </div>
        <div className="relative">
          <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400" size={16} />
          <input
            type="text"
            placeholder="Tìm kiếm đề tài, mã..."
            value={searchTerm}
            onChange={(e) => setSearchTerm(e.target.value)}
            className="pl-9 pr-4 py-2 border border-slate-200 rounded-lg text-sm w-full sm:w-64 focus:outline-none focus:ring-2 focus:ring-violet-500/20 focus:border-violet-400 transition-all"
          />
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {filteredTopics.map((topic, idx) => (
          <Card key={idx} className="p-5 flex flex-col border-slate-200 bg-white hover:border-violet-300 hover:shadow-md transition-all">
            <div className="flex justify-between items-start mb-2">
              <Badge variant="outline" className="bg-violet-50 text-violet-700 border-violet-200 text-xs">
                {topic.code}
              </Badge>
              <Badge variant="secondary" className="text-[10px] flex items-center gap-1 bg-slate-100 text-slate-600">
                <Users size={12} /> Tối đa {topic.max_team || 2} người
              </Badge>
            </div>
            <h3 className="font-bold text-slate-800 text-base mb-2 line-clamp-2" title={topic.title}>{topic.title}</h3>
            
            <p className="text-slate-500 text-xs line-clamp-3 mb-4 flex-1 whitespace-pre-wrap">
              {topic.description}
            </p>
            
            <div className="mt-auto border-t border-slate-100 pt-3 flex items-center justify-between">
              <span className="text-[11px] text-slate-400 font-medium flex items-center gap-1 truncate max-w-[70%]">
                <BookOpen size={12} className="shrink-0" /> {topic.category}
              </span>
              <button 
                onClick={() => onSelectTopic && onSelectTopic(topic)}
                className="text-[11px] font-semibold text-violet-600 hover:text-violet-700 flex items-center gap-1 transition-colors px-2 py-1 rounded-md hover:bg-violet-50 cursor-pointer"
              >
                Phân tích <ArrowRight size={12} />
              </button>
            </div>
          </Card>
        ))}
        {filteredTopics.length === 0 && (
          <div className="col-span-1 md:col-span-2 text-center py-12 text-slate-500 text-sm">
            Không tìm thấy đề tài nào phù hợp.
          </div>
        )}
      </div>
    </div>
  );
}
