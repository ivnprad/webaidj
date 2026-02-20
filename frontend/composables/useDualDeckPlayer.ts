import { nextTick, onMounted, onUnmounted, ref } from 'vue'
import type { Ref } from 'vue'

type OverlapCallback = () => void | Promise<void>
type Logger = (...args: unknown[]) => void

interface CreateTransportControlsDeps {
  getPlayer: (index: number) => HTMLAudioElement | null
  getActivePlayer: () => HTMLAudioElement | null
  isPlaying: Ref<boolean>
  currentTime: Ref<number>
  log: Logger
}

function createTransportControls(deps: CreateTransportControlsDeps) {
  const { getPlayer, getActivePlayer, isPlaying, currentTime, log } = deps

  const stopPlayer = (index: number) => {
    const player = getPlayer(index)
    if (!player) return
    player.pause()
    player.currentTime = 0
  }

  const pausePlayer = (index: number) => {
    const player = getPlayer(index)
    if (!player) return
    player.pause()
  }

  const stopAll = () => {
    stopPlayer(0)
    stopPlayer(1)
    isPlaying.value = false
  }

  const pauseAll = () => {
    pausePlayer(0)
    pausePlayer(1)
    isPlaying.value = false
  }

  const playActive = async () => {
    const player = getActivePlayer()
    if (!player) return
    await player.play()
    isPlaying.value = true
  }

  const togglePlayPause = async () => {
    const active = getActivePlayer()
    if (!active) return

    if (active.paused) {
      await active.play()
      isPlaying.value = true
      log('[dualDeck] play')
      return
    }

    pauseAll()
    log('[dualDeck] pause')
  }

  const seekTo = (time: number) => {
    const active = getActivePlayer()
    if (!active) return
    active.currentTime = time
    currentTime.value = time
  }

  return {
    stopPlayer,
    pausePlayer,
    stopAll,
    pauseAll,
    playActive,
    togglePlayPause,
    seekTo,
  }
}

interface CreateProgressTrackingDeps {
  getActivePlayer: () => HTMLAudioElement | null
  activePlayerIndex: Ref<number>
  overlapStarted: Ref<boolean>
  isPlaying: Ref<boolean>
  currentTime: Ref<number>
  duration: Ref<number>
  lastNearEndLogSecond: Ref<number>
  overlapSeconds: number
  onOverlapTrigger?: OverlapCallback
  log: Logger
}

function createProgressTracking(deps: CreateProgressTrackingDeps) {
  const {
    getActivePlayer,
    activePlayerIndex,
    overlapStarted,
    isPlaying,
    currentTime,
    duration,
    lastNearEndLogSecond,
    overlapSeconds,
    onOverlapTrigger,
    log,
  } = deps

  const onLoadedMetadata = (playerIndex: number) => {
    if (playerIndex !== activePlayerIndex.value) return

    const active = getActivePlayer()
    if (!active) return

    duration.value = Number.isFinite(active.duration) ? active.duration : 0
  }

  const maybeTriggerOverlap = async () => {
    if (!onOverlapTrigger) return
    if (overlapStarted.value || !isPlaying.value) return
    if (!(duration.value > overlapSeconds)) return
    if (currentTime.value < duration.value - overlapSeconds) return

    overlapStarted.value = true
    try {
      log('[dualDeck] overlap trigger reached')
      await onOverlapTrigger()
    } finally {
      overlapStarted.value = false
    }
  }

  const updateProgress = async () => {
    const active = getActivePlayer()
    if (!active) return

    currentTime.value = active.currentTime
    duration.value = Number.isFinite(active.duration) ? active.duration : 0

    const remaining = duration.value - currentTime.value
    if (Number.isFinite(remaining) && remaining <= overlapSeconds + 1 && remaining >= 0) {
      const floored = Math.floor(remaining)
      if (floored !== lastNearEndLogSecond.value) {
        lastNearEndLogSecond.value = floored
        log('[dualDeck] near end', {
          currentTime: currentTime.value.toFixed(2),
          duration: duration.value.toFixed(2),
          remaining: remaining.toFixed(2),
        })
      }
    }

    await maybeTriggerOverlap()
  }

  return {
    onLoadedMetadata,
    updateProgress,
  }
}

interface UseDualDeckPlayerOptions {
  overlapSeconds?: number
  pollIntervalMs?: number
  onOverlapTrigger?: OverlapCallback
  logger?: Logger
}

export function useDualDeckPlayer(options: UseDualDeckPlayerOptions = {}) {
  // options
  const overlapSeconds = options.overlapSeconds ?? 5
  const pollIntervalMs = options.pollIntervalMs ?? 100
  const onOverlapTrigger = options.onOverlapTrigger
  const log = options.logger ?? (() => {})

  // deck elements
  const audioPlayerLeft = ref<HTMLAudioElement | null>(null)
  const audioPlayerRight = ref<HTMLAudioElement | null>(null)

  // deck state
  const playerSources = ref<string[]>(['', ''])
  const activePlayerIndex = ref(0)
  const overlapStarted = ref(false)

  // playback state
  const isPlaying = ref(false)
  const currentTime = ref(0)
  const duration = ref(0)
  const lastNearEndLogSecond = ref(-1)

  // selectors
  const getPlayer = (index: number) => {
    if (index < 0 || index > 1) {
      log('[dualDeck] invalid player index, defaulting to 0', { index })
      index = 0
    }
    return index === 0 ? audioPlayerLeft.value : audioPlayerRight.value
  }

  const getActivePlayer = () => getPlayer(activePlayerIndex.value)
  const getInactivePlayerIndex = () => (activePlayerIndex.value === 0 ? 1 : 0)

  const setActivePlayer = (index: number) => {
    activePlayerIndex.value = index
  }

  const setPlayerSource = async (index: number, source: string) => {
    playerSources.value[index] = source
    await nextTick()
  }

  // transport
  const {
    stopPlayer,
    pausePlayer,
    stopAll,
    pauseAll,
    playActive,
    togglePlayPause,
    seekTo,
  } = createTransportControls({
    getPlayer,
    getActivePlayer,
    isPlaying,
    currentTime,
    log,
  })

  // progress + overlap
  const { onLoadedMetadata, updateProgress } = createProgressTracking({
    getActivePlayer,
    activePlayerIndex,
    overlapStarted,
    isPlaying,
    currentTime,
    duration,
    lastNearEndLogSecond,
    overlapSeconds,
    onOverlapTrigger,
    log,
  })

  // lifecycle polling
  let progressInterval: ReturnType<typeof setInterval> | null = null

  onMounted(() => {
    progressInterval = setInterval(() => {
      void updateProgress()
    }, pollIntervalMs)
  })

  onUnmounted(() => {
    if (progressInterval) clearInterval(progressInterval)
  })

  // public API
  return {
    audioPlayerLeft,
    audioPlayerRight,
    playerSources,
    activePlayerIndex,
    overlapStarted,
    isPlaying,
    currentTime,
    duration,
    lastNearEndLogSecond,

    getPlayer,
    getActivePlayer,
    getInactivePlayerIndex,
    setActivePlayer,
    setPlayerSource,

    stopPlayer,
    pausePlayer,
    stopAll,
    pauseAll,
    playActive,
    togglePlayPause,
    seekTo,

    onLoadedMetadata,
    updateProgress,
  }
}
