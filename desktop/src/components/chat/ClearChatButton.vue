<template>
  <BaseButton
    variant="ghost"
    size="sm"
    icon="delete_sweep"
    @click="showConfirm = true"
  >
    Clear Chat
  </BaseButton>

  <!-- Confirmation Modal -->
  <Teleport to="body">
    <div
      v-if="showConfirm"
      class="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4"
      @click.self="showConfirm = false"
    >
      <BaseCard variant="elevated" padding="none" class="max-w-md w-full">
        <div class="p-6">
          <div class="flex items-start gap-4">
            <div class="shrink-0 w-10 h-10 rounded-full bg-warning/10 flex items-center justify-center">
              <span class="material-symbols-outlined text-warning text-xl">
                warning
              </span>
            </div>

            <div class="flex-1">
              <h3 class="text-lg font-semibold text-slate-900 mb-2">
                Clear Chat History?
              </h3>
              <p class="text-sm text-slate-600">
                This will clear all messages and remove all active clips. This action cannot be undone.
              </p>
            </div>
          </div>
        </div>

        <div class="border-t border-slate-200 p-4 flex justify-end gap-3">
          <BaseButton
            variant="ghost"
            @click="showConfirm = false"
          >
            Cancel
          </BaseButton>
          <BaseButton
            variant="primary"
            @click="handleConfirm"
            class="bg-warning hover:bg-warning/90"
          >
            Clear Chat
          </BaseButton>
        </div>
      </BaseCard>
    </div>
  </Teleport>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import BaseCard from '@/components/ui/BaseCard.vue'

const emit = defineEmits<{
  'clear': []
}>()

const showConfirm = ref(false)

function handleConfirm() {
  emit('clear')
  showConfirm.value = false
}
</script>
