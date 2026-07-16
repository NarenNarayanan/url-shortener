// <input type="datetime-local"> uses "YYYY-MM-DDTHH:mm" in the browser's
// local time, with no timezone info — different from the ISO 8601 UTC
// strings the API sends/expects. These convert between the two.

export function toDatetimeLocalValue(isoString: string | null | undefined): string {
  if (!isoString) return "";
  const date = new Date(isoString);
  const pad = (n: number) => String(n).padStart(2, "0");
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())}T${pad(date.getHours())}:${pad(date.getMinutes())}`;
}

export function fromDatetimeLocalValue(value: string | undefined): string | null {
  if (!value) return null;
  return new Date(value).toISOString();
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString(undefined, { year: "numeric", month: "short", day: "numeric" });
}

export function formatDateTime(isoString: string): string {
  return new Date(isoString).toLocaleString(undefined, {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}
