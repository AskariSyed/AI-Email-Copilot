# Portfolio Demonstration Guidelines

This document provides the exact script to capture a visually impressive and informative demonstration of AI Email Copilot for your GitHub portfolio. The frontend is fully polished with glassmorphism UI, real-time AI generation, and RAG context transparency.

## Required Preparation
Ensure you have running versions of both the frontend (`npm run dev`) and backend (`uvicorn app.main:app`). **Do not use fake data.** Sync your actual Gmail account containing standard, non-sensitive conversational threads to demonstrate the RAG engine properly.

---

## 1. The Inbox & Sync Workflow
**Action**: Click the "Sync" button on the top right. Let the sidebar populate. Select an email that represents a long conversational thread.
**Screenshot**: Capture the full browser window.
**Focus**: The populated left sidebar, the original HTML rendering in the center, and the empty AI Copilot panel on the right.
**Recommended Caption**: `Seamlessly syncs with your actual Gmail account and beautifully renders HTML emails.`
**Placement**: Under the introductory paragraph in `README.md`.

## 2. The RAG Generation
**Action**: In the Copilot panel, type an instruction (e.g., `"Draft a polite decline explaining I am fully booked until Q3"`). Click the **GEN** button. Wait for the generation to finish so the "Sources Retrieved" badge appears below the text area.
**Screenshot**: Capture the full browser window (or a focused crop of the center and right panels).
**Focus**: The generated text inside the glassmorphic text area and the purple "Sources Retrieved" badge showing exactly how many thread messages, past messages, and similar messages were fetched.
**Recommended Caption**: `Context-Aware Generation: The Copilot pulls relevant historical data (RAG) to ground its responses, providing complete transparency into the sources used.`
**Placement**: In the "Key Features" section of `README.md`.

## 3. The Inbox Chat (Bonus)
**Action**: Switch to the **Chat** tab. Ask a question like, `"What was the latest update on the Q3 report?"` Let the AI respond with its cited sources.
**Screenshot**: Capture the Chat interface.
**Focus**: The AI response bubble and the source attribution cards underneath it.
**Recommended Caption**: `Inbox Chat: Converse directly with your entire email history.`
**Placement**: Below the RAG Generation screenshot.

---

## Recommended `README.md` Placement
Once you have captured these screenshots (or recorded them as a GIF/MP4), integrate them into your `README.md` using the standard markdown syntax:

```markdown
![Inbox and Sync Workflow](./docs/assets/inbox_sync.png)
*Seamlessly syncs with your actual Gmail account and beautifully renders HTML emails.*

...

![Context-Aware Generation](./docs/assets/rag_generation.png)
*Context-Aware Generation: The Copilot pulls relevant historical data (RAG) to ground its responses, providing complete transparency into the sources used.*
```
