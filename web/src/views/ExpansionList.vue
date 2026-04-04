<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listExpansionsWithCounts, updateExpansion, deleteExpansion, createExpansion, listExpansionItems } from "../api";
import ItemsDialog from "../components/ItemsDialog.vue";
import ConfirmDialog from "../components/ConfirmDialog.vue";
import { usePerPage } from "../composables/usePerPage";
import type { ExpansionEntry } from "../api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Pencil, Trash2, Plus, SlidersHorizontal } from "lucide-vue-next";
import { Checkbox } from "@/components/ui/checkbox";

const items = ref<ExpansionEntry[]>([]);
const search = ref("");
const loading = ref(true);
const page = ref(1);
const perPage = usePerPage();
const sortField = ref<"name" | "count">("name");
const sortAsc = ref(true);

const itemsDialogOpen = ref(false);
const itemsDialogExpansion = ref("");
const enableDelete = ref(false);
const confirmDeleteOpen = ref(false);
const confirmDeleteName = ref("");
const confirmDeleteCount = ref(0);
const editDialogOpen = ref(false);
const isCreating = ref(false);
const editingExpansion = ref<string | null>(null);
const editName = ref("");
const editDescription = ref("");

const filtered = computed(() => {
  let result = items.value;
  if (search.value) {
    const q = search.value.toLowerCase();
    result = result.filter((i) => i.name.toLowerCase().includes(q) || i.description.toLowerCase().includes(q));
  }
  result = [...result].sort((a, b) => {
    const av = a[sortField.value];
    const bv = b[sortField.value];
    const cmp = typeof av === "number" ? av - (bv as number) : String(av).localeCompare(String(bv));
    return sortAsc.value ? cmp : -cmp;
  });
  return result;
});
const paged = computed(() => filtered.value.slice((page.value - 1) * perPage.value, page.value * perPage.value));
watch(search, () => { page.value = 1; });

function toggleSort(field: typeof sortField.value) {
  if (sortField.value === field) sortAsc.value = !sortAsc.value;
  else { sortField.value = field; sortAsc.value = true; }
  page.value = 1;
}

function sortIndicator(field: string) {
  if (sortField.value !== field) return "";
  return sortAsc.value ? " ↑" : " ↓";
}

async function load() { loading.value = true; items.value = await listExpansionsWithCounts(); loading.value = false; }
function startCreate() { isCreating.value = true; editingExpansion.value = null; editName.value = ""; editDescription.value = ""; editDialogOpen.value = true; }
function startEdit(item: ExpansionEntry) { isCreating.value = false; editingExpansion.value = item.name; editName.value = item.name; editDescription.value = item.description; editDialogOpen.value = true; }

async function saveEdit() {
  if (isCreating.value) {
    if (!editName.value.trim()) return;
    await createExpansion(editName.value.trim(), editDescription.value);
  } else if (editingExpansion.value) {
    const data: { name?: string; description?: string } = {};
    if (editName.value.trim() !== editingExpansion.value) data.name = editName.value.trim();
    data.description = editDescription.value;
    await updateExpansion(editingExpansion.value, data);
  }
  editDialogOpen.value = false; await load();
}

function promptDelete(name: string, count: number) {
  confirmDeleteName.value = name;
  confirmDeleteCount.value = count;
  confirmDeleteOpen.value = true;
}

async function confirmRemove() {
  await deleteExpansion(confirmDeleteName.value);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <Input v-model="search" placeholder="Search expansions..." class="max-w-sm" />
      <Button size="sm" @click="startCreate"><Plus class="h-4 w-4 mr-1" /> Add Expansion</Button>
      <Badge variant="secondary">{{ items.length }} expansions</Badge>
      <Popover>
        <PopoverTrigger as-child>
          <Button variant="outline" size="icon" class="h-9 w-9 shrink-0 ml-auto">
            <SlidersHorizontal class="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="w-48" align="end">
          <div class="flex items-center gap-2">
            <Checkbox id="enable-delete-exp" v-model="enableDelete" />
            <Label for="enable-delete-exp" class="text-sm">Enable deleting</Label>
          </div>
        </PopoverContent>
      </Popover>
    </div>
    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>
    <template v-if="!loading">
      <Table>
        <TableHeader><TableRow>
          <TableHead class="w-[200px] cursor-pointer select-none hover:text-foreground" @click="toggleSort('name')">Expansion{{ sortIndicator("name") }}</TableHead>
          <TableHead>Description</TableHead>
          <TableHead class="w-[100px] text-right cursor-pointer select-none hover:text-foreground" @click="toggleSort('count')">Items{{ sortIndicator("count") }}</TableHead>
          <TableHead :class="enableDelete ? 'w-[100px]' : 'w-[60px]'"></TableHead>
        </TableRow></TableHeader>
        <TableBody>
          <TableRow v-for="item in paged" :key="item.name">
            <TableCell class="font-medium">{{ item.name }}</TableCell>
            <TableCell class="text-muted-foreground text-sm">{{ item.description || "—" }}</TableCell>
            <TableCell class="text-right">
              <Badge variant="outline" class="cursor-pointer hover:bg-accent" @click="itemsDialogExpansion = item.name; itemsDialogOpen = true">{{ item.count }} items</Badge>
            </TableCell>
            <TableCell>
              <div class="flex justify-end gap-1">
                <Button variant="ghost" size="icon" class="h-8 w-8" @click="startEdit(item)"><Pencil class="h-4 w-4" /></Button>
                <Button v-if="enableDelete" variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="promptDelete(item.name, item.count)"><Trash2 class="h-4 w-4" /></Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <PaginationControls :total="filtered.length" :page="page" :per-page="perPage" @update:page="(v) => page = v" @update:per-page="(v) => perPage = v" />
    </template>
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader><DialogTitle>{{ isCreating ? "Add Expansion" : "Edit Expansion" }}</DialogTitle></DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1"><Label>Name</Label><Input v-model="editName" :placeholder="isCreating ? 'Enter expansion name...' : ''" @keydown.enter.prevent="saveEdit" /></div>
          <div class="space-y-1"><Label>Description</Label><Textarea v-model="editDescription" placeholder="Describe this expansion..." rows="3" /></div>
        </div>
        <DialogFooter><Button variant="outline" @click="editDialogOpen = false">Cancel</Button><Button @click="saveEdit">{{ isCreating ? "Add" : "Save" }}</Button></DialogFooter>
      </DialogContent>
    </Dialog>
    <ItemsDialog v-model:open="itemsDialogOpen" :title="`Items in: ${itemsDialogExpansion}`" :fetch-items="() => listExpansionItems(itemsDialogExpansion)" />

    <ConfirmDialog v-model:open="confirmDeleteOpen" title="Delete Expansion" :description="`Remove &quot;${confirmDeleteName}&quot; from ${confirmDeleteCount} items?`" @confirm="confirmRemove" />
  </div>
</template>
