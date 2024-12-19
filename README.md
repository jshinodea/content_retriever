# Content Retriever

An AI-powered content webscraping agent that integrates with custom CMS systems. The agent can gather content from specified URLs, search the web for additional information, and generate content using advanced language models.

## Features

- Natural language command interface
- Web scraping with authentication support
- Web search capabilities
- Content generation using LLMs
- Interactive dialogue system
- Image recognition for content fields
- Structured data output and storage

## Prerequisites

- Python 3.9+
- Docker
- GPU support (for deployment)
- Tavily API key
- Hugging Face access token

## Installation

1. Clone the repository:
```bash
git clone https://github.com/jshinodea/content_retriever.git
cd content_retriever
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Set up environment variables:
Create a `.env` file with:
```
TAVILY_API_KEY=your_tavily_key
HF_ACCESS_TOKEN=your_huggingface_token
```

## Usage

1. Start the application:
```bash
python src/main.py
```

2. Access the UI at `http://localhost:8000`

3. Enter your content gathering specifications and URL in the input box

4. Interact with the agent through the dialogue box

5. Review and confirm the gathered content table

## Docker Deployment

1. Build the container:
```bash
docker build -t content-retriever .
```

2. Run on vast.ai:
- Select a GPU instance on vast.ai
- Pull and run the container:
```bash
docker run -p 8000:8000 --env-file .env content-retriever
```

## Development

- Run tests: `pytest`
- Format code: `black . && isort .`
- Type checking: `mypy .`

## License

MIT License 