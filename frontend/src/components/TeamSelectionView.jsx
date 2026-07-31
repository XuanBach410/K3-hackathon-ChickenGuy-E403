import React, { useState, useEffect } from 'react';
import { Users, CheckCircle2, UserPlus, Save, Plus, Edit2, Trash2, X, PlusCircle } from 'lucide-react';
import { Card } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';

const LOCAL_STORAGE_KEY = 'matchskill_custom_profiles';

const DEFAULT_MOCK = [
  {
    id: 'mock1',
    name: 'Nguyễn Văn A',
    current_industry: 'Software Engineering',
    years_of_experience: 2,
    desired_roles: ['Backend Developer'],
    proficiency: { 'Python': 4, 'Django': 3, 'SQL': 4 }
  }
];

export default function TeamSelectionView({ onSaveTeam, currentTeam }) {
  const [profiles, setProfiles] = useState([]);
  const [selectedProfileIds, setSelectedProfileIds] = useState(
    currentTeam ? currentTeam.map(p => p.id || p.name) : []
  );

  // Modal State
  const [isModalOpen, setIsModalOpen] = useState(false);
  const [editingProfile, setEditingProfile] = useState(null);
  
  // Form State
  const [formData, setFormData] = useState({
    name: '',
    current_industry: '',
    years_of_experience: 0,
    desired_roles: '',
    skills: [{ name: '', score: 1 }]
  });

  useEffect(() => {
    const saved = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (saved) {
      setProfiles(JSON.parse(saved));
    } else {
      setProfiles(DEFAULT_MOCK);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(DEFAULT_MOCK));
    }
  }, []);

  const saveToStorage = (newProfiles) => {
    setProfiles(newProfiles);
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(newProfiles));
  };

  const toggleProfileSelection = (profileId) => {
    setSelectedProfileIds(prev => {
      if (prev.includes(profileId)) {
        return prev.filter(id => id !== profileId);
      }
      return [...prev, profileId];
    });
  };

  const handleSaveWorkspace = () => {
    if (onSaveTeam) {
      const selectedProfiles = profiles.filter(p => selectedProfileIds.includes(p.id));
      onSaveTeam(selectedProfiles);
    }
  };

  const openCreateModal = () => {
    setEditingProfile(null);
    setFormData({
      name: '', current_industry: '', years_of_experience: 0, desired_roles: '', skills: [{ name: '', score: 3 }]
    });
    setIsModalOpen(true);
  };

  const openEditModal = (e, profile) => {
    e.stopPropagation(); // Prevent toggling selection
    setEditingProfile(profile);
    const skillsList = Object.entries(profile.proficiency || {}).map(([name, score]) => ({ name, score }));
    setFormData({
      name: profile.name,
      current_industry: profile.current_industry || '',
      years_of_experience: profile.years_of_experience || 0,
      desired_roles: (profile.desired_roles || []).join(', '),
      skills: skillsList.length > 0 ? skillsList : [{ name: '', score: 3 }]
    });
    setIsModalOpen(true);
  };

  const handleDelete = (e, profileId) => {
    e.stopPropagation();
    if (confirm('Bạn có chắc chắn muốn xóa thành viên này?')) {
      const newProfiles = profiles.filter(p => p.id !== profileId);
      saveToStorage(newProfiles);
      setSelectedProfileIds(prev => prev.filter(id => id !== profileId));
    }
  };

  const handleModalSave = () => {
    if (!formData.name.trim()) {
      alert("Vui lòng nhập tên thành viên.");
      return;
    }

    const proficiency = {};
    formData.skills.forEach(s => {
      if (s.name.trim()) {
        proficiency[s.name.trim()] = parseInt(s.score, 10);
      }
    });

    const newProfileData = {
      id: editingProfile ? editingProfile.id : Date.now().toString(),
      name: formData.name.trim(),
      current_industry: formData.current_industry.trim(),
      years_of_experience: parseInt(formData.years_of_experience, 10) || 0,
      desired_roles: formData.desired_roles.split(',').map(r => r.trim()).filter(r => r),
      proficiency
    };

    let newProfiles;
    if (editingProfile) {
      newProfiles = profiles.map(p => p.id === editingProfile.id ? newProfileData : p);
    } else {
      newProfiles = [...profiles, newProfileData];
    }
    
    saveToStorage(newProfiles);
    
    // Auto select new member
    if (!editingProfile && !selectedProfileIds.includes(newProfileData.id)) {
        setSelectedProfileIds(prev => [...prev, newProfileData.id]);
    }
    setIsModalOpen(false);
  };

  const updateSkill = (index, field, value) => {
    const newSkills = [...formData.skills];
    newSkills[index][field] = value;
    setFormData({ ...formData, skills: newSkills });
  };

  const addSkillRow = () => {
    setFormData({ ...formData, skills: [...formData.skills, { name: '', score: 3 }] });
  };
  
  const removeSkillRow = (index) => {
    const newSkills = formData.skills.filter((_, i) => i !== index);
    setFormData({ ...formData, skills: newSkills });
  };

  return (
    <div className="max-w-5xl mx-auto flex flex-col gap-6">
      <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4">
        <div>
          <h2 className="text-xl font-bold text-slate-900 tracking-tight">
            <span className="aurora-text-gradient">Quản lý Thành viên Nhóm</span>
          </h2>
          <p className="text-sm text-slate-500">Tạo mới, chỉnh sửa và chọn thành viên để hệ thống phân tích</p>
        </div>
        <div className="flex items-center gap-3">
          <span className="text-sm font-medium text-slate-600">
            Đang chọn: <strong className="text-[#0080FF]">{selectedProfileIds.length}</strong> thành viên
          </span>
          <Button onClick={openCreateModal} variant="outline" className="border-[#0080FF] text-[#0080FF] hover:bg-[#0080FF]/10 cursor-pointer rounded-xl">
            <Plus size={16} className="mr-1" /> Thêm thành viên
          </Button>
          <Button onClick={handleSaveWorkspace} className="bg-gradient-to-r from-[#0080FF] via-[#7C3AED] to-[#FF1493] hover:opacity-95 text-white shadow-md shadow-blue-500/20 cursor-pointer font-semibold rounded-xl">
            <Save size={16} className="mr-2" /> Áp dụng nhóm
          </Button>
        </div>
      </div>
      
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {profiles.map((profile) => {
          const isSelected = selectedProfileIds.includes(profile.id);
          
          return (
            <Card 
              key={profile.id} 
              onClick={() => toggleProfileSelection(profile.id)}
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
                    {profile.name.charAt(0).toUpperCase()}
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
                  <div className="text-[10px] font-semibold text-slate-400 uppercase tracking-wider mb-1.5">Kỹ năng nổi bật (Score &ge; 3)</div>
                  <div className="flex flex-wrap gap-1">
                    {Object.entries(profile.proficiency || {})
                      .filter(([_, score]) => score >= 3)
                      .map(([skill, score], sIdx) => (
                        <Badge key={sIdx} variant="outline" className="text-[10px] border-[#0080FF]/30 text-[#0080FF] bg-[#0080FF]/5 font-semibold">
                          {skill}: {score}
                        </Badge>
                      ))}
                    {Object.keys(profile.proficiency || {}).length === 0 && (
                       <span className="text-xs text-slate-400">Chưa có kỹ năng</span>
                    )}
                  </div>
                </div>
              </div>
              
              {/* Action Buttons (Edit/Delete) */}
              <div className="mt-4 pt-3 border-t border-slate-100 flex justify-end gap-2">
                 <Button size="sm" variant="ghost" onClick={(e) => openEditModal(e, profile)} className="h-7 text-slate-500 hover:text-blue-600 px-2 cursor-pointer">
                    <Edit2 size={14} />
                 </Button>
                 <Button size="sm" variant="ghost" onClick={(e) => handleDelete(e, profile.id)} className="h-7 text-slate-500 hover:text-red-600 px-2 cursor-pointer">
                    <Trash2 size={14} />
                 </Button>
              </div>
            </Card>
          );
        })}
        {profiles.length === 0 && (
             <div className="col-span-full py-12 text-center text-slate-500 bg-white/50 rounded-xl border border-dashed border-slate-300">
                Chưa có thành viên nào. Hãy bấm "Thêm thành viên" để bắt đầu.
             </div>
        )}
      </div>

      {/* CREATE / EDIT MODAL */}
      {isModalOpen && (
        <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
          <Card className="w-full max-w-lg p-6 bg-white shadow-2xl animate-in fade-in zoom-in duration-200 max-h-[90vh] overflow-y-auto">
            <div className="flex justify-between items-center mb-6">
              <h3 className="text-lg font-bold text-slate-800">
                {editingProfile ? 'Sửa thông tin thành viên' : 'Thêm thành viên mới'}
              </h3>
              <Button variant="ghost" size="icon" onClick={() => setIsModalOpen(false)} className="h-8 w-8 rounded-full cursor-pointer">
                <X size={16} />
              </Button>
            </div>

            <div className="space-y-4">
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1">Tên thành viên (*)</label>
                <Input value={formData.name} onChange={e => setFormData({...formData, name: e.target.value})} placeholder="Nguyễn Văn A" className="bg-slate-50" />
              </div>
              <div className="grid grid-cols-2 gap-4">
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Chuyên ngành</label>
                  <Input value={formData.current_industry} onChange={e => setFormData({...formData, current_industry: e.target.value})} placeholder="IT / Kinh tế..." className="bg-slate-50" />
                </div>
                <div>
                  <label className="block text-xs font-bold text-slate-500 mb-1">Số năm kinh nghiệm</label>
                  <Input type="number" min="0" value={formData.years_of_experience} onChange={e => setFormData({...formData, years_of_experience: e.target.value})} className="bg-slate-50" />
                </div>
              </div>
              <div>
                <label className="block text-xs font-bold text-slate-500 mb-1">Vai trò mong muốn (cách nhau dấu phẩy)</label>
                <Input value={formData.desired_roles} onChange={e => setFormData({...formData, desired_roles: e.target.value})} placeholder="Backend, Data Analyst..." className="bg-slate-50" />
              </div>
              
              <div className="pt-2 border-t border-slate-100">
                 <div className="flex justify-between items-center mb-2">
                    <label className="block text-xs font-bold text-slate-500">Danh sách Kỹ năng (Tên - Mức độ 1: Cơ bản -&gt; 5: Chuyên gia)</label>
                    <Button type="button" variant="ghost" size="sm" onClick={addSkillRow} className="h-6 text-xs text-blue-600 px-2 cursor-pointer">
                        <PlusCircle size={14} className="mr-1" /> Thêm kỹ năng
                    </Button>
                 </div>
                 <div className="space-y-2">
                    {formData.skills.map((skill, idx) => (
                        <div key={idx} className="flex gap-2 items-center">
                            <Input value={skill.name} onChange={e => updateSkill(idx, 'name', e.target.value)} placeholder="Tên kỹ năng (VD: Python)" className="bg-slate-50 flex-1 h-9" />
                            <select value={skill.score} onChange={e => updateSkill(idx, 'score', e.target.value)} className="h-9 px-2 rounded-md border border-slate-200 bg-slate-50 text-slate-900 outline-none w-24">
                                <option value="1">1 - Biết</option>
                                <option value="2">2 - Cơ bản</option>
                                <option value="3">3 - Khá</option>
                                <option value="4">4 - Giỏi</option>
                                <option value="5">5 - Chuyên gia</option>
                            </select>
                            <Button type="button" variant="ghost" size="icon" onClick={() => removeSkillRow(idx)} className="h-9 w-9 text-slate-400 hover:text-red-600 cursor-pointer shrink-0">
                                <Trash2 size={14} />
                            </Button>
                        </div>
                    ))}
                    {formData.skills.length === 0 && (
                        <div className="text-xs text-slate-400 italic">Chưa có kỹ năng nào.</div>
                    )}
                 </div>
              </div>

            </div>

            <div className="flex gap-3 justify-end mt-8 pt-4 border-t border-slate-100">
              <Button variant="outline" onClick={() => setIsModalOpen(false)} className="cursor-pointer">
                Hủy
              </Button>
              <Button onClick={handleModalSave} className="bg-blue-600 hover:bg-blue-700 text-white cursor-pointer">
                Lưu thành viên
              </Button>
            </div>
          </Card>
        </div>
      )}
    </div>
  );
}
