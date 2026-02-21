<template>
<AudioPlayerShell
  :display-track="displayTrack"
  :album-art-style="albumArtStyle"
  :current-time="currentTime"
  :duration="duration"
  :is-playing="isPlaying"
  :show-transport-controls="hasStreamInitialized"
  :response-message="responseMessage"
  @previous="previousTrack"
  @play-pause="togglePlayPause"
  @next="nextTrack"
  @seek="onProgressChangeFromShell"
  @stream-play="streamPlay"
/>

<audio
  ref="audioPlayerLeft"
  :src="playerSources[0]"
  preload="metadata"
  @loadedmetadata="onLoadedMetadata(0)"
  @ended="onTrackEnded(0)"
/>
<audio
  ref="audioPlayerRight"
  :src="playerSources[1]"
  preload="metadata"
  @loadedmetadata="onLoadedMetadata(1)"
  @ended="onTrackEnded(1)"
/>
</template>

<script setup>

import { computed, ref } from 'vue'
import { useDualDeckPlayer } from '~/composables/useDualDeckPlayer'

const responseMessage = ref('');
const hasStreamInitialized = ref(false)

const streamTrack = ref(null) // {title, artist}
const displayTrack = computed(() => streamTrack.value || {
  title: '',
  artist: 'Unknown Artist',
  coverUrl: null,
})
const albumArtStyle = computed(() => ({
  backgroundImage: `url(${'/assets/images/vector-dj-disk-1241523.jpg'})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  borderRadius: '10px',
  width: '200px',
  height: '200px'
}));
const debugOverlap = true
const streamUrl = ref('')

const logOverlap = (...args) => {
    if (!debugOverlap) return
    console.log('[overlap]', ...args)
}

const {
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
    setOverlapSeconds,
    stopPlayer,
    togglePlayPause: toggleDeckPlayPause,
    seekTo,
    onLoadedMetadata,
} = useDualDeckPlayer({
    overlapSeconds: 5,
    onOverlapTrigger: startNextTrackOverlap,
    logger: (...args) => logOverlap(...args),
})

const togglePlayPause = async () => {
    await toggleDeckPlayPause()
}

const { public: { apiBase } } = useRuntimeConfig()
const normalizedApiBase = String(apiBase || '').replace(/\/+$/, '')

const buildApiUrl = (path) => {
  const normalizedPath = path.startsWith('/') ? path : `/${path}`
  return `${normalizedApiBase}${normalizedPath}`
}

const buildStreamUrl = (pathWithQuery) => {
  if (String(pathWithQuery).startsWith('http://') || String(pathWithQuery).startsWith('https://')) {
    return String(pathWithQuery)
  }
  return buildApiUrl(pathWithQuery)
}

async function refreshOverlapSeconds() {
  try {
    const response = await $fetch(buildApiUrl('/api/player/overlap'))
    const value = Number(response?.overlapSeconds)
    if (Number.isFinite(value) && value >= 0) {
      setOverlapSeconds(value)
      logOverlap('updated overlapSeconds', { overlapSeconds: value, source: response?.source })
      return
    }
  } catch (error) {
    logOverlap('overlap api failed, keeping current overlapSeconds', { error })
  }
}

const onProgressChangeFromShell = (time) => {
  seekTo(Number(time))
}

const nextTrack = async () => {
    await playNextStreamTrack()
}

const previousTrack = async () => {
        await playPreviousStreamTrack()
}

async function startNextTrackOverlap() {
    logOverlap('overlap started while leaving this track index', {
        fromTrackIndex: streamTrack.value?.index??-1,
        activePlayer: activePlayerIndex.value,
    })

    try {

        await playNextStreamTrack({ overlap: true })

    } catch (error) {
        console.error('Error starting overlap playback:', error)
        logOverlap('start overlap failed', error)
    }
}

const onTrackEnded = async(playerIndex) => {
  logOverlap('ended event', { playerIndex, activePlayer: activePlayerIndex.value })
  if (playerIndex !== activePlayerIndex.value) {
    stopPlayer(playerIndex)
    return
  }
  await playNextStreamTrack()
}

async function streamPlay() {
    try {
        stopPlayer(0)
        stopPlayer(1)
        setActivePlayer(0)
        overlapStarted.value = false

        const response = await $fetch(buildApiUrl('/api/play'), {
            method: 'POST'
        })

        streamTrack.value = response.currentTrack
        hasStreamInitialized.value = true
        streamUrl.value = buildStreamUrl(`${response.streamUrl}?t=${Date.now()}`)
        await setPlayerSource(activePlayerIndex.value, streamUrl.value)
        await getActivePlayer().play()
        currentTime.value = 0
        duration.value = 0
        lastNearEndLogSecond.value = -1
        isPlaying.value = true
        await refreshOverlapSeconds()
    } catch (error) {
        console.error('Error starting stream playback:', error)
    }
}

async function applyStreamTrackResponse(response, options = { overlap: false, direction: 'next' }) {
  const overlap = Boolean(options.overlap)
  const direction = options.direction || 'next'
  const nextUrl = buildStreamUrl(`${response.streamUrl}?t=${Date.now()}`)
  const incomingPlayerIndex = getInactivePlayerIndex()

  if (!overlap) {
    stopPlayer(0)
    stopPlayer(1)
  }

  await setPlayerSource(incomingPlayerIndex, nextUrl)
  const incomingPlayer = getPlayer(incomingPlayerIndex)
  if (!incomingPlayer) return

  incomingPlayer.currentTime = 0
  await incomingPlayer.play()
  setActivePlayer(incomingPlayerIndex)
  streamTrack.value = response.currentTrack
  streamUrl.value = nextUrl
  currentTime.value = 0
  duration.value = Number.isFinite(incomingPlayer.duration) ? incomingPlayer.duration : 0
  lastNearEndLogSecond.value = -1

  logOverlap('stream next started', {
    direction,
    overlap,
    toTrackIndex: response.currentTrack?.index,
    incomingPlayer: incomingPlayerIndex,
    src: nextUrl,
  })

  isPlaying.value = true
  await refreshOverlapSeconds()
}

async function playNextStreamTrack(options = { overlap: false }) {
  const overlap = Boolean(options.overlap)
  const response = await $fetch(buildApiUrl('/api/play/next'), { method: 'POST' })
  await applyStreamTrackResponse(response, { overlap, direction: 'next' })
}

async function playPreviousStreamTrack(options = { overlap: false }) {
  const overlap = Boolean(options.overlap)
  const response = await $fetch(buildApiUrl('/api/play/previous'), { method: 'POST' })
  await applyStreamTrackResponse(response, { overlap, direction: 'previous' })
}

</script>
