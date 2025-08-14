import axios from "axios";

// Log environment variables for debugging
console.log('Environment variables:', {
  VITE_API_URL: import.meta.env.VITE_API_URL,
  NODE_ENV: import.meta.env.NODE_ENV,
  MODE: import.meta.env.MODE
});

const API_BASE_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000/api/v1';
console.log('Using API base URL:', API_BASE_URL);

export interface ProcessVideoResponse {
  videoId: string;
  status: string;
  progress?: number;
  resultUrl?: string;
  error?: string;
}

export const processVideo = async (
  file: File | null | undefined,
  personality: string,
  onProgress?: (progress: number) => void
): Promise<ProcessVideoResponse> => {
  if (!file) {
    throw new Error('No file provided');
  }

  const formData = new FormData();
  formData.append('file', file);
  formData.append('personality', personality);

  try {
    const { data, status, headers } = await axios({
      method: 'post',
      url: `${API_BASE_URL}/videos/process`,
      data: formData,
      headers: {
        'Content-Type': 'multipart/form-data',
        'Accept': 'application/json'  // Explicitly ask for JSON
      },
      onUploadProgress: (progressEvent) => {
        if (progressEvent.total) {
          const progress = Math.round(
            (progressEvent.loaded * 100) / progressEvent.total
          );
          onProgress?.(progress);
        }
      },
      validateStatus: (status) => status < 500, // Don't throw on 4xx errors
    });

    console.log('Response status:', status);
    console.log('Response headers:', headers);
    console.log('Response data:', data);

    if (typeof data === 'string' && data.includes('<!DOCTYPE html>')) {
      console.error('Received HTML instead of JSON:', data.substring(0, 200));
      throw new Error('Server returned an HTML error page');
    }

    return data;
  } catch (error: any) {
    if (error.response) {
      console.error('Response error:', {
        status: error.response.status,
        headers: error.response.headers,
        data: error.response.data
      });
    } else if (error.request) {
      console.error('No response received:', error.request);
    } else {
      console.error('Error:', error.message);
    }
    throw error;
  }
};

export const checkJobStatus = async (jobId: string): Promise<ProcessVideoResponse> => {
  try {
    const response = await fetch(`${API_BASE_URL}/status/${jobId}`);
    
    if (!response.ok) {
      let errorMessage = `Failed to check job status (Status: ${response.status})`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorMessage;
      } catch (e) {
        console.error('Error parsing error response:', e);
      }
      throw new Error(errorMessage);
    }

    const data = await response.json();
    if (!data || typeof data !== 'object' || !data.jobId || !data.status) {
      console.error('Invalid job status response:', data);
      throw new Error('Invalid job status response from server');
    }
    
    return data;
  } catch (error) {
    console.error('Error checking job status:', error);
    throw error;
  }
};

export const processYoutubeVideo = async (
  youtubeUrl: string,
  personality: string
): Promise<ProcessVideoResponse> => {
  try {
    if (!youtubeUrl || !youtubeUrl.trim()) {
      throw new Error('YouTube URL is required');
    }

    const response = await fetch(`${API_BASE_URL}/process/youtube`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({
        url: youtubeUrl.trim(),
        personality,
      }),
    });

    if (!response.ok) {
      let errorMessage = `Failed to process YouTube video (Status: ${response.status})`;
      try {
        const errorData = await response.json();
        errorMessage = errorData.message || errorMessage;
      } catch (e) {
        console.error('Error parsing error response:', e);
      }
      throw new Error(errorMessage);
    }

    const responseText = await response.text();
    if (!responseText) {
      throw new Error('Empty response from server');
    }

    const data = JSON.parse(responseText) as ProcessVideoResponse;
    
    // Validate response has required fields
    if (!data || typeof data !== 'object' || !data.videoId || !data.status) {
      console.error('Invalid API response:', data);
      throw new Error('Invalid response format from server');
    }
    
    return data;
  } catch (error) {
    console.error('Error processing YouTube video:', error);
    throw error;
  }
};
