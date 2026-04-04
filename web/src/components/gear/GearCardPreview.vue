<script setup lang="ts">
import { computed } from "vue";
import type { GearDetail } from "../../types";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Tooltip, TooltipContent, TooltipProvider, TooltipTrigger } from "@/components/ui/tooltip";

const props = defineProps<{
  gear: GearDetail;
  iconImages?: Record<string, string>;
  keywordDefinitions?: Record<string, string>;
  ruleDefinitions?: Record<string, string>;
  iconDescriptions?: Record<string, string>;
}>();

const affinityColors: Record<string, string> = {
  red: "bg-red-500",
  green: "bg-green-500",
  blue: "bg-blue-500",
};

// Split card text into segments: plain text and icon tokens
interface TextSegment { type: "text"; value: string }
interface IconSegment { type: "icon"; tag: string }
interface RuleSegment { type: "rule"; name: string }
type Segment = TextSegment | IconSegment | RuleSegment;

// Build a regex that matches known rule names in text (longest first to avoid partial matches)
const rulePattern = computed(() => {
  const names = Object.keys(props.ruleDefinitions || {}).filter((n) => n.length > 1);
  if (!names.length) return null;
  // Sort longest first so "Affinity Bonus" matches before "Affinity"
  const sorted = [...names].sort((a, b) => b.length - a.length);
  const escaped = sorted.map((n) => n.replace(/[.*+?^${}()|[\]\\]/g, "\\$&"));
  return new RegExp(`\\b(${escaped.join("|")})\\b`, "g");
});

function splitTextByRules(text: string): Segment[] {
  const pattern = rulePattern.value;
  if (!pattern) return [{ type: "text", value: text }];

  const segments: Segment[] = [];
  let lastIndex = 0;
  let match;
  // Reset regex state
  pattern.lastIndex = 0;
  while ((match = pattern.exec(text)) !== null) {
    if (match.index > lastIndex) {
      segments.push({ type: "text", value: text.slice(lastIndex, match.index) });
    }
    segments.push({ type: "rule", name: match[1] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    segments.push({ type: "text", value: text.slice(lastIndex) });
  }
  return segments;
}

const cardSegments = computed<Segment[]>(() => {
  const text = props.gear.card_text || "";
  // First pass: split by icon tags
  const iconSegments: Segment[] = [];
  let lastIndex = 0;
  const regex = /\[([a-z_]+)\]/g;
  let match;
  while ((match = regex.exec(text)) !== null) {
    if (match.index > lastIndex) {
      iconSegments.push({ type: "text", value: text.slice(lastIndex, match.index) });
    }
    iconSegments.push({ type: "icon", tag: match[1] });
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < text.length) {
    iconSegments.push({ type: "text", value: text.slice(lastIndex) });
  }

  // Second pass: split text segments by rule names
  const result: Segment[] = [];
  for (const seg of iconSegments) {
    if (seg.type === "text") {
      result.push(...splitTextByRules(seg.value));
    } else {
      result.push(seg);
    }
  }
  return result;
});

const hasAffinities = computed(() =>
  props.gear.affinity_top || props.gear.affinity_bottom || props.gear.affinity_left || props.gear.affinity_right
);
</script>

<template>
  <TooltipProvider :delay-duration="200">
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
          <Tooltip v-for="kw in gear.keywords" :key="kw">
            <TooltipTrigger as-child>
              <span><Badge variant="secondary" class="text-xs cursor-help">{{ kw }}</Badge></span>
            </TooltipTrigger>
            <TooltipContent v-if="keywordDefinitions?.[kw]" class="max-w-xs">
              {{ keywordDefinitions[kw] }}
            </TooltipContent>
          </Tooltip>
        </div>

        <Separator v-if="gear.keywords.length && (gear.special_rules.length || gear.card_text)" />

        <!-- Special Rules -->
        <div v-if="gear.special_rules.length" class="flex flex-wrap gap-1">
          <Tooltip v-for="rule in gear.special_rules" :key="rule">
            <TooltipTrigger as-child>
              <span><Badge variant="outline" class="text-xs cursor-help">{{ rule }}</Badge></span>
            </TooltipTrigger>
            <TooltipContent v-if="ruleDefinitions?.[rule]" class="max-w-xs">
              {{ ruleDefinitions[rule] }}
            </TooltipContent>
          </Tooltip>
        </div>

        <!-- Card Text with inline icon tooltips -->
        <div v-if="cardSegments.length" class="text-sm leading-relaxed whitespace-pre-line">
          <template v-for="(seg, i) in cardSegments" :key="i">
            <template v-if="seg.type === 'text'">{{ seg.value }}</template>
            <Tooltip v-else-if="seg.type === 'rule'">
              <TooltipTrigger as-child>
                <span class="font-semibold border-b border-dotted border-muted-foreground cursor-help">{{ seg.name }}</span>
              </TooltipTrigger>
              <TooltipContent class="max-w-xs">
                {{ ruleDefinitions?.[seg.name] }}
              </TooltipContent>
            </Tooltip>
            <Tooltip v-else>
              <TooltipTrigger as-child>
                <img
                  v-if="iconImages?.[(seg as IconSegment).tag]"
                  :src="iconImages[(seg as IconSegment).tag]"
                  :alt="iconDescriptions?.[(seg as IconSegment).tag] || (seg as IconSegment).tag"
                  class="inline h-4 w-4 align-text-bottom cursor-help"
                />
                <span
                  v-else
                  class="inline-flex items-center justify-center h-4 px-1 rounded bg-muted text-[10px] font-medium align-text-bottom cursor-help"
                >{{ (seg as IconSegment).tag }}</span>
              </TooltipTrigger>
              <TooltipContent>
                {{ iconDescriptions?.[(seg as IconSegment).tag] || (seg as IconSegment).tag }}
              </TooltipContent>
            </Tooltip>
          </template>
        </div>

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
  </TooltipProvider>
</template>
