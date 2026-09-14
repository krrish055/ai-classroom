export function displayName(config?: { appName?: string } | null): string {
  return String(config?.appName || "").trim();
}

export function studioTitle(name: string) {
  return name ? `${name} — Training studio` : "Training studio";
}
