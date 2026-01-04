export interface GoogleCloudSettings {
  GCP_PROJECT_ID: string
  GCP_LOCATION: string
  GEMINI_MODEL: string
}

export interface VideoProcessingSettings {
  CHUNK_DURATION_SECONDS: number
  CHUNK_OVERLAP_SECONDS: number
  FRAME_EXTRACTION_FPS: number
}

export interface SearchEmbeddingSettings {
  EMBEDDING_MAX_WORKERS: number
  TIER1_CANDIDATES: number
  CONFIDENCE_THRESHOLD: number
}

export interface DataStorageSettings {
  DATA_DIR: string
  VIDEOS_DIR: string
  FRAMES_DIR: string
  METADATA_DIR: string
  QDRANT_STORAGE_DIR: string
}

export interface AppSettings {
  googleCloud: GoogleCloudSettings
  videoProcessing: VideoProcessingSettings
  searchEmbedding: SearchEmbeddingSettings
  dataStorage: DataStorageSettings
}

export interface ValidationError {
  field: string
  message: string
}
