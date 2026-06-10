ROOT      := $(CURDIR)

ifeq ($(OS),Windows_NT)
PYTHON    := $(ROOT)/.venv/Scripts/python.exe
PIP       := $(ROOT)/.venv/Scripts/pip.exe
JUPYTER   := $(ROOT)/.venv/Scripts/jupyter.exe
UVICORN   := $(ROOT)/.venv/Scripts/uvicorn.exe
ENV       :=
VENV_PYTHON := python
else
PYTHON    := $(ROOT)/.venv/bin/python
PIP       := $(ROOT)/.venv/bin/pip
JUPYTER   := $(ROOT)/.venv/bin/jupyter
UVICORN   := $(ROOT)/.venv/bin/uvicorn
# Homebrew Python on macOS links pyexpat against its own expat, not the system one.
# Setting DYLD_LIBRARY_PATH makes the Homebrew expat visible to the dynamic linker.
EXPAT_LIB := /opt/homebrew/Cellar/expat/2.8.1/lib
ENV       := DYLD_LIBRARY_PATH=$(EXPAT_LIB)
VENV_PYTHON := /opt/homebrew/bin/python3.13
endif

.PHONY: install mcp-install chatbot support-bot support-cli jupyter claude-features mcp-chat mcp-inspect help

help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "  install       Create .venv and install all dependencies"
	@echo "  mcp-install   Sync the MCP_Learning uv environment"
	@echo "  chatbot       Run Claude Chatbot at http://localhost:8080"
	@echo "  support-bot   Run AI Support Bot web UI at http://localhost:8001"
	@echo "  support-cli   Run AI Support Bot in CLI mode"
	@echo "  jupyter         Start JupyterLab in the JupyterNotebook/ directory"
	@echo "  claude-features Start JupyterLab in the ClaudeFeatures/ directory"
	@echo "  mcp-chat        Run the MCP Chat CLI (MCP_Learning/)"
	@echo "  mcp-inspect     Launch the MCP Inspector against mcp_server.py"
	@echo ""

install: mcp-install
	$(ENV) $(VENV_PYTHON) -m venv .venv
	$(ENV) $(PYTHON) -m pip install --upgrade pip
	$(ENV) $(PYTHON) -m pip install -r requirements.txt
	$(ENV) $(PYTHON) -m ipykernel install --user --name ai-learning-venv \
		--display-name "Python (AI_Learning .venv)"
	@echo ""
	@echo "Done. Run 'make help' to see available commands."

# MCP_Learning manages its own venv via uv (pyproject.toml + uv.lock).
# VIRTUAL_ENV is cleared so uv targets MCP_Learning/.venv, not an activated root .venv.
mcp-install:
	cd $(ROOT)/MCP_Learning && VIRTUAL_ENV= uv sync

chatbot:
	cd $(ROOT)/Claude_Chatbot/backend && $(ENV) $(PYTHON) app.py --port 9000

support-bot:
	cd $(ROOT)/AI_Bot && $(ENV) $(UVICORN) backend.api:app --reload --port 9001

support-cli:
	cd $(ROOT)/AI_Bot && $(ENV) $(PYTHON) -m backend.main

jupyter:
	cd $(ROOT)/JupyterNotebook && $(ENV) $(JUPYTER) lab

claude-features:
	cd $(ROOT)/ClaudeFeatures && $(ENV) $(JUPYTER) lab

mcp-chat:
	cd $(ROOT)/MCP_Learning && $(ENV) VIRTUAL_ENV= uv run main.py

# Launch the MCP Inspector (web UI) against the server. Needs Node/npx on PATH.
# --with-editable . installs the project so the server's deps resolve.
mcp-inspect:
	cd $(ROOT)/MCP_Learning && $(ENV) VIRTUAL_ENV= uv run mcp dev mcp_server.py --with-editable .
