# RAGFlow chat assistants as Open WebUI models

This guide connects a RAGFlow **chat assistant** to Open WebUI, so that people chat
in Open WebUI while RAGFlow searches its datasets and writes the answer.
Each RAGFlow chat assistant becomes one model in Open WebUI.

Follow it once for every chat assistant you want to offer.

## How it works

```
User ──► Open WebUI model  (e.g. "HR policies")
           │
           ├─1─► Task model (vLLM gpt-oss)
           │       picks and runs Workspace tools (date, calculator, …);
           │       also writes chat titles, tags and follow-up questions
           │
           └─2─► RAGFlow chat assistant
                   /api/v1/openai/<chat_id>/chat/completions
                   searches the assistant's datasets and answers,
                   using any tool results Open WebUI added to the question
```

- RAGFlow offers one OpenAI-compatible endpoint per chat assistant. Open WebUI
  treats that endpoint as a normal OpenAI connection.
- The model must use **Legacy** function calling. In that mode the task model,
  not RAGFlow, handles tools. In **Native** mode Open WebUI waits for RAGFlow to
  call tools, which RAGFlow never does, so the reply never finishes.

## Before you start

You need:

- **Admin access** to both RAGFlow and Open WebUI.
- In RAGFlow, a **dataset** that holds the documents, already parsed, with
  status **Success**.
- In Open WebUI, a **tool-capable LLM** connection to use as the task model,
  e.g. the vLLM `gpt-oss-20b` connection.

---

## Part 1 — RAGFlow

### 1.1 Create the chat assistant

1. Open **Chat** and create a new assistant.
2. Under **Datasets**, select the datasets it should answer from.
3. Set the **Empty response** field. RAGFlow returns this text when the search
   finds nothing in the datasets, and the LLM is not called at all.

   | Empty response | Effect |
   |---|---|
   | Filled in (e.g. "The answer you are looking for is not found in the dataset!") | Strict: only answers from the datasets. Questions like "what is today's date?" get this text even when a tool supplied the date. |
   | Left blank | The LLM always answers. Tool results (date, calculations) can be used even when the datasets have nothing on the topic. Keep the assistant's prompt focused on its subject so it stays in scope. |

4. Save.

### 1.2 Copy the chat ID

Open the assistant. The ID is the last part of the page URL:

```
http://<ragflow-host>/chat/d5630eb355e6453c96697a9aa8e20d42
                           └──────────── chat ID ─────────┘
```

### 1.3 Create an API key

1. Click your avatar, then **API**, then create a key (it starts with `ragflow-`).
2. The key must belong to the **same RAGFlow user who owns the assistant**.
   A key from another user cannot reach the assistant.
3. If your RAGFlow uses **access profiles**, the key owner's profile must have
   **API** turned on. Otherwise every request is rejected with 403.

Keep the key secret. Everyone using this Open WebUI model reaches RAGFlow as the
key owner.

### 1.4 Test the endpoint

Run this from the machine that hosts Open WebUI, so it also tests the network path.
Port **9380** is RAGFlow's API port, not the web page port.

```bash
curl -s http://<ragflow-host>:9380/api/v1/openai/<chat_id>/chat/completions \
  -H "Authorization: Bearer <ragflow-api-key>" \
  -H "Content-Type: application/json" \
  -d '{"model":"model","stream":false,"messages":[{"role":"user","content":"hello"}]}'
```

You should get JSON containing `"choices"`. `"model":"model"` tells RAGFlow to
use the LLM configured on the assistant.

> **Local laptops behind Zscaler only:** if a RAGFlow **data source** test fails
> with `URL resolves to a non-public address (100.64.x.x)`, Zscaler is resolving
> the SaaS hostname to its tunnel range. Set `ALLOW_ANY_HOST=1` for the local
> RAGFlow container only. **Never set it on a server**; servers resolve the
> public address and work without it.

---

## Part 2 — Open WebUI

### 2.1 Add the connection

**Admin Settings → Connections → OpenAI API → +**

| Field | Value |
|---|---|
| **Name** | The assistant's name, e.g. `HR policies` |
| **Model Group** | Optional, e.g. `RAG Models` |
| **URL** | `http://<ragflow-host>:9380/api/v1/openai/<chat_id>` |
| **Auth** | `Bearer` + the RAGFlow API key |
| **API Type** | Chat Completions |
| **Prefix ID** | Short, lowercase, **no spaces**, unique per connection, e.g. `hr` |
| **Model IDs** | Type `model` and **click +** so it shows as an entry |

Notes:

- **URL:** do not add `/chat/completions`; Open WebUI adds it. If Open WebUI runs
  in Docker on the same machine as RAGFlow, use `http://host.docker.internal:9380/...`
  instead of `localhost`.
- **Model IDs is required.** RAGFlow's per-assistant endpoint has no model list,
  so Open WebUI cannot discover the model itself. When Model IDs is filled in,
  Open WebUI does not ask RAGFlow for models.
- **Prefix ID:** every RAGFlow connection uses the same model ID `model`. The
  prefix keeps them apart: the model appears as `hr.model`, and Open WebUI
  removes the prefix before calling RAGFlow. A trailing space in the prefix
  produces `hr .model` and breaks the model ("Model ID cannot contain whitespace").
- Clicking the connection's **verify** icon reports an error, because RAGFlow
  answers `GET /models` with 404. This is expected and harmless.

Save and refresh the page.

### 2.2 Set the task model (once for all RAGFlow models)

**Admin Settings → Interface → Task Model (External)** → the vLLM model, e.g.
`gpt-oss-20b`.

The task model picks and runs tools, and writes chat titles, tags and follow-up
questions. If it is left on *Current Model*, all of that is sent to RAGFlow,
which searches the datasets for every one of those requests and returns text
Open WebUI cannot use.

### 2.3 Configure the model

**Admin Settings → Models** → open `<prefix>.model` (e.g. `hr.model`).

**General**

| Setting | Value |
|---|---|
| Name | What users see, e.g. `HR policies` |
| Description | One line on what it answers |
| Profile image | Optional |
| Access | The users or groups who should see it |
| System Prompt | Leave empty. RAGFlow ignores system messages; the assistant's prompt in RAGFlow is the one that counts. |
| Knowledge | None. RAGFlow does the retrieval. |

**Advanced Params → Function Calling = `Legacy`** (required)

The button cycles *Default → Native → Legacy*; click until it shows **Legacy**.
*Default* behaves like *Native*, and then the reply hangs.

**Capabilities**

| Capability | Setting | Why |
|---|---|---|
| Vision | Off | RAGFlow's endpoint answers text only |
| File Upload | Off | RAGFlow answers from its datasets, not from uploaded files |
| Code Interpreter | Off | Needs native tool calls |
| Usage | Optional | Shows token counts |
| Citations | Off | RAGFlow's sources are not passed to Open WebUI |
| Status Updates | On | Harmless |
| Memory | Off | Memories are sent as a system message, which RAGFlow drops |
| Builtin Tools | Off | Ignored in Legacy mode. Leaving it off avoids a hang if someone switches the model to Native. |

**Tools**

Attach any **Workspace tools** (Workspace → Tools) the model should use, e.g. a
date tool. In Legacy mode the task model decides when to call them, and their
results are added to the question that goes to RAGFlow.

Built-in tools (Time & Calculation, Memory, Calendar, Notes, …) do **not** run in
Legacy mode. Use a Workspace tool for anything the model needs.

Click **Save & Update**.

---

## Part 3 — Test

Start a **new** chat and select the model.

| Ask | Expected |
|---|---|
| A question the datasets answer, e.g. "How many casual leaves do I get?" | An answer from the documents |
| A question that needs a tool, e.g. "What is today's date, and how many leave days does the policy give?" | The tool's result plus the document answer |
| Anything | A chat title appears in the sidebar (written by the task model) |

In the RAGFlow server log, each user message should produce one
`POST /api/v1/openai/<chat_id>/chat/completions`. Titles, tags and tool choices
go to the task model and do not appear there.

---

## Troubleshooting

| Symptom | Cause | Fix |
|---|---|---|
| Model missing from the model picker | `model` was typed into Model IDs but not added with **+** | Edit the connection, add the entry, save, refresh |
| Model shows as `hr .model`; "Model ID cannot contain whitespace" | Trailing space in Prefix ID | Retype the prefix without spaces; delete the old `hr .model` entry under Admin → Models |
| Reply stays empty and never finishes | Function Calling is *Default* or *Native*, with Builtin Tools on | Set Function Calling to **Legacy**; start a new chat |
| `GET .../models` 404 in the RAGFlow log | Open WebUI's connection check | Expected; ignore |
| "The answer you are looking for is not found in the dataset!" | Nothing matched in the datasets, and **Empty response** is set | Check the datasets are parsed and linked; blank Empty response if tool-only questions must be answered |
| 401 from RAGFlow | Wrong or deleted API key | Create a new key and update the connection |
| 403 from RAGFlow | Key owner's access profile has **API** off | Turn API on for that profile |
| Error about the chat or dialog not found | Key belongs to a different user than the assistant's owner | Use a key from the assistant's owner |
| Tool results ignored | The Workspace tool is not attached to the model, or Empty response was returned | Attach the tool; blank Empty response if needed |

## Limits

- **One RAGFlow identity:** every Open WebUI user reaches RAGFlow as the API key
  owner. Control who sees each model with Open WebUI **Access**.
- **No system messages:** RAGFlow drops them, so Open WebUI system prompts and
  memories do not reach it.
- **No citations** from RAGFlow are shown in Open WebUI.
- **Built-in tools** do not run in Legacy mode; use Workspace tools.
- **Retrieval on tool turns:** when a tool runs, its output is added to the
  question RAGFlow searches with. Check answer quality if a tool returns long output.
- **One connection per assistant.** Every new assistant needs its own connection
  and model setup, as above.
