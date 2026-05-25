<template>
<div class="page-layout">
  <AudioPlayerShell
    :display-track="displayTrack"
    :album-art-style="albumArtStyle"
    :current-time="currentTime"
    :duration="duration"
    :is-playing="isPlaying"
    :show-transport-controls="hasStreamInitialized"
    :response-message="responseMessage"
    :selected-genre="selectedGenre"
    @previous="previousTrack"
    @play-pause="togglePlayPause"
    @next="nextTrack"
    @seek="onProgressChangeFromShell"
    @stream-play="streamPlay"
    @genre-change="selectedGenre = $event"
  />

  <PlaylistTable
    ref="playlistTableRef"
    :tracks="playlist"
    :current-index="playlistCurrentIndex"
    :available-songs="availableSongs"
    @track-click="jumpToTrack"
    @add-song="handleAddSong"
    @genre-songs-request="fetchAvailableSongs"
  />
</div>

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
import { DEFAULT_GENRE } from '~/constants/genres'

const responseMessage = ref('');
const hasStreamInitialized = ref(false)
const selectedGenre = ref(DEFAULT_GENRE)

const playlist = ref([])
const playlistCurrentIndex = ref(-1)
const availableSongs = ref([])
const playlistTableRef = ref(null)

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
            method: 'POST',
            body: { genre: selectedGenre.value }
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
        await fetchPlaylist()
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
  playlistCurrentIndex.value = response.currentTrack?.index ?? playlistCurrentIndex.value
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

async function fetchPlaylist() {
  try {
    const response = await $fetch(buildApiUrl('/api/playlist'))
    playlist.value = response.tracks ?? []
    playlistCurrentIndex.value = response.currentIndex ?? -1
  } catch {
    // non-fatal: playlist display is optional
  }
}

async function fetchAvailableSongs(genre) {
  try {
    const response = await $fetch(buildApiUrl(`/api/songs?genre=${genre}`))
    availableSongs.value = response.songs ?? []
  } catch {
    availableSongs.value = []
  }
}

async function jumpToTrack(index) {
  try {
    const response = await $fetch(buildApiUrl(`/api/play/jump/${index}`), { method: 'POST' })
    stopPlayer(0)
    stopPlayer(1)
    setActivePlayer(0)
    overlapStarted.value = false
    const url = buildStreamUrl(`${response.streamUrl}?t=${Date.now()}`)
    streamTrack.value = response.currentTrack
    streamUrl.value = url
    await setPlayerSource(activePlayerIndex.value, url)
    await getActivePlayer().play()
    currentTime.value = 0
    duration.value = 0
    lastNearEndLogSecond.value = -1
    isPlaying.value = true
    playlistCurrentIndex.value = index
    await refreshOverlapSeconds()
  } catch (error) {
    console.error('Error jumping to track:', error)
  }
}

async function handleAddSong({ path, genre }) {
  try {
    await $fetch(buildApiUrl('/api/playlist/add'), {
      method: 'POST',
      body: { path, genre },
    })
    await fetchPlaylist()
    playlistTableRef.value?.notifyAddResult(true, 'Song added to playlist.')
  } catch (error) {
    playlistTableRef.value?.notifyAddResult(false, error?.data?.detail ?? 'Failed to add song.')
  }
}

</script>

<style scoped>
.page-layout {
  display: flex;
  flex-direction: column;
  align-items: center;
  padding: 20px;
  min-height: 100vh;
  background: linear-gradient(135deg, #0f1642 0%, #1e2a78 50%, #2a1040 100%);
}
</style>
