SHELL := /bin/bash

include .env
export

echo-env:
	@echo LLM_PROVIDER=$$LLM_PROVIDER
	@echo LLM_MODEL=$$LLM_MODEL
	@echo LLM_MAX_TOKEN=$$LLM_MAX_TOKEN
	@echo AZURE_API_KEY=$$AZURE_API_KEY
	@echo AZURE_API_BASE=$$AZURE_API_BASE
	@echo AZURE_API_VERSION=$$AZURE_API_VERSION
	@echo OPENAI_API_KEY=$$OPENAI_API_KEY

test-litellm:
	python litellm_utils.py