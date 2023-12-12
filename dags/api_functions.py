import argparse
from datetime import date
from tqdm import tqdm

from googleapiclient.discovery import build

from secrets_keys import YOUTUBE_API_KEY as API_KEY


playlists = {
    "PLomXEcQ9kTsGK3CR5SmwGrOr4uGZXn-_b": "📼 Tapes Colection 📼",
    "PLomXEcQ9kTsEK_N7rJa1Feia6zfMakY1A": "Sin()-1",
    "PLomXEcQ9kTsF_XwsVGjICmnpm7ctX3hXH": "grape",
    "PLomXEcQ9kTsGCWHP3OED9pcshiy-kRQVf": "Noviyaa",
    "PLomXEcQ9kTsFnpU1YsQs4gQoNfBZ6tts3": "[no_name]",
    "PLomXEcQ9kTsHw6y_sXWMNFv8kgsAM3Oyt": "{chill}ON//~all",
}


class YoutubeHook:
    def __init__(self, developerKey: str, playlists: dict):
        self.developerKey = developerKey
        self.playlists = playlists

        self.youtube = build("youtube", "v3", developerKey=self.developerKey)

    def _get_playlist_page(self, id, pageToken=None):
        request = self.youtube.playlistItems().list(
            part="id,contentDetails,snippet,status",
            playlistId=id,
            maxResults=50,
            pageToken=pageToken,
        )
        return request.execute()

    def _get_playlist(self, id: str):
        res = self._get_playlist_page(id, pageToken=None)
        playlist = res.copy()
        pages_count = (res["pageInfo"]["totalResults"] - 1) // res["pageInfo"][
            "resultsPerPage"
        ]
        for _ in range(pages_count):
            res = self._get_playlist_page(id, pageToken=res["nextPageToken"])
            playlist["items"].extend(res["items"])
        return playlist

    def _clear_playlist_dic(self, playlist: dict):
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

    def save_to_file(self, filepath: str, progress_bar: bool = False):
        filename = date.today().strftime("%Y-%m-%d") + ".txt"
        with open(
            filepath + filename,
            mode="w",
            encoding="utf-16",
        ) as fout:
            for k, v in tqdm(self.playlists.items(), disable=not progress_bar):
                playlist = self._get_playlist(k)
                playlist = self._clear_playlist_dic(playlist)

                fout.write(v + "\n")
                fout.writelines(playlist)


def main():
    parser = argparse.ArgumentParser(prog="Youtube Api Backup")
    parser.add_argument("filename")
    parser.add_argument("-v", "--verbose", action="store_true")
    args = parser.parse_args()

    if args.verbose:
        print("Making copy ...")
    api = YoutubeHook(API_KEY, playlists)
    api.save_to_file(args.filename, args.verbose)
    if args.verbose:
        print("Done !")


if __name__ == "__main__":
    main()
