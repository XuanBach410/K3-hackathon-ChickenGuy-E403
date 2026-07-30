import React, { useState } from 'react';
import { Key, X, Check } from 'lucide-react';
import { Button } from './ui/button';
import { Input } from './ui/input';
export default function ApiKeyModal({ isOpen, onClose, currentKey, onSave }) {
  const [provider, setProvider] = useState(localStorage.getItem('matchskill_provider') || 'gemini');
  const [apiKey, setApiKey] = useState(currentKey || '');

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-slate-900/60 backdrop-blur-sm z-50 flex items-center justify-center p-4">
      <div className="w-full max-w-md p-6 bg-white rounded-xl shadow-2xl animate-in fade-in zoom-in duration-200">
        <div className="flex justify-between items-center mb-6">
          <h3 className="flex items-center gap-2 text-lg font-bold text-slate-800">
            <Key size={18} className="text-blue-600" /> Cấu Hình LLM API Provider
          </h3>
          <Button variant="ghost" size="icon" onClick={onClose} className="h-8 w-8 rounded-full">
            <X size={16} />
          </Button>
        </div>

        <div className="space-y-4">
          <div>
            <label className="block text-xs font-bold uppercase text-slate-500 mb-2">
              Chọn AI Provider / Model
            </label>
            <select
              value={provider}
              onChange={(e) => setProvider(e.target.value)}
              className="w-full p-2.5 rounded-md border border-slate-200 bg-slate-50 text-slate-900 focus:ring-2 focus:ring-blue-500 outline-none"
            >
              <option value="gemini">Google Gemini (gemini-1.5-flash / pro)</option>
              <option value="openai">OpenAI GPT (gpt-4o / gpt-4o-mini)</option>
            </select>
          </div>

          <div>
            <label className="block text-xs font-bold uppercase text-slate-500 mb-2">
              Nhập API Key
            </label>
            <Input
              type="text"
              value={apiKey}
              onChange={(e) => setApiKey(e.target.value)}
              placeholder="AIzaSy... hoặc sk-proj-..."
              className="font-mono bg-slate-50"
            />
            <p className="text-xs text-slate-500 mt-2">
              * Key được lưu bảo mật trong LocalStorage. Nếu để rỗng, hệ thống sẽ sử dụng Rule-based Offline Engine.
            </p>
          </div>
        </div>

        <div className="flex gap-3 justify-end mt-8 pt-4 border-t border-slate-100">
          <Button variant="outline" onClick={onClose}>
            Hủy
          </Button>
          <Button 
            onClick={() => onSave(provider, apiKey)}
            className="bg-blue-600 hover:bg-blue-700 text-white flex items-center gap-2"
          >
            <Check size={16} /> OK / Lưu Key
          </Button>
        </div>
      </div>
    </div>
  );
}
