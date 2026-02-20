<template>
  <div class="audio-player">
    <div class="player-content">
      <div class="album-art" :style="albumArtStyle"></div>

      <div class="track-info">
        <h2 class="track-title">{{ displayTrack.title }}</h2>
        <p v-if="displayTrack.artist && displayTrack.artist !== 'Unknown Artist'" class="track-artist">
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
          @input="onSeek"
        >
        <div class="time duration">{{ formatTime(duration) }}</div>
      </div>

      <div class="controls">
        <button @click="emit('previous')" class="control-btn previous" aria-label="Previous Track">
          <i class="fas fa-step-backward"></i>
        </button>
        <button @click="emit('play-pause')" class="control-btn play" aria-label="Play/Pause">
          <i :class="isPlaying ? 'fas fa-pause' : 'fas fa-play'"></i>
        </button>
        <button @click="emit('next')" class="control-btn next" aria-label="Next Track">
          <i class="fas fa-step-forward"></i>
        </button>
      </div>

      <div class="backend-controls">
        <button @click="emit('stream-play')" class="control-btn stream-play" aria-label="Stream Play">
          <i class="fas fa-broadcast-tower"></i>
        </button>
        <button @click="emit('toggle-shuffle')" class="control-btn shuffle" aria-label="Shuffle">
          <i :class="isShuffle ? 'fas fa-random' : 'fas fa-sync'"></i>
        </button>
        <div v-if="responseMessage" class="response-message">
          {{ responseMessage }}
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>

// UI props. AudioPlayerShell is a presentational component driven by props.
const props = defineProps({
  displayTrack: { type: Object, required: true },
  albumArtStyle: { type: Object, required: true },
  currentTime: { type: Number, required: true },
  duration: { type: Number, required: true },
  isPlaying: { type: Boolean, required: true },
  isShuffle: { type: Boolean, required: true },
  responseMessage: { type: String, default: '' },
})

const emit = defineEmits([
  'previous',
  'play-pause',
  'next',
  'seek',
  'stream-play',
  'toggle-shuffle',
])

const onSeek = (event) => {
  const value = Number(event.target.value)
  emit('seek', value)
}

const formatTime = (time) => {
  const minutes = Math.floor(time / 60)
  const seconds = Math.floor(time % 60)
  return `${minutes.toString().padStart(2, '0')}:${seconds.toString().padStart(2, '0')}`
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
