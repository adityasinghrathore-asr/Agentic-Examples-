# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Repository Structure

This repo contains two distinct projects:

1. **Root-level Python scripts** — Progressive exercises learning the Anthropic Claude API (numbered `001_*.py` through `008_*.py`, plus `chatbot.py` and Jupyter notebooks)
2. **`uigen/`** — A full-stack AI-powered React component generator web application

---

## Python Scripts (Root Level)

### Setup
```bash
pip install -r requirements.txt   # installs anthropic, python-dotenv
```

### Running
```bash
python 001_firstCloudeCode.py
python chatbot.py
python 008_eval_code_grader.py
```

Requires `ANTHROPIC_API_KEY` in root `.env`.

---

## UIGen Application (`uigen/`)

### Setup & Development
```bash
cd uigen
npm run setup        # install deps + prisma generate + migrate
npm run dev          # dev server at http://localhost:3000 (Turbopack)
```

### Other Commands
```bash
npm run build        # production build
npm start            # production server
npm run lint         # ESLint
npm run test         # Vitest
npm run db:reset     # force-reset SQLite database and re-migrate
```

Node.js 22.x is required (see `.nvmrc`).

### Running a Single Test
```bash
cd uigen
npx vitest run src/lib/__tests__/file-system.test.ts
```

---

## UIGen Architecture

### Request Flow
1. User sends chat message → `POST /api/chat` (Next.js Route Handler)
2. Route streams Claude responses via `@ai-sdk/anthropic` + Vercel AI SDK
3. Claude uses two tools: `str_replace_editor` (modify files) and `file_manager` (create/delete files)
4. Tool calls update the **virtual file system** (in-memory, never writes to disk)
5. Frontend receives streamed tool calls and updates `VirtualFileSystem` state
6. Preview iframe re-renders using `@babel/standalone` for JSX → JS transformation at runtime

### Key Abstractions

**Virtual File System** (`src/lib/file-system.ts`): In-memory tree of files/directories using Maps. All file operations (create, read, update, delete) happen in memory. Supports serialization for database persistence.

**AI Tools** (`src/lib/tools/`): Two tools exposed to Claude — `str_replace_editor` for string-replacement edits and `file_manager` for filesystem operations. Defined using Zod schemas and consumed by the Vercel AI SDK.

**Provider** (`src/lib/provider.ts`): Wraps `@ai-sdk/anthropic`. Falls back to a mock provider when `ANTHROPIC_API_KEY` is absent, enabling development without credentials.

**Server Actions** (`src/actions/`): Next.js server actions handle project CRUD and user management, interfacing with SQLite via Prisma.

### Database
SQLite (`prisma/dev.db`) with two models: `User` and `Project`. Projects store the serialized virtual filesystem as JSON. Authentication is JWT-based (jose + bcrypt).

### Tech Stack
- **Framework**: Next.js 15 (App Router), React 19, TypeScript
- **Styling**: Tailwind CSS v4
- **UI**: Radix UI primitives + lucide-react icons
- **Code Editor**: Monaco Editor (`@monaco-editor/react`)
- **AI**: `@ai-sdk/anthropic` + `ai` (Vercel AI SDK) for streaming
- **Database**: Prisma ORM + SQLite
- **Testing**: Vitest + Testing Library
