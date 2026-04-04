<script setup lang="ts">
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";

const speed = defineModel<string | null>("speed");
const accuracy = defineModel<string | null>("accuracy");
const strength = defineModel<string | null>("strength");
</script>

<template>
  <Card>
    <CardHeader class="pb-3">
      <CardTitle class="text-sm">Weapon Stats</CardTitle>
    </CardHeader>
    <CardContent>
      <div class="flex gap-3">
        <div class="flex-1 space-y-1">
          <Label>Speed</Label>
          <Input v-model="speed" />
        </div>
        <div class="flex-1 space-y-1">
          <Label>Accuracy</Label>
          <Input v-model="accuracy" />
        </div>
        <div class="flex-1 space-y-1">
          <Label>Strength</Label>
          <Input v-model="strength" />
        </div>
      </div>
    </CardContent>
  </Card>
</template>
