// @vitest-environment node
import { describe, it, expect, vi, beforeEach } from "vitest";
import { SignJWT } from "jose";
import { NextRequest } from "next/server";

vi.mock("server-only", () => ({}));

const mockCookieStore = {
  get: vi.fn(),
  set: vi.fn(),
  delete: vi.fn(),
};

vi.mock("next/headers", () => ({
  cookies: vi.fn(() => Promise.resolve(mockCookieStore)),
}));

import {
  createSession,
  getSession,
  deleteSession,
  verifySession,
} from "../auth";

const SECRET = new TextEncoder().encode("development-secret-key");
const COOKIE_NAME = "auth-token";

async function signToken(payload: object, expiresIn = "7d") {
  return new SignJWT(payload as Record<string, unknown>)
    .setProtectedHeader({ alg: "HS256" })
    .setExpirationTime(expiresIn)
    .setIssuedAt()
    .sign(SECRET);
}

beforeEach(() => {
  vi.clearAllMocks();
});

describe("createSession", () => {
  it("sets an httpOnly cookie with a signed JWT", async () => {
    await createSession("user-1", "user@example.com");

    expect(mockCookieStore.set).toHaveBeenCalledOnce();
    const [name, , options] = mockCookieStore.set.mock.calls[0];
    expect(name).toBe(COOKIE_NAME);
    expect(options.httpOnly).toBe(true);
    expect(options.sameSite).toBe("lax");
    expect(options.path).toBe("/");
  });

  it("stores userId and email in the JWT payload", async () => {
    await createSession("user-1", "user@example.com");

    const token = mockCookieStore.set.mock.calls[0][1];
    const { jwtVerify } = await import("jose");
    const { payload } = await jwtVerify(token, SECRET);

    expect(payload.userId).toBe("user-1");
    expect(payload.email).toBe("user@example.com");
  });
});

describe("getSession", () => {
  it("returns null when no cookie is present", async () => {
    mockCookieStore.get.mockReturnValue(undefined);
    expect(await getSession()).toBeNull();
  });

  it("returns the session payload for a valid token", async () => {
    const token = await signToken({ userId: "user-1", email: "user@example.com" });
    mockCookieStore.get.mockReturnValue({ value: token });

    const session = await getSession();
    expect(session?.userId).toBe("user-1");
    expect(session?.email).toBe("user@example.com");
  });

  it("returns null for an expired token", async () => {
    const token = await signToken(
      { userId: "user-1", email: "user@example.com" },
      "-1s"
    );
    mockCookieStore.get.mockReturnValue({ value: token });

    expect(await getSession()).toBeNull();
  });

  it("returns null for a tampered token", async () => {
    mockCookieStore.get.mockReturnValue({ value: "invalid.token.value" });
    expect(await getSession()).toBeNull();
  });
});

describe("deleteSession", () => {
  it("deletes the auth cookie", async () => {
    await deleteSession();
    expect(mockCookieStore.delete).toHaveBeenCalledWith(COOKIE_NAME);
  });
});

describe("verifySession", () => {
  it("returns null when no cookie is present", async () => {
    const req = new NextRequest("http://localhost/");
    expect(await verifySession(req)).toBeNull();
  });

  it("returns the session payload for a valid token", async () => {
    const token = await signToken({ userId: "user-2", email: "b@example.com" });
    const req = new NextRequest("http://localhost/", {
      headers: { cookie: `${COOKIE_NAME}=${token}` },
    });

    const session = await verifySession(req);
    expect(session?.userId).toBe("user-2");
    expect(session?.email).toBe("b@example.com");
  });

  it("returns null for an expired token", async () => {
    const token = await signToken(
      { userId: "user-2", email: "b@example.com" },
      "-1s"
    );
    const req = new NextRequest("http://localhost/", {
      headers: { cookie: `${COOKIE_NAME}=${token}` },
    });

    expect(await verifySession(req)).toBeNull();
  });

  it("returns null for a tampered token", async () => {
    const req = new NextRequest("http://localhost/", {
      headers: { cookie: `${COOKIE_NAME}=bad.token.here` },
    });

    expect(await verifySession(req)).toBeNull();
  });
});
