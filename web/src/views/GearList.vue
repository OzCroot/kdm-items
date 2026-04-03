<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listGear, listKeywords, listSpecialRules } from "../api";
import type { GearListItem } from "../types";

const items = ref<GearListItem[]>([]);
const allKeywords = ref<string[]>([]);
const allRules = ref<string[]>([]);
const loading = ref(true);

const search = ref("");
const filterType = ref("");
const filterExpansion = ref("");
const filterKeyword = ref("");
const filterRule = ref("");
const filterIssues = ref(false);
const sortField = ref<keyof GearListItem>("name");
const sortAsc = ref(true);

const expansions = computed(() => {
  const set = new Set(items.value.map((i) => i.expansion).filter(Boolean));
  return [...set].sort();
});

const filtered = computed(() => {
  let result = items.value;

  if (search.value) {
    const q = search.value.toLowerCase();
    result = result.filter((i) => i.name.toLowerCase().includes(q));
  }
  if (filterType.value) {
    result = result.filter((i) => i.type === filterType.value);
  }
  if (filterExpansion.value) {
    result = result.filter((i) => i.expansion === filterExpansion.value);
  }

  const field = sortField.value;
  result = [...result].sort((a, b) => {
    const av = a[field] ?? "";
    const bv = b[field] ?? "";
    const cmp = String(av).localeCompare(String(bv), undefined, { numeric: true });
    return sortAsc.value ? cmp : -cmp;
  });

  return result;
});

function toggleSort(field: keyof GearListItem) {
  if (sortField.value === field) {
    sortAsc.value = !sortAsc.value;
  } else {
    sortField.value = field;
    sortAsc.value = true;
  }
}

function sortIndicator(field: keyof GearListItem) {
  if (sortField.value !== field) return "";
  return sortAsc.value ? " ↑" : " ↓";
}

async function fetchData() {
  loading.value = true;
  const params: Record<string, string> = {};
  if (filterKeyword.value) params.keyword = filterKeyword.value;
  if (filterRule.value) params.rule = filterRule.value;
  if (filterIssues.value) params.issues = "true";
  items.value = await listGear(params);
  loading.value = false;
}

onMounted(async () => {
  const [kws, rules] = await Promise.all([listKeywords(), listSpecialRules()]);
  allKeywords.value = kws;
  allRules.value = rules;
  await fetchData();
});

watch([filterKeyword, filterRule, filterIssues], fetchData);
</script>

<template>
  <div class="gear-list">
    <div class="filters">
      <input
        v-model="search"
        type="text"
        placeholder="Search by name..."
        class="search-input"
      />
      <select v-model="filterType">
        <option value="">All types</option>
        <option value="weapon">Weapon</option>
        <option value="armor">Armor</option>
        <option value="item">Item</option>
        <option value="other">Other</option>
      </select>
      <select v-model="filterExpansion">
        <option value="">All expansions</option>
        <option v-for="exp in expansions" :key="exp" :value="exp">
          {{ exp }}
        </option>
      </select>
      <select v-model="filterKeyword" @change="fetchData">
        <option value="">All keywords</option>
        <option v-for="kw in allKeywords" :key="kw" :value="kw">
          {{ kw }}
        </option>
      </select>
      <select v-model="filterRule" @change="fetchData">
        <option value="">All rules</option>
        <option v-for="rule in allRules" :key="rule" :value="rule">
          {{ rule }}
        </option>
      </select>
      <label class="issues-toggle">
        <input type="checkbox" v-model="filterIssues" />
        Issues only
      </label>
    </div>

    <div class="count">{{ filtered.length }} items</div>

    <div v-if="loading" class="loading">Loading...</div>

    <table v-else>
      <thead>
        <tr>
          <th @click="toggleSort('name')">Name{{ sortIndicator("name") }}</th>
          <th @click="toggleSort('type')">Type{{ sortIndicator("type") }}</th>
          <th @click="toggleSort('expansion')">Expansion{{ sortIndicator("expansion") }}</th>
          <th @click="toggleSort('category')">Category{{ sortIndicator("category") }}</th>
          <th @click="toggleSort('version')">Ver{{ sortIndicator("version") }}</th>
        </tr>
      </thead>
      <tbody>
        <tr v-for="item in filtered" :key="item.id">
          <td>
            <router-link :to="`/gear/${item.id}`">{{ item.name }}</router-link>
          </td>
          <td>
            <span class="type-badge" :class="item.type || 'other'">
              {{ item.type || "?" }}
            </span>
          </td>
          <td>{{ item.expansion }}</td>
          <td>{{ item.category }}</td>
          <td>{{ item.version }}</td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<style scoped>
.filters {
  display: flex;
  gap: 0.5rem;
  flex-wrap: wrap;
  margin-bottom: 1rem;
}

.search-input {
  flex: 1;
  min-width: 200px;
}

.filters select {
  min-width: 140px;
}

.issues-toggle {
  display: flex;
  align-items: center;
  gap: 0.3rem;
  white-space: nowrap;
}

.count {
  font-size: 0.85rem;
  color: #888;
  margin-bottom: 0.5rem;
}

table {
  width: 100%;
  border-collapse: collapse;
}

th {
  text-align: left;
  padding: 0.5rem;
  border-bottom: 2px solid #444;
  cursor: pointer;
  user-select: none;
  white-space: nowrap;
}

th:hover {
  color: #adf;
}

td {
  padding: 0.4rem 0.5rem;
  border-bottom: 1px solid #333;
}

tr:hover {
  background: #1a1a2e;
}

td a {
  color: #8bf;
  text-decoration: none;
}

td a:hover {
  text-decoration: underline;
}

.type-badge {
  display: inline-block;
  padding: 0.1rem 0.4rem;
  border-radius: 3px;
  font-size: 0.8rem;
  font-weight: 600;
}

.type-badge.weapon { background: #5a2020; color: #f88; }
.type-badge.armor { background: #1a3a5a; color: #8bf; }
.type-badge.item { background: #2a4a1a; color: #8f8; }
.type-badge.other { background: #4a3a1a; color: #fb8; }

.loading {
  text-align: center;
  padding: 2rem;
  color: #888;
}
</style>
