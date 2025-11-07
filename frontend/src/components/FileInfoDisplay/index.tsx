import React from 'react';
import { FileInfo } from '../../types';

interface FileInfoDisplayProps {
  file: File;
  fileInfo: FileInfo | null;
}

export const FileInfoDisplay: React.FC<FileInfoDisplayProps> = ({ file, fileInfo }) => {
  return (
    <div className="file-info">
      <h3>選択されたファイル</h3>
      <p>
        <strong>ファイル名:</strong> {file.name}
      </p>
      <p>
        <strong>ファイルサイズ:</strong> {(file.size / 1024 / 1024).toFixed(1)} MB
      </p>
      {fileInfo && (
        <>
          <p>
            <strong>ページ数:</strong> {fileInfo.pages} ページ
          </p>
          <p>
            <strong>翻訳対象テキスト数:</strong> {fileInfo.textCount} 個
          </p>
        </>
      )}
    </div>
  );
};
