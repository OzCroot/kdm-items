<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listVersionsWithCounts, updateVersion, deleteVersion, createVersion, listVersionItems } from "../api";
import ItemsDialog from "../components/ItemsDialog.vue";
import { usePerPage } from "../composables/usePerPage";
import type { VersionEntry } from "../api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Dialog, DialogContent, DialogHeader, DialogTitle, DialogFooter } from "@/components/ui/dialog";
import { PaginationControls } from "@/components/ui/pagination-controls";
import { Table, TableBody, TableCell, TableHead, TableHeader, TableRow } from "@/components/ui/table";
import { Pencil, Trash2, Plus } from "lucide-vue-next";

const items = ref<VersionEntry[]>([]);
const search = ref("");
const loading = ref(true);
const page = ref(1);
const perPage = usePerPage();

const itemsDialogOpen = ref(false);
const itemsDialogVersion = ref("");
const editDialogOpen = ref(false);
const isCreating = ref(false);
const editingVersion = ref<string | null>(null);
const editName = ref("");
const editDescription = ref("");

const filtered = computed(() => {
  if (!search.value) return items.value;
  const q = search.value.toLowerCase();
  return items.value.filter((i) => i.name.toLowerCase().includes(q) || i.description.toLowerCase().includes(q));
});
const paged = computed(() => filtered.value.slice((page.value - 1) * perPage.value, page.value * perPage.value));
watch(search, () => { page.value = 1; });

async function load() { loading.value = true; items.value = await listVersionsWithCounts(); loading.value = false; }
function startCreate() { isCreating.value = true; editingVersion.value = null; editName.value = ""; editDescription.value = ""; editDialogOpen.value = true; }
function startEdit(item: VersionEntry) { isCreating.value = false; editingVersion.value = item.name; editName.value = item.name; editDescription.value = item.description; editDialogOpen.value = true; }

async function saveEdit() {
  if (isCreating.value) {
    if (!editName.value.trim()) return;
    await createVersion(editName.value.trim(), editDescription.value);
  } else if (editingVersion.value) {
    const data: { name?: string; description?: string } = {};
    if (editName.value.trim() !== editingVersion.value) data.name = editName.value.trim();
    data.description = editDescription.value;
    await updateVersion(editingVersion.value, data);
  }
  editDialogOpen.value = false; await load();
}

async function remove(name: string, count: number) {
  if (!confirm(`Remove version "${name}"? (${count} items affected)`)) return;
  await deleteVersion(name); await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <Input v-model="search" placeholder="Search versions..." class="max-w-sm" />
      <Button size="sm" @click="startCreate"><Plus class="h-4 w-4 mr-1" /> Add Version</Button>
      <Badge variant="secondary">{{ items.length }} versions</Badge>
    </div>
    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>
    <template v-if="!loading">
      <Table>
        <TableHeader><TableRow>
          <TableHead class="w-[100px]">Version</TableHead>
          <TableHead>Description</TableHead>
          <TableHead class="w-[100px] text-right">Items</TableHead>
          <TableHead class="w-[80px]"></TableHead>
        </TableRow></TableHeader>
        <TableBody>
          <TableRow v-for="item in paged" :key="item.name">
            <TableCell class="font-medium">{{ item.name }}</TableCell>
            <TableCell class="text-muted-foreground text-sm">{{ item.description || "—" }}</TableCell>
            <TableCell class="text-right">
              <Badge variant="outline" class="cursor-pointer hover:bg-accent" @click="itemsDialogVersion = item.name; itemsDialogOpen = true">{{ item.count }} items</Badge>
            </TableCell>
            <TableCell>
              <div class="flex justify-end gap-1">
                <Button variant="ghost" size="icon" class="h-8 w-8" @click="startEdit(item)"><Pencil class="h-4 w-4" /></Button>
                <Button variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="remove(item.name, item.count)"><Trash2 class="h-4 w-4" /></Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <PaginationControls :total="filtered.length" :page="page" :per-page="perPage" @update:page="(v) => page = v" @update:per-page="(v) => perPage = v" />
    </template>
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader><DialogTitle>{{ isCreating ? "Add Version" : "Edit Version" }}</DialogTitle></DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1"><Label>Name</Label><Input v-model="editName" :placeholder="isCreating ? 'e.g. 1.6' : ''" @keydown.enter.prevent="saveEdit" /></div>
          <div class="space-y-1"><Label>Description</Label><Textarea v-model="editDescription" placeholder="Describe this version..." rows="3" /></div>
        </div>
        <DialogFooter><Button variant="outline" @click="editDialogOpen = false">Cancel</Button><Button @click="saveEdit">{{ isCreating ? "Add" : "Save" }}</Button></DialogFooter>
      </DialogContent>
    </Dialog>
    <ItemsDialog v-model:open="itemsDialogOpen" :title="`Items with version: ${itemsDialogVersion}`" :fetch-items="() => listVersionItems(itemsDialogVersion)" />
  </div>
</template>
