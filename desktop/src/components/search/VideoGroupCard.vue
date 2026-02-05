<template>
  <BaseCard variant="bordered" padding="none" hover>
    <div class="p-5">
      <!-- Metadata -->
      <div class="flex items-center gap-4 text-sm mb-4">
        <div class="flex items-center gap-2">
          <span class="text-xs font-medium text-slate-500">Score:</span>
          <span class="text-sm font-semibold text-slate-900">
            {{ formatConfidence(group.best_score) }}
          </span>
          <ConfidenceBadge :score="group.best_score" />
        </div>

        <div class="h-4 w-px bg-slate-200"></div>

        <div class="flex items-center gap-1.5 text-slate-600">
          <span class="material-symbols-outlined text-base">
            schedule
          </span>
          <span>{{ timeRange }}</span>
        </div>

        <div class="h-4 w-px bg-slate-200"></div>

        <div class="flex items-center gap-1.5 text-slate-600">
          <span class="material-symbols-outlined text-base">
            movie
          </span>
          <span class="truncate">{{ group.title }}</span>
        </div>
      </div>

      <!-- All thumbnails in a single horizontal row -->
      <div class="flex gap-2 overflow-x-auto mb-4">
        <div
          v-for="frame in allFrames"
          :key="frame.url"
          class="shrink-0 w-36 aspect-video bg-slate-100 rounded-lg overflow-hidden"
        >
          <img
            :src="frame.url"
            :alt="frame.alt"
            class="w-full h-full object-cover"
          />
        </div>
      </div>

      <!-- Combined content -->
      <div class="space-y-3 mb-4">
        <!-- Visual descriptions -->
        <div v-if="visualDescriptions.length > 0">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-sm text-slate-500">
              visibility
            </span>
            <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Visual
            </span>
          </div>
          <div class="text-sm text-slate-700 leading-relaxed space-y-2">
            <p v-for="(desc, i) in visualDescriptions" :key="i">{{ desc }}</p>
          </div>
        </div>

        <!-- Audio transcripts -->
        <div v-if="audioTranscripts.length > 0">
          <div class="flex items-center gap-2 mb-2">
            <span class="material-symbols-outlined text-sm text-slate-500">
              mic
            </span>
            <span class="text-xs font-medium text-slate-500 uppercase tracking-wide">
              Audio
            </span>
          </div>
          <div class="text-sm text-slate-700 leading-relaxed space-y-2">
            <p v-for="(transcript, i) in audioTranscripts" :key="i">{{ transcript }}</p>
          </div>
        </div>
      </div>

      <!-- Actions -->
      <div class="flex items-center gap-2">
        <BaseButton
          variant="primary"
          size="sm"
          icon="add_comment"
          @click="emit('add-all-to-chat', group)"
        >
          Add to Chat
        </BaseButton>

        <BaseButton
          variant="ghost"
          size="sm"
          icon="play_arrow"
          @click="emit('play-clip', group.clips[0])"
        >
          Play Video
        </BaseButton>
      </div>
    </div>
  </BaseCard>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import BaseCard from '@/components/ui/BaseCard.vue'
import BaseButton from '@/components/ui/BaseButton.vue'
import ConfidenceBadge from './ConfidenceBadge.vue'
import { formatConfidence, formatTimestampRange } from '@/types/search'
import { getThumbnailUrl } from '@/types/video'
import type { VideoResultGroup, SearchResult } from '@/types/search'

interface Props {
  group: VideoResultGroup
}

const props = defineProps<Props>()

const emit = defineEmits<{
  'add-all-to-chat': [group: VideoResultGroup]
  'play-clip': [result: SearchResult]
}>()

// Overall time range across all clips
const timeRange = computed(() => {
  const minStart = Math.min(...props.group.clips.map(c => c.start_time))
  const maxEnd = Math.max(...props.group.clips.map(c => c.end_time))
  return formatTimestampRange(minStart, maxEnd)
})

// Collect evenly-sampled frames from each clip (max 6 per clip)
const allFrames = computed(() => {
  const frames: { url: string; alt: string }[] = []
  const maxPerClip = 6
  for (const clip of props.group.clips) {
    const paths = clip.frame_paths || []
    if (paths.length === 0) continue

    const sampled = paths.length <= maxPerClip
      ? paths
      : Array.from({ length: maxPerClip }, (_, i) =>
          paths[Math.floor((paths.length - 1) * (i / (maxPerClip - 1)))]
        )

    for (const path of sampled) {
      const url = getThumbnailUrl(path)
      if (url) frames.push({ url, alt: clip.chunk_id })
    }
  }
  return frames
})

// Collect non-empty visual descriptions
const visualDescriptions = computed(() => {
  return props.group.clips
    .map(c => c.visual_description)
    .filter(d => d && d.trim())
})

// Collect non-empty audio transcripts, stripping redundant "Transcript:" label
const audioTranscripts = computed(() => {
  return props.group.clips
    .map(c => c.audio_transcript?.replace(/ ?Transcript: ?/g, ' ').trim())
    .filter(t => t && t.trim())
})
</script>
