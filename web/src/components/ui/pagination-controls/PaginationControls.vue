<script setup lang="ts">
import { computed } from "vue";
import { Button } from "@/components/ui/button";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { ChevronLeft, ChevronRight } from "lucide-vue-next";

const props = defineProps<{
  total: number;
  page: number;
  perPage: number;
}>();

const emit = defineEmits<{
  "update:page": [value: number];
  "update:perPage": [value: number];
}>();

const totalPages = computed(() => Math.max(1, Math.ceil(props.total / props.perPage)));

const visiblePages = computed(() => {
  const pages: number[] = [];
  const tp = totalPages.value;
  const current = props.page;

  if (tp <= 7) {
    for (let i = 1; i <= tp; i++) pages.push(i);
  } else {
    pages.push(1);
    if (current > 3) pages.push(-1); // ellipsis
    const start = Math.max(2, current - 1);
    const end = Math.min(tp - 1, current + 1);
    for (let i = start; i <= end; i++) pages.push(i);
    if (current < tp - 2) pages.push(-1); // ellipsis
    pages.push(tp);
  }
  return pages;
});

const perPageOptions = ["25", "50", "100"];
</script>

<template>
  <div class="grid grid-cols-3 items-center py-4">
    <div class="flex items-center gap-2">
      <span class="text-sm text-muted-foreground">Rows</span>
      <Select
        :model-value="String(perPage)"
        @update:model-value="(v) => { emit('update:perPage', Number(v)); emit('update:page', 1); }"
      >
        <SelectTrigger class="w-[70px] h-8">
          <SelectValue />
        </SelectTrigger>
        <SelectContent>
          <SelectItem v-for="opt in perPageOptions" :key="opt" :value="opt">
            {{ opt }}
          </SelectItem>
        </SelectContent>
      </Select>
    </div>
    <div class="flex items-center justify-center gap-1">
      <Button
        variant="outline"
        size="icon"
        class="h-8 w-8"
        :disabled="page <= 1"
        @click="emit('update:page', page - 1)"
      >
        <ChevronLeft class="h-4 w-4" />
      </Button>
      <template v-for="(p, i) in visiblePages" :key="i">
        <span v-if="p === -1" class="px-1 text-muted-foreground">...</span>
        <Button
          v-else
          :variant="p === page ? 'default' : 'outline'"
          size="icon"
          class="h-8 w-8"
          @click="emit('update:page', p)"
        >
          {{ p }}
        </Button>
      </template>
      <Button
        variant="outline"
        size="icon"
        class="h-8 w-8"
        :disabled="page >= totalPages"
        @click="emit('update:page', page + 1)"
      >
        <ChevronRight class="h-4 w-4" />
      </Button>
    </div>
    <div class="text-sm text-muted-foreground text-right">
      {{ total }} items
    </div>
  </div>
</template>
