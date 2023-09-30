import argparse
import googleapiclient.discovery
import googleapiclient.errors
from langchain.embeddings import BedrockEmbeddings
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain.vectorstores import MongoDBAtlasVectorSearch
import os
from pymongo import MongoClient
import requests
import string
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled

def get_youtube_client():
    api_key = os.environ["YOUTUBE_API_KEY"]
    return googleapiclient.discovery.build("youtube", "v3", developerKey=api_key)

def get_embeddings():
    return BedrockEmbeddings()

def get_videos_for_user(channel_id: string, next_page_token: string = None):
    youtube = get_youtube_client()

    request = youtube.channels().list(
        part="contentDetails",
        id=channel_id
    )

    response = request.execute()
    
    uploads_playlist_id = response["items"][0]["contentDetails"]["relatedPlaylists"]["uploads"]

    request = youtube.playlistItems().list(
        playlistId=uploads_playlist_id,
        part="snippet",
        maxResults=25, # 50 is the max allowed per page of results
        pageToken=next_page_token
    )

    youtube_api_next_page_token = None
    
    response = request.execute()
    
    if 'nextPageToken' in response:
        youtube_api_next_page_token = response["nextPageToken"]

    video_ids_with_titles = []

    if 'items' in response:
        for item in response['items']:
            if 'snippet' in item and 'resourceId' in item['snippet'] and 'title' in item['snippet'] and 'videoId' in item['snippet']['resourceId']:
                video_title = item['snippet']['title']
                video_id = item['snippet']['resourceId']['videoId']
                video_ids_with_titles.append({"id": video_id, "title": video_title})
    
    return video_ids_with_titles, youtube_api_next_page_token

# TODO: Look into how this works under the hood
def get_video_transcript(video_id: string):
    return YouTubeTranscriptApi.get_transcript(video_id)

# TODO: Implement this functionality ourselves to avoid calling this API:
# https://github.com/Benjamin-Loison/YouTube-operational-API/blob/db1d2667b801dcc581ab29f29ab0757bc29f898a/videos.php#L272-L306
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

        chapter["text"] = text.strip()

    return chapters

def create_documents(video_info_with_transcripts):
    base_url = f"https://www.youtube.com/watch?v={video_id}"
    query_params_format = "&t={start}s"
    documents = []
    
    for video_info in video_info_with_transcripts:
        for chapter in video_info["chapters"]:
            text = chapter["text"]
            start = chapter["time"]
            url = base_url + query_params_format.format(start=start)

            documents.append({
                "text": text,
                "metadata": {
                    "source": url,
                    "title": video_info["title"],
                    "chapter-title": chapter["title"]
                }
            })

    return documents

def prep_documents_for_vector_storage(documents):
    text_splitter = RecursiveCharacterTextSplitter.from_tiktoken_encoder(
        chunk_size=500, chunk_overlap=100, allowed_special="all"
    )

    text_chunks, metadatas = [], []

    for document in documents:
        doc_text, doc_metadata = document["text"], document["metadata"]
        chunked_doc_texts = text_splitter.split_text(doc_text)
        doc_metadatas = [doc_metadata] * len(chunked_doc_texts)
        text_chunks += chunked_doc_texts
        metadatas += doc_metadatas

    return text_chunks, metadatas

def save_documents_with_vector_embeddings(documents):
    client = MongoClient(os.environ["MONGODB_ATLAS_CLUSTER_URI"])

    db_name = "youtube_ai_search"
    collection_name = "video_transcripts"
    collection = client[db_name][collection_name]
    index_name = "video_transcripts"
    embeddings = get_embeddings()

    text_chunks, metadatas = prep_documents_for_vector_storage(documents)
    
    vector_store = MongoDBAtlasVectorSearch(collection, embeddings, index_name=index_name)
    vector_store.add_texts(text_chunks, metadatas)

# Main
argParser = argparse.ArgumentParser()
argParser.add_argument("-c", "--channel")

args = argParser.parse_args()
youtube_channel_id = args.channel

video_ids_with_titles, youtube_api_next_page_token = get_videos_for_user(youtube_channel_id)
process_videos = True

while (process_videos):
    video_info_with_transcripts = []

    for video_id_with_title in video_ids_with_titles:
        video_id = video_id_with_title["id"]
        video_title = video_id_with_title["title"]

        print(f"Processing video: {video_title}")

        try:
            transcript = get_video_transcript(video_id)
            chapters = get_video_chapters(video_id)
            chapters = add_transcript_to_chapters(chapters, transcript)

            video_info_with_transcripts.append({
                "id": video_id,
                "title": video_title,
                "chapters": chapters
            })
        except TranscriptsDisabled:
            print(f"No transcript is available for the video: {video_title}")

    documents = create_documents(video_info_with_transcripts)
    save_documents_with_vector_embeddings(documents)
    
    if (youtube_api_next_page_token):
        video_ids_with_titles, youtube_api_next_page_token = get_videos_for_user(youtube_channel_id, youtube_api_next_page_token)
    else:
        process_videos = False
