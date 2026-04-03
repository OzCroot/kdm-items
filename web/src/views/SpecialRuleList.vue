<script setup lang="ts">
import { ref, computed, onMounted } from "vue";
import { listSpecialRulesWithCounts, updateSpecialRule, deleteSpecialRule } from "../api";
import type { SpecialRuleEntry } from "../api";
import { Input } from "@/components/ui/input";
import { Textarea } from "@/components/ui/textarea";
import { Button } from "@/components/ui/button";
import { Badge } from "@/components/ui/badge";
import { Label } from "@/components/ui/label";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import {
  Table,
  TableBody,
  TableCell,
  TableHead,
  TableHeader,
  TableRow,
} from "@/components/ui/table";
import { Pencil, Trash2, Check, X } from "lucide-vue-next";

const items = ref<SpecialRuleEntry[]>([]);
const search = ref("");
const loading = ref(true);

const editingRule = ref<string | null>(null);
const editName = ref("");
const editDefinition = ref("");

const filtered = computed(() => {
  if (!search.value) return items.value;
  const q = search.value.toLowerCase();
  return items.value.filter(
    (i) => i.rule.toLowerCase().includes(q) || i.definition.toLowerCase().includes(q)
  );
});

async function load() {
  loading.value = true;
  items.value = await listSpecialRulesWithCounts();
  loading.value = false;
}

function startEdit(item: SpecialRuleEntry) {
  editingRule.value = item.rule;
  editName.value = item.rule;
  editDefinition.value = item.definition;
}

function cancelEdit() {
  editingRule.value = null;
}

async function saveEdit(oldRule: string) {
  const data: { rule?: string; definition?: string } = {};
  if (editName.value.trim() !== oldRule) data.rule = editName.value.trim();
  data.definition = editDefinition.value;
  await updateSpecialRule(oldRule, data);
  cancelEdit();
  await load();
}

async function remove(rule: string, count: number) {
  if (!confirm(`Remove "${rule}" from ${count} items?`)) return;
  await deleteSpecialRule(rule);
  await load();
}

onMounted(load);
</script>

<template>
  <div>
    <div class="flex items-center justify-between mb-4">
      <h2 class="text-lg font-semibold">Special Rules</h2>
      <Badge variant="secondary">{{ items.length }} rules</Badge>
    </div>

    <Input
      v-model="search"
      placeholder="Search rules or definitions..."
      class="mb-4 max-w-sm"
    />

    <div v-if="loading" class="text-center py-8 text-muted-foreground">Loading...</div>

    <Card v-if="editingRule" class="mb-4">
      <CardHeader class="pb-3">
        <CardTitle class="text-sm">Edit Special Rule</CardTitle>
      </CardHeader>
      <CardContent class="space-y-3">
        <div class="space-y-1">
          <Label>Name</Label>
          <Input
            v-model="editName"
            class="max-w-xs"
            @keydown.enter.prevent="saveEdit(editingRule!)"
          />
        </div>
        <div class="space-y-1">
          <Label>Definition</Label>
          <Textarea
            v-model="editDefinition"
            placeholder="Enter the definition for this rule..."
            rows="3"
          />
        </div>
        <div class="flex gap-2">
          <Button size="sm" @click="saveEdit(editingRule!)">
            <Check class="h-4 w-4 mr-1" /> Save
          </Button>
          <Button variant="outline" size="sm" @click="cancelEdit">Cancel</Button>
        </div>
      </CardContent>
    </Card>

    <Table v-if="!loading">
      <TableHeader>
        <TableRow>
          <TableHead class="w-[140px]">Rule</TableHead>
          <TableHead>Definition</TableHead>
          <TableHead class="w-[80px] text-right">Items</TableHead>
          <TableHead class="w-[80px]"></TableHead>
        </TableRow>
      </TableHeader>
      <TableBody>
        <TableRow v-for="item in filtered" :key="item.rule">
          <TableCell class="font-medium whitespace-nowrap">{{ item.rule }}</TableCell>
          <TableCell class="text-muted-foreground text-sm">
            {{ item.definition || "—" }}
          </TableCell>
          <TableCell class="text-right text-muted-foreground">
            {{ item.count }}
          </TableCell>
          <TableCell>
            <div class="flex justify-end gap-1">
              <Button variant="ghost" size="icon" class="h-8 w-8" @click="startEdit(item)">
                <Pencil class="h-4 w-4" />
              </Button>
              <Button variant="ghost" size="icon" class="h-8 w-8 text-destructive" @click="remove(item.rule, item.count)">
                <Trash2 class="h-4 w-4" />
              </Button>
            </div>
          </TableCell>
        </TableRow>
      </TableBody>
    </Table>
  </div>
</template>
