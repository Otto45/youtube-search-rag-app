import argparse
import googleapiclient.discovery
import googleapiclient.errors
import json
import os
from pathlib import Path
import requests
import string
from youtube_transcript_api import YouTubeTranscriptApi

def get_video_subtitles(video_id: string):
    return YouTubeTranscriptApi.get_transcript(video_id)

def get_video_chapters(video_id: string):
    url = "https://yt.lemnoslife.com/videos"
    params = {"id": video_id, "part": "chapters"}
    
    response = requests.get(url, params=params)
    response.raise_for_status()

    chapters = response.json()["items"][0]["chapters"]["chapters"]
    assert len(chapters) >= 0, "Video has no chapters"

    for chapter in chapters:
        del chapter["thumbnails"]
    
    return chapters

def add_transcript_to_chapters(chapters, subtitles):
    for ii, chapter in enumerate(chapters):
        next_chapter = chapters[ii + 1] if ii < len(chapters) - 1 else {"time": 1e10}

        text = " ".join(
            [
                seg["text"]
                for seg in subtitles
                if seg["start"] >= chapter["time"]
                and seg["start"] < next_chapter["time"]
            ]
        )

        chapter["text"] = text

    return chapters

def create_documents(chapters, video_id, video_title):
    base_url = f"https://www.youtube.com/watch?v={video_id}"
    query_params_format = "&t={start}s"
    documents = []

    for chapter in chapters:
        text = chapter["text"].strip()
        start = chapter["time"]
        url = base_url + query_params_format.format(start=start)

        document = {"text": text, "metadata": {"source": url}}

        document["metadata"]["title"] = video_title
        document["metadata"]["chapter-title"] = chapter["title"]

        documents.append(document)

    return documents

def get_videos_for_user(channel_id: string):
    api_key = os.environ["YOUTUBE_API_KEY"]
    youtube = googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )

    response = request.execute()
    
    uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]
    
    # TODO: Implement pagination to get as many videos as possible for the channel
    request = youtube.playlistItems().list(
        part="snippet",
        maxResults=10,
        playlistId=uploads_playlist_id
    )

    response = request.execute()
    
    video_ids = []

    if 'items' in response:
        for item in response['items']:
            if 'snippet' in item and 'resourceId' in item['snippet'] and 'videoId' in item['snippet']['resourceId']:
                video_id = item['snippet']['resourceId']['videoId']
                video_ids.append(video_id)
    
    return video_ids


argParser = argparse.ArgumentParser()
argParser.add_argument("-c", "--channel")

args = argParser.parse_args()
youtube_channel_id = args.channel

video_ids = get_videos_for_user(youtube_channel_id)
print(video_ids)


# video_title = "So You Think You Know C#? Delegates & Higher Order Functions"
# video_id = "q1BCmwnkFfM"

# # Get transcript (the Youtube generated subtitles) and combine them into the video chapters
# subtitles = get_video_subtitles(video_id)
# chapters = get_video_chapters(video_id)
# chapters = add_transcript_to_chapters(chapters, subtitles)

# # Create the documents we are going to store in the db
# # The documents will be the "chunks" of our full video transcript we will create embeddings for
# documents = create_documents(chapters, video_id, video_title)
