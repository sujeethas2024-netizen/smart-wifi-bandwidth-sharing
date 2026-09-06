import { apiFetch } from "./api";

export async function fetchResearchResults() {
  return apiFetch("/api/experiment/results", {}, 120000);
}
