<script setup lang="ts">
import type { AffinityLink } from "../types";

defineProps<{
  links: AffinityLink[];
}>();

// Cell dimensions: 208px wide (w-52), 256px tall (h-64), 8px gap
const CELL_W = 208;
const CELL_H = 256;
const GAP = 8;

function linkStyle(link: AffinityLink) {
  const [r1, c1] = link.from;
  const [r2, c2] = link.to;

  const colorMap: Record<string, string> = {
    red: "#ef4444",
    green: "#22c55e",
    blue: "#3b82f6",
  };

  if (link.direction === "horizontal") {
    // Line between right edge of from and left edge of to
    const x = c1 * (CELL_W + GAP) + CELL_W;
    const y = r1 * (CELL_H + GAP) + CELL_H / 2;
    return {
      position: "absolute" as const,
      left: `${x}px`,
      top: `${y - 1}px`,
      width: `${GAP}px`,
      height: "3px",
      background: colorMap[link.color],
      boxShadow: `0 0 8px ${colorMap[link.color]}`,
    };
  } else {
    // Line between bottom edge of from and top edge of to
    const x = c1 * (CELL_W + GAP) + CELL_W / 2;
    const y = r1 * (CELL_H + GAP) + CELL_H;
    return {
      position: "absolute" as const,
      left: `${x - 1}px`,
      top: `${y}px`,
      width: "3px",
      height: `${GAP}px`,
      background: colorMap[link.color],
      boxShadow: `0 0 8px ${colorMap[link.color]}`,
    };
  }
}
</script>

<template>
  <div class="absolute inset-0 pointer-events-none">
    <div
      v-for="(link, i) in links"
      :key="i"
      :style="linkStyle(link)"
      class="rounded-full"
    />
  </div>
</template>
