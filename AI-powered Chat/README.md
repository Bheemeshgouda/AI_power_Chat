# 🎯 AI-Powered Chat Application for PowerPoint Generation

<div align="center">

![Version](https://img.shields.io/badge/version-1.0.0-blue.svg)
![Python](https://img.shields.io/badge/python-3.8+-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)

**Create stunning PowerPoint presentations through natural conversation with AI!**

[Quick Start](#-quick-start) • [Features](#-features) • [Documentation](#-documentation) • [Examples](#-examples)

</div>

---

## 🌟 Overview

This is a full-stack web application that combines the power of Google's Gemini AI with PowerPoint generation. Simply chat with the AI to create, edit, and download professional presentations—no design skills required!

### ✨ What Makes This Special?

- 🗣️ **Conversational Interface** - Just describe what you want in plain English
- 🤖 **AI-Powered** - Gemini AI understands context and generates relevant content
- ⚡ **Real-time Generation** - See your slides appear as they're created
- ✏️ **Easy Editing** - Modify slides by chatting, no complex tools needed
- 🎨 **AI-Generated Images** - Automatically finds and adds relevant photos (NEW!)
- 📥 **Instant Download** - Get your PowerPoint file with one click
- 🎨 **Beautiful UI** - Modern, responsive design that works on any device

---

## 🚀 Quick Start

### Prerequisites

- Python 3.8 or higher
- A free Gemini API key ([Get one here](https://makersuite.google.com/app/apikey))

### Installation (3 Easy Steps)

**1️⃣ Install Dependencies**
```powershell
pip install -r requirements.txt
```

**2️⃣ Add Your API Key**

Open `.env` file and add your Gemini API key:
```env
GEMINI_API_KEY=your_actual_api_key_here
```

**3️⃣ Run the App**
```powershell
python app.py
```

Then open **http://localhost:5000** in your browser!

## 🎯 Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| 💬 **Chat Interface** | Natural language interaction for creating presentations |
| 🤖 **Gemini AI** | Powered by Google's latest Gemini 2.0 Flash model |
| 📊 **Slide Preview** | See all slides in real-time before downloading |
| ✏️ **Edit Slides** | Modify content through simple chat commands |
| 🤖 **AI Images** | Automatically finds and adds relevant photos (no uploads!) |
| 📥 **Download PPT** | Export as standard PowerPoint .pptx format |
| 🎨 **Modern UI** | Beautiful, responsive design inspired by MagicSlides |
| 🔄 **Chat History** | Track your conversation and changes |
| 🌐 **Cross-Platform** | Works on Windows, Mac, and Linux |

### Technical Features

- **RESTful API** - Clean backend architecture
- **Real-time Updates** - Dynamic UI without page refreshes
- **Error Handling** - Graceful error messages and recovery
- **Responsive Design** - Mobile, tablet, and desktop support
- **Smooth Animations** - Professional UI/UX transitions
- **Secure** - API keys protected, input sanitization

---



### Creating Presentations

```
👤 You: "Create 5 slides about Artificial Intelligence in Education"

🤖 AI: Generates slides with titles and content:
   1. Introduction to AI in Education
   2. Benefits of AI for Students
   3. AI-Powered Learning Tools
   4. Challenges and Concerns
   5. Future of AI in Education
```

### Adding Images

```
👤 You: "Create travel presentation about Paris with images"

🤖 AI: Generates slides with automatically fetched images:
   - Searches Unsplash for relevant photos
   - Downloads and embeds images automatically
   - No manual uploads needed!
   
Slides include:
   1. Paris Overview (Eiffel Tower image)
   2. Famous Landmarks (Louvre Museum)
   3. French Cuisine (croissants and cafe)
   4. Culture & Arts (street art)
   5. Travel Tips (Paris metro)
```

### Editing Slides

```
👤 You: "Edit slide 2: change the title to 'How AI Helps Students'"

🤖 AI: Updates slide 2 with new title

👤 You: "Add a point about personalized learning to slide 2"

🤖 AI: Adds new bullet point to slide 2
```



---

## 🛠️ Tech Stack

### Backend
- **Python 3.8+** - Core language
- **Flask** - Web framework
- **Google Generative AI** - Gemini API integration
- **python-dotenv** - Environment management

### Frontend
- **HTML5** - Structure
- **CSS3** - Styling with custom variables
- **Bootstrap 5** - UI framework
- **JavaScript (ES6+)** - Interactive functionality
- **PptxGenJS** - PowerPoint generation library

### AI Model
- **Gemini 2.0 Flash** - Fast, efficient content generation
- **JSON Response Format** - Structured slide data

---

## 📁 Project Structure

```
AI-powered Chat/
│
├── 📄 app.py                    # Flask backend server
├── 📄 requirements.txt          # Python dependencies
├── 📄 .env                      # Environment variables (API keys)
├── 📄 .env.example              # Example environment file
├── 📄 .gitignore                # Git ignore rules
│
├── 📁 templates/
│   └── 📄 index.html            # Main chat interface
│
├── 📁 static/
│   ├── 📁 css/
│   │   └── 📄 style.css         # Custom styles
│   └── 📁 js/
│       └── 📄 app.js            # Frontend logic
│
├── 📄 README.md                 # This file
├── 📄 QUICK_START.md           # Quick reference guide
├── 📄 SETUP_GUIDE.md           # Detailed setup instructions
├── 📄 PROJECT_DOCS.md          # Technical documentation
├── 📄 EXAMPLES.md              # Usage examples
└── 📄 start.ps1                # Quick start script
```



## 🔧 Configuration

### Environment Variables

Create a `.env` file with:

```env
GEMINI_API_KEY=AIzaSyAJiW4gBQYziFS7QK9ylEuvRRBuklALCFU
FLASK_ENV=development
FLASK_DEBUG=True
```

### Customization

- **Theme Colors**: Edit `static/css/style.css` CSS variables
- **AI Prompts**: Modify system prompts in `app.py`
- **UI Layout**: Adjust `templates/index.html`


