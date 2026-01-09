<template>
  <Teleport to="body">
    <div
      v-if="show"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="emit('cancel')"
    >
      <BaseCard variant="elevated" padding="none" class="max-w-md w-full">
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="shrink-0 w-10 h-10 rounded-full bg-error/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-error text-xl">
                warning
              </span>
            </div>

            <div class="flex-1">
              <h3 class="text-lg font-semibold text-slate-900 mb-2">
                Delete Video
              </h3>
              <p class="text-sm text-slate-600 mb-1">
                Are you sure you want to delete "<span class="font-medium">{{ videoTitle }}</span>"?
              </p>
              <p class="text-sm text-slate-500">
                This will permanently delete the video, all its chunks, and embeddings. This action cannot be undone.
              </p>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-200 p-4 flex justify-end gap-3">
          <BaseButton
            variant="ghost"
            @click="emit('cancel')"
            :disabled="loading"
          >
            Cancel
          </BaseButton>
          <BaseButton
            variant="primary"
            @click="emit('confirm')"
            :loading="loading"
            class="bg-error hover:bg-error/90"
          >
            Delete Video
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'

interface Props {
  show: boolean
  videoTitle: string
  loading?: boolean
}

defineProps<Props>()
const emit = defineEmits<{
  'confirm': []
  'cancel': []
}>()
</script>
