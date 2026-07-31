import React, { useState, useEffect } from 'react';
import { Users, CheckCircle2, UserPlus, Save } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';

const API_BASE = import.meta.env.VITE_API_BASE || 'http://localhost:8000/api';

export default function TeamSelectionView({ onSaveTeam, currentTeam }) {
  const [profiles, setProfiles] = useState([]);
  const [loading, setLoading] = useState(true);
  const [selectedProfiles, setSelectedProfiles] = useState(currentTeam || []);

  useEffect(() => {
    fetch(`${API_BASE}/profiles/`)
      .then(res => res.json())
      .then(data => {
        setProfiles(data.profiles || []);
        setLoading(false);
      })
      .catch(err => {
        console.error("Lỗi tải mock profiles:", err);
        setLoading(false);
      });
  }, []);

  const toggleProfile = (profile) => {
    setSelectedProfiles(prev => {
      const isSelected = prev.some(p => p.name === profile.name);
      if (isSelected) {
        return prev.filter(p => p.name !== profile.name);
      } else {
        return [...prev, profile];
      }
    });
  };

  const handleSave = () => {
    if (onSaveTeam) {
      onSaveTeam(selectedProfiles);
    }
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full py-12">
        <div className="animate-pulse flex flex-col items-center">
          <div className="w-8 h-8 rounded-full bg-violet-400 mb-4" />
          <div className="text-slate-500 font-medium text-sm">Đang tải mock data...</div>
        </div>
      </div>
    );
  }

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            <span className="aurora-text-gradient">Thiết lập & Kỹ năng nhóm</span>
          </h2>
          <p className="text-sm text-slate-500">Chọn thành viên từ mock data để mô phỏng nhóm của bạn</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-600">
            Đã chọn: <strong className="text-[#0080FF]">{selectedProfiles.length}</strong> thành viên
          </span>
          <Button onClick={handleSave} className="bg-gradient-to-r from-[#0080FF] via-[#7C3AED] to-[#FF1493] hover:opacity-95 text-white shadow-md shadow-blue-500/20 cursor-pointer font-semibold rounded-xl">
            <Save size={16} className="mr-2" /> Lưu & Quay lại
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {profiles.map((profile, idx) => {
          const isSelected = selectedProfiles.some(p => p.name === profile.name);
          
          return (
            <Card 
              key={idx} 
              onClick={() => toggleProfile(profile)}
              className={`p-5 flex flex-col cursor-pointer aurora-card-hover rounded-xl transition-all ${
                isSelected 
                  ? 'border-[#0080FF] bg-gradient-to-br from-[#0080FF]/10 via-[#FF1493]/5 to-transparent shadow-md ring-2 ring-[#0080FF]/40' 
                  : 'border-slate-200/80 bg-white/90 backdrop-blur-sm hover:border-[#0080FF]/40 hover:shadow-sm'
              }`}
            >
              <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                  <div className={`w-10 h-10 rounded-xl flex items-center justify-center text-white font-bold text-sm shrink-0 shadow-sm ${
                    isSelected ? 'aurora-mesh aurora-glow-primary' : 'bg-slate-300'
                  }`}>
                    {profile.name.charAt(0)}
                  </div>
                  <div>
                    <h3 className="font-bold text-slate-800 text-sm leading-tight">{profile.name}</h3>
                    <p className="text-[11px] text-slate-500">{profile.current_industry} • {profile.years_of_experience} năm KN</p>
                  </div>
                </div>
                {isSelected ? (
                  <CheckCircle2 size={20} className="text-[#0080FF] shrink-0" />
                ) : (
                  <UserPlus size={20} className="text-slate-300 shrink-0" />
                )}
              </div>
              
              <div className="flex-1 space-y-3">
                <div>
                  <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Vai trò mong muốn</div>
                  <div className="flex flex-wrap gap-1">
                    {profile.desired_roles?.map((role, rIdx) => (
                      <Badge key={rIdx} variant="secondary" className="text-[9px] bg-slate-100/90 text-slate-600 font-medium">
                        {role}
                      </Badge>
                    ))}
                  </div>
                </div>
                
                <div>
                  <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Kỹ năng nổi bật (Score &gt; 3)</div>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(profile.proficiency || {})
                      .filter(([_, score]) => score > 3)
                      .map(([skill, score], sIdx) => (
                        <Badge key={sIdx} variant="outline" className="text-[9px] border-[#0080FF]/30 text-[#0080FF] bg-[#0080FF]/10 font-semibold">
                          {skill}: {score}
                        </Badge>
                      ))}
                  </div>
                </div>
              </div>
            </Card>
          );
        })}
      </div>
    </div>
  );
}
