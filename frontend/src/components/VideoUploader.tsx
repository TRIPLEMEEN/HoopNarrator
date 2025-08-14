import { useCallback, useState } from 'react';
import { useDropzone } from 'react-dropzone';
import { FiUpload } from 'react-icons/fi';

interface VideoUploaderProps {
  onFileSelected: (file: File) => void;
}

export default function VideoUploader({ onFileSelected }: VideoUploaderProps) {
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);

  const onDrop = useCallback((acceptedFiles: File[]) => {
    const file = acceptedFiles[0];
    if (file && file.type.startsWith('video/')) {
      onFileSelected(file);
      setPreviewUrl(URL.createObjectURL(file));
    }
  }, [onFileSelected]);

  const { getRootProps, getInputProps, isDragActive } = useDropzone({
    onDrop,
    accept: { 'video/*': ['.mp4', '.webm', '.mov'] },
    maxFiles: 1,
    multiple: false
  });

  if (previewUrl) {
    return (
      <div className="aspect-video bg-black rounded-lg overflow-hidden">
        <video
          src={previewUrl}
          controls
          className="w-full h-full object-contain"
        />
      </div>
    );
  }

  return (
    <div 
      {...getRootProps()}
      className={`border-2 border-dashed rounded-lg p-12 text-center cursor-pointer transition-colors ${
        isDragActive ? 'border-blue-500 bg-blue-50' : 'border-gray-300 hover:border-blue-300'
      }`}
    >
      <input {...getInputProps()} />
      <div className="space-y-2">
        <FiUpload className="mx-auto h-12 w-12 text-gray-400" />
        <p className="text-lg font-medium">Drag and drop your video here</p>
        <p className="text-sm text-gray-500">or click to browse files (MP4, WebM, or MOV)</p>
      </div>
    </div>
  );
}
