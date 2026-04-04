<script setup lang="ts">
import { imageUrl } from "../../api";
import { Card, CardContent } from "@/components/ui/card";

defineProps<{
  imagePath: string | null;
  name: string;
}>();
</script>

<template>
  <div class="sticky top-4 self-start">
    <Card>
      <CardContent class="p-2">
        <img
          v-if="imagePath"
          :src="imageUrl(imagePath)"
          :alt="name"
          class="w-full rounded-md"
        />
        <div
          v-else
          class="w-full aspect-[3/4] rounded-md bg-muted flex items-center justify-center text-muted-foreground"
        >
          No image
        </div>
      </CardContent>
    </Card>
  </div>
</template>
