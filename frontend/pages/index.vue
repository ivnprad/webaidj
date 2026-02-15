<template>
    <div class="audio-player">
        <div class="player-content">
            <div class="album-art" :style="albumArtStyle"></div>
            <div class="track-info">
                <h2 class="track-title">{{ displayTrack.title }}</h2>
                <p v-if="displayTrack.artist && displayTrack.artist !='Unknown Artist'"class="track-artist">
                    {{ displayTrack.artist }}
                </p>
            </div>
            <div class="progress-container">
                <div class="time current-time">{{ formatTime(currentTime) }}</div>
                <input 
                type="range"
                class="progress-bar"
                :max="duration"
                :value="currentTime"
                @input="onProgressChange"
                > 
                <div class="time duration">{{ formatTime(duration) }}</div>
            </div> 
            <div class="controls">
                <button @click="previousTrack" class="control-btn previous" aria-label="Previous Track">
                    <i class="fas fa-step-backward"></i>
                </button>
                <button @click="togglePlayPause" class="control-btn play" aria-label="Play/Pause">
                    <i :class="isPlaying? 'fas fa-pause' : 'fas fa-play'"></i>
                </button>
                <button @click="nextTrack" class="control-btn next" aria-label="Next Track">
                    <i class="fas fa-step-forward"></i>
                </button>
            </div>

            <div class="backend-controls">
                <button @click="streamPlay" class="control-btn stream-play" aria-label="Stream Play">
                    <i class="fas fa-broadcast-tower"></i>
                </button>
                <button @click="toggleShuffle" class="control-btn shuffle" aria-label="Shuffle">
                    <i :class="isShuffle ? 'fas fa-random' : 'fas fa-sync'"></i>
                </button>
                <div v-if="responseMessage" class="response-message">
                    {{ responseMessage }}
                </div>
            </div>
        </div>

        <audio 
        ref="audioPlayer" 
        :src="activeAudioSource" 
        preload="medata" 
        @loadedmetadata="onLoadedMetadata"
        @ended="onTrackEnded">
        </audio>

    </div>
</template>

<script setup>

import { computed, ref , onMounted, onUnmounted,nextTick} from 'vue'

const audioPlayer = ref(null)
const duration = ref(0)
const currentTime = ref(0)
const isPlaying = ref(false)
const isShuffle = ref(false)
const responseMessage = ref('false');
const streamUrl = ref('')
const streamTrack = ref(null) // {title, artist}

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

const currentTrackIndex = ref(0)
const currentTrack = ref(playlist[0])
const activeAudioSource = computed(() => streamUrl.value || currentTrack.value.source)
const displayTrack = computed(()=>streamTrack.value || currentTrack.value)

const albumArtStyle = computed(() => ({
  backgroundImage: `url(${currentTrack.value.albumArt})`,
  backgroundSize: 'cover',
  backgroundPosition: 'center',
  borderRadius: '10px',
  width: '200px',
  height: '200px'
}));

const formatTime = (time) => {
    const minutes = Math.floor(time / 60)
    const seconds = Math.floor(time % 60)
    return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
}

const togglePlayPause = () => {
    if (audioPlayer.value.paused) {
        audioPlayer.value.play()
        isPlaying.value = true
    } else {
        audioPlayer.value.pause()
        isPlaying.value = false
    }
}

const onLoadedMetadata = () => {
    if (audioPlayer.value) {
        duration.value = audioPlayer.value.duration;
    }
}

const updateProgress = () => {
    currentTime.value = audioPlayer.value.currentTime
}

const onProgressChange = (event) => {
    const time = Number(event.target.value)
    audioPlayer.value.currentTime = time
    currentTime.value = time
}

const nextTrack = () => {
    currentTrackIndex.value = (currentTrackIndex.value + 1) % playlist.length
    currentTrack.value = playlist[currentTrackIndex.value]
    isPlaying.value = false
    setTimeout(() => {
        audioPlayer.value.play()
        isPlaying.value = true
    }, 0)
}

const previousTrack = () => {
    currentTrackIndex.value = (currentTrackIndex.value - 1 + playlist.length) % playlist.length
    currentTrack.value = playlist[currentTrackIndex.value]
    isPlaying.value = false
    setTimeout(() => {
        audioPlayer.value.play()
        isPlaying.value = true
    }, 0)
}

const onTrackEnded = () => {
    nextTrack()
}

let progressInterval

onMounted(() => {
    if (audioPlayer.value) {
        duration.value = audioPlayer.value.duration;
    }
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
        const response = await $fetch('/api/play', {
            method: 'POST',
            body: { path: '/Users/ivanherrera/Music/Salsa/cuba/timba/100MBP/Mi_Historia_Entre_Tus_Dedos.m4a' },
        })

        streamTrack.value = response.currentTrack
        streamUrl.value = `${response.streamUrl}?t=${Date.now()}`
        await nextTick()
        await audioPlayer.value.play()
        isPlaying.value = true
    } catch (error) {
        console.error('Error starting stream playback:', error)
    }
}

</script>

<style scoped>

.audio-player {
    width: 300px;
    background: linear-gradient(to right, #1e2a78, #ff6b6b); 
    border-radius: 20px;
    padding: 20px;
    box-shadow: 0 0 10px rgba(0, 0, 0, 0.5);
    color: white;
    font-family: 'Arial', sans-serif;
}

.player-content {
    display: flex;
    flex-direction: column;
    align-items: center;
}

/* .album-art {
    width: 200px;
    height: 200px;
    background-image: url('@/assets/images/vecteezy_illustration-of-blue-headphone-headset-and-technology-for_4969269.jpg');
    background-size: cover;
    background-position: center;
    border-radius: 10px;
} */

.track-info {
    text-align: center;
    margin-top: 10px;
}

.track-title {
    font-size: 1.2em;
    margin: 0;
    font-weight: bold;
}

.track-artist {
    font-size: 0.9em;
    margin: 5px 0 0;
    opacity: 0.8;
}

.progress-container {
    width: 100%;
    display: flex;
    align-items: center;
    margin-top: 5px;
    justify-content: center;
}

.time {
    font-size: 0.8em;
    width: 35px;
}

.progress-bar {
    flex-grow: 1;
    margin: 0 10px;
    -webkit-appearance: none;
    appearance: none;
    background: rgba(255, 255, 255, 0.2);
    outline: none;
    height: 5px;
    border-radius: 5px;
}

.progress-bar::-webkit-slider-thumb { 
    -webkit-appearance: none;
    appearance: none;
    width: 15px;
    height: 15px;
    background: white;
    cursor: pointer;
    border-radius: 50%;
}

.progress-bar::-moz-range-thumb {
    width: 15px;
    height: 15px;
    background: white;
    cursor: pointer;
    border-radius: 50%;
}

.controls {
    display: flex;
    justify-content: center;
    align-items: center;
}

.control-btn {
  background: none;
  border: none;
  color: white;
  font-size: 24px;
  cursor: pointer;
  margin: 0 15px;
  transition: transform 0.2s;
  display: flex;
  align-items: center;
  justify-content: center;
  width: 50px;
  height: 50px;
  border-radius: 50%;
  background-color: rgba(255, 255, 255, 0.2);
}

.control-btn:hover {
  transform: scale(1.1);
  background-color: rgba(255, 255, 255, 0.3);
}

.play-pause {
  font-size: 28px;
  width: 60px;
  height: 60px;
}

@keyframes pulse {
  0% {
    transform: scale(1);
  }
  50% {
    transform: scale(1.05);
  }
  100% {
    transform: scale(1);
  }
}

.play-pause:hover {
  animation: pulse 1s infinite;
}

</style>
