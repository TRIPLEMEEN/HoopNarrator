# HoopNarrator 🏀🎙️

AI-Powered Basketball Clip Commentator

## Overview

HoopNarrator is an AI-powered platform that automatically generates exciting commentary for basketball clips. Upload any NBA highlight, choose your preferred commentary style, and get a personalized voiceover in seconds!

## Features

- **Video Analysis**: Automatically detects players, ball movement, and key events
- **Multiple Commentary Styles**: Choose from various personalities (Hype Beast, Analyst, Trash Talk, etc.)
- **AI-Generated Voiceovers**: Natural-sounding commentary in multiple voices
- **Social Media Ready**: Export in vertical format for TikTok, Instagram Reels, and more

## Tech Stack

- **Backend**: Python, FastAPI, OpenCV, YOLOv8, MediaPipe
- **AI**: OpenAI GPT-4, ElevenLabs TTS
- **Frontend**: React, TypeScript, Tailwind CSS
- **Video Processing**: FFmpeg, MoviePy

## Getting Started

### Prerequisites

- Python 3.9+
- Node.js 16+
- FFmpeg
- OpenAI API Key
- ElevenLabs API Key (optional)

### Backend Setup

1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/hoop-narrator.git
   cd hoop-narrator/backend
   ```

2. Create and activate a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file in the backend directory:
   ```env
   OPENAI_API_KEY=your_openai_api_key
   ELEVENLABS_API_KEY=your_elevenlabs_api_key
   SECRET_KEY=your_secret_key
   ```

5. Run the backend server:
   ```bash
   uvicorn app.main:app --reload
   ```

### Frontend Setup

1. Navigate to the frontend directory:
   ```bash
   cd ../frontend
   ```

2. Install dependencies:
   ```bash
   npm install
   ```

3. Create a `.env` file in the frontend directory:
   ```env
   VITE_API_URL=http://localhost:8000/api
   ```

4. Start the development server:
   ```bash
   npm run dev
   ```

5. Open your browser to `http://localhost:3000`

## API Documentation

Once the backend is running, you can access the interactive API documentation at:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## Project Structure

```
hoop-narrator/
├── backend/                  # Backend server
│   ├── app/
│   │   ├── api/              # API routes
│   │   ├── core/             # Core configuration
│   │   ├── models/           # Database models
│   │   ├── services/         # Business logic
│   │   └── utils/            # Utility functions
│   ├── tests/               # Backend tests
│   └── requirements.txt      # Python dependencies
├── frontend/                # Frontend application
│   ├── public/              # Static files
│   └── src/                 # Source code
│       ├── components/      # React components
│       ├── pages/           # Page components
│       ├── services/        # API services
│       └── styles/          # CSS/SCSS files
└── README.md               # This file
```

## Contributing

1. Fork the repository
2. Create a new branch: `git checkout -b feature/your-feature`
3. Commit your changes: `git commit -am 'Add some feature'`
4. Push to the branch: `git push origin feature/your-feature`
5. Open a pull request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- Thanks to the open-source community for the amazing tools and libraries that made this project possible.
- Inspired by the energy and excitement of basketball commentators worldwide.
