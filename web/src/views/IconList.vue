<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listIcons, updateIcon, deleteIcon, createIcon, imageUrl } from "../api";
import { usePerPage } from "../composables/usePerPage";
import type { IconEntry } from "../api";
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
import ConfirmDialog from "../components/ConfirmDialog.vue";

const items = ref<IconEntry[]>([]);
const search = ref("");
const loading = ref(true);
const page = ref(1);
const perPage = usePerPage();
const sortField = ref<"tag" | "display_name">("tag");
const sortAsc = ref(true);

const enableDelete = ref(false);
const confirmDeleteOpen = ref(false);
const confirmDeleteName = ref("");
const confirmDeleteCount = ref(0);
const editDialogOpen = ref(false);
const isCreating = ref(false);
const editingTag = ref<string | null>(null);
const editTag = ref("");
const editDisplayName = ref("");
const editIconUrl = ref("");
const editDescription = ref("");

const filtered = computed(() => {
  let result = items.value;
  if (search.value) {
    const q = search.value.toLowerCase();
    result = result.filter((i) => i.tag.toLowerCase().includes(q) || i.display_name.toLowerCase().includes(q) || i.description.toLowerCase().includes(q));
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

async function load() { loading.value = true; items.value = await listIcons(); loading.value = false; }

function startCreate() { isCreating.value = true; editingTag.value = null; editTag.value = ""; editDisplayName.value = ""; editIconUrl.value = ""; editDescription.value = ""; editDialogOpen.value = true; }
function startEdit(item: IconEntry) { isCreating.value = false; editingTag.value = item.tag; editTag.value = item.tag; editDisplayName.value = item.display_name; editIconUrl.value = item.icon_url; editDescription.value = item.description; editDialogOpen.value = true; }

async function saveEdit() {
  if (isCreating.value) {
    if (!editTag.value.trim()) return;
    await createIcon(editTag.value.trim(), editDisplayName.value || editTag.value.trim(), editIconUrl.value, editDescription.value);
  } else if (editingTag.value) {
    const data: { tag?: string; display_name?: string; icon_url?: string; description?: string } = {};
    if (editTag.value.trim() !== editingTag.value) data.tag = editTag.value.trim();
    data.display_name = editDisplayName.value;
    data.icon_url = editIconUrl.value;
    data.description = editDescription.value;
    await updateIcon(editingTag.value, data);
  }
  editDialogOpen.value = false; await load();
}

function promptDelete(tag: string) {
  confirmDeleteName.value = tag;
  confirmDeleteCount.value = 0;
  confirmDeleteOpen.value = true;
}

async function confirmRemove() {
  await deleteIcon(confirmDeleteName.value);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <Input v-model="search" placeholder="Search icons..." class="max-w-sm" />
      <Button size="sm" @click="startCreate"><Plus class="h-4 w-4 mr-1" /> Add Icon</Button>
      <Badge variant="secondary">{{ items.length }} icons</Badge>
      <Popover>
        <PopoverTrigger as-child>
          <Button variant="outline" size="icon" class="h-9 w-9 shrink-0 ml-auto">
            <SlidersHorizontal class="h-4 w-4" />
          </Button>
        </PopoverTrigger>
        <PopoverContent class="w-48" align="end">
          <div class="flex items-center gap-2">
            <Checkbox id="enable-delete-icon" v-model="enableDelete" />
            <Label for="enable-delete-icon" class="text-sm">Enable deleting</Label>
          </div>
        </PopoverContent>
      </Popover>
    </div>
    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>
    <template v-if="!loading">
      <Table>
        <TableHeader><TableRow>
          <TableHead class="w-[50px]"></TableHead>
          <TableHead class="w-[140px] cursor-pointer select-none hover:text-foreground" @click="toggleSort('tag')">Tag{{ sortIndicator("tag") }}</TableHead>
          <TableHead class="w-[140px] cursor-pointer select-none hover:text-foreground" @click="toggleSort('display_name')">Display Name{{ sortIndicator("display_name") }}</TableHead>
          <TableHead>Description</TableHead>
          <TableHead :class="enableDelete ? 'w-[100px]' : 'w-[60px]'"></TableHead>
        </TableRow></TableHeader>
        <TableBody>
          <TableRow v-for="item in paged" :key="item.tag">
            <TableCell>
              <img
                v-if="item.icon_url"
                :src="imageUrl(`icons/${item.tag}.png`)"
                :alt="item.display_name"
                class="h-6 w-6"
              />
            </TableCell>
            <TableCell>
              <code class="text-sm bg-muted px-1.5 py-0.5 rounded">[{{ item.tag }}]</code>
            </TableCell>
            <TableCell class="font-medium">{{ item.display_name }}</TableCell>
            <TableCell class="text-muted-foreground text-sm">{{ item.description || "—" }}</TableCell>
            <TableCell>
              <div class="flex justify-end gap-1">
                <Button variant="ghost" size="icon" class="h-8 w-8" @click="startEdit(item)"><Pencil class="h-4 w-4" /></Button>
                <Button v-if="enableDelete" variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="promptDelete(item.tag)"><Trash2 class="h-4 w-4" /></Button>
              </div>
            </TableCell>
          </TableRow>
        </TableBody>
      </Table>
      <PaginationControls :total="filtered.length" :page="page" :per-page="perPage" @update:page="(v) => page = v" @update:per-page="(v) => perPage = v" />
    </template>
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader><DialogTitle>{{ isCreating ? "Add Icon" : "Edit Icon" }}</DialogTitle></DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1"><Label>Tag</Label><Input v-model="editTag" :placeholder="isCreating ? 'e.g. activation' : ''" @keydown.enter.prevent="saveEdit" /></div>
          <div class="space-y-1"><Label>Display Name</Label><Input v-model="editDisplayName" placeholder="e.g. Activation" /></div>
          <div class="space-y-1"><Label>Icon URL</Label><Input v-model="editIconUrl" placeholder="https://..." /></div>
          <div class="space-y-1"><Label>Description</Label><Textarea v-model="editDescription" placeholder="What this icon represents..." rows="3" /></div>
        </div>
        <DialogFooter><Button variant="outline" @click="editDialogOpen = false">Cancel</Button><Button @click="saveEdit">{{ isCreating ? "Add" : "Save" }}</Button></DialogFooter>
      </DialogContent>
    </Dialog>

    <ConfirmDialog v-model:open="confirmDeleteOpen" title="Delete Icon" :description="`Delete icon &quot;${confirmDeleteName}&quot;?`" @confirm="confirmRemove" />
  </div>
</template>
