// @vitest-environment jsdom
import { describe, it, expect } from "vitest";
import { render, screen } from "@testing-library/react";
import { ToolCallBadge } from "../ToolCallBadge";

function make(toolName: string, args: Record<string, unknown>, state = "call") {
  return { toolName, args, state };
}

describe("str_replace_editor labels", () => {
  it("shows Creating <path> for create command", () => {
    render(<ToolCallBadge tool={make("str_replace_editor", { command: "create", path: "/App.jsx" })} />);
    expect(screen.getByText("Creating /App.jsx")).toBeTruthy();
  });

  it("shows Editing <path> for str_replace command", () => {
    render(<ToolCallBadge tool={make("str_replace_editor", { command: "str_replace", path: "/components/Button.jsx" })} />);
    expect(screen.getByText("Editing /components/Button.jsx")).toBeTruthy();
  });

  it("shows Editing <path> for insert command", () => {
    render(<ToolCallBadge tool={make("str_replace_editor", { command: "insert", path: "/App.jsx" })} />);
    expect(screen.getByText("Editing /App.jsx")).toBeTruthy();
  });

  it("shows Reading <path> for view command", () => {
    render(<ToolCallBadge tool={make("str_replace_editor", { command: "view", path: "/App.jsx" })} />);
    expect(screen.getByText("Reading /App.jsx")).toBeTruthy();
  });
});

describe("file_manager labels", () => {
  it("shows Deleting <path> for delete command", () => {
    render(<ToolCallBadge tool={make("file_manager", { command: "delete", path: "/old.jsx" })} />);
    expect(screen.getByText("Deleting /old.jsx")).toBeTruthy();
  });

  it("shows Renaming with both paths for rename command", () => {
    render(<ToolCallBadge tool={make("file_manager", { command: "rename", path: "/old.jsx", new_path: "/new.jsx" })} />);
    expect(screen.getByText("Renaming /old.jsx → /new.jsx")).toBeTruthy();
  });
});

describe("state indicators", () => {
  it("shows spinner when in-progress", () => {
    const { container } = render(
      <ToolCallBadge tool={make("str_replace_editor", { command: "create", path: "/App.jsx" }, "call")} />
    );
    expect(container.querySelector(".animate-spin")).not.toBeNull();
  });

  it("hides spinner when done", () => {
    const { container } = render(
      <ToolCallBadge tool={make("str_replace_editor", { command: "create", path: "/App.jsx" }, "result")} />
    );
    expect(container.querySelector(".animate-spin")).toBeNull();
  });
});

describe("unknown tool fallback", () => {
  it("renders the raw tool name when unrecognized", () => {
    render(<ToolCallBadge tool={make("some_unknown_tool", {})} />);
    expect(screen.getByText("some_unknown_tool")).toBeTruthy();
  });
});
