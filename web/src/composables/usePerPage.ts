import { ref, watch } from "vue";

const STORAGE_KEY = "kdm-per-page";
const DEFAULT = 50;

function read(): number {
  const stored = localStorage.getItem(STORAGE_KEY);
  if (stored) {
    const n = Number(stored);
    if ([25, 50, 100].includes(n)) return n;
  }
  return DEFAULT;
}

export function usePerPage() {
  const perPage = ref(read());

  watch(perPage, (v) => {
    localStorage.setItem(STORAGE_KEY, String(v));
  });

  return perPage;
}
