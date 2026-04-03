<script setup lang="ts">
</script>

<template>
  <div class="app">
    <header>
      <h1><router-link to="/">KDM Gear Database</router-link></h1>
    </header>
    <main>
      <router-view />
    </main>
  </div>
</template>

<style scoped>
.app {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 1rem;
}

header {
  padding: 1rem 0;
  border-bottom: 1px solid #333;
  margin-bottom: 1.5rem;
}

header h1 {
  margin: 0;
  font-size: 1.4rem;
}

header a {
  color: inherit;
  text-decoration: none;
}
</style>
