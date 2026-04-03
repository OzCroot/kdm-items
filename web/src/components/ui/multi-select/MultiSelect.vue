<script setup lang="ts">
import { computed, ref } from "vue";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandInput, CommandItem, CommandList } from "@/components/ui/command";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Check, ChevronsUpDown, X } from "lucide-vue-next";
import { cn } from "@/lib/utils";

const props = defineProps<{
  options: string[];
  placeholder?: string;
  class?: string;
}>();

const selected = defineModel<string[]>({ default: () => [] });
const open = ref(false);

const displayText = computed(() => {
  if (!selected.value.length) return props.placeholder || "Select...";
  if (selected.value.length === 1) return selected.value[0];
  return `${selected.value.length} selected`;
});

function toggle(value: string) {
  const idx = selected.value.indexOf(value);
  if (idx >= 0) {
    selected.value = selected.value.filter((v) => v !== value);
  } else {
    selected.value = [...selected.value, value];
  }
}

function remove(value: string) {
  selected.value = selected.value.filter((v) => v !== value);
}

function clear() {
  selected.value = [];
}
</script>

<template>
  <div :class="cn('flex flex-col gap-1.5', props.class)">
    <Popover v-model:open="open">
      <PopoverTrigger as-child>
        <Button
          variant="outline"
          role="combobox"
          :aria-expanded="open"
          class="justify-between font-normal"
        >
          <span class="truncate text-sm">{{ displayText }}</span>
          <ChevronsUpDown class="ml-2 h-4 w-4 shrink-0 opacity-50" />
        </Button>
      </PopoverTrigger>
      <PopoverContent class="w-[220px] p-0" align="start">
        <Command>
          <CommandInput placeholder="Search..." />
          <CommandEmpty>No results.</CommandEmpty>
          <CommandList>
            <CommandGroup>
              <CommandItem
                v-for="opt in options"
                :key="opt"
                :value="opt"
                @select.prevent="toggle(opt)"
              >
                <Check
                  :class="cn('mr-2 h-4 w-4', selected.includes(opt) ? 'opacity-100' : 'opacity-0')"
                />
                {{ opt }}
              </CommandItem>
            </CommandGroup>
          </CommandList>
        </Command>
      </PopoverContent>
    </Popover>
    <div v-if="selected.length" class="flex flex-wrap gap-1">
      <Badge
        v-for="val in selected"
        :key="val"
        variant="secondary"
        class="cursor-pointer gap-1 text-xs"
        @click="remove(val)"
      >
        {{ val }}
        <X class="h-3 w-3" />
      </Badge>
      <button
        v-if="selected.length > 1"
        class="text-xs text-muted-foreground hover:text-foreground"
        @click="clear"
      >
        Clear all
      </button>
    </div>
  </div>
</template>
