<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listGear, listKeywords, listSpecialRules } from "../api";
import type { GearListItem } from "../types";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { MultiSelect } from "@/components/ui/multi-select";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const items = ref<GearListItem[]>([]);
const allKeywords = ref<string[]>([]);
const allRules = ref<string[]>([]);
const loading = ref(true);

const search = ref("");
const filterTypes = ref<string[]>([]);
const filterExpansions = ref<string[]>([]);
const filterKeywords = ref<string[]>([]);
const filterRules = ref<string[]>([]);
const filterIssues = ref(false);
const sortField = ref<keyof GearListItem>("name");
const sortAsc = ref(true);

const typeOptions = ["weapon", "armor", "item", "other"];

const expansions = computed(() => {
  const set = new Set(items.value.map((i) => i.expansion).filter(Boolean));
  return [...set].sort() as string[];
});

const filtered = computed(() => {
  let result = items.value;

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
  if (filterKeywords.value.length) params.keyword = filterKeywords.value.join(",");
  if (filterRules.value.length) params.rule = filterRules.value.join(",");
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

watch([filterKeywords, filterRules, filterIssues], fetchData);
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-2 mb-4 items-start">
      <Input
        v-model="search"
        type="text"
        placeholder="Search by name..."
        class="flex-1 min-w-[200px]"
      />
      <MultiSelect
        v-model="filterTypes"
        :options="typeOptions"
        placeholder="All types"
        class="w-[180px]"
      />
      <MultiSelect
        v-model="filterExpansions"
        :options="expansions"
        placeholder="All expansions"
        class="w-[200px]"
      />
      <MultiSelect
        v-model="filterKeywords"
        :options="allKeywords"
        placeholder="All keywords"
        class="w-[180px]"
      />
      <MultiSelect
        v-model="filterRules"
        :options="allRules"
        placeholder="All rules"
        class="w-[180px]"
      />
      <div class="flex items-center gap-2 h-9">
        <Checkbox
          id="issues"
          :checked="filterIssues"
          @update:checked="(v: boolean) => filterIssues = v"
        />
        <Label for="issues" class="whitespace-nowrap cursor-pointer">Issues only</Label>
      </div>
    </div>

    <p class="text-sm text-muted-foreground mb-2">{{ filtered.length }} items</p>

    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <Table v-else>
      <TableHeader>
        <TableRow>
          <TableHead class="cursor-pointer select-none hover:text-foreground w-[30%]" @click="toggleSort('name')">
            Name{{ sortIndicator("name") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground w-[10%]" @click="toggleSort('type')">
            Type{{ sortIndicator("type") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground w-[25%]" @click="toggleSort('expansion')">
            Expansion{{ sortIndicator("expansion") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground w-[25%]" @click="toggleSort('category')">
            Category{{ sortIndicator("category") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground w-[10%]" @click="toggleSort('version')">
            Ver{{ sortIndicator("version") }}
          </TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="item in filtered" :key="item.id">
          <TableCell>
            <router-link :to="`/gear/${item.id}`" class="text-blue-400 hover:underline">
              {{ item.name }}
            </router-link>
          </TableCell>
          <TableCell>
            <Badge :variant="(item.type as any) || 'other'">
              {{ item.type || "?" }}
            </Badge>
          </TableCell>
          <TableCell>{{ item.expansion }}</TableCell>
          <TableCell>{{ item.category }}</TableCell>
          <TableCell>{{ item.version }}</TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
