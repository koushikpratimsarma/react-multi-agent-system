# Multi-Agent Research System

A simple AI system that uses multiple specialized agents to search for information, answer questions, and explore the web.

## What It Does

- **Supervisor Agent** - Main coordinator that directs questions to the right specialized agents
- **Research Agent** - Searches for research papers and academic content  
- **Web Agent** - Searches the general web for information
- **News Agent** - Finds latest news and current events
- **Arxiv Agent** - Searches academic papers on Arxiv

## How to Use

### Command Line
```
python main.py
```
Ask questions and the system will find answers using the right agents.

### Web Interface
```
uv run uvicorn api.main:app --reload
```
Open your browser and chat with the agents through the web interface.

## Requirements

- Python 3.10+
- PostgreSQL database
- API keys for: OpenAI, Tavily Search, Exa Search

## Setup

1. Clone the project
2. Create `.env` file with your API keys:
   ```
   OPENAI_API_KEY=your_key
   TAVILY_API_KEY=your_key
   EXA_API_KEY=your_key
   POSTGRES_URI=your_database_url
   ```
3. Install dependencies: `uv sync`
4. Run the system