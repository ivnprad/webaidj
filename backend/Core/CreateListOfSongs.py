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

def _BuildSortedList(songDataClean):
    d = FirstGenerativePattern(songDataClean) or {}
    for pattern in [Pattern.PATTERN_DESCENDING, Pattern.PATTERN_ASCENDING,
                    Pattern.PATTERN_DESCENDING, Pattern.PATTERN_ASCENDING]:
        result = FirstGenerativePattern(songDataClean, pattern)
        if result:
            d.update(result)
    return list(d.keys())

def InterleaveGenres(salsa_list, bachata_list, salsa_n, bachata_n):
    result = []
    si, bi = 0, 0
    while si < len(salsa_list) or bi < len(bachata_list):
        for _ in range(salsa_n):
            if si < len(salsa_list):
                result.append(salsa_list[si])
                si += 1
        for _ in range(bachata_n):
            if bi < len(bachata_list):
                result.append(bachata_list[bi])
                bi += 1
    return result

#TODO pack FirstGenerativePattern in one function -> better set time in hours
def CreateNewListOfSongs(genre, salsa_n=3, bachata_n=3):
    DeleteFile(songsListFile)

    if genre == "both":
        salsaPath = GetDirectory("salsa")
        bachataPath = GetDirectory("bachata")
        if not salsaPath or not os.path.isdir(salsaPath):
            raise FileNotFoundError(f"Salsa folder not found: {salsaPath}")
        if not bachataPath or not os.path.isdir(bachataPath):
            raise FileNotFoundError(f"Bachata folder not found: {bachataPath}")

        ConvertM4AtoMp3(salsaPath)
        ConvertM4AtoMp3(bachataPath)
        salsaSongPaths = ListFilesInFolderRecursively(salsaPath)
        bachataSongPaths = ListFilesInFolderRecursively(bachataPath)
        allSongPaths = salsaSongPaths + bachataSongPaths

        songData = GetSongData()
        songsPlayed = set(ListOfSongsPlayed())

        for song in allSongPaths:
            if not song.endswith(".mp3"):
                continue
            if song not in songData:
                floatBeats = CalculateBeats(song)
                beats = round(floatBeats[0])
                songData[song] = beats

        SaveToJson(songData, filename=songBeatsFile)

        salsaPathsSet = set(salsaSongPaths)
        bachataPathsSet = set(bachataSongPaths)
        salsaClean = {s: b for s, b in songData.items() if s in salsaPathsSet and s not in songsPlayed}
        bachataClean = {s: b for s, b in songData.items() if s in bachataPathsSet and s not in songsPlayed}

        salsaSorted = _BuildSortedList(salsaClean)
        bachataSorted = _BuildSortedList(bachataClean)

        interleaved = InterleaveGenres(salsaSorted, bachataSorted, salsa_n, bachata_n)
        SaveToJson({s: songData[s] for s in interleaved}, songsListFile)
        return interleaved

    # Single genre
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

    for song in songPaths:
        if not song.endswith(".mp3"):# TODO check if song name in .m4a is in .mp3 if not convert it
            continue
        if song not in songData:
            floatBeats = CalculateBeats(song)
            beats = round(floatBeats[0])
            songData[song] = beats

    SaveToJson(songData, filename=songBeatsFile)

    songDataClean = {s: b for s, b in songData.items() if s in songPathsSet and s not in songsPlayed}

    sortedSongs = _BuildSortedList(songDataClean)
    SaveToJson({s: songData[s] for s in sortedSongs}, songsListFile)
    return sortedSongs
