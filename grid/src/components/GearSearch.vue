<script setup lang="ts">
import { ref, computed, watch, nextTick } from "vue";
import type { GearItem } from "../types";

const props = defineProps<{
  open: boolean;
  items: GearItem[];
}>();

const emit = defineEmits<{
  close: [];
  select: [item: GearItem];
}>();

const query = ref("");
const inputRef = ref<HTMLInputElement | null>(null);
const selectedIndex = ref(0);

const filtered = computed(() => {
  if (!query.value) return props.items.slice(0, 50);
  const q = query.value.toLowerCase();
  return props.items
    .filter((i) =>
      i.name.toLowerCase().includes(q) ||
      i.keywords.some((k) => k.toLowerCase().includes(q)) ||
      (i.type && i.type.toLowerCase().includes(q))
    )
    .slice(0, 50);
});

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    query.value = "";
    selectedIndex.value = 0;
    await nextTick();
    inputRef.value?.focus();
  }
});

function onKeydown(e: KeyboardEvent) {
  if (e.key === "ArrowDown") {
    e.preventDefault();
    selectedIndex.value = Math.min(selectedIndex.value + 1, filtered.value.length - 1);
  } else if (e.key === "ArrowUp") {
    e.preventDefault();
    selectedIndex.value = Math.max(selectedIndex.value - 1, 0);
  } else if (e.key === "Enter") {
    e.preventDefault();
    if (filtered.value[selectedIndex.value]) {
      emit("select", filtered.value[selectedIndex.value]);
    }
  } else if (e.key === "Escape") {
    emit("close");
  }
}

const typeColors: Record<string, string> = {
  weapon: "text-red-400",
  armor: "text-blue-400",
  item: "text-green-400",
  other: "text-amber-400",
};
</script>

<template>
  <Teleport to="body">
    <div
      v-if="open"
      class="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]"
    >
      <!-- Backdrop -->
      <div class="absolute inset-0 bg-black/60" @click="emit('close')" />

      <!-- Search panel -->
      <div class="relative bg-[var(--card)] border border-[var(--border)] rounded-lg shadow-2xl w-[480px] max-h-[60vh] flex flex-col">
        <div class="p-3 border-b border-[var(--border)]">
          <input
            ref="inputRef"
            v-model="query"
            placeholder="Search gear by name, keyword, or type..."
            class="w-full bg-transparent outline-none text-sm"
            @keydown="onKeydown"
          />
        </div>
        <div class="overflow-y-auto flex-1">
          <div
            v-for="(item, i) in filtered"
            :key="item.id"
            class="flex items-center gap-3 px-3 py-2 cursor-pointer text-sm"
            :class="i === selectedIndex ? 'bg-[var(--accent)]' : 'hover:bg-[var(--muted)]'"
            @click="emit('select', item)"
            @mouseenter="selectedIndex = i"
          >
            <div class="w-8 h-8 rounded bg-[var(--muted)] overflow-hidden shrink-0">
              <img
                v-if="item.image_path"
                :src="`/images/${item.image_path}`"
                :alt="item.name"
                class="w-full h-full object-cover"
              />
            </div>
            <div class="flex-1 min-w-0">
              <div class="truncate font-medium">{{ item.name }}</div>
              <div class="text-[10px] text-[var(--muted-fg)]">
                {{ item.expansion }}
                <span v-if="item.keywords.length"> · {{ item.keywords.slice(0, 3).join(', ') }}</span>
              </div>
            </div>
            <span class="text-xs shrink-0" :class="typeColors[item.type || 'other']">
              {{ item.type }}
            </span>
          </div>
          <div v-if="!filtered.length" class="px-3 py-8 text-center text-[var(--muted-fg)] text-sm">
            No gear found
          </div>
        </div>
      </div>
    </div>
  </Teleport>
</template>
