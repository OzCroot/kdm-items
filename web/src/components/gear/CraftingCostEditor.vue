<script setup lang="ts">
import { ref } from "vue";
import type { CraftingCost } from "../../types";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { X, Plus } from "lucide-vue-next";

const props = defineProps<{
  costs: CraftingCost[];
  locations: string[];
}>();

const craftingLocation = defineModel<string | null>("craftingLocation");
const gainedBy = defineModel<string | null>("gainedBy");

const emit = defineEmits<{
  "add-cost": [cost: CraftingCost];
  "remove-cost": [index: number];
}>();

const newResource = ref("");
const newQuantity = ref(1);

function addCost() {
  if (!newResource.value.trim()) return;
  emit("add-cost", { resource: newResource.value.trim(), quantity: newQuantity.value });
  newResource.value = "";
  newQuantity.value = 1;
}
</script>

<template>
  <Card>
    <CardHeader class="pb-3">
      <CardTitle class="text-sm">Crafting</CardTitle>
    </CardHeader>
    <CardContent class="space-y-3">
      <div class="space-y-1">
        <Label>Crafting Location</Label>
        <Select :model-value="craftingLocation ?? undefined" @update:model-value="(v) => craftingLocation = v ?? null">
          <SelectTrigger>
            <SelectValue placeholder="None" />
          </SelectTrigger>
          <SelectContent>
            <SelectItem v-for="loc in locations" :key="loc" :value="loc">{{ loc }}</SelectItem>
          </SelectContent>
        </Select>
      </div>
      <Separator />
      <div class="space-y-2">
        <div
          v-for="(cost, i) in costs"
          :key="i"
          class="flex items-center gap-2"
        >
          <Input v-model.number="cost.quantity" type="number" min="1" class="w-16 text-center" />
          <span class="text-muted-foreground">×</span>
          <Input v-model="cost.resource" class="flex-1" />
          <Button variant="destructive" size="icon" class="h-8 w-8 shrink-0" @click="emit('remove-cost', i)">
            <X class="h-3 w-3" />
          </Button>
        </div>
        <div class="flex items-center gap-2">
          <Input v-model.number="newQuantity" type="number" min="1" class="w-16 text-center" />
          <span class="text-muted-foreground">×</span>
          <Input v-model="newResource" placeholder="Resource..." class="flex-1" @keydown.enter.prevent="addCost" />
          <Button variant="outline" size="icon" class="h-8 w-8 shrink-0" @click="addCost">
            <Plus class="h-3 w-3" />
          </Button>
        </div>
      </div>
      <Separator />
      <div class="space-y-1">
        <Label>Gained By</Label>
        <Input v-model="gainedBy" />
      </div>
    </CardContent>
  </Card>
</template>
