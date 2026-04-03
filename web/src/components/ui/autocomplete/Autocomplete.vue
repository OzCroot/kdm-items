<script setup lang="ts">
import { ref, computed } from "vue";
import { Popover, PopoverContent, PopoverTrigger } from "@/components/ui/popover";
import { Command, CommandEmpty, CommandGroup, CommandItem, CommandList } from "@/components/ui/command";
import { Input } from "@/components/ui/input";

const props = defineProps<{
  options: string[];
  placeholder?: string;
  class?: string;
}>();

const emit = defineEmits<{
  select: [value: string];
}>();

const inputValue = ref("");
const open = ref(false);

const filtered = computed(() => {
  if (!inputValue.value) return props.options.slice(0, 20);
  const q = inputValue.value.toLowerCase();
  return props.options.filter((o) => o.toLowerCase().includes(q)).slice(0, 20);
});

function onSelect(value: string) {
  emit("select", value);
  inputValue.value = "";
  open.value = false;
}

function onEnter() {
  if (inputValue.value.trim()) {
    emit("select", inputValue.value.trim());
    inputValue.value = "";
    open.value = false;
  }
}

function onInput() {
  if (inputValue.value) {
    open.value = true;
  }
}
</script>

<template>
  <Popover v-model:open="open">
    <PopoverTrigger as-child>
      <Input
        v-model="inputValue"
        :placeholder="placeholder"
        :class="props.class"
        @input="onInput"
        @focus="open = true"
        @keydown.enter.prevent="onEnter"
      />
    </PopoverTrigger>
    <PopoverContent
      class="w-[220px] p-0"
      align="start"
      @open-auto-focus.prevent
    >
      <Command>
        <CommandList>
          <CommandEmpty>No matches. Press Enter to add.</CommandEmpty>
          <CommandGroup>
            <CommandItem
              v-for="opt in filtered"
              :key="opt"
              :value="opt"
              @select.prevent="onSelect(opt)"
            >
              {{ opt }}
            </CommandItem>
          </CommandGroup>
        </CommandList>
      </Command>
    </PopoverContent>
  </Popover>
</template>
