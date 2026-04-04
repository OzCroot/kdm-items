<script setup lang="ts">
import type { BadgeVariants } from "@/components/ui/badge";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";
import { Plus } from "lucide-vue-next";

defineProps<{
  title: string;
  items: string[];
  definitions?: Record<string, string>;
  variant?: BadgeVariants["variant"];
}>();

const emit = defineEmits<{
  edit: [];
}>();
</script>

<template>
  <Card>
    <CardHeader class="pb-3 flex flex-row items-center justify-between">
      <CardTitle class="text-sm">{{ title }}</CardTitle>
      <Button variant="outline" size="sm" class="h-7 text-xs" @click="emit('edit')">
        <Plus class="h-3 w-3 mr-1" /> Edit
      </Button>
    </CardHeader>
    <CardContent>
      <TooltipProvider :delay-duration="200">
        <div class="flex flex-wrap gap-1.5">
          <Tooltip v-for="item in items" :key="item">
            <TooltipTrigger as-child>
              <Badge :variant="variant ?? 'secondary'">
                {{ item }}
              </Badge>
            </TooltipTrigger>
            <TooltipContent v-if="definitions?.[item]" class="max-w-xs">
              {{ definitions[item] }}
            </TooltipContent>
          </Tooltip>
          <span v-if="!items.length" class="text-sm text-muted-foreground">None</span>
        </div>
      </TooltipProvider>
    </CardContent>
  </Card>
</template>
