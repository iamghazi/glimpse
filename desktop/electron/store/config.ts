import Store from 'electron-store'
import type { AppSettings } from '../../src/types/settings'

const defaultSettings: AppSettings = {
  googleCloud: {
    GCP_PROJECT_ID: '',
    GCP_LOCATION: 'us-central1',
    GEMINI_MODEL: 'gemini-2.0-flash-exp'
  },
  videoProcessing: {
    CHUNK_DURATION_SECONDS: 30,
    CHUNK_OVERLAP_SECONDS: 5,
    FRAME_EXTRACTION_FPS: 1
  },
  searchEmbedding: {
    EMBEDDING_MAX_WORKERS: 5,
    TIER1_CANDIDATES: 50,
    CONFIDENCE_THRESHOLD: 0.8
  },
  dataStorage: {
    DATA_DIR: './data',
    VIDEOS_DIR: './data/videos',
    FRAMES_DIR: './data/frames',
    METADATA_DIR: './data/metadata',
    QDRANT_STORAGE_DIR: './data/qdrant_storage'
  }
}

export const configStore = new Store<{ settings: AppSettings }>({
  name: 'config',
  defaults: {
    settings: defaultSettings
  }
})

export { defaultSettings }
