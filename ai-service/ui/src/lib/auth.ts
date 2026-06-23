import type { UserContext } from "../types/copilot";

type StoredUser = {
  id?: string | number;
  username?: string;
  role?: string;
  merchantId?: string | number | null;
  token?: string;
};

const ALLOWED_ROLES = new Set(["USER", "MERCHANT", "ADMIN"]);

export function readStoredUser(): StoredUser | null {
  if (typeof window === "undefined") {
    return null;
  }

  try {
    const raw = window.localStorage.getItem("user");
    if (!raw) {
      return null;
    }
    const parsed = JSON.parse(raw);
    return parsed && typeof parsed === "object" ? parsed : null;
  } catch {
    return null;
  }
}

export function buildAuthHeaders(): Record<string, string> {
  const token = readStoredUser()?.token;
  if (typeof token !== "string" || !token.trim()) {
    return {};
  }

  return {
    Authorization: `Bearer ${token.trim()}`
  };
}

export function buildUserContextFromStorage(): UserContext | null {
  const user = readStoredUser();
  if (!user?.id || !user.username) {
    return null;
  }

  const roleValue = String(user.role || "USER").trim().toUpperCase();
  const role = ALLOWED_ROLES.has(roleValue) ? roleValue as UserContext["role"] : "USER";

  return {
    id: String(user.id),
    username: String(user.username),
    role,
    merchantId: user.merchantId === "" || user.merchantId === null || user.merchantId === undefined
      ? null
      : String(user.merchantId)
  };
}
