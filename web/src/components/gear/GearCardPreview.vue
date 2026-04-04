<script setup lang="ts">
import { computed } from "vue";
import type { GearDetail } from "../../types";
import { imageUrl } from "../../api";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";

const props = defineProps<{
  gear: GearDetail;
  iconImages?: Record<string, string>;
}>();

const affinityColors: Record<string, string> = {
  red: "bg-red-500",
  green: "bg-green-500",
  blue: "bg-blue-500",
};

// Parse card text and replace [tag] with icon images or styled spans
const renderedCardText = computed(() => {
  const text = props.gear.card_text || "";
  return text.replace(/\[([a-z_]+)\]/g, (_, tag: string) => {
    if (props.iconImages?.[tag]) {
      return `<img src="${props.iconImages[tag]}" alt="${tag}" class="inline h-4 w-4 align-text-bottom" />`;
    }
    return `<span class="inline-flex items-center justify-center h-4 px-1 rounded bg-muted text-[10px] font-medium align-text-bottom">${tag}</span>`;
  });
});

const hasAffinities = computed(() =>
  props.gear.affinity_top || props.gear.affinity_bottom || props.gear.affinity_left || props.gear.affinity_right
);
</script>

<template>
  <Card class="max-w-lg mx-auto">
    <CardContent class="p-6 space-y-4">
      <!-- Header: Name + Type badge -->
      <div class="flex items-start justify-between gap-3">
        <h3 class="text-xl font-bold">{{ gear.name }}</h3>
        <Badge :variant="(gear.type as any) || 'other'" class="shrink-0">
          {{ gear.type || "?" }}
        </Badge>
      </div>

      <!-- Weapon stats bar -->
      <div v-if="gear.type === 'weapon' && (gear.speed || gear.accuracy || gear.strength)" class="flex gap-4 text-sm">
        <div class="flex flex-col items-center px-3 py-1.5 bg-muted rounded">
          <span class="text-muted-foreground text-[10px] uppercase">Speed</span>
          <span class="font-bold text-lg">{{ gear.speed }}</span>
        </div>
        <div class="flex flex-col items-center px-3 py-1.5 bg-muted rounded">
          <span class="text-muted-foreground text-[10px] uppercase">Accuracy</span>
          <span class="font-bold text-lg">{{ gear.accuracy }}</span>
        </div>
        <div class="flex flex-col items-center px-3 py-1.5 bg-muted rounded">
          <span class="text-muted-foreground text-[10px] uppercase">Strength</span>
          <span class="font-bold text-lg">{{ gear.strength }}</span>
        </div>
      </div>

      <!-- Armor stats bar -->
      <div v-if="gear.type === 'armor' && (gear.hit_location || gear.armor_rating)" class="flex gap-4 text-sm">
        <div class="flex flex-col items-center px-3 py-1.5 bg-muted rounded">
          <span class="text-muted-foreground text-[10px] uppercase">Location</span>
          <span class="font-bold">{{ gear.hit_location }}</span>
        </div>
        <div class="flex flex-col items-center px-3 py-1.5 bg-muted rounded">
          <span class="text-muted-foreground text-[10px] uppercase">Armor</span>
          <span class="font-bold text-lg">{{ gear.armor_rating }}</span>
        </div>
      </div>

      <!-- Keywords -->
      <div v-if="gear.keywords.length" class="flex flex-wrap gap-1">
        <Badge v-for="kw in gear.keywords" :key="kw" variant="secondary" class="text-xs">
          {{ kw }}
        </Badge>
      </div>

      <Separator v-if="gear.keywords.length && (gear.special_rules.length || gear.card_text)" />

      <!-- Special Rules -->
      <div v-if="gear.special_rules.length" class="flex flex-wrap gap-1">
        <Badge v-for="rule in gear.special_rules" :key="rule" variant="outline" class="text-xs">
          {{ rule }}
        </Badge>
      </div>

      <!-- Card Text -->
      <div
        v-if="gear.card_text"
        class="text-sm leading-relaxed whitespace-pre-line"
        v-html="renderedCardText"
      />

      <!-- Affinities -->
      <div v-if="hasAffinities" class="flex items-center gap-3 pt-1">
        <span class="text-xs text-muted-foreground">Affinities:</span>
        <div v-for="(dir, label) in { top: gear.affinity_top, bottom: gear.affinity_bottom, left: gear.affinity_left, right: gear.affinity_right }" :key="label" class="flex items-center gap-1">
          <template v-if="dir">
            <span class="h-3 w-3 rounded-full" :class="affinityColors[dir]" />
            <span class="text-xs text-muted-foreground capitalize">{{ label }}</span>
          </template>
        </div>
      </div>
    </CardContent>
  </Card>
</template>
