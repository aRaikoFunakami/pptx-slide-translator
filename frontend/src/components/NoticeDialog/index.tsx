import React from 'react';

interface NoticeDialogProps {
  html: string;
  onClose: () => void;
}

/**
 * 運用告知用モーダルダイアログ
 * - 外部 (public/) に配置した静的HTMLを読み込んで表示
 * - 文字列は信頼済み想定のため dangerouslySetInnerHTML を使用
 */
export const NoticeDialog: React.FC<NoticeDialogProps> = ({ html, onClose }) => {
  return (
    <div style={overlayStyle} role="dialog" aria-modal="true" aria-label="お知らせ">
      <div style={dialogStyle} className="notice-dialog">
        <div style={headerStyle} className="notice-dialog-header">
          <h2 style={{margin: 0, fontSize: '18px'}}>お知らせ</h2>
          <button onClick={onClose} style={closeButtonStyle} aria-label="閉じる">×</button>
        </div>
        <div
          className="notice-dialog-content"
          style={contentStyle}
          dangerouslySetInnerHTML={{ __html: html }}
        />
        <div style={footerStyle} className="notice-dialog-footer">
          <button onClick={onClose} style={primaryButtonStyle}>閉じる</button>
        </div>
      </div>
    </div>
  );
};

// Inline styles (既存CSSが少ないため簡易実装)
const overlayStyle: React.CSSProperties = {
  position: 'fixed',
  inset: 0,
  background: 'rgba(0,0,0,0.45)',
  display: 'flex',
  alignItems: 'flex-start',
  justifyContent: 'center',
  padding: '60px 16px 40px',
  zIndex: 9999,
};

const dialogStyle: React.CSSProperties = {
  background: '#fff',
  width: '100%',
  maxWidth: '720px',
  borderRadius: '10px',
  boxShadow: '0 4px 16px rgba(0,0,0,0.25)',
  display: 'flex',
  flexDirection: 'column',
  overflow: 'hidden',
  fontFamily: 'system-ui, sans-serif'
};

const headerStyle: React.CSSProperties = {
  display: 'flex',
  alignItems: 'center',
  justifyContent: 'space-between',
  padding: '14px 18px',
  borderBottom: '1px solid #e5e5e5',
  background: '#f8f9fa'
};

const closeButtonStyle: React.CSSProperties = {
  border: 'none',
  background: 'transparent',
  fontSize: '20px',
  cursor: 'pointer',
  lineHeight: 1,
  padding: '4px 8px'
};

const contentStyle: React.CSSProperties = {
  padding: '20px 24px',
  maxHeight: '60vh',
  overflowY: 'auto',
  fontSize: '14px',
  lineHeight: 1.6
};

const footerStyle: React.CSSProperties = {
  padding: '12px 18px',
  borderTop: '1px solid #e5e5e5',
  display: 'flex',
  justifyContent: 'flex-end',
  background: '#f8f9fa'
};

const primaryButtonStyle: React.CSSProperties = {
  background: '#2563eb',
  color: '#fff',
  border: 'none',
  padding: '8px 20px',
  fontSize: '14px',
  borderRadius: '6px',
  cursor: 'pointer'
};
