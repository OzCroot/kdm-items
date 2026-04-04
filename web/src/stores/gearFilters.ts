import { defineStore } from "pinia";
import { ref, computed, watch } from "vue";
import { listGear, listKeywords, listSpecialRules } from "../api";
import type { GearListItem } from "../types";

const SESSION_KEY = "kdm-gear-filters";

interface FilterState {
  search: string;
  types: string[];
  expansions: string[];
  keywords: string[];
  rules: string[];
  issues: boolean;
  sortField: string;
  sortAsc: boolean;
}

function loadSession(): Partial<FilterState> {
  try {
    const raw = sessionStorage.getItem(SESSION_KEY);
    return raw ? JSON.parse(raw) : {};
  } catch {
    return {};
  }
}

function saveSession(state: FilterState) {
  sessionStorage.setItem(SESSION_KEY, JSON.stringify(state));
}

export const useGearFiltersStore = defineStore("gearFilters", () => {
  const saved = loadSession();

  // Filter state
  const search = ref(saved.search ?? "");
  const filterTypes = ref<string[]>(saved.types ?? []);
  const filterExpansions = ref<string[]>(saved.expansions ?? []);
  const filterKeywords = ref<string[]>(saved.keywords ?? []);
  const filterRules = ref<string[]>(saved.rules ?? []);
  const filterIssues = ref(saved.issues ?? false);
  const sortField = ref(saved.sortField ?? "name");
  const sortAsc = ref(saved.sortAsc ?? true);

  // Data
  const allItems = ref<GearListItem[]>([]);
  const allKeywordOptions = ref<string[]>([]);
  const allRuleOptions = ref<string[]>([]);
  const loaded = ref(false);
  const loading = ref(false);

  // Persist filters to sessionStorage
  watch(
    [search, filterTypes, filterExpansions, filterKeywords, filterRules, filterIssues, sortField, sortAsc],
    () => {
      saveSession({
        search: search.value,
        types: filterTypes.value,
        expansions: filterExpansions.value,
        keywords: filterKeywords.value,
        rules: filterRules.value,
        issues: filterIssues.value,
        sortField: sortField.value,
        sortAsc: sortAsc.value,
      });
    },
    { deep: true },
  );

  // Computed: available expansions from loaded data
  const expansionOptions = computed(() => {
    const set = new Set(allItems.value.map((i) => i.expansion).filter(Boolean));
    return [...set].sort() as string[];
  });

  // Computed: filtered + sorted list
  const filtered = computed(() => {
    let result = allItems.value;

    if (search.value) {
      const q = search.value.toLowerCase();
      result = result.filter((i) => i.name.toLowerCase().includes(q));
    }
    if (filterTypes.value.length) {
      result = result.filter((i) => filterTypes.value.includes(i.type || ""));
    }
    if (filterExpansions.value.length) {
      result = result.filter((i) => filterExpansions.value.includes(i.expansion || ""));
    }

    const field = sortField.value as keyof GearListItem;
    result = [...result].sort((a, b) => {
      const av = a[field] ?? "";
      const bv = b[field] ?? "";
      const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
      return sortAsc.value ? cmp : -cmp;
    });

    return result;
  });

  // Fetch data from API (server-side filters for keywords/rules)
  async function fetchData() {
    loading.value = true;
    const params: Record<string, string> = {};
    if (filterKeywords.value.length) params.keyword = filterKeywords.value.join(",");
    if (filterRules.value.length) params.rule = filterRules.value.join(",");
    if (filterIssues.value) params.issues = "true";
    allItems.value = await listGear(params);
    loading.value = false;
    loaded.value = true;
  }

  // Initial load: data + filter options
  async function init() {
    if (loaded.value) return;
    loading.value = true;
    const [kws, rules] = await Promise.all([listKeywords(), listSpecialRules()]);
    allKeywordOptions.value = kws;
    allRuleOptions.value = rules;
    await fetchData();
  }

  function toggleSort(field: string) {
    if (sortField.value === field) {
      sortAsc.value = !sortAsc.value;
    } else {
      sortField.value = field;
      sortAsc.value = true;
    }
  }

  function sortIndicator(field: string) {
    if (sortField.value !== field) return "";
    return sortAsc.value ? " ↑" : " ↓";
  }

  return {
    search,
    filterTypes,
    filterExpansions,
    filterKeywords,
    filterRules,
    filterIssues,
    sortField,
    sortAsc,
    allItems,
    allKeywordOptions,
    allRuleOptions,
    expansionOptions,
    filtered,
    loaded,
    loading,
    fetchData,
    init,
    toggleSort,
    sortIndicator,
  };
});
