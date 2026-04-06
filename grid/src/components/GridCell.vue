<script setup lang="ts">
import type { GearItem, AffinityLink } from "../types";
import { computed } from "vue";
import { X } from "lucide-vue-next";

const baseUrl = import.meta.env.BASE_URL;

const props = defineProps<{
  gear: GearItem | null;
  row: number;
  col: number;
  links: AffinityLink[];
  dragOver: boolean;
}>();

const emit = defineEmits<{
  click: [];
  clear: [];
  replace: [];
  dragstart: [row: number, col: number];
  dragover: [row: number, col: number];
  dragleave: [];
  drop: [row: number, col: number];
}>();

const colorMap: Record<string, string> = {
  red: "bg-red-500",
  green: "bg-green-500",
  blue: "bg-blue-500",
};

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

function onDragStart(e: DragEvent) {
  if (!props.gear) return;
  e.dataTransfer!.effectAllowed = "move";
  emit("dragstart", props.row, props.col);
}

function onDragOver(e: DragEvent) {
  e.preventDefault();
  e.dataTransfer!.dropEffect = "move";
  emit("dragover", props.row, props.col);
}

function onDrop(e: DragEvent) {
  e.preventDefault();
  emit("drop", props.row, props.col);
}
</script>

<template>
  <div
    class="relative w-52 h-64 border-2 rounded-xl overflow-hidden cursor-pointer group transition-colors"
    :class="[
      gear ? 'bg-[var(--card)]' : 'bg-[var(--muted)] hover:bg-[var(--accent)]',
      dragOver ? 'border-blue-500 bg-blue-500/10' : 'border-[var(--border)]',
    ]"
    :draggable="!!gear"
    @click="gear ? emit('replace') : emit('click')"
    @dragstart="onDragStart"
    @dragover="onDragOver"
    @dragleave="emit('dragleave')"
    @drop="onDrop"
  >
    <!-- Affinity edge indicators -->
    <div v-if="gear?.affinity_top" class="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-2 rounded-b z-10" :class="[colorMap[gear.affinity_top], topLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />
    <div v-if="gear?.affinity_bottom" class="absolute bottom-0 left-1/2 -translate-x-1/2 w-8 h-2 rounded-t z-10" :class="[colorMap[gear.affinity_bottom], bottomLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />
    <div v-if="gear?.affinity_left" class="absolute left-0 top-1/2 -translate-y-1/2 w-2 h-8 rounded-r z-10" :class="[colorMap[gear.affinity_left], leftLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />
    <div v-if="gear?.affinity_right" class="absolute right-0 top-1/2 -translate-y-1/2 w-2 h-8 rounded-l z-10" :class="[colorMap[gear.affinity_right], rightLink ? 'opacity-100 shadow-lg shadow-current' : 'opacity-40']" />

    <!-- Empty state -->
    <div v-if="!gear" class="flex items-center justify-center h-full text-[var(--muted-fg)] text-sm">
      + Add Gear
    </div>

    <!-- Filled state -->
    <template v-else>
      <button
        class="absolute top-1.5 right-1.5 z-20 opacity-0 group-hover:opacity-100 bg-black/60 rounded-md p-1 cursor-pointer"
        @click.stop="emit('clear')"
      >
        <X class="h-4 w-4" />
      </button>

      <!-- Square image -->
      <div class="w-full aspect-square overflow-hidden bg-[var(--muted)]">
        <img
          v-if="gear.image_path"
          :src="`${baseUrl}images/${gear.image_path}`"
          :alt="gear.name"
          class="w-full h-full object-cover object-top pointer-events-none"
        />
        <div v-else class="w-full h-full flex items-center justify-center text-[var(--muted-fg)] text-xs">
          No image
        </div>
      </div>

      <!-- Info -->
      <div class="p-2">
        <div class="text-sm font-medium truncate">{{ gear.name }}</div>
        <div class="text-xs text-[var(--muted-fg)]">
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
