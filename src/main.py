# -*- coding: utf-8 -*-

# Initial code skeleton took from:
# https://developers.google.com/explorer-help/guides/code_samples#python

import os
import time

import googleapiclient.discovery
import googleapiclient.errors
import isodate as isodate

scopes = ["https://www.googleapis.com/auth/youtube.readonly"]

channel_names = {
    'martinstankievitz': 'Martin_Stankiewicz',
    'SciTeraz': 'Sci-fun',
    'EdiPoszukiwacz': 'Poszukiwacz',
    'bankowo1': 'AdBuster',
    'Polimaty': 'Polimaty'
}

# Disable OAuthlib's HTTPS verification when running locally.
# *DO NOT* leave this option enabled in production.
os.environ["OAUTHLIB_INSECURE_TRANSPORT"] = "1"

api_service_name = "youtube"
api_version = "v3"
api_key = "YOUR_API_KEY"

youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=api_key)


def main():
    categories_dict = get_categories_dict()

    for channel_id, channel_name in channel_names.items():

        videos = get_most_recent_videos(channel_id, 6)

        for video_id in videos:
            duration_seconds, views, dislikes, likes, category_id, comments, quality, description_length, tags_count, published_at = get_video_statistics(
                video_id)

            category = "\"{}\"".format(categories_dict[category_id])

            top_comment_like_count = get_top_comment_like_count(video_id)

            captions = get_captions_count(video_id)

            print(duration_seconds, views, likes, dislikes, category, comments, top_comment_like_count,
                  quality, captions, published_at, channel_name, sep=", ")
            time.sleep(10)


def get_categories_dict() -> dict:
    categories_dict = {}
    request = youtube.videoCategories().list(
        part="snippet",
        regionCode="PL",
        hl="pl_PL"
    )
    response = request.execute()
    for item in response['items']:
        categories_dict[int(item['id'])] = item['snippet']['title']

    return categories_dict


def get_most_recent_videos(channel_name: str, max_results: int) -> list:
    request = youtube.channels().list(
        part="snippet,contentDetails,statistics",
        forUsername=channel_name,
        maxResults=max_results
    )
    response = request.execute()
    upload_id = response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    request = youtube.playlistItems().list(
        part="snippet,contentDetails",
        maxResults=max_results,
        playlistId=upload_id
    )
    response = request.execute()

    return list(map(lambda x: x['contentDetails']['videoId'], response['items']))


def get_video_statistics(video_id: str):
    request = youtube.videos().list(
        part="snippet,contentDetails,statistics",
        id=video_id
    )
    response = request.execute()

    video = response['items'][0]
    statistics = video['statistics']
    snippet = video['snippet']
    content_details = video['content_details']

    views, likes, dislikes, comments = statistics['viewCount'], statistics['likeCount'], statistics['dislikeCount'], \
                                       statistics['commentCount']

    description_length = len(str(snippet['description']))

    tags_count = len(snippet.get('tags', []))

    category_id = int(snippet['categoryId'])

    duration = str(content_details['duration'])
    duration_seconds = int(isodate.parse_duration(duration).total_seconds())

    quality = str(content_details['definition'])

    published_at = snippet['publishedAt']

    return duration_seconds, views, dislikes, likes, category_id, comments, quality, description_length, tags_count, published_at


def get_top_comment_like_count(video_id: str):
    request = youtube.commentThreads().list(
        part="snippet,replies",
        videoId=video_id,
        maxResults=99
    )
    response = request.execute()

    next_page_token = response.get('nextPageToken', None)
    top_comment = get_top_liked_comment(response)

    while next_page_token is not None:
        request = youtube.commentThreads().list(
            part="snippet,replies",
            videoId=video_id,
            maxResults=99,
            pageToken=next_page_token
        )
        response = request.execute()

        next_page_token = response.get('nextPageToken', None)
        top_comment = max(top_comment, get_top_liked_comment(response))

    return top_comment


def get_top_liked_comment(response):
    max_likes = 0
    for item in response['items']:

        like_count = int(item['snippet']['topLevelComment']['snippet']['likeCount'])
        replies = item.get('replies', None)
        if replies is None:
            max_likes = max(max_likes, like_count)
        else:
            reply_like_count = max(list(replies['comments']), key=lambda x: int(x['snippet']['likeCount']))['snippet'][
                'likeCount']
            max_likes = max(max_likes, like_count, reply_like_count)
    return max_likes


def get_captions_count(video_id):
    request = youtube.captions().list(
        part="snippet",
        videoId=video_id
    )
    response = request.execute()
    return len(response['items'])


if __name__ == "__main__":
    main()
