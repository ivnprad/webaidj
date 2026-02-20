<template>
<AudioPlayerShell
  :display-track="displayTrack"
  :album-art-style="albumArtStyle"
  :current-time="currentTime"
  :duration="duration"
  :is-playing="isPlaying"
  :is-shuffle="isShuffle"
  :response-message="responseMessage"
  @previous="previousTrack"
  @play-pause="togglePlayPause"
  @next="nextTrack"
  @seek="onProgressChangeFromShell"
  @stream-play="streamPlay"
  @toggle-shuffle="toggleShuffle"
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

import { computed, ref , onMounted, onUnmounted,nextTick} from 'vue'

// UI props 
const isPlaying = ref(false)
const isShuffle = ref(false)
const responseMessage = ref('false');
const currentTime = ref(0)
const duration = ref(0)

const playlist = [
    { 
        title: 'Leave Me Alone', 
        artist: 'Florian bur',
        source: '/audio/Florian bur - Leave Me Alone.mp3',
        albumArt: '/assets/images/vecteezy_illustration-of-blue-headphone-headset-and-technology-for_4969269.jpg'
    },
    { 
        title: 'Secret', 
        artist: 'Florian bur',
        source: '/audio/04_Florian_bur_Secret_feat_Deryn.mp3',
        albumArt: '/assets/images/pexels-mark-angelo-sampan-738078-1587927.jpg'
    },
    { 
        title: 'Sound of Heart', 
        artist: 'Florian bur',
        source: '/audio/01 Florian bur - Sound of Heart.mp3',
        albumArt: '/assets/images/vector-dj-disk-1241523.jpg'
    }
]

const currentTrack = ref(playlist[0])
const streamTrack = ref(null) // {title, artist}
const displayTrack = computed(()=>streamTrack.value || currentTrack.value)
const albumArtStyle = computed(() => ({
  backgroundImage: `url(${currentTrack.value.albumArt})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  borderRadius: '10px',
  width: '200px',
  height: '200px'
}));

const audioPlayerLeft = ref(null)
const audioPlayerRight = ref(null)
const playerSources = ref(['', ''])
const activePlayerIndex = ref(0)
const overlapStarted = ref(false)
const overlapSeconds = 5 // PLACEHOLDER
const debugOverlap = true
const lastNearEndLogSecond = ref(-1)
const streamUrl = ref('')

const currentTrackIndex = ref(0)
const streamPlaylist = ref([
  '/Users/ivanherrera/Music/Salsa/cuba/timba/100MBP/Mi_Historia_Entre_Tus_Dedos.m4a',
  '/Users/ivanherrera/Music/Salsa/colombianas/90MBP/01_Oiga_Mir_Vea.m4a',
  '/Users/ivanherrera/Music/Salsa/romanticas/88MBP/03_Conciencia.m4a'
])

const logOverlap = (...args) => {
    if (!debugOverlap) return
    console.log('[overlap]', ...args)
}

const getPlayer = (index) => (index === 0 ? audioPlayerLeft.value : audioPlayerRight.value)
const getActivePlayer = () => getPlayer(activePlayerIndex.value)
const getInactivePlayerIndex = () => (activePlayerIndex.value === 0 ? 1 : 0)

const setPlayerSource = async (index, source) => {
    playerSources.value[index] = source
    await nextTick()
}

const stopPlayer = (index) => {
    const player = getPlayer(index)
    if (!player) return
    player.pause()
    player.currentTime = 0
}

const pausePlayer = (index) => {
    const player = getPlayer(index)
    if (!player) return
    player.pause()
}

const togglePlayPause = () => {
    const activePlayer = getActivePlayer()
    if (!activePlayer) return

    if (activePlayer.paused) {
        activePlayer.play()
        isPlaying.value = true
        logOverlap('play', {
            player: activePlayerIndex.value,
            src: playerSources.value[activePlayerIndex.value],
        })
    } else {
        pausePlayer(0)
        pausePlayer(1)
        isPlaying.value = false
        logOverlap('pause')
    }
}

const onLoadedMetadata = (playerIndex) => {
    if (playerIndex !== activePlayerIndex.value) return
    const activePlayer = getActivePlayer()
    if (activePlayer) {
        duration.value = activePlayer.duration;
        logOverlap('metadata loaded', {
            player: playerIndex,
            duration: activePlayer.duration,
            src: playerSources.value[playerIndex],
        })
    }
}

const updateProgress = () => {
    const activePlayer = getActivePlayer()
    if (!activePlayer) return

    currentTime.value = activePlayer.currentTime
    duration.value = Number.isFinite(activePlayer.duration) ? activePlayer.duration : 0

    const remaining = duration.value - currentTime.value
    if (Number.isFinite(remaining) && remaining <= overlapSeconds + 1 && remaining >= 0) {
        const remainingFloor = Math.floor(remaining)
        if (remainingFloor !== lastNearEndLogSecond.value) {
            lastNearEndLogSecond.value = remainingFloor
            logOverlap('near end', {
                player: activePlayerIndex.value,
                currentTime: currentTime.value.toFixed(2),
                duration: duration.value.toFixed(2),
                remaining: remaining.toFixed(2),
                overlapStarted: overlapStarted.value,
                isPlaying: isPlaying.value,
            })
        }
    }

    if (
        isPlaying.value &&
        !overlapStarted.value &&
        duration.value > overlapSeconds &&
        currentTime.value >= duration.value - overlapSeconds
    ) {
        logOverlap('trigger reached', {
            currentTime: currentTime.value.toFixed(2),
            duration: duration.value.toFixed(2),
            threshold: (duration.value - overlapSeconds).toFixed(2),
        })
        startNextTrackOverlap()
    }
}
const onProgressChangeFromShell = (time) => {
  const activePlayer = getActivePlayer()
  if (!activePlayer) return
  activePlayer.currentTime = Number(time)
  currentTime.value = Number(time)
}

const playLocalTrack = async (trackIndex) => {
    streamUrl.value = ''
    streamTrack.value = null
    overlapStarted.value = false

    stopPlayer(0)
    stopPlayer(1)

    const nextActiveIndex = getInactivePlayerIndex()

    currentTrackIndex.value = trackIndex
    currentTrack.value = playlist[trackIndex]
    currentTime.value = 0
    duration.value = 0

    await setPlayerSource(nextActiveIndex, currentTrack.value.source)
    activePlayerIndex.value = nextActiveIndex

    const activePlayer = getActivePlayer()
    if (!activePlayer) return
    await activePlayer.play()
    isPlaying.value = true
}

const nextTrack = async () => {
    if (streamUrl.value) {
        await playNextStreamTrack()
        return
    }
    const nextIndex = (currentTrackIndex.value + 1) % playlist.length
    await playLocalTrack(nextIndex)
}

const previousTrack = async () => {
    if (streamUrl.value) {
        await playPreviousStreamTrack()
        return
    }
    const previousIndex = (currentTrackIndex.value - 1 + playlist.length) % playlist.length
    await playLocalTrack(previousIndex)
}

const startNextTrackOverlap = async () => {
    overlapStarted.value = true
    logOverlap('start overlap begin', {
        fromTrackIndex: currentTrackIndex.value,
        activePlayer: activePlayerIndex.value,
    })

    try {
        if (streamUrl.value) {
            await playNextStreamTrack({ overlap: true })
            return
        }

        const nextIndex = (currentTrackIndex.value + 1) % playlist.length
        const incomingPlayerIndex = getInactivePlayerIndex()

        currentTrackIndex.value = nextIndex
        currentTrack.value = playlist[nextIndex]

        await setPlayerSource(incomingPlayerIndex, currentTrack.value.source)
        const incomingPlayer = getPlayer(incomingPlayerIndex)
        if (!incomingPlayer) return

        incomingPlayer.currentTime = 0
        await incomingPlayer.play()
        activePlayerIndex.value = incomingPlayerIndex
        isPlaying.value = true
        currentTime.value = 0
        duration.value = Number.isFinite(incomingPlayer.duration) ? incomingPlayer.duration : 0
        lastNearEndLogSecond.value = -1
        logOverlap('next started', {
            toTrackIndex: nextIndex,
            incomingPlayer: incomingPlayerIndex,
            src: playerSources.value[incomingPlayerIndex],
        })
    } catch (error) {
        console.error('Error starting overlap playback:', error)
        logOverlap('start overlap failed', error)
    } finally {
        overlapStarted.value = false
        logOverlap('start overlap end')
    }
}

const onTrackEnded = async(playerIndex) => {
  logOverlap('ended event', { playerIndex, activePlayer: activePlayerIndex.value })
  if (playerIndex !== activePlayerIndex.value) {
    stopPlayer(playerIndex)
    return
  }

  if (streamUrl.value) {
    await playNextStreamTrack()
    return
  }
  await nextTrack()
}

let progressInterval

onMounted(() => {
    playerSources.value[activePlayerIndex.value] = currentTrack.value.source
    progressInterval = setInterval(updateProgress, 100)
})

onUnmounted(() => {
    clearInterval(progressInterval)
})


const setCommandData = ref({
  ip_address: '192.168.141.10',
  component: 'SensorHead',
  command: 'LaserOn',
  data_type: 'Int16',
  payload: '1',
})

async function toggleShuffle() {
    
    isShuffle.value = !isShuffle.value
    responseMessage.value = 'Shuffle is toggle'

    try {
        const response = await $fetch('/api/toggle-shuffle', {
            method: 'POST',
            body: setCommandData.value,
        })
        responseMessage.value = response.message
    } catch (error) {
        console.error('Error toggling shuffle:', error)
    }
}

async function streamPlay() {
    try {
        stopPlayer(0)
        stopPlayer(1)
        activePlayerIndex.value = 0
        overlapStarted.value = false

        const response = await $fetch('/api/play', {
            method: 'POST',
            body: { paths: streamPlaylist.value, start_index: 0 },
        })

        streamTrack.value = response.currentTrack
        streamUrl.value = `${response.streamUrl}?t=${Date.now()}`
        await setPlayerSource(activePlayerIndex.value, streamUrl.value)
        await getActivePlayer().play()
        currentTime.value = 0
        duration.value = 0
        lastNearEndLogSecond.value = -1
        isPlaying.value = true
    } catch (error) {
        console.error('Error starting stream playback:', error)
    }
}

async function applyStreamTrackResponse(response, options = { overlap: false, direction: 'next' }) {
  const overlap = Boolean(options.overlap)
  const direction = options.direction || 'next'
  const nextUrl = `${response.streamUrl}?t=${Date.now()}`
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
  activePlayerIndex.value = incomingPlayerIndex
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
}

async function playNextStreamTrack(options = { overlap: false }) {
  const overlap = Boolean(options.overlap)
  const response = await $fetch('/api/play/next', { method: 'POST' })
  await applyStreamTrackResponse(response, { overlap, direction: 'next' })
}

async function playPreviousStreamTrack(options = { overlap: false }) {
  const overlap = Boolean(options.overlap)
  const response = await $fetch('/api/play/previous', { method: 'POST' })
  await applyStreamTrackResponse(response, { overlap, direction: 'previous' })
}

</script>
