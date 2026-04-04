<script setup lang="ts">
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";

const hitLocation = defineModel<string | null>("hitLocation");
const armorRating = defineModel<string | null>("armorRating");
</script>

<template>
  <Card>
    <CardHeader class="pb-3">
      <CardTitle class="text-sm">Armor Stats</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="flex gap-3">
        <div class="flex-1 space-y-1">
          <Label>Hit Location</Label>
          <Select :model-value="hitLocation ?? undefined" @update:model-value="(v) => hitLocation = v ?? null">
            <SelectTrigger>
              <SelectValue placeholder="—" />
            </SelectTrigger>
            <SelectContent>
              <SelectItem value="Head">Head</SelectItem>
              <SelectItem value="Arms">Arms</SelectItem>
              <SelectItem value="Body">Body</SelectItem>
              <SelectItem value="Waist">Waist</SelectItem>
              <SelectItem value="Legs">Legs</SelectItem>
            </SelectContent>
          </Select>
        </div>
        <div class="flex-1 space-y-1">
          <Label>Armor Rating</Label>
          <Input v-model="armorRating" />
        </div>
      </div>
    </CardContent>
  </Card>
</template>
