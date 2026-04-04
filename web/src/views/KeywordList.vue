<script setup lang="ts">
import { ref, computed, onMounted, watch } from "vue";
import { listKeywordsWithCounts, updateKeyword, deleteKeyword, createKeyword, listKeywordItems } from "../api";
import ItemsDialog from "../components/ItemsDialog.vue";
import { usePerPage } from "../composables/usePerPage";
import type { KeywordEntry } from "../api";
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

const items = ref<KeywordEntry[]>([]);
const search = ref("");
const loading = ref(true);
const page = ref(1);
const perPage = usePerPage();

const itemsDialogOpen = ref(false);
const itemsDialogKeyword = ref("");

const editDialogOpen = ref(false);
const isCreating = ref(false);
const editingKeyword = ref<string | null>(null);
const editName = ref("");
const editDefinition = ref("");

const filtered = computed(() => {
  if (!search.value) return items.value;
  const q = search.value.toLowerCase();
  return items.value.filter(
    (i) => i.keyword.toLowerCase().includes(q) || i.definition.toLowerCase().includes(q)
  );
});

const paged = computed(() => {
  const start = (page.value - 1) * perPage.value;
  return filtered.value.slice(start, start + perPage.value);
});

watch(search, () => { page.value = 1; });

async function load() {
  loading.value = true;
  items.value = await listKeywordsWithCounts();
  loading.value = false;
}

function startCreate() {
  isCreating.value = true;
  editingKeyword.value = null;
  editName.value = "";
  editDefinition.value = "";
  editDialogOpen.value = true;
}

function startEdit(item: KeywordEntry) {
  isCreating.value = false;
  editingKeyword.value = item.keyword;
  editName.value = item.keyword;
  editDefinition.value = item.definition;
  editDialogOpen.value = true;
}

async function saveEdit() {
  if (isCreating.value) {
    if (!editName.value.trim()) return;
    await createKeyword(editName.value.trim(), editDefinition.value);
  } else if (editingKeyword.value) {
    const data: { keyword?: string; definition?: string } = {};
    if (editName.value.trim() !== editingKeyword.value) data.keyword = editName.value.trim();
    data.definition = editDefinition.value;
    await updateKeyword(editingKeyword.value, data);
  }
  editDialogOpen.value = false;
  await load();
}

async function remove(keyword: string, count: number) {
  if (!confirm(`Remove "${keyword}" from ${count} items?`)) return;
  await deleteKeyword(keyword);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="flex items-center gap-3 mb-4">
      <Input
        v-model="search"
        placeholder="Search keywords or definitions..."
        class="max-w-sm"
      />
      <Button size="sm" @click="startCreate">
        <Plus class="h-4 w-4 mr-1" /> Add Keyword
      </Button>
      <Badge variant="secondary">{{ items.length }} keywords</Badge>
    </div>

    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <template v-if="!loading">
      <Table>
        <TableHeader>
          <TableRow>
            <TableHead class="w-[120px]">Keyword</TableHead>
            <TableHead>Definition</TableHead>
            <TableHead class="w-[100px] text-right">Items</TableHead>
            <TableHead class="w-[80px]"></TableHead>
          </TableRow>
        </TableHeader>
        <TableBody>
          <TableRow v-for="item in paged" :key="item.keyword">
            <TableCell class="font-medium">{{ item.keyword }}</TableCell>
            <TableCell class="text-muted-foreground text-sm">
              {{ item.definition || "—" }}
            </TableCell>
            <TableCell class="text-right">
              <Badge
                variant="outline"
                class="cursor-pointer hover:bg-accent"
                @click="itemsDialogKeyword = item.keyword; itemsDialogOpen = true"
              >
                {{ item.count }} items
              </Badge>
            </TableCell>
            <TableCell>
              <div class="flex justify-end gap-1">
                <Button variant="ghost" size="icon" class="h-8 w-8" @click="startEdit(item)">
                  <Pencil class="h-4 w-4" />
                </Button>
                <Button variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="remove(item.keyword, item.count)">
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

    <!-- Edit/Create Dialog -->
    <Dialog v-model:open="editDialogOpen">
      <DialogContent class="max-w-md">
        <DialogHeader>
          <DialogTitle>{{ isCreating ? "Add Keyword" : "Edit Keyword" }}</DialogTitle>
        </DialogHeader>
        <div class="space-y-4 py-2">
          <div class="space-y-1">
            <Label>Name</Label>
            <Input
              v-model="editName"
              :placeholder="isCreating ? 'Enter keyword name...' : ''"
              @keydown.enter.prevent="saveEdit"
            />
          </div>
          <div class="space-y-1">
            <Label>Definition</Label>
            <Textarea
              v-model="editDefinition"
              placeholder="Enter the definition for this keyword..."
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

    <!-- Items Dialog -->
    <ItemsDialog
      v-model:open="itemsDialogOpen"
      :title="`Items with keyword: ${itemsDialogKeyword}`"
      :fetch-items="() => listKeywordItems(itemsDialogKeyword)"
    />
  </div>
</template>
