import { useState, useRef, useEffect } from 'react';
import { FiYoutube, FiLoader, FiAlertCircle, FiCheckCircle } from 'react-icons/fi';
import VideoUploader from '../components/VideoUploader';
import { processVideo, processYoutubeVideo, checkJobStatus } from '../services/api';
import type { ProcessVideoResponse } from '../services/api';

interface Personality {
  id: string;
  name: string;
  description: string;
}

const personalities: Personality[] = [
  { id: 'hype', name: 'Hype Beast', description: 'Energetic and over-the-top commentary' },
  { id: 'analyst', name: 'Analyst', description: 'Technical breakdown of plays' },
  { id: 'trash', name: 'Trash Talk', description: 'Funny and competitive banter' },
];

export default function Home() {
  const [videoFile, setVideoFile] = useState<File | null>(null);
  const [isProcessing, setIsProcessing] = useState(false);
  const [progress, setProgress] = useState(0);
  const [youtubeUrl, setYoutubeUrl] = useState('');
  const [selectedPersonality, setSelectedPersonality] = useState('hype');
  const [error, setError] = useState<string | null>(null);
  const [success, setSuccess] = useState<string | null>(null);
  const [resultUrl, setResultUrl] = useState<string | null>(null);
  const jobIdRef = useRef<string | null>(null);
  const pollIntervalRef = useRef<number | null>(null);

  const handleFileSelected = (file: File) => {
    setVideoFile(file);
  };

  const handleYoutubeSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    console.log('handleYoutubeSubmit called with URL:', youtubeUrl);
    
    if (!youtubeUrl) {
      const errorMsg = 'Please enter a YouTube URL';
      console.error(errorMsg);
      setError(errorMsg);
      return;
    }
    
    if (!selectedPersonality) {
      const errorMsg = 'Please select a commentator style';
      console.error(errorMsg);
      setError(errorMsg);
      return;
    }
    
    try {
      setError(null);
      setSuccess('Processing YouTube video...');
      setResultUrl(null);
      setIsProcessing(true);
      
      const response: ProcessVideoResponse = await processYoutubeVideo(youtubeUrl, selectedPersonality);
      
      if (!response?.videoId) {
        throw new Error('Invalid response from server');
      }
      
      jobIdRef.current = response.videoId;
      startPolling(response.videoId);
    } catch (err) {
      console.error('YouTube processing error:', err);
      setError(err instanceof Error ? err.message : 'Failed to process YouTube video');
      setIsProcessing(false);
      setProgress(0);
    }
  };

  const startPolling = (videoId: string) => {
    if (pollIntervalRef.current) {
      clearInterval(pollIntervalRef.current);
    }

    const poll = async () => {
      try {
        const status = await checkJobStatus(videoId);
        
        if (status.progress) {
          setProgress(status.progress);
        }

        if (status.status === 'completed' && status.resultUrl) {
          setResultUrl(status.resultUrl);
          setSuccess('Video processed successfully!');
          setIsProcessing(false);
          if (pollIntervalRef.current) {
            clearInterval(pollIntervalRef.current);
            pollIntervalRef.current = null;
          }
        } else if (status.status === 'failed') {
          throw new Error(status.error || 'Video processing failed');
        }
      } catch (err) {
        setError(err instanceof Error ? err.message : 'Error processing video');
        setIsProcessing(false);
        if (pollIntervalRef.current) {
          clearInterval(pollIntervalRef.current);
          pollIntervalRef.current = null;
        }
      }
    };

    // Initial poll
    poll();
    // Then poll every 5 seconds
    pollIntervalRef.current = window.setInterval(poll, 5000);
  };

  useEffect(() => {
    return () => {
      if (pollIntervalRef.current) {
        clearInterval(pollIntervalRef.current);
      }
    };
  }, []);

  const handleVideoProcessing = async (): Promise<ProcessVideoResponse | void> => {
    console.log('handleVideoProcessing called');
    
    if (!videoFile) {
      const errorMsg = 'Please select a video file';
      console.error(errorMsg);
      setError(errorMsg);
      return;
    }
    
    if (!selectedPersonality) {
      const errorMsg = 'Please select a commentator style';
      console.error(errorMsg);
      setError(errorMsg);
      return;
    }
    
    console.log('Starting video processing with file:', videoFile.name, 'and personality:', selectedPersonality);
    
    try {
      setError(null);
      setSuccess('Uploading video...');
      setResultUrl(null);
      setIsProcessing(true);
      
      const response: ProcessVideoResponse = await processVideo(videoFile, selectedPersonality, (progress) => {
        setProgress(progress);
      });
      
      if (!response?.videoId) {
        throw new Error('Invalid response from server');
      }
      
      jobIdRef.current = response.videoId;
      startPolling(response.videoId);
      return response;
    } catch (err) {
      console.error('Video processing error:', err);
      setError(err instanceof Error ? err.message : 'Failed to process video');
      setIsProcessing(false);
      setProgress(0);
      throw err; // Re-throw to be handled by the caller if needed
    }
  };

  return (
    <div className="min-h-screen bg-gray-50 py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-3xl mx-auto">
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Turn Your Basketball Clips into Epic Highlights
          </h1>
          <p className="text-lg text-gray-600">
            Upload your video or paste a YouTube link to add professional commentary
          </p>
        </div>

        <div className="bg-white rounded-xl shadow-lg p-6">
          {/* Error Message */}
          {error && (
            <div className="mb-6 p-4 bg-red-50 text-red-700 rounded-lg flex items-start">
              <FiAlertCircle className="flex-shrink-0 h-5 w-5 mt-0.5 mr-3" />
              <div>
                <p className="font-medium">Error</p>
                <p className="text-sm">{error}</p>
                <button
                  onClick={() => setError(null)}
                  className="mt-2 text-sm text-red-600 hover:text-red-800"
                >
                  Dismiss
                </button>
              </div>
            </div>
          )}

          {/* Success Message */}
          {success && (
            <div className="mb-6 p-4 bg-green-50 text-green-700 rounded-lg flex items-start">
              <FiCheckCircle className="flex-shrink-0 h-5 w-5 mt-0.5 mr-3" />
              <div>
                <p className="font-medium">Success</p>
                <p className="text-sm">{success}</p>
                {resultUrl && (
                  <a
                    href={resultUrl}
                    target="_blank"
                    rel="noopener noreferrer"
                    className="inline-block mt-2 px-4 py-2 bg-green-600 text-white text-sm font-medium rounded-md hover:bg-green-700"
                  >
                    Download Result
                  </a>
                )}
              </div>
            </div>
          )}
          <VideoUploader onFileSelected={handleFileSelected} />
          
          {videoFile && (
            <div className="mt-4 flex justify-between items-center">
              <span className="text-sm text-gray-600 truncate">
                {videoFile.name}
              </span>
              <button
                onClick={() => setVideoFile(null)}
                className="text-sm text-blue-600 hover:text-blue-800"
              >
                Change
              </button>
            </div>
          )}

          <div className="mt-8">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <div className="w-full border-t border-gray-200"></div>
              </div>
              <div className="relative flex justify-center text-sm">
                <span className="px-2 bg-white text-gray-500">Or</span>
              </div>
            </div>

            <form onSubmit={handleYoutubeSubmit} className="mt-6">
              <div className="flex">
                <input
                  type="text"
                  value={youtubeUrl}
                  onChange={(e) => setYoutubeUrl(e.target.value)}
                  placeholder="Paste YouTube URL"
                  className="flex-1 min-w-0 block w-full px-4 py-3 rounded-l-lg border border-gray-300 focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                />
                <button
                  type="submit"
                  disabled={!youtubeUrl}
                  className="inline-flex items-center px-6 py-3 border border-transparent text-sm font-medium rounded-r-lg text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500 disabled:opacity-50"
                >
                  Process
                </button>
              </div>
            </form>
          </div>

          <div className="mt-8">
            <h3 className="text-lg font-medium text-gray-900 mb-4">
              Select Commentator Style
            </h3>
            <div className="grid grid-cols-1 gap-4 sm:grid-cols-2">
              {personalities.map((personality) => (
                <div
                  key={personality.id}
                  onClick={() => setSelectedPersonality(personality.id)}
                  className={`p-4 border rounded-lg cursor-pointer transition-colors ${
                    selectedPersonality === personality.id
                      ? 'border-blue-500 bg-blue-50'
                      : 'border-gray-200 hover:border-gray-300'
                  }`}
                >
                  <h4 className="font-medium text-gray-900">{personality.name}</h4>
                  <p className="text-sm text-gray-500">{personality.description}</p>
                </div>
              ))}
            </div>
          </div>

          <div className="mt-8">
            <button
              onClick={() => handleVideoProcessing()}
              disabled={!videoFile || isProcessing}
              className={`mt-4 w-full py-3 px-6 rounded-lg font-bold transition-colors ${
                !videoFile || isProcessing
                  ? 'bg-gray-300 cursor-not-allowed'
                  : 'bg-blue-600 hover:bg-blue-700 text-white'
              }`}
            >
              {isProcessing ? (
                <>
                  <FiLoader className="animate-spin -ml-1 mr-3 h-5 w-5 text-white inline" />
                  Processing... ({progress}%)
                </>
              ) : (
                'Generate Commentary'
              )}
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
