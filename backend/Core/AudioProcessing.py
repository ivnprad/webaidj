import os
os.environ["PYGAME_HIDE_SUPPORT_PROMPT"] = "hide" # Set PYGAME_HIDE_SUPPORT_PROMPT to hide the support prompt
import pygame
import librosa
import tempfile
import soundfile as sf
from pydub import AudioSegment
import os
import time
import simpleaudio as sa
from asyncio import to_thread
from Core.FileHandling import DeleteAndCreate
from Logging.MainLogger import mainLogger
# TODO Continuous music beat

silenceThresholdInDbfs= -35
milisecondsToSeconds = 1/1000 
MIN_CROSSFADE_SECONDS = 2.0
MAX_CROSSFADE_SECONDS = 20.0
DEFAULT_CROSSFADE_SECONDS = 6.0

# def fade_out_and_stop(play_obj, fade_duration_ms,song,current_position):
#     remaining_segment = song[current_position:]
#     fade_out_segment = remaining_segment.fade_out(fade_duration_ms)
#     play_obj.stop()
#     raw_data = fade_out_segment.raw_data
#     sample_rate = fade_out_segment.frame_rate
#     num_channels = fade_out_segment.channels
#     sa.play_buffer(raw_data, num_channels, 2, sample_rate).wait_done()

def Play(filePath, logUntilThisLimit,stopEvent,startPos=0):
    # Load the file
    song = AudioSegment.from_file(filePath)
    secondsToMilisecondsFactor = 1000
    startPosMS = startPos * secondsToMilisecondsFactor
    playbackSegment = song[startPosMS:]

    # Convert the segment to raw audio data. Get the sample rate. Get the number of channels
    rawData = playbackSegment.raw_data
    sampleRate = playbackSegment.frame_rate
    numChannels = playbackSegment.channels
    playObj = sa.play_buffer(rawData, numChannels, 2, sampleRate)

    startTime = time.time()
    while playObj.is_playing():
        currentTime = time.time() - startTime + startPos 
        if currentTime<logUntilThisLimit:
            mainLogger.debug(f"{filePath[-30:]} Current playback position: {currentTime:.2f} seconds")
            DeleteAndCreate(filePath,currentTime)
        time.sleep(0.5)
        if stopEvent.is_set():
            playObj.stop()
            #currentPosition=time.time() - startTime + startPos 
            #fade_out_and_stop(playObj, 1000,song,currentPosition)
            break
    
    mainLogger.debug(f" {filePath.split('/')[-1]} playing done.")

    return currentTime

async def PlayAsync(filePath, logUntilThisLimit,stopEvent,startPos=0):
    await to_thread(Play, filePath, logUntilThisLimit, stopEvent,startPos)

# Calculate beats 
def CalculateBeats(mp3Path):
    audio, sr = librosa.load(mp3Path, sr=None)

    with tempfile.NamedTemporaryFile(suffix=".wav", delete=True) as temp_wav:
        sf.write(temp_wav.name, audio, sr)
        tempo, beats = librosa.beat.beat_track(y=audio, sr=sr)

    return tempo

# Get mp3 from file
def GetMP3FromFile(filePath):
    root, extension = os.path.splitext(filePath)

    if extension.lower() == '.mp3':
        return filePath
    elif extension.lower() == '.m4a':
        audio = AudioSegment.from_file(filePath, format="m4a")
        outputFile = root + '.mp3'
        if os.path.exists(outputFile):
            return outputFile
        audio.export(outputFile,format="mp3")
        return outputFile
    else:
        return None

def ConvertM4AtoMp3(folderPath):
    try:
        for root, dirs, files in os.walk(folderPath):
            for file in files:
                if file.endswith((".m4a")):
                    mp3file = file[:-4] + ".mp3"
                    outputFile = root + "/"+ mp3file
                    if os.path.exists(outputFile):
                        continue
                    inputFile = root + "/"+ file
                    audio = AudioSegment.from_file(inputFile, format="m4a")
                    audio.export(outputFile, format="mp3")
    except Exception as e:
         raise ValueError("converting .m4a to .mp3 raise this exception ") from e
         

def GetSongWithAudioSegment(song):

    audioSegmentSong = None
    if not isinstance(song, AudioSegment):
        try:
            audioSegmentSong = AudioSegment.from_file(song)
            return audioSegmentSong
        except Exception as e:
            raise ValueError("Provided 'song' must be an AudioSegment object or a valid file path") from e
    
    return song
   
# Detect silecente portions of with threshold of -35
def DetectSilencePortionsOfSong(song):

    song = GetSongWithAudioSegment(song)
    durationMs = len(song)

    # Find start_ms
    for nonSilentStartTimeInMs in range(durationMs):
        if song[nonSilentStartTimeInMs].dBFS > silenceThresholdInDbfs:
            break

    # Find end_ms
    for nonSilentEndTimeInMs in range(durationMs - 1, -1, -1):
        if song[nonSilentEndTimeInMs].dBFS > silenceThresholdInDbfs:
            break

    songDuration = durationMs*milisecondsToSeconds
    nonSilentStartTime = nonSilentStartTimeInMs*milisecondsToSeconds
    nonSilentEndTime  = nonSilentEndTimeInMs*milisecondsToSeconds
    silenceAtEndDuration = songDuration-nonSilentEndTime
    
    return nonSilentStartTime,nonSilentEndTime,silenceAtEndDuration, songDuration

def GetNonSilentStartTime(song):
    song = GetSongWithAudioSegment(song)
    durationMs = len(song)
    nonSilentStartTimeInMs = durationMs

    for nonSilentStartTimeInMs in range(durationMs):
        if song[nonSilentStartTimeInMs].dBFS > silenceThresholdInDbfs:
            break    
    
    return nonSilentStartTimeInMs*milisecondsToSeconds

def GetNonSilentEndTime(song):
    song = GetSongWithAudioSegment(song)
    durationMs = len(song)
    nonSilentEndTimeInMs = 0

    for nonSilentEndTimeInMs in range(durationMs - 1, -1, -1):
        if song[nonSilentEndTimeInMs].dBFS > silenceThresholdInDbfs:
            break
    
    return nonSilentEndTimeInMs*milisecondsToSeconds

def GetSongDuration(song):
    song = GetSongWithAudioSegment(song)
    return len(song)*milisecondsToSeconds     

def GetSilenceAtEndDuration(song):
    return max(0.0, GetSongDuration(song) - GetNonSilentEndTime(song))


# Beat/tempo match
# Align BPM (or time-stretch slightly) so kicks/snare grids line up.

# Phrase alignment
# Start the incoming track on musical boundaries (often every 8/16/32 bars), not arbitrary seconds.

# Harmonic compatibility
# Prefer compatible keys (Camelot-style neighbors) or apply key shift carefully.

# EQ-based blend
# During overlap, reduce bass on one track to avoid low-end clash, then swap bass at phrase points.

# Structured gain automation
# Use controlled volume curves (not abrupt changes): intro in, outgoing out, with planned overlap length.

# Section-aware transitions
# Mix based on song parts (outro -> intro, break -> drop), using cue points/hot cues.

# Loudness/headroom control
# Keep perceived loudness consistent and avoid clipping/limiter pumping.

# Safety constraints
# Clamp min/max mix length, avoid dead air, detect problematic intros/outros.


# What can be wrong in practice:

# If either song has little/no silence, transition can feel abrupt.
# If silenceAtEndDuration + nextStart > currentSongDuration, delay becomes negative.
# It ignores tempo, phrasing, and beat alignment.
# Silence detection thresholds can misclassify quiet intros/outros.
# Loading full audio each time may be expensive.

def CalculateTransition(currentSong,nextSong):
    currentMp3 = GetMP3FromFile(currentSong)
    nextMp3 = GetMP3FromFile(nextSong)

    if currentMp3 is None or nextMp3 is None:
        mainLogger.warning(
            f"CalculateTransition fallback: unsupported audio extension. currentSong={currentSong}, nextSong={nextSong}"
        )
        return 0.0

    try:
        currentDeckSong = AudioSegment.from_file(currentMp3)
        silenceAtEndDuration = max(0.0, GetSilenceAtEndDuration(currentDeckSong))
        currentSongDuration = max(0.0, GetSongDuration(currentDeckSong))

        nextDeckSong = AudioSegment.from_file(nextMp3)
        nextSongLeadInSilenceSec = max(0.0, GetNonSilentStartTime(nextDeckSong))
    except Exception as e:
        mainLogger.warning(
            f"CalculateTransition fallback due to analysis error. currentSong={currentSong}, nextSong={nextSong}, error={e}"
        )
        return 0.0

    rawCrossfade = silenceAtEndDuration + nextSongLeadInSilenceSec
    crossfade = max(MIN_CROSSFADE_SECONDS, min(MAX_CROSSFADE_SECONDS, rawCrossfade))
    crossfade = min(crossfade, currentSongDuration)
    nextSongStartTimeSec = max(0.0, currentSongDuration - crossfade)

    # Fallback for very short or problematic tracks.
    if currentSongDuration == 0.0:
        nextSongStartTimeSec = 0.0
    elif rawCrossfade <= 0.0:
        crossfade = min(max(DEFAULT_CROSSFADE_SECONDS, MIN_CROSSFADE_SECONDS), currentSongDuration)
        nextSongStartTimeSec = max(0.0, currentSongDuration - crossfade)

    mainLogger.debug(
        f"currentSong={os.path.basename(currentSong)}, nextSong={os.path.basename(nextSong)}, "
        f"currentSongDuration={currentSongDuration:.3f}s, silenceAtEnd={silenceAtEndDuration:.3f}s, "
        f"nextSongLeadInSilenceSec={nextSongLeadInSilenceSec:.3f}s, rawCrossfade={rawCrossfade:.3f}s, crossfade={crossfade:.3f}s, nextSongStartTimeSec={nextSongStartTimeSec:.3f}s"
    )

    return nextSongStartTimeSec

