<script setup lang="ts">
import { ref, onMounted, computed } from "vue";
import { useRouter } from "vue-router";
import { getGear, updateGear, imageUrl, listGear } from "../api";
import type { GearDetail, GearListItem } from "../types";

const props = defineProps<{ id: string }>();
const router = useRouter();

const gear = ref<GearDetail | null>(null);
const allItems = ref<GearListItem[]>([]);
const loading = ref(true);
const saving = ref(false);
const saved = ref(false);
const error = ref("");
const newKeyword = ref("");
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

// Re-load when route changes (prev/next navigation)
import { watch } from "vue";
watch(() => props.id, load);
</script>

<template>
  <div class="gear-edit">
    <div class="top-bar">
      <router-link to="/" class="back-link">Back to list</router-link>
      <div class="actions">
        <span v-if="saved" class="save-indicator">Saved</span>
        <span v-if="error" class="error-indicator">{{ error }}</span>
        <button @click="save" :disabled="saving" class="save-btn">
          {{ saving ? "Saving..." : "Save" }}
        </button>
      </div>
    </div>

    <div v-if="loading" class="loading">Loading...</div>

    <div v-else-if="gear" class="content">
      <div class="card-image">
        <img
          v-if="gear.image_path"
          :src="imageUrl(gear.image_path)"
          :alt="gear.name"
        />
        <div v-else class="no-image">No image</div>
      </div>

      <div class="form">
        <div class="field">
          <label>Name</label>
          <input v-model="gear.name" />
        </div>

        <div class="field-row">
          <div class="field">
            <label>Type</label>
            <select v-model="gear.type">
              <option value="weapon">Weapon</option>
              <option value="armor">Armor</option>
              <option value="item">Item</option>
              <option value="other">Other</option>
            </select>
          </div>
          <div class="field">
            <label>Version</label>
            <input v-model="gear.version" />
          </div>
        </div>

        <div class="field-row">
          <div class="field">
            <label>Expansion</label>
            <input v-model="gear.expansion" />
          </div>
          <div class="field">
            <label>Category</label>
            <input v-model="gear.category" />
          </div>
        </div>

        <!-- Weapon Stats -->
        <fieldset v-if="gear.type === 'weapon'">
          <legend>Weapon Stats</legend>
          <div class="field-row">
            <div class="field">
              <label>Speed</label>
              <input v-model="gear.speed" />
            </div>
            <div class="field">
              <label>Accuracy</label>
              <input v-model="gear.accuracy" />
            </div>
            <div class="field">
              <label>Strength</label>
              <input v-model="gear.strength" />
            </div>
          </div>
        </fieldset>

        <!-- Armor Stats -->
        <fieldset v-if="gear.type === 'armor'">
          <legend>Armor Stats</legend>
          <div class="field-row">
            <div class="field">
              <label>Hit Location</label>
              <select v-model="gear.hit_location">
                <option value="">—</option>
                <option value="Head">Head</option>
                <option value="Arms">Arms</option>
                <option value="Body">Body</option>
                <option value="Waist">Waist</option>
                <option value="Legs">Legs</option>
              </select>
            </div>
            <div class="field">
              <label>Armor Rating</label>
              <input v-model="gear.armor_rating" />
            </div>
          </div>
        </fieldset>

        <!-- Keywords -->
        <fieldset>
          <legend>Keywords</legend>
          <div class="tags">
            <span
              v-for="kw in gear.keywords"
              :key="kw"
              class="tag"
              @click="removeKeyword(kw)"
              title="Click to remove"
            >
              {{ kw }} ×
            </span>
            <div class="tag-input">
              <input
                v-model="newKeyword"
                placeholder="Add keyword..."
                @keydown.enter.prevent="addKeyword"
              />
              <button @click="addKeyword">+</button>
            </div>
          </div>
        </fieldset>

        <!-- Card Text -->
        <div class="field">
          <label>Card Text</label>
          <textarea v-model="gear.card_text" rows="4"></textarea>
        </div>

        <!-- Gained By -->
        <div class="field">
          <label>Gained By</label>
          <input v-model="gear.gained_by" />
        </div>

        <!-- Crafting -->
        <fieldset>
          <legend>Crafting</legend>
          <div class="field">
            <label>Crafting Location</label>
            <input v-model="gear.crafting_location" />
          </div>
          <div class="cost-list">
            <div
              v-for="(cost, i) in gear.crafting_costs"
              :key="i"
              class="cost-item"
            >
              <input v-model.number="cost.quantity" type="number" min="1" class="cost-qty" />
              <span>×</span>
              <input v-model="cost.resource" class="cost-resource" />
              <button @click="removeCost(i)" class="remove-btn">×</button>
            </div>
            <div class="cost-add">
              <input
                v-model.number="newCostQuantity"
                type="number"
                min="1"
                class="cost-qty"
              />
              <span>×</span>
              <input
                v-model="newCostResource"
                placeholder="Resource..."
                class="cost-resource"
                @keydown.enter.prevent="addCost"
              />
              <button @click="addCost">+</button>
            </div>
          </div>
        </fieldset>

        <!-- Affinities -->
        <fieldset>
          <legend>Affinities</legend>
          <div class="field-row">
            <div class="field" v-for="dir in ['top', 'right', 'bottom', 'left']" :key="dir">
              <label>{{ dir.charAt(0).toUpperCase() + dir.slice(1) }}</label>
              <select v-model="(gear as Record<string, unknown>)[`affinity_${dir}`]">
                <option :value="null">None</option>
                <option value="red">Red</option>
                <option value="green">Green</option>
                <option value="blue">Blue</option>
              </select>
            </div>
          </div>
        </fieldset>
      </div>
    </div>

    <div class="nav-bar">
      <button :disabled="prevId === null" @click="navigateTo(prevId)">
        ← Prev
      </button>
      <span v-if="gear" class="nav-position">
        {{ currentIndex + 1 }} / {{ allItems.length }}
      </span>
      <button :disabled="nextId === null" @click="navigateTo(nextId)">
        Next →
      </button>
    </div>
  </div>
</template>

<style scoped>
.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 1rem;
}

.back-link {
  color: #8bf;
}

.actions {
  display: flex;
  gap: 0.5rem;
  align-items: center;
}

.save-indicator {
  color: #8f8;
  font-size: 0.85rem;
}

.error-indicator {
  color: #f88;
  font-size: 0.85rem;
}

.save-btn {
  padding: 0.4rem 1.2rem;
  background: #2a6a2a;
  color: white;
  border: none;
  border-radius: 4px;
  cursor: pointer;
}

.save-btn:disabled {
  opacity: 0.5;
}

.content {
  display: grid;
  grid-template-columns: 300px 1fr;
  gap: 1.5rem;
}

.card-image {
  position: sticky;
  top: 1rem;
  align-self: start;
}

.card-image img {
  width: 100%;
  border-radius: 6px;
  border: 1px solid #444;
}

.no-image {
  width: 100%;
  aspect-ratio: 3/4;
  background: #1a1a2e;
  border: 1px dashed #444;
  border-radius: 6px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #666;
}

.form {
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}

.field {
  display: flex;
  flex-direction: column;
  gap: 0.2rem;
  flex: 1;
}

.field label {
  font-size: 0.8rem;
  color: #999;
  text-transform: uppercase;
  letter-spacing: 0.05em;
}

.field input,
.field select,
.field textarea {
  padding: 0.4rem 0.5rem;
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 4px;
  color: #eee;
  font-size: 0.9rem;
}

.field textarea {
  resize: vertical;
  font-family: inherit;
}

.field-row {
  display: flex;
  gap: 0.75rem;
}

fieldset {
  border: 1px solid #333;
  border-radius: 6px;
  padding: 0.75rem;
}

legend {
  font-size: 0.85rem;
  color: #aaa;
  padding: 0 0.4rem;
}

.tags {
  display: flex;
  flex-wrap: wrap;
  gap: 0.3rem;
  align-items: center;
}

.tag {
  display: inline-block;
  padding: 0.2rem 0.5rem;
  background: #2a2a4a;
  border-radius: 3px;
  font-size: 0.8rem;
  cursor: pointer;
}

.tag:hover {
  background: #4a2020;
}

.tag-input {
  display: flex;
  gap: 0.2rem;
}

.tag-input input {
  width: 120px;
  padding: 0.2rem 0.4rem;
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 3px;
  color: #eee;
  font-size: 0.8rem;
}

.tag-input button {
  padding: 0.2rem 0.5rem;
  background: #2a4a2a;
  border: none;
  border-radius: 3px;
  color: #8f8;
  cursor: pointer;
}

.cost-list {
  display: flex;
  flex-direction: column;
  gap: 0.3rem;
  margin-top: 0.5rem;
}

.cost-item,
.cost-add {
  display: flex;
  align-items: center;
  gap: 0.3rem;
}

.cost-qty {
  width: 50px;
  padding: 0.3rem;
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 3px;
  color: #eee;
  text-align: center;
}

.cost-resource {
  flex: 1;
  padding: 0.3rem 0.4rem;
  background: #1a1a2e;
  border: 1px solid #333;
  border-radius: 3px;
  color: #eee;
}

.cost-add input {
  font-size: 0.85rem;
}

.cost-add button {
  padding: 0.3rem 0.6rem;
  background: #2a4a2a;
  border: none;
  border-radius: 3px;
  color: #8f8;
  cursor: pointer;
}

.remove-btn {
  padding: 0.2rem 0.5rem;
  background: #4a2020;
  border: none;
  border-radius: 3px;
  color: #f88;
  cursor: pointer;
}

.nav-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-top: 1.5rem;
  padding: 0.75rem 0;
  border-top: 1px solid #333;
}

.nav-bar button {
  padding: 0.4rem 1rem;
  background: #2a2a4a;
  border: none;
  border-radius: 4px;
  color: #eee;
  cursor: pointer;
}

.nav-bar button:disabled {
  opacity: 0.3;
  cursor: default;
}

.nav-position {
  color: #888;
  font-size: 0.85rem;
}

.loading {
  text-align: center;
  padding: 2rem;
  color: #888;
}
</style>
