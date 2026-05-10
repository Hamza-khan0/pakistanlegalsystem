import { type ClassValue, clsx } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

const dateFormatter = new Intl.DateTimeFormat("en-PK", {
  day: "2-digit",
  month: "short",
  year: "numeric",
});

const compactDateFormatter = new Intl.DateTimeFormat("en-PK", {
  day: "2-digit",
  month: "short",
});

const dateTimeFormatter = new Intl.DateTimeFormat("en-PK", {
  day: "2-digit",
  month: "short",
  year: "numeric",
  hour: "2-digit",
  minute: "2-digit",
});

function parseSafeDate(date?: string | null) {
  if (!date) {
    return null;
  }

  const parsed = new Date(date);
  return Number.isNaN(parsed.getTime()) ? null : parsed;
}

export function formatDate(date?: string | null) {
  const parsed = parseSafeDate(date);
  return parsed ? dateFormatter.format(parsed) : "Not set";
}

export function formatCompactDate(date?: string | null) {
  const parsed = parseSafeDate(date);
  return parsed ? compactDateFormatter.format(parsed) : "Not set";
}

export function formatDateTime(date?: string | null) {
  const parsed = parseSafeDate(date);
  return parsed ? dateTimeFormatter.format(parsed) : "Not set";
}

export function getDaysUntil(date?: string | null) {
  const target = parseSafeDate(date);
  if (!target) {
    return 0;
  }

  const now = new Date();
  const diff = Math.ceil(
    (target.getTime() - now.setHours(0, 0, 0, 0)) / (1000 * 60 * 60 * 24),
  );

  return diff;
}

export function getInitials(name: string) {
  return name
    .split(" ")
    .filter(Boolean)
    .slice(0, 2)
    .map((part) => part[0]?.toUpperCase())
    .join("");
}
