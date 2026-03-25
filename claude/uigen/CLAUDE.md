# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Commands

```bash
npm run setup           # First-time setup: install deps, prisma generate, migrate
npm run dev             # Dev server at http://localhost:3000 (Turbopack)
npm run build           # Production build
npm run lint            # ESLint
npm run test            # Vitest (all tests)
npx vitest run src/lib/__tests__/file-system.test.ts  # Single test file
npm run db:reset        # Drop and recreate SQLite database
```

Node.js 22.x required (see `.nvmrc`). The app runs without an `ANTHROPIC_API_KEY` — a mock provider serves static component scaffolding instead.

## Architecture Overview

### Request / Response Flow

1. User sends a chat message from the browser
2. `ChatInterface` calls `POST /api/chat` with the full message history + serialized virtual filesystem
3. The route handler (`src/app/api/chat/route.ts`) reconstructs a `VirtualFileSystem` from the payload, calls `streamText` (Vercel AI SDK) with Claude, and streams the response back
4. Claude invokes one of two tools — `str_replace_editor` or `file_manager` — to mutate files
5. Streamed tool calls are forwarded to the client; `FileSystemContext.handleToolCall` applies them to the in-memory `VirtualFileSystem`
6. `PreviewFrame` re-renders whenever `refreshTrigger` increments: it calls `createImportMap` which Babel-transforms every JSX/TSX file into a blob URL, builds a native ES `importmap`, then sets `iframe.srcdoc` to a self-contained HTML page that boots React and mounts the app

### Virtual File System

`src/lib/file-system.ts` — `VirtualFileSystem` is an in-memory tree backed by a flat `Map<path, FileNode>`. Nothing is ever written to disk. It supports full CRUD plus rename, `viewFile` (with line numbers), `replaceInFile`, and `insertInFile` — the last three are what Claude's tools call internally. `FileSystemContext` wraps a single `VirtualFileSystem` instance in React state and exposes `handleToolCall` as the bridge between streamed AI tool calls and the in-memory FS.

Projects persist the serialized FS as JSON in SQLite (`data` column on the `Project` model). On load the server hydrates a `VirtualFileSystem` via `deserializeFromNodes`.

### AI Tools

Defined in `src/lib/tools/`:
- `str_replace_editor` — commands: `create`, `str_replace`, `insert`, `view`
- `file_manager` — commands: `rename`, `delete`

Both tools receive a bound `VirtualFileSystem` instance on the server; their return values are streamed to the client where `handleToolCall` replays the same mutations on the client-side FS.

### Preview Pipeline (`src/lib/transform/jsx-transformer.ts`)

- `transformJSX` — uses `@babel/standalone` to compile JSX/TSX to plain JS in-browser
- `createImportMap` — iterates all files, transforms each, creates blob URLs, builds a native `importmap`. Third-party imports (anything not starting with `.`, `/`, or `@/`) are resolved via `https://esm.sh/<package>`. Missing local imports get auto-generated placeholder modules so the preview doesn't crash.
- `createPreviewHTML` — returns a full HTML document with Tailwind CDN, the import map, an error boundary, and a `loadApp()` bootstrap. Syntax errors from Babel are displayed inline in the preview instead of crashing.
- The `@/` import alias maps to the virtual FS root `/`.

### Authentication

`src/lib/auth.ts` — JWT sessions via `jose` (no Next-Auth). Passwords hashed with `bcrypt`. Anonymous projects (no `userId`) are supported; they're saved to the DB but not associated with any account. `src/middleware.ts` gates session validation.

### Provider

`src/lib/provider.ts` — `getLanguageModel()` returns an Anthropic model (`claude-haiku-4-5`) if `ANTHROPIC_API_KEY` is set, otherwise a `MockLanguageModel` that emits hardcoded Counter/Form/Card component scaffolding as a streaming simulation.

### Key Contexts

- `FileSystemContext` — owns the `VirtualFileSystem`, `selectedFile`, `refreshTrigger`, and `handleToolCall`
- `ChatContext` (`src/lib/contexts/chat-context.tsx`) — owns chat message history and the `useChat` (Vercel AI SDK) state

### Database

SQLite via Prisma. Schema: `User` (email + bcrypt password) → `Project` (name, serialized `messages` JSON, serialized FS `data` JSON). Prisma client is generated to `src/generated/prisma/`.

### System Prompt Constraints (for component generation)

- Every project must have `/App.jsx` as the root entry point with a default export
- Style with Tailwind only (no inline styles)
- Local imports must use the `@/` alias (e.g. `@/components/Button`)
- No HTML files; the virtual FS root `/` is the working directory
