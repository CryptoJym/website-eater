# Google URL Context Tool - Quick Start Guide

## What is Google's URL Context Tool?

Google's URL Context tool is a new feature in the Gemini API that allows you to:
- Extract content directly from URLs without writing scrapers
- Process up to 20 URLs in a single API call
- Combine with Google Search for comprehensive analysis
- Access web content through Google's infrastructure

## Getting Started

### 1. Get a Google API Key

Visit https://makersuite.google.com/app/apikey to create your API key.

### 2. Install Dependencies

```bash
pip install google-genai python-dotenv
```

### 3. Basic Usage

```python
from google import genai
from google.genai.types import Tool, GenerateContentConfig

# Initialize client
client = genai.Client(api_key="YOUR_API_KEY")

# Create URL Context tool
tools = [Tool(url_context={})]

# Extract content from a URL
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-05-20",
    contents="Summarize this article: https://example.com/article",
    config=GenerateContentConfig(
        tools=tools,
        response_modalities=["TEXT"],
    )
)

# Print the result
for part in response.candidates[0].content.parts:
    print(part.text)
```

## Advanced Features

### Combine with Google Search

```python
# Use both URL Context and Google Search
tools = [
    Tool(url_context={}),
    Tool(google_search={})
]

response = client.models.generate_content(
    model="gemini-2.5-flash-preview-05-20",
    contents="""
    Research current AI trends and compare with this article:
    https://example.com/ai-2025-predictions
    """,
    config=GenerateContentConfig(tools=tools)
)
```

### Process Multiple URLs

```python
# Compare multiple sources
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-05-20",
    contents="""
    Compare these three articles about climate change:
    1. https://example1.com/climate-article
    2. https://example2.com/climate-research
    3. https://example3.com/climate-opinion
    
    What are the main agreements and disagreements?
    """,
    config=GenerateContentConfig(tools=[Tool(url_context={})])
)
```

### Extract Specific Information

```python
# Extract structured data
response = client.models.generate_content(
    model="gemini-2.5-flash-preview-05-20",
    contents="""
    From this product page: https://example.com/product
    
    Extract:
    - Product name
    - Price
    - Key features (as bullet points)
    - Customer rating
    - Availability
    """,
    config=GenerateContentConfig(tools=[Tool(url_context={})])
)
```

## Use Cases

1. **Content Summarization**: Quickly summarize articles, blog posts, or documentation
2. **Competitive Analysis**: Compare multiple product pages or company websites
3. **Research Assistant**: Gather information from multiple sources on a topic
4. **Data Extraction**: Pull structured data from web pages
5. **Content Monitoring**: Track changes or updates to specific pages
6. **Fact Checking**: Verify information across multiple sources

## Limitations & Quotas

- **URLs per request**: Maximum 20
- **Daily quotas**: 
  - API: 1,500 requests per day per project
  - Google AI Studio: 100 requests per day per user
- **Content types**: Best with standard web pages (HTML)
- **Cost**: Free during experimental phase

## Integration with Website Eater

The Website Eater system uses this tool to:
1. Extract content from any URL you provide
2. Process it with AI to classify and understand the content
3. Store it in mem0 memory for future reference
4. Route it to appropriate systems based on content type

## Tips for Best Results

1. **Be specific in prompts**: Tell Gemini exactly what to extract
2. **Use deep analysis**: Combine with Google Search for context
3. **Handle failures gracefully**: Some sites may block access
4. **Respect rate limits**: Monitor your daily usage
5. **Process in batches**: Use the 20 URL limit efficiently

## Troubleshooting

### Common Issues:

**"URL_RETRIEVAL_STATUS_FAILED"**
- The website may be blocking automated access
- Try a different URL or check if the site is accessible

**Empty responses**
- The content might be behind a login wall
- The site might use heavy JavaScript rendering

**Quota exceeded**
- Check your usage at https://console.cloud.google.com
- Consider upgrading your plan or optimizing requests

## Example Projects

1. **News Aggregator**: Collect and summarize news from multiple sources
2. **Price Monitor**: Track product prices across e-commerce sites
3. **Documentation Compiler**: Gather API docs from various sources
4. **Research Tool**: Compile information on topics from authoritative sources
5. **Content Curator**: Build collections of relevant content on specific topics

## Next Steps

1. Try the simple examples in `simple_example.py`
2. Run the full Website Eater system with `python app.py`
3. Explore the CLI with `python cli.py --help`
4. Build your own applications using the URL Context tool

## Resources

- [Official Documentation](https://ai.google.dev/gemini-api/docs/url-context)
- [Gemini API Reference](https://ai.google.dev/api/rest)
- [Google AI Studio](https://makersuite.google.com)
- [This Project on GitHub](https://github.com/yourusername/website-eater)
