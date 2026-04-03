<script setup lang="ts">
</script>

<template>
  <div class="mx-auto max-w-[1200px] px-4">
    <header class="border-b border-border py-4 mb-6">
      <h1 class="text-xl font-semibold m-0">
        <router-link to="/" class="text-foreground no-underline hover:text-foreground/80">
          KDM Gear Database
        </router-link>
      </h1>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>
