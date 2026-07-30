import React from 'react';
import { Key, X, Check } from 'lucide-react';

export default function ApiKeyModal({ isOpen, onClose, provider, setProvider, apiKey, setApiKey, onSave }) {
  if (!isOpen) return null;

  return (
    <div style={{
      position: 'fixed', top: 0, left: 0, width: '100%', height: '100%',
      background: 'rgba(0,0,0,0.6)', zIndex: 9999, display: 'flex',
      alignItems: 'center', justifyContent: 'center'
    }}>
      <div style={{
        background: 'var(--surface-primary)', border: '1px solid var(--border-color)',
        borderRadius: 'var(--radius)', width: '90%', maxWidth: '480px', padding: '24px',
        boxShadow: 'var(--shadow-hover)'
      }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
          <h3 style={{ display: 'flex', alignItems: 'center', gap: '8px', fontSize: '1.1rem' }}>
            <Key size={18} color="var(--signal-red)" /> Cấu Hình LLM API Provider
          </h3>
          <button style={{ background: 'none', border: 'none', cursor: 'pointer' }} onClick={onClose}>
            <X size={18} />
          </button>
        </div>

        <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          Chọn AI Provider / Model
        </label>
        <select
          value={provider}
          onChange={(e) => setProvider(e.target.value)}
          style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)', marginBottom: '16px' }}
        >
          <option value="gemini">Google Gemini (gemini-3.6-flash / gemini-1.5-flash)</option>
          <option value="openai">OpenAI GPT (gpt-4o / gpt-4o-mini)</option>
        </select>

        <label style={{ display: 'block', fontSize: '12px', fontWeight: 600, textTransform: 'uppercase', color: 'var(--text-secondary)', marginBottom: '8px' }}>
          Nhập API Key
        </label>
        <input
          type="text"
          value={apiKey}
          onChange={(e) => setApiKey(e.target.value)}
          placeholder="AIzaSy... hoặc sk-..."
          className="mono"
          style={{ width: '100%', padding: '10px', borderRadius: '4px', border: '1px solid var(--border-color)', marginBottom: '8px' }}
        />
        <p style={{ fontSize: '12px', color: 'var(--text-secondary)', marginBottom: '20px' }}>
          * Key được lưu bảo mật trong LocalStorage. Nếu để rỗng, hệ thống sẽ sử dụng Rule-based Offline Engine.
        </p>

        <div style={{ display: 'flex', gap: '12px', justifyContent: 'flex-end' }}>
          <button
            onClick={onClose}
            style={{ padding: '8px 16px', background: 'var(--surface-primary)', border: '1px solid var(--border-color)', borderRadius: '4px', cursor: 'pointer' }}
          >
            Hủy
          </button>
          <button
            onClick={onSave}
            style={{ padding: '8px 16px', background: 'var(--signal-red)', color: '#FFF', border: 'none', borderRadius: '4px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: '6px', fontWeight: 600 }}
          >
            <Check size={16} /> OK / Lưu Key
          </button>
        </div>
      </div>
    </div>
  );
}
