<script setup lang="ts">
import { ref, computed, watch, reactive } from "vue";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Checkbox } from "@/components/ui/checkbox";
import { Label } from "@/components/ui/label";
import { ScrollArea } from "@/components/ui/scroll-area";
import {
  Dialog,
  DialogContent,
  DialogHeader,
  DialogTitle,
  DialogFooter,
} from "@/components/ui/dialog";

const props = defineProps<{
  open: boolean;
  title: string;
  options: string[];
  selected: string[];
  descriptions?: Record<string, string>;
}>();

const emit = defineEmits<{
  "update:open": [value: boolean];
  "update:selected": [value: string[]];
}>();

const search = ref("");
const checked = reactive<Record<string, boolean>>({});

watch(() => props.open, (isOpen) => {
  if (isOpen) {
    // Clear and repopulate
    for (const key of Object.keys(checked)) {
      delete checked[key];
    }
    for (const item of props.selected) {
      checked[item] = true;
    }
    search.value = "";
  }
});

const filtered = computed(() => {
  const list = props.options;
  if (!search.value) return list;
  const q = search.value.toLowerCase();
  return list.filter((o) => o.toLowerCase().includes(q));
});

const selectedCount = computed(() => Object.values(checked).filter(Boolean).length);

function toggle(option: string) {
  checked[option] = !checked[option];
}

function save() {
  const result = props.options.filter((o) => checked[o]);
  emit("update:selected", result);
  emit("update:open", false);
}
</script>

<template>
  <Dialog :open="open" @update:open="(v) => emit('update:open', v)">
    <DialogContent class="max-w-sm max-h-[80vh] flex flex-col">
      <DialogHeader>
        <DialogTitle>{{ title }}</DialogTitle>
      </DialogHeader>
      <Input
        v-model="search"
        placeholder="Search..."
        class="mb-2"
      />
      <ScrollArea class="flex-1 -mx-6 px-6" style="max-height: 50vh;">
        <div class="space-y-1">
          <div
            v-for="opt in filtered"
            :key="opt"
            class="flex items-start gap-2 py-1.5 rounded px-1 hover:bg-accent/50 cursor-pointer"
            @click="toggle(opt)"
          >
            <Checkbox
              :checked="!!checked[opt]"
              @update:checked="() => toggle(opt)"
              class="mt-0.5"
            />
            <div class="flex-1 min-w-0">
              <Label class="text-sm">{{ opt }}</Label>
              <p
                v-if="descriptions?.[opt]"
                class="text-xs text-muted-foreground mt-0.5 line-clamp-2"
              >
                {{ descriptions[opt] }}
              </p>
            </div>
          </div>
          <p v-if="!filtered.length" class="text-sm text-muted-foreground py-4 text-center">No matches</p>
        </div>
      </ScrollArea>
      <DialogFooter class="mt-2">
        <span class="text-sm text-muted-foreground mr-auto">{{ selectedCount }} selected</span>
        <Button variant="outline" @click="emit('update:open', false)">Cancel</Button>
        <Button @click="save">Apply</Button>
      </DialogFooter>
    </DialogContent>
  </Dialog>
</template>
