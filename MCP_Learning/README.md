# MCP Chat

MCP Chat is a command-line interface application that enables interactive chat capabilities with AI models through the Anthropic API. The application supports document retrieval, command-based prompts, and extensible tool integrations via the MCP (Model Control Protocol) architecture.

## Prerequisites

- Python 3.9+
- Anthropic API Key

## Quick start (from the repo root)

This project is wired into the `AI_Learning` root `Makefile` and reads keys from
the single root `.env` (`AI_Learning/.env`) shared by all subprojects:

```bash
make mcp-install   # uv sync the MCP_Learning environment
make mcp-chat      # run the MCP Chat CLI
```

`make install` also runs `mcp-install` as part of the full setup.

## Setup

### Step 1: Configure the environment variables

Keys live in the **`AI_Learning/.env` at the repo root** (one level above this
directory) — not in `MCP_Learning/`. Copy `AI_Learning/.env.example` to
`AI_Learning/.env` and verify these variables are set:

```
ANTHROPIC_API_KEY=""              # Your Anthropic API secret key
CLAUDE_MODEL="claude-sonnet-4-6"  # Model id passed to the Claude service
USE_UV=1                          # Spawn the MCP server via `uv run` (1) or `python` (0)
```

### Step 2: Install dependencies

#### Option 1: Setup with uv (Recommended)

[uv](https://github.com/astral-sh/uv) is a fast Python package installer and resolver.

1. Install uv, if not already installed:

```bash
pip install uv
```

2. Create and activate a virtual environment:

```bash
uv venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

3. Install dependencies:

```bash
uv pip install -e .
```

4. Run the project

```bash
uv run main.py
```

#### Option 2: Setup without uv

1. Create and activate a virtual environment:

```bash
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
```

2. Install dependencies:

```bash
pip install anthropic python-dotenv prompt-toolkit "mcp[cli]==1.8.0"
```

3. Run the project

```bash
python main.py
```

## Usage

### Basic Interaction

Simply type your message and press Enter to chat with the model.

### Document Retrieval

Use the @ symbol followed by a document ID to include document content in your query:

```
> Tell me about @deposition.md
```

### Commands

Use the / prefix to execute commands defined in the MCP server:

```
> /summarize deposition.md
```

Commands will auto-complete when you press Tab.

## MCP Inspector

The [MCP Inspector](https://github.com/modelcontextprotocol/inspector) is a web UI
for exercising the server's tools, resources, and prompts directly — no Claude in
the loop. It ships with `mcp[cli]` and is launched via `mcp dev`.

**Prerequisite:** Node.js / `npx` on your PATH (the Inspector UI runs through npx).

From the repo root:

```bash
make mcp-inspect
```

Or directly from this directory:

```bash
uv run mcp dev mcp_server.py --with-editable .
```

This starts a proxy on `localhost:6277` and the Inspector UI on `localhost:6274`.
Open the printed URL (it includes a session token) in your browser, then use the
tabs to list/call `read_doc_contents` and `edit_document`, read the
`docs://documents` resources, and run the `format` prompt. Stop it with `Ctrl+C`.

## Development

### Adding New Documents

Edit the `mcp_server.py` file to add new documents to the `docs` dictionary.

### Implementing MCP Features

To fully implement the MCP features:

1. Complete the TODOs in `mcp_server.py`
2. Implement the missing functionality in `mcp_client.py`

### Linting and Typing Check

There are no lint or type checks implemented.
