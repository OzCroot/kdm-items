<script setup lang="ts">
import type { GearItem, AffinityLink } from "../types";
import { computed } from "vue";
import { X } from "lucide-vue-next";

const props = defineProps<{
  gear: GearItem | null;
  row: number;
  col: number;
  links: AffinityLink[];
}>();

const emit = defineEmits<{
  click: [];
  clear: [];
  replace: [];
}>();

const colorMap: Record<string, string> = {
  red: "bg-red-500",
  green: "bg-green-500",
  blue: "bg-blue-500",
};

// Check if this cell has active links on each edge
function hasLink(edge: "top" | "bottom" | "left" | "right"): string | null {
  for (const link of props.links) {
    if (edge === "right" && link.direction === "horizontal" && link.from[0] === props.row && link.from[1] === props.col) return link.color;
    if (edge === "left" && link.direction === "horizontal" && link.to[0] === props.row && link.to[1] === props.col) return link.color;
    if (edge === "bottom" && link.direction === "vertical" && link.from[0] === props.row && link.from[1] === props.col) return link.color;
    if (edge === "top" && link.direction === "vertical" && link.to[0] === props.row && link.to[1] === props.col) return link.color;
  }
  return null;
}

const topLink = computed(() => hasLink("top"));
const bottomLink = computed(() => hasLink("bottom"));
const leftLink = computed(() => hasLink("left"));
const rightLink = computed(() => hasLink("right"));
</script>

<template>
  <div
    class="relative w-36 h-48 border border-[var(--border)] rounded-lg overflow-hidden cursor-pointer group"
    :class="gear ? 'bg-[var(--card)]' : 'bg-[var(--muted)] hover:bg-[var(--accent)]'"
    @click="emit(gear ? 'replace' : 'click')"
  >
    <!-- Affinity edge indicators -->
    <div v-if="gear?.affinity_top" class="absolute top-0 left-1/2 -translate-x-1/2 w-6 h-1.5 rounded-b" :class="[colorMap[gear.affinity_top], topLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />
    <div v-if="gear?.affinity_bottom" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-6 h-1.5 rounded-t" :class="[colorMap[gear.affinity_bottom], bottomLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />
    <div v-if="gear?.affinity_left" class="absolute left-0 top-1/2 -translate-y-1/2 w-1.5 h-6 rounded-r" :class="[colorMap[gear.affinity_left], leftLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />
    <div v-if="gear?.affinity_right" class="absolute right-0 top-1/2 -translate-y-1/2 w-1.5 h-6 rounded-l" :class="[colorMap[gear.affinity_right], rightLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />

    <!-- Empty state -->
    <div v-if="!gear" class="flex items-center justify-center h-full text-[var(--muted-fg)] text-xs">
      + Add Gear
    </div>

    <!-- Filled state -->
    <template v-else>
      <button
        class="absolute top-1 right-1 z-10 opacity-0 group-hover:opacity-100 bg-black/60 rounded p-0.5 cursor-pointer"
        @click.stop="emit('clear')"
      >
        <X class="h-3 w-3" />
      </button>

      <!-- Image -->
      <div v-if="gear.image_path" class="h-28 overflow-hidden">
        <img
          :src="`/images/${gear.image_path}`"
          :alt="gear.name"
          class="w-full h-full object-cover object-top"
        />
      </div>
      <div v-else class="h-28 bg-[var(--muted)] flex items-center justify-center text-[var(--muted-fg)] text-xs">
        No image
      </div>

      <!-- Info -->
      <div class="p-1.5">
        <div class="text-xs font-medium truncate">{{ gear.name }}</div>
        <div class="text-[10px] text-[var(--muted-fg)]">
          <span v-if="gear.type === 'weapon' && gear.speed">
            {{ gear.speed }}/{{ gear.accuracy }}/{{ gear.strength }}
          </span>
          <span v-else-if="gear.type === 'armor' && gear.armor_rating">
            {{ gear.hit_location }} {{ gear.armor_rating }}
          </span>
          <span v-else>{{ gear.type }}</span>
        </div>
      </div>
    </template>
  </div>
</template>
