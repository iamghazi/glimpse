<template>
  <div class="grid grid-cols-5 gap-2">
    <div
      v-for="(frame, index) in frames"
      :key="frame || `placeholder-${index}`"
      class="aspect-video bg-slate-100 rounded-lg overflow-hidden"
    >
      <img
        v-if="frame"
        :src="frame"
        :alt="`Frame ${index + 1}`"
        class="w-full h-full object-cover"
      />
      <div v-else class="w-full h-full flex items-center justify-center">
        <span class="material-symbols-outlined text-2xl text-slate-300">
          image
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
interface Props {
  frames: (string | null)[]
}

defineProps<Props>()
</script>
