<script setup lang="ts">
import { ref, onMounted, onUnmounted, computed, watch } from "vue";
import { useRouter } from "vue-router";
import { getGear, updateGear, listKeywordsWithCounts, listSpecialRulesWithCounts, listLocations, listVersions, listExpansions, listIcons, imageUrl } from "../api";
import type { IconEntry } from "../api";
import type { KeywordEntry, SpecialRuleEntry } from "../api";
import type { GearDetail, CraftingCost } from "../types";
import { useGearFiltersStore } from "../stores/gearFilters";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Label } from "@/components/ui/label";
import { Textarea } from "@/components/ui/textarea";
import { Separator } from "@/components/ui/separator";
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from "@/components/ui/select";
import { Tabs, TabsContent } from "@/components/ui/tabs";
import TagPickerDialog from "../components/TagPickerDialog.vue";
import GearImageCard from "../components/gear/GearImageCard.vue";
import WeaponStats from "../components/gear/WeaponStats.vue";
import ArmorStats from "../components/gear/ArmorStats.vue";
import TagBadges from "../components/gear/TagBadges.vue";
import AffinityPicker from "../components/gear/AffinityPicker.vue";
import CraftingCostEditor from "../components/gear/CraftingCostEditor.vue";
import GearCardPreview from "../components/gear/GearCardPreview.vue";
import { ChevronLeft, ChevronRight, ExternalLink } from "lucide-vue-next";
import { toast } from "vue-sonner";

const props = defineProps<{ id: string }>();
const router = useRouter();
const store = useGearFiltersStore();

const gear = ref<GearDetail | null>(null);
const loading = ref(true);
const saving = ref(false);
const allKeywordEntries = ref<KeywordEntry[]>([]);
const allRuleEntries = ref<SpecialRuleEntry[]>([]);
const allLocations = ref<string[]>([]);
const allVersions = ref<string[]>([]);
const allExpansions = ref<string[]>([]);
const allIconEntries = ref<IconEntry[]>([]);
const iconImages = computed(() => {
  const map: Record<string, string> = {};
  for (const icon of allIconEntries.value) {
    map[icon.tag] = imageUrl(`icons/${icon.tag}.png`);
  }
  return map;
});
const iconDescriptions = computed(() => {
  const map: Record<string, string> = {};
  for (const icon of allIconEntries.value) {
    map[icon.tag] = icon.description || icon.display_name;
  }
  return map;
});
const allKeywords = computed(() => allKeywordEntries.value.map((e) => e.keyword));
const allRules = computed(() => allRuleEntries.value.map((e) => e.rule));
const keywordDefs = computed(() => Object.fromEntries(allKeywordEntries.value.map((e) => [e.keyword, e.definition])));
const ruleDefs = computed(() => Object.fromEntries(allRuleEntries.value.map((e) => [e.rule, e.definition])));
const keywordPickerOpen = ref(false);
const rulePickerOpen = ref(false);
const activeTab = ref("details");

const gearId = computed(() => parseInt(props.id, 10));

const navItems = computed(() => store.filtered);
const currentIndex = computed(() => navItems.value.findIndex((i) => i.id === gearId.value));
const prevId = computed(() => currentIndex.value > 0 ? navItems.value[currentIndex.value - 1].id : null);
const nextId = computed(() => currentIndex.value < navItems.value.length - 1 ? navItems.value[currentIndex.value + 1].id : null);

async function load() {
  loading.value = true;
  try {
    gear.value = await getGear(gearId.value);
    await store.init();
    if (!allKeywordEntries.value.length) {
      const [kws, rules, locs, vers, exps, icons] = await Promise.all([
        listKeywordsWithCounts(), listSpecialRulesWithCounts(), listLocations(), listVersions(), listExpansions(), listIcons(),
      ]);
      allKeywordEntries.value = kws;
      allRuleEntries.value = rules;
      allLocations.value = locs;
      allVersions.value = vers;
      allExpansions.value = exps;
      allIconEntries.value = icons;
    }
  } catch (e: unknown) {
    toast.error(e instanceof Error ? e.message : "Failed to load");
  }
  loading.value = false;
}

async function save() {
  if (!gear.value) return;
  saving.value = true;
  try {
    gear.value = await updateGear(gearId.value, gear.value);
    toast.success("Changes saved");
  } catch (e: unknown) {
    toast.error(e instanceof Error ? e.message : "Failed to save");
  }
  saving.value = false;
}

function addCost(cost: CraftingCost) {
  gear.value?.crafting_costs.push(cost);
}

function removeCost(index: number) {
  gear.value?.crafting_costs.splice(index, 1);
}

function navigateTo(id: number | null) {
  if (id !== null) router.push(`/gear/${id}`);
}

function onKeydown(e: KeyboardEvent) {
  const tag = (e.target as HTMLElement)?.tagName;
  if (tag === "INPUT" || tag === "TEXTAREA" || tag === "SELECT") return;
  if (e.key === "s" || e.key === "S") {
    e.preventDefault();
    save();
  } else if (e.key === "ArrowLeft" && prevId.value !== null) {
    e.preventDefault();
    navigateTo(prevId.value);
  } else if (e.key === "ArrowRight" && nextId.value !== null) {
    e.preventDefault();
    navigateTo(nextId.value);
  }
}

onMounted(() => {
  load();
  window.addEventListener("keydown", onKeydown);
});
onUnmounted(() => {
  window.removeEventListener("keydown", onKeydown);
});
watch(() => props.id, load);
</script>

<template>
  <div>
    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <Tabs v-else-if="gear" :model-value="activeTab" @update:model-value="(v) => activeTab = v as string">
      <!-- App bar -->
      <div class="-mx-4 px-4 py-3 mb-4 bg-card border-y border-border flex items-center gap-4">
        <h2 class="text-lg font-semibold truncate flex-1">{{ gear.name }}</h2>
        <nav class="flex gap-4 shrink-0">
          <button
            v-for="tab in [{ value: 'details', label: 'Details' }, { value: 'crafting', label: 'Crafting' }, { value: 'preview', label: 'Preview' }]"
            :key="tab.value"
            class="text-sm pb-1 border-b-2 transition-colors"
            :class="activeTab === tab.value
              ? 'text-foreground border-foreground'
              : 'text-muted-foreground border-transparent hover:text-foreground hover:border-muted-foreground'"
            @click="activeTab = tab.value"
          >
            {{ tab.label }}
          </button>
        </nav>
        <Separator orientation="vertical" class="h-5" />
        <div class="flex items-center gap-3 shrink-0">
          <a
            v-if="gear.url"
            :href="gear.url"
            target="_blank"
            class="text-sm text-muted-foreground hover:text-foreground inline-flex items-center gap-1"
          >
            <ExternalLink class="h-3.5 w-3.5" />
            Wiki
          </a>
          <Button size="sm" @click="save" :disabled="saving">
            {{ saving ? "Saving..." : "Save" }}
          </Button>
        </div>
      </div>

      <TabsContent value="details">
        <div class="grid grid-cols-[300px_1fr] gap-6 mt-4">
          <GearImageCard :image-path="gear.image_path" :name="gear.name" />

          <div class="flex flex-col gap-4">
            <!-- Core fields 2x2 -->
            <div class="grid grid-cols-2 gap-3">
              <div class="space-y-1">
                <Label>Name</Label>
                <Input v-model="gear.name" />
              </div>
              <div class="space-y-1">
                <Label>Type</Label>
                <Select :model-value="gear.type ?? undefined" @update:model-value="(v) => gear!.type = v ?? null">
                  <SelectTrigger><SelectValue placeholder="Select type" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem value="weapon">Weapon</SelectItem>
                    <SelectItem value="armor">Armor</SelectItem>
                    <SelectItem value="item">Item</SelectItem>
                    <SelectItem value="other">Other</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-1">
                <Label>Expansion</Label>
                <Select :model-value="gear.expansion ?? undefined" @update:model-value="(v) => gear!.expansion = v ?? null">
                  <SelectTrigger><SelectValue placeholder="Select expansion" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="exp in allExpansions" :key="exp" :value="exp">{{ exp }}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
              <div class="space-y-1">
                <Label>Version</Label>
                <Select :model-value="gear.version ?? undefined" @update:model-value="(v) => gear!.version = v ?? null">
                  <SelectTrigger><SelectValue placeholder="Select version" /></SelectTrigger>
                  <SelectContent>
                    <SelectItem v-for="ver in allVersions" :key="ver" :value="ver">{{ ver }}</SelectItem>
                  </SelectContent>
                </Select>
              </div>
            </div>

            <WeaponStats v-if="gear.type === 'weapon'" v-model:speed="gear.speed" v-model:accuracy="gear.accuracy" v-model:strength="gear.strength" />
            <ArmorStats v-if="gear.type === 'armor'" v-model:hit-location="gear.hit_location" v-model:armor-rating="gear.armor_rating" />

            <TagBadges title="Keywords" :items="gear.keywords" :definitions="keywordDefs" variant="secondary" @edit="keywordPickerOpen = true" />
            <TagBadges title="Special Rules" :items="gear.special_rules" :definitions="ruleDefs" variant="outline" @edit="rulePickerOpen = true" />

            <div class="space-y-1">
              <Label>Card Text</Label>
              <Textarea v-model="gear.card_text" rows="4" />
            </div>

            <AffinityPicker v-model:top="gear.affinity_top" v-model:bottom="gear.affinity_bottom" v-model:left="gear.affinity_left" v-model:right="gear.affinity_right" />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="crafting">
        <div class="grid grid-cols-[300px_1fr] gap-6 mt-4">
          <GearImageCard :image-path="gear.image_path" :name="gear.name" />

          <div class="flex flex-col gap-4">
            <CraftingCostEditor
              :costs="gear.crafting_costs"
              :locations="allLocations"
              v-model:crafting-location="gear.crafting_location"
              v-model:gained-by="gear.gained_by"
              @add-cost="addCost"
              @remove-cost="removeCost"
            />
          </div>
        </div>
      </TabsContent>

      <TabsContent value="preview">
        <div class="grid grid-cols-[300px_1fr] gap-6 mt-4">
          <GearImageCard :image-path="gear.image_path" :name="gear.name" />
          <GearCardPreview
            :gear="gear"
            :icon-images="iconImages"
            :keyword-definitions="keywordDefs"
            :rule-definitions="ruleDefs"
            :icon-descriptions="iconDescriptions"
          />
        </div>
      </TabsContent>

      <!-- Picker dialogs (outside tabs so they overlay properly) -->
      <TagPickerDialog v-model:open="keywordPickerOpen" title="Select Keywords" :options="allKeywords" :selected="gear.keywords" :descriptions="keywordDefs" @update:selected="(v) => gear!.keywords = v" />
      <TagPickerDialog v-model:open="rulePickerOpen" title="Select Special Rules" :options="allRules" :selected="gear.special_rules" :descriptions="ruleDefs" @update:selected="(v) => gear!.special_rules = v" />
    </Tabs>

    <!-- Navigation -->
    <Separator class="my-6" />
    <div class="flex items-center justify-between pb-8">
      <Button variant="outline" :disabled="prevId === null" @click="navigateTo(prevId)">
        <ChevronLeft class="h-4 w-4 mr-1" /> Prev
      </Button>
      <span v-if="gear" class="text-sm text-muted-foreground">
        {{ currentIndex + 1 }} / {{ navItems.length }}
      </span>
      <Button variant="outline" :disabled="nextId === null" @click="navigateTo(nextId)">
        Next <ChevronRight class="h-4 w-4 ml-1" />
      </Button>
    </div>
  </div>
</template>
