ROOT      := $(CURDIR)
PYTHON    := $(ROOT)/.venv/bin/python
PIP       := $(ROOT)/.venv/bin/pip
JUPYTER   := $(ROOT)/.venv/bin/jupyter
UVICORN   := $(ROOT)/.venv/bin/uvicorn
# Homebrew Python on macOS links pyexpat against its own expat, not the system one.
# Setting DYLD_LIBRARY_PATH makes the Homebrew expat visible to the dynamic linker.
EXPAT_LIB := /opt/homebrew/Cellar/expat/2.8.1/lib
ENV       := DYLD_LIBRARY_PATH=$(EXPAT_LIB)

.PHONY: install chatbot support-bot support-cli jupyter help

help:
	@echo ""
	@echo "Usage: make <target>"
	@echo ""
	@echo "  install       Create .venv and install all dependencies"
	@echo "  chatbot       Run Claude Chatbot at http://localhost:8080"
	@echo "  support-bot   Run AI Support Bot web UI at http://localhost:8001"
	@echo "  support-cli   Run AI Support Bot in CLI mode"
	@echo "  jupyter       Start JupyterLab in the JupyterNotebook/ directory"
	@echo ""

install:
	$(ENV) /opt/homebrew/bin/python3.13 -m venv .venv
	$(ENV) $(PIP) install --upgrade pip
	$(ENV) $(PIP) install -r requirements.txt
	$(ENV) $(PYTHON) -m ipykernel install --user --name ai-learning-venv \
		--display-name "Python (AI_Learning .venv)"
	@echo ""
	@echo "Done. Run 'make help' to see available commands."

chatbot:
	cd $(ROOT)/Claude_Chatbot/backend && $(ENV) $(PYTHON) app.py

support-bot:
	cd $(ROOT)/AI_Support_Bot && $(ENV) $(UVICORN) backend.api:app --reload --port 8001

support-cli:
	cd $(ROOT)/AI_Support_Bot && $(ENV) $(PYTHON) -m backend.main

jupyter:
	cd $(ROOT)/JupyterNotebook && $(ENV) $(JUPYTER) lab
