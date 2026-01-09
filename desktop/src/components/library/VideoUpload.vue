<template>
  <BaseCard
    variant="bordered"
    padding="lg"
    :class="dropZoneClasses"
    @click="handleClick"
    @dragover.prevent="isDragging = true"
    @dragleave.prevent="isDragging = false"
    @drop.prevent="handleDrop"
  >
    <div class="flex flex-col items-center justify-center text-center">
      <div :class="iconClasses">
        <span class="material-symbols-outlined text-4xl">
          {{ isDragging ? 'download' : 'upload_file' }}
        </span>
      </div>

      <h3 class="text-lg font-semibold text-slate-900 mb-1">
        {{ isDragging ? 'Drop video here' : 'Upload Video' }}
      </h3>

      <p class="text-sm text-slate-500 mb-4">
        {{ isDragging ? 'Release to upload' : 'Drag and drop a video file or click to browse' }}
      </p>

      <BaseButton
        variant="primary"
        icon="upload"
        :disabled="disabled"
      >
        Select Video File
      </BaseButton>

      <p class="text-xs text-slate-400 mt-4">
        Supported formats: MP4, MOV, AVI, MKV, WebM
      </p>
    </div>

    <input
      ref="fileInput"
      type="file"
      accept="video/*,.mp4,.mov,.avi,.mkv,.webm"
      class="hidden"
      @change="handleFileSelect"
    />
  </BaseCard>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  disabled?: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  'file-selected': [file: File]
}>()

const fileInput = ref<HTMLInputElement>()
const isDragging = ref(false)

const dropZoneClasses = computed(() => [
  'cursor-pointer transition-all',
  isDragging.value && 'border-primary bg-primary/5 border-2'
])

const iconClasses = computed(() => [
  'w-16 h-16 rounded-full flex items-center justify-center mb-4 transition-colors',
  isDragging.value ? 'bg-primary/10 text-primary' : 'bg-slate-100 text-slate-400'
])

function handleClick() {
  fileInput.value?.click()
}

function handleFileSelect(event: Event) {
  const target = event.target as HTMLInputElement
  const file = target.files?.[0]
  if (file) {
    emit('file-selected', file)
    target.value = '' // Reset input
  }
}

function handleDrop(event: DragEvent) {
  isDragging.value = false
  const file = event.dataTransfer?.files[0]
  if (file && file.type.startsWith('video/')) {
    emit('file-selected', file)
  }
}
</script>
