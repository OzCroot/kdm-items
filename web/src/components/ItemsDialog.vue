<script setup lang="ts">
import { ref, watch } from "vue";
import type { GearRef } from "../api";
import { Badge } from "@/components/ui/badge";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
} from "@/components/ui/dialog";

const props = defineProps<{
  open: boolean;
  title: string;
  fetchItems: () => Promise<GearRef[]>;
}>();

const emit = defineEmits<{
  "update:open": [value: boolean];
}>();

const items = ref<GearRef[]>([]);
const loading = ref(false);

watch(() => props.open, async (isOpen) => {
  if (isOpen) {
    loading.value = true;
    items.value = await props.fetchItems();
    loading.value = false;
  }
});
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="max-w-md max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>{{ title }}</DialogTitle>
      </DialogHeader>
      <div v-if="loading" class="py-4 text-center text-muted-foreground">Loading...</div>
      <div v-else class="overflow-y-auto flex-1 -mx-6 px-6">
        <div v-for="item in items" :key="item.id" class="flex items-center justify-between py-1.5 border-b border-border last:border-0">
          <router-link
            :to="`/gear/${item.id}`"
            class="text-sm text-blue-400 hover:underline"
            @click="emit('update:open', false)"
          >
            {{ item.name }}
          </router-link>
          <div class="flex items-center gap-2">
            <span class="text-xs text-muted-foreground">{{ item.expansion }}</span>
            <Badge :variant="(item.type as any) || 'other'" class="text-[10px]">
              {{ item.type }}
            </Badge>
          </div>
        </div>
      </div>
    </DialogContent>
  </Dialog>
</template>
