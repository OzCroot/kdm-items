<script setup lang="ts">
import { useRoute } from "vue-router";
import { computed } from "vue";

const route = useRoute();

const navItems = [
  { path: "/", label: "Items" },
  { path: "/keywords", label: "Keywords" },
  { path: "/special-rules", label: "Special Rules" },
];

function isActive(path: string) {
  if (path === "/") return route.path === "/" || route.path.startsWith("/gear/");
  return route.path === path;
}
</script>

<template>
  <div class="mx-auto max-w-[1200px] px-4">
    <header class="py-4">
      <div class="flex items-center justify-between">
        <h1 class="text-xl font-semibold m-0">
          <router-link to="/" class="text-foreground no-underline hover:text-foreground/80">
            KDM Gear Database
          </router-link>
        </h1>
      </div>
      <nav class="flex gap-4 mt-3">
        <router-link
          v-for="item in navItems"
          :key="item.path"
          :to="item.path"
          class="text-sm no-underline pb-2 -mb-[1px] border-b-2 transition-colors"
          :class="isActive(item.path)
            ? 'text-foreground border-foreground'
            : 'text-muted-foreground border-transparent hover:text-foreground hover:border-muted-foreground'"
        >
          {{ item.label }}
        </router-link>
      </nav>
    </header>
    <!-- nav tabs provide their own border-bottom visual -->
    <main>
      <router-view />
    </main>
  </div>
</template>
