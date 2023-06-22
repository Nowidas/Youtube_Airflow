import json
from datetime import date
from tqdm import tqdm

from googleapiclient.discovery import build

from secrets_keys import YOUTUBE_API_KEY as API_KEY


# playlists = {
#     "📼 Tapes Colection 📼": "PLomXEcQ9kTsGK3CR5SmwGrOr4uGZXn-_b",
#     "Sin()-1": "PLomXEcQ9kTsEK_N7rJa1Feia6zfMakY1A",
#     "grape": "PLomXEcQ9kTsF_XwsVGjICmnpm7ctX3hXH",
#     "Noviyaa": "PLomXEcQ9kTsGCWHP3OED9pcshiy-kRQVf",
#     "[no_name]": "PLomXEcQ9kTsFnpU1YsQs4gQoNfBZ6tts3",
#     "{chill}ON//~all": "PLomXEcQ9kTsHw6y_sXWMNFv8kgsAM3Oyt",
# }

playlists = {
    "PLomXEcQ9kTsGK3CR5SmwGrOr4uGZXn-_b": "📼 Tapes Colection 📼",
    "PLomXEcQ9kTsEK_N7rJa1Feia6zfMakY1A": "Sin()-1",
    "PLomXEcQ9kTsF_XwsVGjICmnpm7ctX3hXH": "grape",
    "PLomXEcQ9kTsGCWHP3OED9pcshiy-kRQVf": "Noviyaa",
    "PLomXEcQ9kTsFnpU1YsQs4gQoNfBZ6tts3": "[no_name]",
    "PLomXEcQ9kTsHw6y_sXWMNFv8kgsAM3Oyt": "{chill}ON//~all",
}

youtube = build("youtube", "v3", developerKey=API_KEY)


def get_playlist_page(id, pageToken=None):
    request = youtube.playlistItems().list(
        part="id,contentDetails,snippet,status",
        playlistId=id,
        maxResults=50,
        pageToken=pageToken,
    )
    return request.execute()


def get_playlist(id):
    res = get_playlist_page(id, pageToken=None)
    playlist = res.copy()
    pages_count = res["pageInfo"]["totalResults"] // res["pageInfo"]["resultsPerPage"]
    for _ in range(pages_count):
        res = get_playlist_page(id, pageToken=res["nextPageToken"])
        playlist["items"].extend(res["items"])
    return playlist


def clear_playlist_dic(playlist):
    playlist_out = []
    for n, vid in enumerate(playlist["items"]):
        name = "N/D"
        try:
            id = vid.get("contentDetails").get("videoId")
            name = vid.get("snippet").get("title")
        except:
            pass
        if name in ["Deleted video", "Private video"]:
            name = "DELETED_VIDEO"
        playlist_out.append("\t".join([str(n), id, name + "\n"]))
    return playlist_out


def main():
    pass


if __name__ == "__main__":
    main()
