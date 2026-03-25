"use client";

import { Loader2, CheckCircle2, FilePlus, FilePen, Trash2, ArrowRightLeft, Eye } from "lucide-react";

interface ToolInvocation {
  toolName: string;
  state: string;
  args?: Record<string, unknown>;
}

interface ToolCallBadgeProps {
  tool: ToolInvocation;
}

function getLabel(toolName: string, args?: Record<string, unknown>): { icon: React.ReactNode; text: string } {
  const path = typeof args?.path === "string" ? args.path : "";
  const newPath = typeof args?.new_path === "string" ? args.new_path : "";
  const command = typeof args?.command === "string" ? args.command : "";

  if (toolName === "str_replace_editor") {
    switch (command) {
      case "create":
        return { icon: <FilePlus className="w-3 h-3" />, text: `Creating ${path}` };
      case "str_replace":
      case "insert":
        return { icon: <FilePen className="w-3 h-3" />, text: `Editing ${path}` };
      case "view":
        return { icon: <Eye className="w-3 h-3" />, text: `Reading ${path}` };
    }
  }

  if (toolName === "file_manager") {
    switch (command) {
      case "delete":
        return { icon: <Trash2 className="w-3 h-3" />, text: `Deleting ${path}` };
      case "rename":
        return { icon: <ArrowRightLeft className="w-3 h-3" />, text: `Renaming ${path} → ${newPath}` };
    }
  }

  return { icon: null, text: toolName };
}

export function ToolCallBadge({ tool }: ToolCallBadgeProps) {
  const done = tool.state === "result";
  const { icon, text } = getLabel(tool.toolName, tool.args);

  return (
    <div className="inline-flex items-center gap-2 mt-2 px-3 py-1.5 bg-neutral-50 rounded-lg text-xs border border-neutral-200">
      {done ? (
        <CheckCircle2 className="w-3 h-3 text-emerald-500 shrink-0" />
      ) : (
        <Loader2 className="w-3 h-3 animate-spin text-blue-600 shrink-0" />
      )}
      {icon && <span className="text-neutral-400">{icon}</span>}
      <span className="text-neutral-700 font-mono">{text}</span>
    </div>
  );
}
