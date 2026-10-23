# VerityWrite AI ✍️

**VerityWrite AI** is an AI-powered writing assistant that transforms robotic or AI-generated text into natural, readable, human-like writing while preserving the original meaning and important facts.

## 🌐 Live Demo

**Try the application here:** https://veritywrite-ai.onrender.com

## 🚀 Features

- **AI Text Humanization:** Rewrites text into natural, fluent language.
- **FactLock:** Helps preserve important facts, names, dates, and numbers.
- **Tone and Domain Selection:** Adapts writing style to different purposes.
- **Naturalness Detection:** Checks whether text may benefit from rewriting.
- **Fact and Meaning Verification:** Helps identify changes in meaning or important details.
- **Voice Input:** Supports voice-based text entry.
- **Screenshot Input:** Supports extracting or processing text from screenshots.
- **Readability Analysis:** Compares readability before and after rewriting.
- **Text-to-Speech:** Converts text into audio.
- **Export Options:** Supports exporting results for further use.

*Feature availability depends on the deployed application's configuration.*

## 🛠️ Tech Stack

- Python
- Streamlit
- Google Gemini API
- Natural Language Processing (NLP)
- Pandas
- gTTS
- OCR and speech-to-text components

## ⚙️ Installation and Setup

### 1. Clone the repository

```bash
git clone https://github.com/snehithareddy867/VerityWrite-AI.git
cd VerityWrite-AI
```

### 2. Create a virtual environment

```bash
python -m venv .venv
```

Activate it on Windows:

```powershell
.venv\Scripts\Activate.ps1
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Configure environment variables

Create a `.env` file if your project uses environment variables, and add the API key using the variable name expected by your code.

Never commit API keys or other secrets to GitHub.

### 5. Run the application

```bash
streamlit run app.py
```

The application will display a local URL in your terminal, usually `http://localhost:8501`.

## 🎯 Project Objective

The objective of VerityWrite AI is to improve the naturalness and readability of written content while helping preserve its original facts and meaning. It combines AI-powered rewriting with verification and readability tools to support clearer communication.

## 👥 Intended Users

- Students
- Content writers
- Professionals
- HR recruiters
- Researchers
- Digital marketers

## 🔗 Links

- **Live Application:** https://veritywrite-ai.onrender.com
- **GitHub Repository:** https://github.com/snehithareddy867/VerityWrite-AI

## 👩‍💻 Author

Developed as an AI-powered writing assistant project.
