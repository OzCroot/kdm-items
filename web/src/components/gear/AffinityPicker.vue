<script setup lang="ts">
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const top = defineModel<string | null>("top");
const bottom = defineModel<string | null>("bottom");
const left = defineModel<string | null>("left");
const right = defineModel<string | null>("right");

const colorClasses: Record<string, string> = {
  red: "bg-red-500",
  green: "bg-green-500",
  blue: "bg-blue-500",
};

function capitalize(s: string) {
  return s.charAt(0).toUpperCase() + s.slice(1);
}
</script>

<template>
  <Card>
    <CardHeader class="pb-3">
      <CardTitle class="text-sm">Affinities</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="grid grid-cols-3 gap-2 w-[340px] mx-auto">
        <!-- Top -->
        <div />
        <div class="space-y-1 text-center">
          <Label class="text-center block text-xs">Top</Label>
          <Select :model-value="top ?? 'none'" @update:model-value="(v) => top = v === 'none' ? null : v">
            <SelectTrigger>
              <span v-if="top" class="inline-flex items-center gap-1.5">
                <span class="h-3 w-3 rounded-full" :class="colorClasses[top]" />
                {{ capitalize(top) }}
              </span>
              <SelectValue v-else placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem v-for="c in ['red', 'green', 'blue']" :key="c" :value="c">
                <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-full" :class="colorClasses[c]" />{{ capitalize(c) }}</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div />

        <!-- Left / Right -->
        <div class="space-y-1 text-center">
          <Label class="text-center block text-xs">Left</Label>
          <Select :model-value="left ?? 'none'" @update:model-value="(v) => left = v === 'none' ? null : v">
            <SelectTrigger>
              <span v-if="left" class="inline-flex items-center gap-1.5">
                <span class="h-3 w-3 rounded-full" :class="colorClasses[left]" />
                {{ capitalize(left) }}
              </span>
              <SelectValue v-else placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem v-for="c in ['red', 'green', 'blue']" :key="c" :value="c">
                <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-full" :class="colorClasses[c]" />{{ capitalize(c) }}</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div />
        <div class="space-y-1 text-center">
          <Label class="text-center block text-xs">Right</Label>
          <Select :model-value="right ?? 'none'" @update:model-value="(v) => right = v === 'none' ? null : v">
            <SelectTrigger>
              <span v-if="right" class="inline-flex items-center gap-1.5">
                <span class="h-3 w-3 rounded-full" :class="colorClasses[right]" />
                {{ capitalize(right) }}
              </span>
              <SelectValue v-else placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem v-for="c in ['red', 'green', 'blue']" :key="c" :value="c">
                <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-full" :class="colorClasses[c]" />{{ capitalize(c) }}</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>

        <!-- Bottom -->
        <div />
        <div class="space-y-1 text-center">
          <Label class="text-center block text-xs">Bottom</Label>
          <Select :model-value="bottom ?? 'none'" @update:model-value="(v) => bottom = v === 'none' ? null : v">
            <SelectTrigger>
              <span v-if="bottom" class="inline-flex items-center gap-1.5">
                <span class="h-3 w-3 rounded-full" :class="colorClasses[bottom]" />
                {{ capitalize(bottom) }}
              </span>
              <SelectValue v-else placeholder="None" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="none">None</SelectItem>
              <SelectItem v-for="c in ['red', 'green', 'blue']" :key="c" :value="c">
                <span class="inline-flex items-center gap-1.5"><span class="h-3 w-3 rounded-full" :class="colorClasses[c]" />{{ capitalize(c) }}</span>
              </SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div />
      </div>
    </CardContent>
  </Card>
</template>
