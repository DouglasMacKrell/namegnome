# LLM Features & Usage Guide

> This guide explains how to use NameGnome's LLM-powered features for fuzzy matching,
> anthology splitting, and advanced media file renaming. It covers model installation,
> model selection, confidence thresholds, caching, and troubleshooting.

---

## 1 · Introduction

NameGnome leverages local LLMs (via Ollama) to assist with ambiguous or complex
media file renaming tasks. LLMs help with anthology episode splitting, fuzzy title
guessing, and manual override workflows.

---

## 2 · Model Installation (Ollama)

NameGnome requires a local Ollama server for LLM features. To install Ollama:

```sh
curl -fsSL https://ollama.com/install.sh | sh
ollama run deepseek-coder-instruct:1.5b
```

See [Ollama documentation](https://ollama.com/) for platform-specific details.

---

## 3 · Listing Available Models

To list all installed LLM models:

```sh
namegnome llm list
```

---

## 4 · Selecting and Setting Default Model

You can specify the LLM model for a scan using the `--llm-model` flag. You must also specify at least one media type (tv, movie, or music):

```sh
namegnome scan /path/to/media --media-type tv --llm-model deepseek-coder-instruct:1.5b
```

To set a default model for all future runs:

```sh
namegnome llm set-default deepseek-coder-instruct:1.5b
```

**Note:** The --media-type option is required for all scan commands. NameGnome will not scan unless you specify at least one media type.

---

## 5 · Confidence Threshold & Manual Flag

LLM responses include a confidence score. If the score is below the threshold
(default: 0.7), the item is flagged as manual and requires user review.

- Adjust the threshold via the `NGN_LLM_THRESHOLD` environment variable.
- Manual items are highlighted in red in the diff table.
- CLI exits with code 2 if any manual items are present.

---

## 6 · LLM Cache Path & Usage

LLM responses are cached in a local SQLite database to avoid redundant calls.

- Default cache path: `.namegnome/llm_cache.sqlite`
- Use `--no-cache` to bypass the cache for fresh LLM responses.

---

## 7 · Example CLI Commands

- Scan with LLM assist (uses default if --llm-model is omitted):
  ```sh
  namegnome scan /media/tv --media-type tv
  ```
- Scan with explicit model:
  ```sh
  namegnome scan /media/tv --media-type tv --llm-model deepseek-coder-instruct:1.5b
  ```
- List models:
  ```sh
  namegnome llm list
  ```
- Set default model:
  ```sh
  namegnome llm set-default deepseek-coder-instruct:1.5b
  ```

---

## 8 · Troubleshooting & FAQ

- **Ollama not running:** Ensure the Ollama server is started before using LLM features.
- **Model not found:** Use `namegnome llm list` to see available models.
- **Manual flag confusion:** Items flagged as manual require user review due to low LLM confidence.
- **Cache issues:** Delete `.namegnome/llm_cache.sqlite` to reset the cache.

---

## 9 · Demo

_A demo GIF or asciinema recording will be added here to illustrate anthology splitting
and manual flag behavior._

**How to record the demo:**

1. **Prepare a test folder** with a multi-episode TV file (e.g., `PawPatrol.S01E01E02.mkv`).
2. **Start asciinema recording:**
   ```sh
   asciinema rec -c "zsh" demo-anthology.cast
   ```
3. **Run the scan command with anthology splitting:**
   ```sh
   namegnome scan /path/to/test/folder --media-type tv --anthology
   ```
4. **Show the diff table** with LLM-powered episode split and any manual flags.
5. **Optionally, show apply/undo:**
   ```sh
   namegnome apply <plan-id>
   namegnome undo <plan-id>
   ```
6. **Stop recording** (Ctrl-D or type `exit`).
7. **Convert to GIF** (optional, for embedding):
   ```sh
   asciinema2gif demo-anthology.cast demo-anthology.gif
   ```
8. **Embed the GIF here** when ready:
   ```markdown
   ![Anthology Demo](demo-anthology.gif)
   ```

---

## Recommended Models

For best results, we recommend the following models with NameGnome:

- **Default:** `llama3:8b` (Meta)
- **Lightweight fallback:** `mistral:7b`
- **Code-focused fallback:** `deepseek-coder-v2:16b-lite-instruct-q4_K_M`

**Rationale:**
- Open weights and permissive license
- Strong performance on code, structured text, and fuzzy matching
- Efficient resource use (Llama 3 8B and Mistral 7B run on most modern hardware; DeepSeek-Coder-V2-Instruct is lightweight at ~10GB and excels at code tasks)
- Broad support in Ollama and other local inference engines
- Privacy-friendly and supports commercial use

To install these models with Ollama:

```sh
ollama pull llama3:8b
ollama pull mistral:7b
ollama pull deepseek-coder-v2:16b-lite-instruct-q4_K_M
```

You can then set your preferred default model:

```sh
namegnome llm set-default llama3:8b
```

Or, for lightweight or code-focused workflows:

```sh
namegnome llm set-default mistral:7b
namegnome llm set-default deepseek-coder-v2:16b-lite-instruct-q4_K_M
```

**References:**
- [Deploying DeepSeek-Coder Locally (Medium)](https://medium.com/@howard.zhang/deploying-deepseek-coder-locally-guided-by-deepseek-r1-part-2-f77939cdc20b)
- [DeepSeek-Coder-V2-Instruct on HuggingFace](https://huggingface.co/deepseek-ai/DeepSeek-Coder-V2-Instruct) 