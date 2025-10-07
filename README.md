# Any LLM Code Review

A model-agnostic LLM code reviewer for GitHub using [pydantic-ai](https://ai.pydantic.dev/). Unlike other code review tools that lock you into a single AI provider, this tool supports **any model provider** that pydantic-ai supports.

## Supported Model Providers

- **OpenAI** (GPT-4, GPT-3.5, etc.) ✅ Full support
- **Anthropic** (Claude 3.5 Sonnet, Claude 3 Opus, etc.) ✅ Full support
- **Google Gemini** (Gemini 2.0 Flash, Gemini 1.5 Pro, etc.) ✅ Full support
- **Groq** (Llama, Mixtral, etc.) ✅ Full support
- **Mistral** (Mistral Large, etc.) ✅ Full support
- **Hugging Face** (Qwen, Llama, DeepSeek, and thousands more) ⚠️ Large models only (70B+)
- **Cohere** ✅ Full support
- **AWS Bedrock** ✅ Full support
- **Google Vertex AI** ✅ Full support
- **Ollama** (Local/self-hosted models) ✅ Full support

## Features

- 🤖 **Model Agnostic**: Use any AI provider you prefer
- 🔒 **Your API Keys**: Bring your own API keys - full control over costs and usage
- 📊 **Structured Reviews**: Categorized feedback with severity levels (error, warning, info)
- 🎯 **Smart Filtering**: Configurable file patterns and size limits
- 💬 **Inline Comments**: Posts review comments directly on PR diffs
- 📝 **Detailed Analysis**: Checks for bugs, security issues, performance, and best practices

## Known Limitations

### Hugging Face Models

Due to structured output requirements, **only large models (70B+ parameters) work with HuggingFace Inference API**:

✅ **Works:**
- `Qwen/Qwen2.5-72B-Instruct`
- `meta-llama/Llama-3.3-70B-Instruct`
- `mistralai/Mixtral-8x7B-Instruct-v0.1`

❌ **Doesn't work:**
- Smaller models like `Qwen2.5-Coder-7B`, `Llama-3.1-8B`, etc.
- Error: `UNSUPPORTED_OPENAI_PARAMS: tools`

**Recommended alternatives for smaller/faster models:**
- **Gemini 2.0 Flash Lite** - Fast, free tier, excellent quality
- **Groq** - Very fast inference, free tier available
- **OpenAI GPT-4o-mini** - Affordable, reliable

## Quick Start

### 1. Add to Your Repository

Create a workflow file `.github/workflows/ai-code-review.yml`:

```yaml
name: AI Code Review

on:
  pull_request:
    types: [opened, synchronize, reopened]

jobs:
  ai-review:
    runs-on: ubuntu-latest
    permissions:
      pull-requests: write
      contents: read

    steps:
      - name: Checkout code
        uses: actions/checkout@v4

      - name: AI Code Review
        uses: GlobeTrotte-com/any-llm-code-review@v1
        with:
          model_provider: 'openai'
          model_name: 'gpt-4'
          api_key: ${{ secrets.OPENAI_API_KEY }}
          github_token: ${{ secrets.GITHUB_TOKEN }}
```

### 2. Configure Secrets

Add your API key to GitHub Secrets:
- Go to your repository settings
- Navigate to Secrets and variables → Actions
- Add a new secret (e.g., `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`, etc.)

### 3. Open a Pull Request

The action will automatically review your code and post comments!

## Configuration Options

| Input | Description | Required | Default |
|-------|-------------|----------|---------|
| `model_provider` | AI provider (openai, anthropic, gemini, groq, mistral, ollama) | Yes | - |
| `model_name` | Specific model (e.g., gpt-4, claude-3-5-sonnet-20241022) | Yes | - |
| `api_key` | API key for the provider | No* | - |
| `github_token` | GitHub token for API access | Yes | `${{ github.token }}` |
| `base_url` | Custom API endpoint (useful for Ollama) | No | - |
| `max_tokens` | Maximum tokens for response | No | 4000 |
| `temperature` | Model temperature (0.0-1.0) | No | 0.3 |
| `ignore_patterns` | Comma-separated file patterns to ignore | No | `*.md,*.txt,*.json,*.yaml,*.yml,package-lock.json,yarn.lock,poetry.lock` |
| `max_file_size` | Maximum file size in characters | No | 10000 |
| `custom_prompt` | Custom system prompt for code reviewer | No | - |
| `review_title` | Title for the review comment | No | AI Code Review |
| `always_pass` | Always pass (exit 0) regardless of review outcome | No | false |

*Not required for Ollama (self-hosted)

## Usage Examples

### OpenAI GPT-4

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'openai'
    model_name: 'gpt-4'
    api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Anthropic Claude

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'anthropic'
    model_name: 'claude-3-5-sonnet-20241022'
    api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Google Gemini

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'gemini'
    model_name: 'gemini-1.5-pro'
    api_key: ${{ secrets.GEMINI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Groq (Fast Inference)

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'groq'
    model_name: 'llama-3.1-70b-versatile'
    api_key: ${{ secrets.GROQ_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Ollama (Self-hosted)

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'ollama'
    model_name: 'llama3.1'
    base_url: 'http://localhost:11434'
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

### Hugging Face (Thousands of Models)

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'huggingface'
    model_name: 'Qwen/Qwen2.5-72B-Instruct'  # or meta-llama/Llama-3.3-70B-Instruct
    api_key: ${{ secrets.HF_TOKEN }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
```

Popular Hugging Face models (with tool calling support):
- `Qwen/Qwen2.5-72B-Instruct` - High quality, supports structured output
- `meta-llama/Llama-3.3-70B-Instruct` - Meta's latest with tool support
- `mistralai/Mixtral-8x7B-Instruct-v0.1` - Fast MoE with tools

**⚠️ Important Limitation:**
- **Small models (<30B parameters) on HuggingFace Inference API don't support structured outputs**
- This includes popular models like `Qwen2.5-Coder-7B` or `Llama-3.1-8B`
- Use **larger 70B+ models** on HuggingFace, OR
- Use **Gemini 2.0 Flash** (fast, free, works great with small parameter count)

### Always Pass Mode

Prevent the action from failing when changes are requested (useful for informational reviews):

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'openai'
    model_name: 'gpt-4'
    api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    always_pass: 'true'  # Action will never fail
```

### Custom Configuration

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'openai'
    model_name: 'gpt-4'
    api_key: ${{ secrets.OPENAI_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    temperature: '0.2'
    max_tokens: '8000'
    ignore_patterns: '*.md,*.txt,test/**,*.lock'
    max_file_size: '15000'
```

### Custom Review Prompts

Customize the review focus and title:

```yaml
- uses: GlobeTrotte-com/any-llm-code-review@v1
  with:
    model_provider: 'anthropic'
    model_name: 'claude-3-5-sonnet-20241022'
    api_key: ${{ secrets.ANTHROPIC_API_KEY }}
    github_token: ${{ secrets.GITHUB_TOKEN }}
    review_title: 'Claude Security Review'  # Custom title
    custom_prompt: |
      You are a senior security engineer reviewing code for vulnerabilities.
      Focus ONLY on security issues:
      - SQL injection, XSS, CSRF
      - Authentication/authorization flaws
      - Secrets in code

      Categorize as error/warning/info and approve only if no issues found.
```

## Local Development

### Setup with uv

```bash
# Install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

# Create virtual environment
uv venv

# Activate virtual environment
source .venv/bin/activate  # On Unix
# or
.venv\Scripts\activate  # On Windows

# Install dependencies
uv pip install -r requirements.txt
```

### Run Locally

```bash
export MODEL_PROVIDER=openai
export MODEL_NAME=gpt-4
export API_KEY=your-api-key
export GITHUB_TOKEN=your-github-token
export GITHUB_REPOSITORY=owner/repo
export GITHUB_REF=refs/pull/123/merge

python -m any-llm-code-review.main review-from-env
```

Or use the CLI directly:

```bash
python -m any-llm-code-review.main review \
  --provider openai \
  --model gpt-4 \
  --api-key your-api-key \
  --github-token your-github-token \
  --repository owner/repo \
  --pr-number 123
```

## How It Works

1. **Fetch Changes**: Retrieves the diff for all files in the pull request
2. **Filter Files**: Applies ignore patterns and size limits
3. **AI Analysis**: Sends code changes to your chosen AI model using pydantic-ai
4. **Structured Review**: AI returns categorized feedback with severity levels
5. **Post Comments**: Posts inline comments and overall review on GitHub

## Review Categories

The AI reviews code for:

- **Bugs & Logic Errors**: Potential runtime errors, logic flaws
- **Security Vulnerabilities**: SQL injection, XSS, exposed secrets
- **Performance Issues**: Inefficient algorithms, memory leaks
- **Code Quality**: Best practices, readability, maintainability
- **Edge Cases**: Unhandled scenarios, null checks
- **Testing**: Missing test coverage, test quality

## Severity Levels

- 🚨 **error**: Critical issues that must be fixed
- ⚠️ **warning**: Important issues that should be addressed
- 💡 **info**: Suggestions and minor improvements

## Why Model Agnostic?

Different teams have different preferences and requirements:

- **Cost**: Some models are cheaper than others
- **Privacy**: Self-hosted Ollama for sensitive code
- **Speed**: Groq for fast inference
- **Quality**: Claude or GPT-4 for complex analysis
- **Compliance**: Specific providers required by organization

This tool lets you choose what works best for your team.
