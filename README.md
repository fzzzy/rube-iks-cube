# rube-iks-cube

## Setup Instructions

### 1. Environment Setup

Make sure uv is installed.

First, copy the environment template and configure your API keys:

```bash
cp .env.template .env
```

### 2. Get Your Composio API Key

1. Visit [https://app.composio.dev/](https://app.composio.dev/)
2. Sign up or log in to your account
3. Go to **Settings > API Keys**
4. Copy your API key

### 3. Configure Environment Variables

Edit the `.env` file and add your API key:

```bash
nano .env  # or use your preferred editor
```

Update the `COMPOSIO_API_KEY` value with your actual key.

### 4. Run

```bash
./run.sh
```