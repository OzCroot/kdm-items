<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { useGearFiltersStore } from "../stores/gearFilters";
import { usePerPage } from "../composables/usePerPage";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { MultiSelect } from "@/components/ui/multi-select";
import { Button } from "@/components/ui/button";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { SlidersHorizontal } from "lucide-vue-next";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";

const store = useGearFiltersStore();
const page = ref(1);
const perPage = usePerPage();

const typeOptions = ["weapon", "armor", "item", "other"];

const paged = computed(() => {
  const start = (page.value - 1) * perPage.value;
  return store.filtered.slice(start, start + perPage.value);
});

// Reset page when filters change
watch(
  [() => store.search, () => store.filterTypes, () => store.filterExpansions, () => store.filterKeywords, () => store.filterRules, () => store.filterIssues],
  () => { page.value = 1; },
  { deep: true },
);

// Refetch when server-side filters change
watch(
  [() => store.filterKeywords, () => store.filterRules, () => store.filterIssues],
  () => { store.fetchData(); },
  { deep: true },
);

onMounted(() => store.init());
</script>

<template>
  <div>
    <div class="flex flex-wrap gap-2 mb-4 items-start">
      <Input
        v-model="store.search"
        type="text"
        placeholder="Search by name..."
        class="flex-1 min-w-[200px]"
      />
      <MultiSelect
        v-model="store.filterTypes"
        :options="typeOptions"
        placeholder="All types"
        class="w-[180px]"
      />
      <MultiSelect
        v-model="store.filterExpansions"
        :options="store.expansionOptions"
        placeholder="All expansions"
        class="w-[200px]"
      />
      <MultiSelect
        v-model="store.filterKeywords"
        :options="store.allKeywordOptions"
        placeholder="All keywords"
        class="w-[180px]"
      />
      <MultiSelect
        v-model="store.filterRules"
        :options="store.allRuleOptions"
        placeholder="All rules"
        class="w-[180px]"
      />
      <Popover>
        <PopoverTrigger as-child>
          <Button variant="outline" size="icon" class="h-9 w-9 shrink-0">
            <SlidersHorizontal class="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="w-48" align="end">
          <div class="flex items-center gap-2">
            <Checkbox
              id="issues"
              :checked="store.filterIssues"
              @update:checked="(v: boolean | 'indeterminate') => { store.filterIssues = v === true; store.fetchData() }"
            />
            <Label for="issues" class="text-sm">Issues only</Label>
          </div>
        </PopoverContent>
      </Popover>
    </div>

    <div v-if="store.loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <template v-else>
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="cursor-pointer select-none hover:text-foreground w-[30%]" @click="store.toggleSort('name')">
              Name{{ store.sortIndicator("name") }}
            </TableHead>
            <TableHead class="cursor-pointer select-none hover:text-foreground w-[10%]" @click="store.toggleSort('type')">
              Type{{ store.sortIndicator("type") }}
            </TableHead>
            <TableHead class="cursor-pointer select-none hover:text-foreground w-[25%]" @click="store.toggleSort('expansion')">
              Expansion{{ store.sortIndicator("expansion") }}
            </TableHead>
            <TableHead class="cursor-pointer select-none hover:text-foreground w-[25%]" @click="store.toggleSort('category')">
              Category{{ store.sortIndicator("category") }}
            </TableHead>
            <TableHead class="cursor-pointer select-none hover:text-foreground w-[10%]" @click="store.toggleSort('version')">
              Ver{{ store.sortIndicator("version") }}
            </TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="item in paged" :key="item.id">
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

      <PaginationControls
        :total="store.filtered.length"
        :page="page"
        :per-page="perPage"
        @update:page="(v) => page = v"
        @update:per-page="(v) => perPage = v"
      />
    </template>
  </div>
</template>
