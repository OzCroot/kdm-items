<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listLocationsWithCounts, updateLocation, deleteLocation, createLocation, listLocationItems } from "../api";
import ItemsDialog from "../components/ItemsDialog.vue";
import { usePerPage } from "../composables/usePerPage";
import type { LocationEntry } from "../api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";
import { PaginationControls } from "@/components/ui/pagination-controls";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Pencil, Trash2, Plus } from "lucide-vue-next";

const items = ref<LocationEntry[]>([]);
const search = ref("");
const loading = ref(true);
const page = ref(1);
const perPage = usePerPage();

const itemsDialogOpen = ref(false);
const itemsDialogLocation = ref("");

const editDialogOpen = ref(false);
const isCreating = ref(false);
const editingLocation = ref<string | null>(null);
const editName = ref("");
const editDefinition = ref("");

const filtered = computed(() => {
  if (!search.value) return items.value;
  const q = search.value.toLowerCase();
  return items.value.filter(
    (i) => i.name.toLowerCase().includes(q) || i.definition.toLowerCase().includes(q)
  );
});

const paged = computed(() => {
  const start = (page.value - 1) * perPage.value;
  return filtered.value.slice(start, start + perPage.value);
});

watch(search, () => { page.value = 1; });

async function load() {
  loading.value = true;
  items.value = await listLocationsWithCounts();
  loading.value = false;
}

function startCreate() {
  isCreating.value = true;
  editingLocation.value = null;
  editName.value = "";
  editDefinition.value = "";
  editDialogOpen.value = true;
}

function startEdit(item: LocationEntry) {
  isCreating.value = false;
  editingLocation.value = item.name;
  editName.value = item.name;
  editDefinition.value = item.definition;
  editDialogOpen.value = true;
}

async function saveEdit() {
  if (isCreating.value) {
    if (!editName.value.trim()) return;
    await createLocation(editName.value.trim(), editDefinition.value);
  } else if (editingLocation.value) {
    const data: { name?: string; definition?: string } = {};
    if (editName.value.trim() !== editingLocation.value) data.name = editName.value.trim();
    data.definition = editDefinition.value;
    await updateLocation(editingLocation.value, data);
  }
  editDialogOpen.value = false;
  await load();
}

async function remove(name: string, count: number) {
  if (!confirm(`Remove "${name}"? (${count} items will have their crafting location cleared)`)) return;
  await deleteLocation(name);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <Input
        v-model="search"
        placeholder="Search locations or definitions..."
        class="max-w-sm"
      />
      <Button size="sm" @click="startCreate">
        <Plus class="h-4 w-4 mr-1" /> Add Location
      </Button>
      <Badge variant="secondary">{{ items.length }} locations</Badge>
    </div>

    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <template v-if="!loading">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-[160px]">Location</TableHead>
            <TableHead>Definition</TableHead>
            <TableHead class="w-[100px] text-right">Items</TableHead>
            <TableHead class="w-[80px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="item in paged" :key="item.name">
            <TableCell class="font-medium">{{ item.name }}</TableCell>
            <TableCell class="text-muted-foreground text-sm">
              {{ item.definition || "—" }}
            </TableCell>
            <TableCell class="text-right">
              <Badge
                variant="outline"
                class="cursor-pointer hover:bg-accent"
                @click="itemsDialogLocation = item.name; itemsDialogOpen = true"
              >
                {{ item.count }} items
              </Badge>
            </TableCell>
            <TableCell>
              <div class="flex justify-end gap-1">
                <Button variant="ghost" size="icon" class="h-8 w-8" @click="startEdit(item)">
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="remove(item.name, item.count)">
                  <Trash2 class="h-4 w-4" />
                </Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>

      <PaginationControls
        :total="filtered.length"
        :page="page"
        :per-page="perPage"
        @update:page="(v) => page = v"
        @update:per-page="(v) => perPage = v"
      />
    </template>

    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ isCreating ? "Add Settlement Location" : "Edit Settlement Location" }}</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1">
            <Label>Name</Label>
            <Input
              v-model="editName"
              :placeholder="isCreating ? 'Enter location name...' : ''"
              @keydown.enter.prevent="saveEdit"
            />
          </div>
          <div class="space-y-1">
            <Label>Definition</Label>
            <Textarea
              v-model="editDefinition"
              placeholder="Enter the definition for this location..."
              rows="4"
            />
          </div>
        </div>
        <DialogFooter>
          <Button variant="outline" @click="editDialogOpen = false">Cancel</Button>
          <Button @click="saveEdit">{{ isCreating ? "Add" : "Save" }}</Button>
        </DialogFooter>
      </DialogContent>
    </Dialog>

    <ItemsDialog
      v-model:open="itemsDialogOpen"
      :title="`Items at: ${itemsDialogLocation}`"
      :fetch-items="() => listLocationItems(itemsDialogLocation)"
    />
  </div>
</template>
