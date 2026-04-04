<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import type { GearItem, Grid, AffinityLink, SavedGrid } from "./types";
import { findAffinityLinks } from "./grid-logic";
import GridCell from "./components/GridCell.vue";
import GearSearch from "./components/GearSearch.vue";
import AffinityLinkOverlay from "./components/AffinityLinkOverlay.vue";

const allGear = ref<GearItem[]>([]);
const grid = ref<Grid>([
  [null, null, null],
  [null, null, null],
  [null, null, null],
]);
const selectedCell = ref<[number, number] | null>(null);
const searchOpen = ref(false);
const savedGrids = ref<SavedGrid[]>([]);
const saveName = ref("");

const links = computed<AffinityLink[]>(() => findAffinityLinks(grid.value));
const linkCount = computed(() => links.value.length);

async function loadGear() {
  const res = await fetch("/gear-data.json");
  allGear.value = await res.json();
}

function openSearch(row: number, col: number) {
  selectedCell.value = [row, col];
  searchOpen.value = true;
}

function placeGear(item: GearItem) {
  if (!selectedCell.value) return;
  const [row, col] = selectedCell.value;
  grid.value[row][col] = item;
  searchOpen.value = false;
  selectedCell.value = null;
}

function clearCell(row: number, col: number) {
  grid.value[row][col] = null;
}

function clearGrid() {
  grid.value = [[null, null, null], [null, null, null], [null, null, null]];
}

// Save/Load
const STORAGE_KEY = "kdm-saved-grids";

function loadSavedGrids() {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    savedGrids.value = raw ? JSON.parse(raw) : [];
  } catch { savedGrids.value = []; }
}

function persistSavedGrids() {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(savedGrids.value));
}

function saveGrid() {
  const name = saveName.value.trim() || `Grid ${savedGrids.value.length + 1}`;
  const ids = grid.value.map((row) => row.map((cell) => cell?.id ?? null));
  savedGrids.value.push({ name, grid: ids, timestamp: Date.now() });
  persistSavedGrids();
  saveName.value = "";
}

function loadGrid(saved: SavedGrid) {
  const gearById = new Map(allGear.value.map((g) => [g.id, g]));
  grid.value = saved.grid.map((row) =>
    row.map((id) => (id !== null ? gearById.get(id) ?? null : null))
  );
}

function deleteSavedGrid(index: number) {
  savedGrids.value.splice(index, 1);
  persistSavedGrids();
}

onMounted(() => {
  loadGear();
  loadSavedGrids();
});
</script>

<template>
  <div class="max-w-4xl mx-auto px-4 py-8">
    <h1 class="text-2xl font-bold mb-6">KDM Gear Grid Builder</h1>

    <!-- Grid -->
    <div class="relative mb-8">
      <div class="grid grid-cols-3 gap-1 w-fit mx-auto">
        <template v-for="(row, ri) in grid" :key="ri">
          <GridCell
            v-for="(cell, ci) in row"
            :key="`${ri}-${ci}`"
            :gear="cell"
            :row="ri"
            :col="ci"
            :links="links"
            @click="cell ? undefined : openSearch(ri, ci)"
            @clear="clearCell(ri, ci)"
            @replace="openSearch(ri, ci)"
          />
        </template>
      </div>
      <AffinityLinkOverlay :links="links" />
    </div>

    <!-- Link summary -->
    <div v-if="linkCount > 0" class="text-center mb-6">
      <span class="text-sm text-[var(--muted-fg)]">
        {{ linkCount }} affinity link{{ linkCount !== 1 ? 's' : '' }} active
      </span>
      <div class="flex justify-center gap-2 mt-1">
        <span
          v-for="link in links"
          :key="`${link.from[0]}-${link.from[1]}-${link.to[0]}-${link.to[1]}`"
          class="inline-flex items-center gap-1 text-xs"
        >
          <span class="h-2.5 w-2.5 rounded-full" :class="{
            'bg-red-500': link.color === 'red',
            'bg-green-500': link.color === 'green',
            'bg-blue-500': link.color === 'blue',
          }" />
          {{ link.direction }}
        </span>
      </div>
    </div>

    <!-- Actions -->
    <div class="flex items-center justify-center gap-3 mb-8">
      <input
        v-model="saveName"
        placeholder="Grid name..."
        class="bg-[var(--muted)] border border-[var(--border)] rounded px-3 py-1.5 text-sm w-48"
        @keydown.enter="saveGrid"
      />
      <button
        class="bg-[var(--accent)] hover:bg-[var(--accent)]/80 border border-[var(--border)] rounded px-4 py-1.5 text-sm cursor-pointer"
        @click="saveGrid"
      >
        Save
      </button>
      <button
        class="border border-[var(--border)] rounded px-4 py-1.5 text-sm cursor-pointer hover:bg-[var(--muted)]"
        @click="clearGrid"
      >
        Clear
      </button>
    </div>

    <!-- Saved grids -->
    <div v-if="savedGrids.length" class="mb-8">
      <h2 class="text-lg font-semibold mb-3">Saved Grids</h2>
      <div class="space-y-2">
        <div
          v-for="(saved, i) in savedGrids"
          :key="i"
          class="flex items-center justify-between bg-[var(--card)] border border-[var(--border)] rounded px-4 py-2"
        >
          <div>
            <span class="font-medium">{{ saved.name }}</span>
            <span class="text-xs text-[var(--muted-fg)] ml-2">{{ new Date(saved.timestamp).toLocaleDateString() }}</span>
          </div>
          <div class="flex gap-2">
            <button
              class="text-sm text-[#8bf] hover:underline cursor-pointer"
              @click="loadGrid(saved)"
            >Load</button>
            <button
              class="text-sm text-red-400 hover:underline cursor-pointer"
              @click="deleteSavedGrid(i)"
            >Delete</button>
          </div>
        </div>
      </div>
    </div>

    <!-- Search dialog -->
    <GearSearch
      :open="searchOpen"
      :items="allGear"
      @close="searchOpen = false"
      @select="placeGear"
    />
  </div>
</template>
