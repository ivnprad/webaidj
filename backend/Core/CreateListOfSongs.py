from Core.FileHandling import currentSongFile, GetCurrentSongAndPosition, GetSongData, songsListFile, SubSetFromKey
from Core.FileHandling import DeleteFile, GetDirectory, SaveDirectory, ListFilesInFolderRecursively, ListOfSongsPlayed
from Core.FileHandling import SaveToJson, songBeatsFile
from Core.PatternGeneration import FirstGenerativePattern, Pattern
from Core.UI import SelecDirectory
from Core.AudioProcessing import ConvertM4AtoMp3, CalculateBeats
import os

def GetPreviousSessionSongs(jsonFile=currentSongFile):
    # currentSongPath, resumePosition = GetCurrentSongAndPosition(currentSongFile)
    # listOfSongsGeneratedInPreviousCycle = GetSongData(songsListFile)
    # subset = SubSetFromKey(listOfSongsGeneratedInPreviousCycle, currentSongPath)
    # subsetList = list(subset.keys())
    # if not subsetList:
    #     raise ValueError("currentSongPath not found")
    # return subsetList, resumePosition
    listOfSongsGeneratedInPreviousCycle = GetSongData(songsListFile)
    subsetList = list(listOfSongsGeneratedInPreviousCycle.keys())
    if not subsetList:
        raise ValueError("currentSongPath not found")
    return subsetList

#TODO pack FirstGenerativePattern in one function -> better set time in hours
def CreateNewListOfSongs(genre):
    DeleteFile(songsListFile)

    folderPaths = GetDirectory(genre)
    if folderPaths is None:
        raise ValueError(f"Unknown genre: {genre}")

    if isinstance(folderPaths, str):
        folderPaths = [folderPaths]

    for path in folderPaths:
        if not os.path.isdir(path):
            raise FileNotFoundError(f"folder path does not exist: {path}")

    songPaths = []
    for path in folderPaths:
        ConvertM4AtoMp3(path)
        songPaths.extend(ListFilesInFolderRecursively(path))

    songPathsSet = set(songPaths)
    songData = GetSongData()
    songsPlayed = set(ListOfSongsPlayed())

    # For song list in the given directory that end with .mp3 and are not in songData calculate Beats
    for song in songPaths:
        if not song.endswith(".mp3"):# TODO check if song name in .m4a is in .mp3 if not convert it
            continue
        if song not in songData:
            floatBeats = CalculateBeats(song)
            beats = round(floatBeats[0])
            songData[song] = beats

    SaveToJson(songData, filename=songBeatsFile) # update list to json

    songDataClean = {}
    for song, beat in songData.items():
        if song in songPathsSet and song not in songsPlayed:
            songDataClean[song] = beat

    sortedSongsDict = FirstGenerativePattern(songDataClean)
    sortedSongsDict2 = FirstGenerativePattern(songDataClean,Pattern.PATTERN_DESCENDING)
    sortedSongsDict3 = FirstGenerativePattern(songDataClean,Pattern.PATTERN_ASCENDING)
    sortedSongsDict4= FirstGenerativePattern(songDataClean,Pattern.PATTERN_DESCENDING)
    sortedSongsDict5= FirstGenerativePattern(songDataClean,Pattern.PATTERN_ASCENDING)

    sortedSongsDict.update(sortedSongsDict2)
    sortedSongsDict.update(sortedSongsDict3)
    sortedSongsDict.update(sortedSongsDict4)
    sortedSongsDict.update(sortedSongsDict5)
    SaveToJson(sortedSongsDict,songsListFile)
    sortedSongs = list(sortedSongsDict.keys())

    return sortedSongs