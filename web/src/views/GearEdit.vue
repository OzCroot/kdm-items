<script setup lang="ts">
import { ref, onMounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { getGear, updateGear, imageUrl, listGear } from "../api";
import type { GearDetail, GearListItem } from "../types";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Separator } from "@/components/ui/separator";
import {
  Select,
  SelectContent,
  SelectItem,
  SelectTrigger,
  SelectValue,
} from "@/components/ui/select";
import { X, Plus, ChevronLeft, ChevronRight, ArrowLeft } from "lucide-vue-next";

const props = defineProps<{ id: string }>();
const router = useRouter();

const gear = ref<GearDetail | null>(null);
const allItems = ref<GearListItem[]>([]);
const loading = ref(true);
const saving = ref(false);
const saved = ref(false);
const error = ref("");
const newKeyword = ref("");
const newRule = ref("");
const newCostResource = ref("");
const newCostQuantity = ref(1);

const gearId = computed(() => parseInt(props.id, 10));

const currentIndex = computed(() =>
  allItems.value.findIndex((i) => i.id === gearId.value)
);
const prevId = computed(() =>
  currentIndex.value > 0 ? allItems.value[currentIndex.value - 1].id : null
);
const nextId = computed(() =>
  currentIndex.value < allItems.value.length - 1
    ? allItems.value[currentIndex.value + 1].id
    : null
);

async function load() {
  loading.value = true;
  error.value = "";
  try {
    gear.value = await getGear(gearId.value);
    if (!allItems.value.length) {
      allItems.value = await listGear();
    }
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to load";
  }
  loading.value = false;
}

async function save() {
  if (!gear.value) return;
  saving.value = true;
  saved.value = false;
  error.value = "";
  try {
    gear.value = await updateGear(gearId.value, gear.value);
    saved.value = true;
    setTimeout(() => (saved.value = false), 2000);
  } catch (e: unknown) {
    error.value = e instanceof Error ? e.message : "Failed to save";
  }
  saving.value = false;
}

function addKeyword() {
  if (!gear.value || !newKeyword.value.trim()) return;
  const kw = newKeyword.value.trim().toLowerCase();
  if (!gear.value.keywords.includes(kw)) {
    gear.value.keywords.push(kw);
  }
  newKeyword.value = "";
}

function removeKeyword(kw: string) {
  if (!gear.value) return;
  gear.value.keywords = gear.value.keywords.filter((k) => k !== kw);
}

function addRule() {
  if (!gear.value || !newRule.value.trim()) return;
  const rule = newRule.value.trim();
  if (!gear.value.special_rules.includes(rule)) {
    gear.value.special_rules.push(rule);
  }
  newRule.value = "";
}

function removeRule(rule: string) {
  if (!gear.value) return;
  gear.value.special_rules = gear.value.special_rules.filter((r) => r !== rule);
}

function addCost() {
  if (!gear.value || !newCostResource.value.trim()) return;
  gear.value.crafting_costs.push({
    resource: newCostResource.value.trim(),
    quantity: newCostQuantity.value,
  });
  newCostResource.value = "";
  newCostQuantity.value = 1;
}

function removeCost(index: number) {
  if (!gear.value) return;
  gear.value.crafting_costs.splice(index, 1);
}

function navigateTo(id: number | null) {
  if (id !== null) router.push(`/gear/${id}`);
}

onMounted(load);
watch(() => props.id, load);
</script>

<template>
  <div>
    <!-- Top bar -->
    <div class="flex items-center justify-between mb-4">
      <router-link to="/" class="inline-flex items-center gap-1 text-sm text-muted-foreground hover:text-foreground">
        <ArrowLeft class="h-4 w-4" />
        Back to list
      </router-link>
      <div class="flex items-center gap-2">
        <span v-if="saved" class="text-sm text-green-400">Saved</span>
        <span v-if="error" class="text-sm text-red-400">{{ error }}</span>
        <Button @click="save" :disabled="saving">
          {{ saving ? "Saving..." : "Save" }}
        </Button>
      </div>
    </div>

    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <div v-else-if="gear" class="grid grid-cols-[300px_1fr] gap-6">
      <!-- Card image -->
      <div class="sticky top-4 self-start">
        <Card>
          <CardContent class="p-2">
            <img
              v-if="gear.image_path"
              :src="imageUrl(gear.image_path)"
              :alt="gear.name"
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

      <!-- Form -->
      <div class="flex flex-col gap-4">
        <!-- Name -->
        <div class="space-y-1">
          <Label>Name</Label>
          <Input v-model="gear.name" />
        </div>

        <!-- Type + Version -->
        <div class="flex gap-3">
          <div class="flex-1 space-y-1">
            <Label>Type</Label>
            <Select :model-value="gear.type ?? undefined" @update:model-value="(v) => gear!.type = v ?? null">
              <SelectTrigger>
                <SelectValue placeholder="Select type" />
              </SelectTrigger>
              <SelectContent>
                <SelectItem value="weapon">Weapon</SelectItem>
                <SelectItem value="armor">Armor</SelectItem>
                <SelectItem value="item">Item</SelectItem>
                <SelectItem value="other">Other</SelectItem>
              </SelectContent>
            </Select>
          </div>
          <div class="flex-1 space-y-1">
            <Label>Version</Label>
            <Input v-model="gear.version" />
          </div>
        </div>

        <!-- Expansion + Category -->
        <div class="flex gap-3">
          <div class="flex-1 space-y-1">
            <Label>Expansion</Label>
            <Input v-model="gear.expansion" />
          </div>
          <div class="flex-1 space-y-1">
            <Label>Category</Label>
            <Input v-model="gear.category" />
          </div>
        </div>

        <!-- Weapon Stats -->
        <Card v-if="gear.type === 'weapon'">
          <CardHeader class="pb-3">
            <CardTitle class="text-sm">Weapon Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex gap-3">
              <div class="flex-1 space-y-1">
                <Label>Speed</Label>
                <Input v-model="gear.speed" />
              </div>
              <div class="flex-1 space-y-1">
                <Label>Accuracy</Label>
                <Input v-model="gear.accuracy" />
              </div>
              <div class="flex-1 space-y-1">
                <Label>Strength</Label>
                <Input v-model="gear.strength" />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Armor Stats -->
        <Card v-if="gear.type === 'armor'">
          <CardHeader class="pb-3">
            <CardTitle class="text-sm">Armor Stats</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex gap-3">
              <div class="flex-1 space-y-1">
                <Label>Hit Location</Label>
                <Select :model-value="gear.hit_location ?? undefined" @update:model-value="(v) => gear!.hit_location = v ?? null">
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
                <Input v-model="gear.armor_rating" />
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Keywords -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-sm">Keywords</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex flex-wrap gap-1.5 items-center">
              <Badge
                v-for="kw in gear.keywords"
                :key="kw"
                variant="secondary"
                class="cursor-pointer gap-1"
                @click="removeKeyword(kw)"
              >
                {{ kw }}
                <X class="h-3 w-3" />
              </Badge>
              <div class="flex gap-1">
                <Input
                  v-model="newKeyword"
                  placeholder="Add keyword..."
                  class="h-7 w-28 text-xs"
                  @keydown.enter.prevent="addKeyword"
                />
                <Button variant="outline" size="icon" class="h-7 w-7" @click="addKeyword">
                  <Plus class="h-3 w-3" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Special Rules -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-sm">Special Rules</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex flex-wrap gap-1.5 items-center">
              <Badge
                v-for="rule in gear.special_rules"
                :key="rule"
                variant="outline"
                class="cursor-pointer gap-1"
                @click="removeRule(rule)"
              >
                {{ rule }}
                <X class="h-3 w-3" />
              </Badge>
              <div class="flex gap-1">
                <Input
                  v-model="newRule"
                  placeholder="Add rule..."
                  class="h-7 w-28 text-xs"
                  @keydown.enter.prevent="addRule"
                />
                <Button variant="outline" size="icon" class="h-7 w-7" @click="addRule">
                  <Plus class="h-3 w-3" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Card Text -->
        <div class="space-y-1">
          <Label>Card Text</Label>
          <Textarea v-model="gear.card_text" rows="4" />
        </div>

        <!-- Gained By -->
        <div class="space-y-1">
          <Label>Gained By</Label>
          <Input v-model="gear.gained_by" />
        </div>

        <!-- Crafting -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-sm">Crafting</CardTitle>
          </CardHeader>
          <CardContent class="space-y-3">
            <div class="space-y-1">
              <Label>Crafting Location</Label>
              <Input v-model="gear.crafting_location" />
            </div>
            <Separator />
            <div class="space-y-2">
              <div
                v-for="(cost, i) in gear.crafting_costs"
                :key="i"
                class="flex items-center gap-2"
              >
                <Input
                  v-model.number="cost.quantity"
                  type="number"
                  min="1"
                  class="w-16 text-center"
                />
                <span class="text-muted-foreground">×</span>
                <Input v-model="cost.resource" class="flex-1" />
                <Button variant="destructive" size="icon" class="h-8 w-8 shrink-0" @click="removeCost(i)">
                  <X class="h-3 w-3" />
                </Button>
              </div>
              <div class="flex items-center gap-2">
                <Input
                  v-model.number="newCostQuantity"
                  type="number"
                  min="1"
                  class="w-16 text-center"
                />
                <span class="text-muted-foreground">×</span>
                <Input
                  v-model="newCostResource"
                  placeholder="Resource..."
                  class="flex-1"
                  @keydown.enter.prevent="addCost"
                />
                <Button variant="outline" size="icon" class="h-8 w-8 shrink-0" @click="addCost">
                  <Plus class="h-3 w-3" />
                </Button>
              </div>
            </div>
          </CardContent>
        </Card>

        <!-- Affinities -->
        <Card>
          <CardHeader class="pb-3">
            <CardTitle class="text-sm">Affinities</CardTitle>
          </CardHeader>
          <CardContent>
            <div class="flex gap-3">
              <div v-for="dir in (['top', 'right', 'bottom', 'left'] as const)" :key="dir" class="flex-1 space-y-1">
                <Label>{{ dir.charAt(0).toUpperCase() + dir.slice(1) }}</Label>
                <Select
                  :model-value="(gear as Record<string, any>)[`affinity_${dir}`] ?? undefined"
                  @update:model-value="(v) => (gear as Record<string, any>)[`affinity_${dir}`] = v ?? null"
                >
                  <SelectTrigger>
                    <SelectValue placeholder="None" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="red">Red</SelectItem>
                    <SelectItem value="green">Green</SelectItem>
                    <SelectItem value="blue">Blue</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>

    <!-- Navigation -->
    <Separator class="my-6" />
    <div class="flex items-center justify-between pb-8">
      <Button variant="outline" :disabled="prevId === null" @click="navigateTo(prevId)">
        <ChevronLeft class="h-4 w-4 mr-1" />
        Prev
      </Button>
      <span v-if="gear" class="text-sm text-muted-foreground">
        {{ currentIndex + 1 }} / {{ allItems.length }}
      </span>
      <Button variant="outline" :disabled="nextId === null" @click="navigateTo(nextId)">
        Next
        <ChevronRight class="h-4 w-4 ml-1" />
      </Button>
    </div>
  </div>
</template>
