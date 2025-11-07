import React, { useCallback } from 'react';

interface FileUploadAreaProps {
  isDragOver: boolean;
  fileInputRef: React.RefObject<HTMLInputElement>;
  onFileSelect: (file: File) => void;
}

export const FileUploadArea: React.FC<FileUploadAreaProps> = ({
  isDragOver,
  fileInputRef,
  onFileSelect,
}) => {
  const handleDragOver = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDragLeave = useCallback((e: React.DragEvent) => {
    e.preventDefault();
  }, []);

  const handleDrop = useCallback(
    (e: React.DragEvent) => {
      e.preventDefault();
      const files = Array.from(e.dataTransfer.files);
      if (files.length > 0) {
        onFileSelect(files[0]);
      }
    },
    [onFileSelect]
  );

  const handleFileInputChange = useCallback(
    (e: React.ChangeEvent<HTMLInputElement>) => {
      const files = e.target.files;
      if (files && files.length > 0) {
        onFileSelect(files[0]);
      }
    },
    [onFileSelect]
  );

  return (
    <div
      className={`upload-area ${isDragOver ? 'drag-over' : ''}`}
      onDragOver={handleDragOver}
      onDragLeave={handleDragLeave}
      onDrop={handleDrop}
      onClick={() => fileInputRef.current?.click()}
    >
      <div className="upload-icon">📄</div>
      <div className="upload-text">PPTXファイルをドラッグ&ドロップ</div>
      <div className="upload-subtext">またはクリックしてファイルを選択</div>
      <input
        ref={fileInputRef}
        type="file"
        accept=".pptx"
        className="file-input"
        onChange={handleFileInputChange}
      />
    </div>
  );
};
