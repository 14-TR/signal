# Signal.ai Application Synopsis

**Date:** 2025-09-10

## 1. Executive Summary


Signal.ai is a command-line application designed to automate the creation of a specialized newsletter on Artificial Intelligence. It operates as a self-contained pipeline that gathers information from pre-configured sources, ranks it based on relevance and importance, and generates a formatted Markdown file ready for distribution. The project is currently in "Stage 1," emphasizing a minimal, file-based approach without external databases or cloud services.

In addition to serving as an automated content pipeline, Signal.ai is also envisioned as a **networking catalyst**. By curating high-signal insights and distributing them consistently, the project provides a natural touchpoint for initiating conversations with peers, thought leaders, and potential collaborators in the AI ecosystem. The long-term goal is to evolve the newsletter into a platform that not only delivers distilled information but also facilitates **network value creation** — enabling subscribers to share, comment, and connect around the most relevant developments.

## 2. System Architecture & Workflow

The application's logic is centralized in a single Python script, `signalai.py`. While the engineering specification outlines a more modular design with separate components for fetching, ranking, and output generation, the current implementation consolidates all functionality into one file.

The workflow is as follows:

1.  **Load Configuration**: The application reads `feeds.json`, which contains a list of sources to monitor, including RSS feeds, GitHub repositories, and ArXiv queries.
2.  **Fetch Data**: It fetches the latest entries from each source.
3.  **Normalize & Deduplicate**: Each fetched item is converted into a standard format. Its URL is used to create a unique hash, which is checked against the `sources.json` file. If the hash is new, the item is added to the processing queue and appended to `sources.json` to prevent future duplication.
4.  **Rank Items**: All items are scored based on a "signal" metric, which is a weighted combination of:
    *   **Novelty**: How recently the item was published.
    *   **Authority**: A predefined score for the source domain (e.g., `openai.com` has a high authority).
    *   **Keywords**: The presence of specific technical terms (e.g., "agent," "multimodal," "inference").
5.  **Generate Newsletter**: The top-ranked items are selected, with a cap to ensure source diversity. These are then formatted into a Markdown file (`out/newsletter_<YYYY-MM-DD>.md`) containing two sections:
    *   `Top Signals`: A bulleted list of the most important findings.
    *   `Predicted Impacts`: A thematic analysis with pre-written commentary based on keywords found in the top signals.

## 3. Technical Stack

*   **Language**: Python 3
*   **Core Libraries**: `requests` (for HTTP requests), `feedparser` (for RSS/Atom feeds).
*   **Data Storage**:
    *   `feeds.json`: Input configuration for data sources.
    *   `sources.json`: Persistent storage of all processed items to handle state and prevent duplicates.
*   **Execution**: The application is run via a shell script (`run_signalai.sh`) and is designed to be easily scheduled as a recurring task.

## 4. Current Status vs. Specification

The application successfully implements the core functionality described in the `signal-spec-stage-1.md` document. The primary deviation is the architectural choice to use a single monolithic script instead of the specified modular directory structure (`fetchers/`, `rank/`, `emit/`). This simplifies the current codebase but may require refactoring as the project grows into future stages outlined in the roadmap (e.g., adding a database backend, API integrations).

## 5. Key Artifacts

*   **Code**: `signalai.py`
*   **Specification**: `docs/signal-spec-stage-1.md`
*   **Configuration**: `feeds.json`
*   **Data Store**: `sources.json`
*   **Example Output**: `out/newsletter_2025-09-09.md`
