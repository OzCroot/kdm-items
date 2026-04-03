<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listGear, listKeywords, listSpecialRules } from "../api";
import type { GearListItem } from "../types";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
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
const filterType = ref<string>();
const filterExpansion = ref<string>();
const filterKeyword = ref<string>();
const filterRule = ref<string>();
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
  <div>
    <div class="flex flex-wrap gap-2 mb-4">
      <Input
        v-model="search"
        type="text"
        placeholder="Search by name..."
        class="flex-1 min-w-[200px]"
      />
      <Select :model-value="filterType" @update:model-value="(v) => filterType = v || undefined">
        <SelectTrigger class="w-[150px]">
          <SelectValue placeholder="All types" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem value="weapon">Weapon</SelectItem>
          <SelectItem value="armor">Armor</SelectItem>
          <SelectItem value="item">Item</SelectItem>
          <SelectItem value="other">Other</SelectItem>
        </SelectContent>
      </Select>
      <Select :model-value="filterExpansion" @update:model-value="(v) => filterExpansion = v || undefined">
        <SelectTrigger class="w-[180px]">
          <SelectValue placeholder="All expansions" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="exp in expansions" :key="exp!" :value="exp!">
            {{ exp }}
          </SelectItem>
        </SelectContent>
      </Select>
      <Select :model-value="filterKeyword" @update:model-value="(v) => { filterKeyword = v || undefined; fetchData() }">
        <SelectTrigger class="w-[150px]">
          <SelectValue placeholder="All keywords" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="kw in allKeywords" :key="kw" :value="kw">
            {{ kw }}
          </SelectItem>
        </SelectContent>
      </Select>
      <Select :model-value="filterRule" @update:model-value="(v) => { filterRule = v || undefined; fetchData() }">
        <SelectTrigger class="w-[150px]">
          <SelectValue placeholder="All rules" />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="rule in allRules" :key="rule" :value="rule">
            {{ rule }}
          </SelectItem>
        </SelectContent>
      </Select>
      <div class="flex items-center gap-2">
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
          <TableHead class="cursor-pointer select-none hover:text-foreground" @click="toggleSort('name')">
            Name{{ sortIndicator("name") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground" @click="toggleSort('type')">
            Type{{ sortIndicator("type") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground" @click="toggleSort('expansion')">
            Expansion{{ sortIndicator("expansion") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground" @click="toggleSort('category')">
            Category{{ sortIndicator("category") }}
          </TableHead>
          <TableHead class="cursor-pointer select-none hover:text-foreground" @click="toggleSort('version')">
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
