<template>
  <div class="playlist-container">
    <div class="playlist-header">
      <h3 class="playlist-title">Playlist</h3>

      <div class="add-song-section">
        <button class="toggle-add-btn" @click="showAddForm = !showAddForm">
          <i class="fas fa-plus"></i> Add Song
        </button>

        <div v-if="showAddForm" class="add-song-form">
          <div class="form-row">
            <select v-model="addGenre" class="genre-select">
              <option value="salsa">Salsa</option>
              <option value="bachata">Bachata</option>
            </select>
            <div class="search-wrap">
              <input
                v-model="searchQuery"
                type="text"
                class="search-input"
                placeholder="Search songs..."
                @input="onSearchInput"
              />
              <ul v-if="filteredSongs.length > 0" class="song-dropdown">
                <li
                  v-for="song in filteredSongs"
                  :key="song.path"
                  class="song-option"
                  @click="selectSong(song)"
                >
                  <span class="song-name">{{ song.name }}</span>
                  <span v-if="song.bpm" class="song-bpm">{{ song.bpm }} BPM</span>
                </li>
              </ul>
            </div>
            <input
              v-model="selectedPath"
              type="text"
              class="path-input"
              placeholder="or paste path directly"
            />
            <button class="add-btn" :disabled="!selectedPath || adding" @click="submitAdd">
              <i :class="adding ? 'fas fa-spinner fa-spin' : 'fas fa-plus'"></i>
              {{ adding ? 'Adding…' : 'Add' }}
            </button>
          </div>
          <p v-if="addMessage" :class="['add-message', addMessageType]">{{ addMessage }}</p>
        </div>
      </div>
    </div>

    <div v-if="tracks.length === 0" class="empty-state">No tracks loaded — press play to start a session.</div>

    <table v-else class="playlist-table">
      <thead>
        <tr>
          <th>#</th>
          <th>Title</th>
          <th>Artist</th>
          <th>Duration</th>
          <th>BPM</th>
          <th>Genre</th>
        </tr>
      </thead>
      <tbody>
        <tr
          v-for="track in tracks"
          :key="track.index"
          :class="['track-row', { current: track.index === currentIndex }]"
          @click="emit('track-click', track.index)"
        >
          <td class="col-num">
            <i v-if="track.index === currentIndex" class="fas fa-volume-up playing-icon"></i>
            <span v-else>{{ track.index + 1 }}</span>
          </td>
          <td class="col-title">{{ track.title }}</td>
          <td class="col-artist">{{ track.artist }}</td>
          <td class="col-duration">{{ formatDuration(track.durationSec) }}</td>
          <td class="col-bpm">{{ track.bpm ?? '—' }}</td>
          <td class="col-genre">
            <span :class="['genre-badge', track.genre]">{{ track.genre }}</span>
          </td>
        </tr>
      </tbody>
    </table>
  </div>
</template>

<script setup>
import { ref, watch } from 'vue'

const props = defineProps({
  tracks: { type: Array, default: () => [] },
  currentIndex: { type: Number, default: -1 },
  availableSongs: { type: Array, default: () => [] },
})

const emit = defineEmits(['track-click', 'add-song', 'genre-songs-request'])

const showAddForm = ref(false)
const addGenre = ref('salsa')
const searchQuery = ref('')
const selectedPath = ref('')
const filteredSongs = ref([])
const adding = ref(false)
const addMessage = ref('')
const addMessageType = ref('success')

watch(addGenre, () => {
  searchQuery.value = ''
  selectedPath.value = ''
  filteredSongs.value = []
  emit('genre-songs-request', addGenre.value)
})

watch(showAddForm, (val) => {
  if (val) emit('genre-songs-request', addGenre.value)
})

const onSearchInput = () => {
  const q = searchQuery.value.toLowerCase().trim()
  if (!q) {
    filteredSongs.value = []
    return
  }
  filteredSongs.value = props.availableSongs
    .filter(s => s.name.toLowerCase().includes(q))
    .slice(0, 8)
}

const selectSong = (song) => {
  selectedPath.value = song.path
  searchQuery.value = song.name
  filteredSongs.value = []
}

const submitAdd = async () => {
  if (!selectedPath.value) return
  adding.value = true
  addMessage.value = ''
  emit('add-song', { path: selectedPath.value, genre: addGenre.value })
}

const notifyAddResult = (success, message) => {
  adding.value = false
  addMessage.value = message
  addMessageType.value = success ? 'success' : 'error'
  if (success) {
    selectedPath.value = ''
    searchQuery.value = ''
    filteredSongs.value = []
  }
}

defineExpose({ notifyAddResult })

const formatDuration = (sec) => {
  if (sec == null) return '—'
  const m = Math.floor(sec / 60)
  const s = Math.floor(sec % 60)
  return `${m}:${s.toString().padStart(2, '0')}`
}
</script>

<style scoped>
.playlist-container {
  width: 100%;
  max-width: 900px;
  margin: 20px auto 0;
  background: rgba(255, 255, 255, 0.05);
  border-radius: 12px;
  padding: 16px;
  color: white;
}

.playlist-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 12px;
  margin-bottom: 12px;
  flex-wrap: wrap;
}

.playlist-title {
  font-size: 1em;
  font-weight: bold;
  margin: 0;
  opacity: 0.8;
  text-transform: uppercase;
  letter-spacing: 0.05em;
  line-height: 2;
}

.empty-state {
  text-align: center;
  opacity: 0.5;
  padding: 24px 0;
  font-size: 0.9em;
}

.playlist-table {
  width: 100%;
  border-collapse: collapse;
  font-size: 0.85em;
}

.playlist-table th {
  text-align: left;
  padding: 6px 10px;
  opacity: 0.5;
  font-weight: normal;
  font-size: 0.8em;
  text-transform: uppercase;
  letter-spacing: 0.04em;
  border-bottom: 1px solid rgba(255,255,255,0.1);
}

.track-row {
  cursor: pointer;
  border-radius: 6px;
  transition: background 0.15s;
}

.track-row:hover {
  background: rgba(255,255,255,0.08);
}

.track-row.current {
  background: rgba(255,255,255,0.15);
}

.track-row td {
  padding: 8px 10px;
  border-bottom: 1px solid rgba(255,255,255,0.05);
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  max-width: 200px;
}

.col-num {
  width: 32px;
  text-align: center;
  opacity: 0.5;
}

.playing-icon {
  color: #ff6b6b;
  opacity: 1;
}

.col-title { font-weight: 500; }
.col-artist { opacity: 0.7; }
.col-duration, .col-bpm { opacity: 0.6; width: 60px; }
.col-genre { width: 80px; }

.genre-badge {
  padding: 2px 8px;
  border-radius: 10px;
  font-size: 0.8em;
  font-weight: 500;
  text-transform: capitalize;
}

.genre-badge.salsa { background: rgba(255, 107, 107, 0.3); color: #ff9e9e; }
.genre-badge.bachata { background: rgba(107, 107, 255, 0.3); color: #9e9eff; }
.genre-badge.unknown { background: rgba(255,255,255,0.1); color: rgba(255,255,255,0.5); }

.add-song-section {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}

.toggle-add-btn {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  border-radius: 8px;
  padding: 6px 14px;
  font-size: 0.8em;
  cursor: pointer;
  transition: background 0.15s;
}

.toggle-add-btn:hover { background: rgba(255,255,255,0.2); }

.add-song-form {
  margin-top: 10px;
}

.form-row {
  display: flex;
  gap: 8px;
  align-items: flex-start;
  flex-wrap: wrap;
}

.genre-select {
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.85em;
  cursor: pointer;
}

.genre-select option { background: #1e2a78; color: white; }

.search-wrap {
  position: relative;
  flex: 1;
  min-width: 160px;
}

.search-input {
  width: 100%;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.85em;
  box-sizing: border-box;
}

.search-input::placeholder { color: rgba(255,255,255,0.4); }

.song-dropdown {
  position: absolute;
  top: calc(100% + 4px);
  left: 0;
  right: 0;
  background: #1e2a78;
  border: 1px solid rgba(255,255,255,0.2);
  border-radius: 8px;
  list-style: none;
  margin: 0;
  padding: 4px 0;
  z-index: 100;
  max-height: 220px;
  overflow-y: auto;
}

.song-option {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 6px 12px;
  cursor: pointer;
  font-size: 0.85em;
  gap: 8px;
}

.song-option:hover { background: rgba(255,255,255,0.1); }

.song-name {
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.song-bpm {
  opacity: 0.5;
  font-size: 0.8em;
  white-space: nowrap;
}

.path-input {
  flex: 1;
  min-width: 120px;
  background: rgba(255,255,255,0.1);
  border: 1px solid rgba(255,255,255,0.2);
  color: white;
  border-radius: 8px;
  padding: 6px 10px;
  font-size: 0.85em;
}

.path-input::placeholder { color: rgba(255,255,255,0.4); }

.add-btn {
  background: rgba(255, 107, 107, 0.5);
  border: 1px solid rgba(255, 107, 107, 0.6);
  color: white;
  border-radius: 8px;
  padding: 6px 16px;
  font-size: 0.85em;
  cursor: pointer;
  white-space: nowrap;
  transition: background 0.15s;
}

.add-btn:hover:not(:disabled) { background: rgba(255, 107, 107, 0.7); }
.add-btn:disabled { opacity: 0.5; cursor: not-allowed; }

.add-message {
  margin: 8px 0 0;
  font-size: 0.8em;
}

.add-message.success { color: #7eff9e; }
.add-message.error { color: #ff7e7e; }
</style>
