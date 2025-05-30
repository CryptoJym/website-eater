# 🌐 Website Eater

An AI-powered URL digestion tool that uses Google Gemini to extract and analyze content from YouTube videos, GitHub repositories, and any webpage.

## ✨ Features

- **🎬 YouTube Video Analysis**: Extract transcripts, summaries, and key insights from YouTube videos
- **💻 GitHub Repository Analysis**: Analyze code repositories, documentation, and project structure
- **📰 Webpage Content Extraction**: Digest articles, blogs, documentation, and any public webpage
- **🧠 AI-Powered Understanding**: Uses Google Gemini 2.5 Pro for intelligent content analysis
- **💾 Memory Storage**: Creates searchable memories from extracted content
- **🎯 Smart Routing**: Automatically categorizes content (video, code, documentation, etc.)
- **🌐 Web Interface**: Clean, modern UI for easy URL submission and result viewing
- **🐛 Bug Report Integration**: Drop Loom videos for bug reports with automatic transcription
- **💬 Feedback System**: Submit context, feedback, and additional information to AI database

## 🚀 Quick Start

### Prerequisites

- Python 3.8+
- Google Cloud account with billing enabled
- Google Gemini API key

### Installation

1. Clone the repository:
```bash
git clone https://github.com/CryptoJym/website-eater.git
cd website-eater
```

2. Set up the backend:
```bash
cd backend
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements.txt
```

3. Configure your API key:
```bash
# Copy the template
cp .env.template .env

# Edit .env and add your Google API key
# GOOGLE_API_KEY=your-api-key-here
```

4. Start the server:
```bash
cd ..
./restart_server.sh
```

5. Open your browser to http://localhost:5003

## 🔑 Getting a Google Gemini API Key

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create or select a project
3. Enable billing for the project
4. Navigate to APIs & Services → Credentials
5. Click "+ CREATE CREDENTIALS" → "API key"
6. Enable the Generative Language API
7. Copy your API key (starts with `AIza...`)

**Note**: Make sure you create an API key, not an OAuth client or service account key!

## 📖 Usage

### Web Interface

1. Open http://localhost:5003 in your browser
2. Paste any URL in the input field:
   - YouTube videos: `https://www.youtube.com/watch?v=...`
   - GitHub repos: `https://github.com/owner/repo`
   - Any webpage: `https://example.com/article`
3. Click "Digest URL"
4. View the extracted content and analysis

### API Endpoint

```bash
curl -X POST http://localhost:5003/api/digest \
  -H "Content-Type: application/json" \
  -d '{"url": "https://www.youtube.com/watch?v=dQw4w9WgXcQ"}'
```

### Python Example

```python
import requests

response = requests.post('http://localhost:5003/api/digest', 
                        json={'url': 'https://github.com/google/gemini'})
                        
data = response.json()
print(f"Title: {data['title']}")
print(f"Content Type: {data['content_type']}")
print(f"Analysis: {data['analysis']}")
```

### Feedback & Bug Reports

The bottom section of the interface allows you to submit:

- **Loom Videos**: Automatically detects and processes Loom URLs for bug reports
- **General Feedback**: Feature requests, ideas, or any context
- **Bug Reports**: Detailed descriptions with optional video evidence

Example:
```
https://www.loom.com/share/abc123...
Bug: The submit button doesn't work when...
```

All feedback is automatically:
- Processed by Gemini AI
- Categorized (bug_report, feature_request, etc.)
- Routed to appropriate destinations (bug_tracker, development_backlog)
- Stored in the knowledge base for future reference

## 🏗️ Architecture

```
website-eater/
├── backend/
│   ├── app_url_digestion.py    # Main Flask application
│   ├── requirements.txt         # Python dependencies
│   └── .env                    # Configuration (git-ignored)
├── frontend/                   # Frontend assets (if any)
├── restart_server.sh          # Server restart script
├── update_api_key.py         # API key updater utility
└── README.md                 # This file
```

## 🛠️ Configuration

Edit `backend/.env` to configure:

- `GOOGLE_API_KEY`: Your Gemini API key
- `GEMINI_MODEL`: Model to use (default: gemini-2.5-pro-preview-03-25)
- `USER_ID`: User identifier for memory storage
- `AGENT_ID`: Agent identifier

## 🔧 Troubleshooting

### "API quota exceeded" error
- Check your Google Cloud billing is enabled
- Use the preview model for higher quotas: `gemini-2.5-pro-preview-03-25`
- Wait a few minutes if you hit rate limits

### "Wrong credential type" error
- Make sure you created an API key, not OAuth or Service Account credentials
- API keys start with `AIza...`

### Server won't start
- Check if port 5003 is already in use
- Ensure Python virtual environment is activated
- Check logs for specific error messages

## 📝 API Response Format

```json
{
  "status": "success",
  "url": "https://example.com",
  "title": "Extracted Title",
  "content_type": "article|video|code|documentation",
  "memory_id": "mem_abc123",
  "content_length": 1234,
  "analysis": "Full content analysis...",
  "url_accessed": true,
  "routes": [
    {"destination": "knowledge_base"}
  ]
}
```

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🙏 Acknowledgments

- Built with [Google Gemini](https://ai.google.dev/)
- Flask web framework
- Modern web technologies

## 🔒 Security

- Never commit your `.env` file or API keys
- Keep your API keys secure and rotate them regularly
- Use environment variables for sensitive configuration

## 📧 Support

For issues, questions, or contributions, please open an issue on GitHub.

---

**Happy URL Digesting! 🌐🍽️**
**Key documentation for the May 20 2025 Gemini API update**

| Area                   | Doc / Notebook                                                             | What it covers                                                                                                       |
| ---------------------- | -------------------------------------------------------------------------- | -------------------------------------------------------------------------------------------------------------------- |
| **Official reference** | *Gemini API – URL context tool* ([Google AI for Developers][1])            | Parameters, limits (20 URLs/request, quota), usage examples, and best-practice notes for the new `url_context` tool. |
|                        | *Gemini API – Release notes (May 20 2025)* ([Google AI for Developers][2]) | Full changelog—including URL context, multi-tool calls, async Live API, and video-frame controls.                    |
|                        | *Gemini API reference* (root) ([Google AI for Developers][3])              | Updated method and type definitions for SDK v1.0, including `Tool(url_context={})`.                                  |
| **Hands-on examples**  | *Cookbook – “Browser as a tool”* notebook ([GitHub][4])                    | Three worked examples showing URL context alongside code-execution and Google-Search grounding.                      |
|                        | *Quickstart – “Get started”* notebook ([Google Colab][5])                  | Minimal Colab that installs `google-genai`, enables URL context, and runs a compare-two-sites demo.                  |
| **Open-source repo**   | *google-gemini/cookbook* (GitHub) ([GitHub][6])                            | All quickstarts + Apache-2.0 code kept in sync with the docs.                                                        |

These links take you straight to the authoritative pages and example notebooks so you can dive into the new URL-context feature, review the full API surface, and copy/paste runnable samples.

[1]: https://ai.google.dev/gemini-api/docs/url-context?utm_source=chatgpt.com "URL context | Gemini API | Google AI for Developers"
[2]: https://ai.google.dev/gemini-api/docs/changelog?utm_source=chatgpt.com "Release notes | Gemini API | Google AI for Developers"
[3]: https://ai.google.dev/api?utm_source=chatgpt.com "Gemini API reference | Google AI for Developers"
[4]: https://github.com/google-gemini/cookbook/blob/main/examples/Browser_as_a_tool.ipynb?utm_source=chatgpt.com "Browser_as_a_tool.ipynb - google-gemini/cookbook - GitHub"
[5]: https://colab.research.google.com/github/google-gemini/cookbook/blob/main/quickstarts/Get_started.ipynb?utm_source=chatgpt.com "Gemini API: Getting started with Gemini models - Colab - Google"
[6]: https://github.com/google-gemini/cookbook?utm_source=chatgpt.com "Welcome to the Gemini API Cookbook - GitHub"
