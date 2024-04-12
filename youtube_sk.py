
import googleapiclient.discovery
import googleapiclient.errors
import pandas as pd
import streamlit as st
import pymysql
import datetime
import matplotlib.pyplot as plt

def use_api():
    API_KEY = "AIzaSyD-Dt31mbje1XN6IX6rP-GHXFQonsqC6DQ"
    
    api_service_name = "youtube"
    api_version = "v3"

    youtube = googleapiclient.discovery.build(
    api_service_name, api_version, developerKey=API_KEY)

    return youtube

youtube=use_api()

#get channel info
#id="UCS84kz7Fs8bzRs6xcPY9lQQ"
def get_channel_info(channel_id):
    chan_info=[]
    request=youtube.channels().list(
                    part="snippet,ContentDetails,statistics",
                    id=channel_id
    )
    response=request.execute()

    for i in response['items']:
        data=dict(channel_Name=i['snippet']['title'],
                channel_Id=i['id'],
                Subscribers=i['statistics']['subscriberCount'],
                Views=i['statistics']['viewCount'],
                Total_Videos=i["statistics"]["videoCount"],
                channel_Description=i['snippet']['description'],
                Playlist_Id=i['contentDetails']['relatedPlaylists']['uploads'])
        chan_info.append(data)
        return chan_info 
    
    # Collect Video IDs
def get_video_ids(channel_id):
    video_ids=[]
    response=youtube.channels().list(id=channel_id,
                                part='contentDetails').execute()

    Playlist_Id=response['items'][0]['contentDetails']['relatedPlaylists']['uploads']

    next_Page=None

    while True:
        response1 = youtube.playlistItems().list(
                                            playlistId=Playlist_Id,
                                            part='snippet',
                                            maxResults=150,
                                            pageToken=next_Page).execute()
        for i in range(len(response1['items'])):
            video_ids.append(response1['items'][i]['snippet']['resourceId']['videoId'])
        next_Page=response1.get('nextPageToken')

        if next_Page is None:
            break
    return video_ids

def list_to_string(lst):
    if lst is None:
        return None
    filtered_list = filter(lambda x: x is not None, lst)  # Filter out None values
    return ', '.join(map(str, filtered_list))

def parse_duration(duration_str):
    duration_str = duration_str.replace('PT', '')  # Remove the PT prefix
    hours, minutes, seconds = 0, 0, 0
    
    if 'H' in duration_str:
        hours, duration_str = duration_str.split('H')
        hours = int(hours)
    if 'M' in duration_str:
        minutes, duration_str = duration_str.split('M')
        minutes = int(minutes)
    if 'S' in duration_str:
        seconds = int(duration_str.replace('S', ''))
    
    total_minutes = hours * 60 + minutes
    return total_minutes, seconds

import datetime

# Collect Video information
def get_video_info(video_ids):
    video_details=[]
    for video_info in video_ids:
        request = youtube.videos().list(
            part='snippet,ContentDetails,statistics',
            id=video_info
        )
        response = request.execute()

        for item in response['items']:
            tags = item['snippet'].get('tags')
            tags_str = list_to_string(tags) if tags else None
            published_at = datetime.datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
            published_at_str = published_at.strftime("%Y-%m-%d %H:%M:%S")
            
            # Parse duration using the parse_duration function
            total_minutes, seconds = parse_duration(item['contentDetails']['duration'])
            #total_duration_minutes = total_minutes + seconds / 60  # Calculate total duration in minutes
         
            data = dict(channel_Id=item['snippet']['channelId'],
                        video_Id=item['id'],
                        title=item['snippet']['title'],
                        Tags= tags_str,
                        Description=item['snippet'].get('description'),
                        Published_Dates=published_at_str,
                        Duration_minutes=total_minutes,
                        Views=item['statistics'].get('viewCount'),
                        Likes=item['statistics'].get('likeCount'),
                        Dislikes=item['statistics'].get('dislikeCount'),
                        Comments=item['statistics'].get('commentCount'),
                        Favorite_Count=item['statistics']['favoriteCount'],
                        Definition=item['contentDetails']['definition'],
                        caption_status=item['contentDetails']['caption']
                        )
            video_details.append(data)
    return video_details

#get comment info

def get_comment_info(video_ids):
    com_info=[]
    try:
        for video_info in video_ids:
            request=youtube.commentThreads().list(
                part="snippet",
                videoId=video_info,
                maxResults=50
            )
            response=request.execute()

            for item in response['items']:
                data=dict(Comment_Id=item['snippet']['topLevelComment']['id'],
                        Video_Id=item['snippet']['topLevelComment']['snippet']['videoId'],
                        Comment_Text=item['snippet']['topLevelComment']['snippet']['textDisplay'],
                        Comment_Author=item['snippet']['topLevelComment']['snippet']['authorDisplayName'],
                        Comment_Published=datetime.datetime.strptime(item['snippet']['topLevelComment']['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ").strftime("%Y-%m-%d %H:%M:%S")
                        )
                
                com_info.append(data)
                    
    except:
        pass
    return com_info

#get_playlist_details
import datetime
def get_playlist_details(channel_id):
        next_page_token=None
        play_info=[]
        while True:
                request=youtube.playlists().list(
                        part='snippet,contentDetails',
                        channelId=channel_id,
                        maxResults=50,
                        pageToken=next_page_token
                )
                response=request.execute()

                for item in response['items']:
                        published_at = datetime.datetime.strptime(item['snippet']['publishedAt'], "%Y-%m-%dT%H:%M:%SZ")
                        publishedAt = published_at.strftime("%Y-%m-%d %H:%M:%S")
                        data=dict(Playlist_Id=item['id'],
                                Title=item['snippet']['title'],
                                Channel_Id=item['snippet']['channelId'],
                                Channel_Name=item['snippet']['channelTitle'],
                                #PublishedAt=item['snippet']['publishedAt'],
                                publishedAt = published_at.strftime("%Y-%m-%d %H:%M:%S"),
                                Video_Count=item['contentDetails']['itemCount'])
                        play_info.append(data)

                next_page_token=response.get('nextPageToken')
                if next_page_token is None:
                        break
        return play_info

# SQL connection

def connect_to_mysql():
    my_conn = pymysql.connect(host='localhost', user='root', password='admin123456', port=3306)
    mycursor = my_conn.cursor()
    database='youtube_sk'

    mycursor.execute(f"create database if not exists {database}")
    print (f"Database '{database}" "created successfully")

    #using database:
    mycursor.execute(f"use {database};")
    my_conn.commit()
    return

# Function to create table schemas
def create_tables():
    with connect_to_mysql() as my_conn:
        mycursor = my_conn.cursor()
        create_channel_table = """
        CREATE TABLE IF NOT EXISTS channels (
        channel_Name VARCHAR(255),
        channel_Id VARCHAR(80),
        Subscribers INT,
        Views INT,
        Total_Videos INT,
        channel_Description TEXT,
        Playlist_Id VARCHAR(80)
        )
        """
        create_playlist_table = """
        CREATE TABLE IF NOT EXISTS playlists (
        Playlist_Id VARCHAR(100),
        Title VARCHAR(255),
        Channel_Id VARCHAR(80),
        Channel_Name VARCHAR(255),
        PublishedAt DATETIME,
        Video_Count INT
        )
        """
        create_video_table = """
        CREATE TABLE IF NOT EXISTS videos (
        channel_Id VARCHAR(80),
        video_Id VARCHAR(30),
        title VARCHAR(255),
        Tags TEXT,
        Description TEXT,
        Published_Dates DATETIME,
        Duration INT,
        Views BIGINT,
        Likes BIGINT,
        Dislikes BIGINT,
        Comments INT,
        Favorite_Count INT,
        Definition VARCHAR(100),
        caption_status VARCHAR(250)
        )
        """
        create_comment_table = """
        CREATE TABLE IF NOT EXISTS comments (
        Comment_Id VARCHAR(100),
        Video_Id VARCHAR(100),
        Comment_Text TEXT,
        Comment_Author VARCHAR(150),
        Comment_Published DATETIME
        )
        """
        mycursor.execute(create_channel_table)
        mycursor.execute(create_playlist_table)
        mycursor.execute(create_video_table)
        mycursor.execute(create_comment_table)
        my_conn.commit()

    # Function to fetch data from YouTube API
def fetch_data(channel_id):
    youtube = use_api()
    channel_info = get_channel_info(channel_id)
    playlist_info = get_playlist_details(channel_id)
    video_ids = get_video_ids(channel_id)
    video_info = get_video_info(video_ids)
    comment_info = get_comment_info(video_ids)
    return channel_info, playlist_info, video_info, comment_info

my_conn = pymysql.connect(host='localhost', user='root', password='admin123456', port=3306,database='youtube_sk')
mycursor = my_conn.cursor()

# Function to execute SQL query and fetch data from the selected table
def fetch_data(table_name):
    mycursor.execute(f"SELECT * FROM {table_name}")
    data = mycursor.fetchall()
    my_conn.commit()
    return data

# Function to display data in a table
def display_data(data):
    if data:
        df = pd.DataFrame(data)
        st.write(df)
    else:
        st.write("No data available")        

# Main Streamlit app
def main():
    st.title(':red[Youtube] :blue[Data Fetcher]')
    # User input for channel ID
    channel_id = st.text_input("Enter Channel ID:")
    if st.button("Fetch Data"):
        if channel_id:
            # Fetch data from YouTube API
            channel_info = get_channel_info(channel_id)
            playlist_info = get_playlist_details(channel_id)
            video_ids = get_video_ids(channel_id)
            video_info = get_video_info(video_ids)
            comment_info = get_comment_info(video_ids)

            # Check if the channel already exists in the channels table
            mycursor.execute("SELECT channel_id FROM channels WHERE channel_id = %s", (channel_id,))
            existing_channel = mycursor.fetchone()

            if not existing_channel:
                # Insert fetched data into MySQL tables
                for channel_data in channel_info:
                    mycursor.execute("INSERT INTO channels VALUES (%s, %s, %s, %s, %s, %s, %s)", tuple(channel_data.values()))

                for playlist_data in playlist_info:
                    mycursor.execute("INSERT INTO playlists VALUES (%s, %s, %s, %s, %s, %s)", tuple(playlist_data.values()))

                for video_data in video_info:
                    mycursor.execute("INSERT INTO videos VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                                    tuple(video_data.values()))

                for comment_data in comment_info:
                    mycursor.execute("INSERT INTO comments VALUES (%s, %s, %s, %s, %s)", tuple(comment_data.values()))

                my_conn.commit()
                st.success("Data fetched and saved successfully!")
        else:
            st.warning("Channel already exists in the database.") 
                
    # Dropdown to select table
    selected_table = st.selectbox("Select Table", ("channels", "playlists", "videos", "comments"))

    # Button to fetch data from the selected table
    if st.button("Fetch Table Data"):
        table_data = fetch_data(selected_table)
        display_data(table_data)

def sidebar():
    # Sidebar with input fields
    with st.sidebar:
        st.title(":blue[Skills and Tools]")
        st.write("Showcasing learning skills and tools used:")
        st.write("- Python with scripting")
        st.write("- MySQL")
        st.write("- API Integration")
        st.write("- Data Collection")
        st.write("- Streamlit")

if __name__ == "__main__":
    sidebar()    
    main()


question = st.selectbox("Select your question", ['FAQ - Question for future decision',
                                                "1. What are the names of all the videos and their corresponding channels",
                                                "2. Which channels have the most number of videos, and how many videos do they have",
                                                "3. What are the top 10 most viewed videos and their respective channels?",
                                                "4. How many comments were made on each video, and what are their corresponding video names?",
                                                "5. Which videos have the highest number of likes, and what are their corresponding channel names?",
                                                "6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?",
                                                "7. What is the total number of views for each channel, and what are their corresponding channel names?",
                                                "8. What are the names of all the channels that have published videos in the year 2022?",
                                                "9. What is the average duration of all videos in each channel, and what are their corresponding channel names?",
                                                "10. Which videos have the highest number of comments, and what are their corresponding channel names?"])
              
if question:
    if question.startswith("1. What are the names of all the videos and their corresponding channels"):
        data = fetch_data("videos")  # Fetch data for all videos and channels
        st.write(pd.DataFrame(data, columns=["channel_Id","video_Id","title","Tags","Description","Published_Dates","Duration","Views","Likes","Dislikes","Comments","Favorite_Count","Definition","caption_status"]))

    elif question.startswith("2. Which channels have the most number of videos, and how many videos do they have"):
        # Query to fetch channels with the most number of videos and their count
        mycursor.execute("""
        SELECT c.channel_Id, c.channel_Name, COUNT(v.video_Id) AS Total_Videos
        FROM channels c
        LEFT JOIN videos v ON c.channel_Id = v.channel_Id
        GROUP BY c.channel_Id, c.channel_Name 
        ORDER BY Total_Videos DESC;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["channel_Id", "channel_Name", "Total_Videos"]))

    elif question.startswith("3. What are the top 10 most viewed videos and their respective channels?"):
        # Query to fetch the top 10 most viewed videos and their respective channels
        mycursor.execute("""
        SELECT v.title AS Video_Title, c.channel_Name AS Channel_Name, v.views AS Views
        FROM videos v
        INNER JOIN channels c ON v.channel_Id = c.channel_Id
        ORDER BY v.views DESC
        LIMIT 10;
        """)
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=["Video Title", "Channel Name", "Views"])
        st.write(df)

    elif question.startswith("4. How many comments were made on each video, and what are their corresponding video names?"):
        # Query to fetch the total number of comments for each video and their corresponding titles
        mycursor.execute("""
        SELECT v.title AS Video_Title, COUNT(c.comment_id) AS Total_Comments
        FROM videos v
        LEFT JOIN comments c ON v.video_id = c.video_id
        GROUP BY v.video_id, v.title;
        """)
        data = mycursor.fetchall()
        df = pd.DataFrame(data, columns=["Video Title", "Total Comments"])
        st.write(df)

    elif question.startswith("5. Which videos have the highest number of likes, and what are their corresponding channel names?"):
        # Query to fetch videos with the highest number of likes and their corresponding channel names
        mycursor.execute("""
        SELECT v.title AS Video_Title, v.likes AS Likes, c.channel_Name AS Channel_Name
        FROM videos v
        INNER JOIN channels c ON v.channel_id = c.channel_id
        ORDER BY v.likes DESC
        LIMIT 150;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["Video Title", "Likes", "Channel Name"]))

    elif question.startswith("6. What is the total number of likes and dislikes for each video, and what are their corresponding video names?"):
        # Query to fetch total likes and dislikes for each video along with their names
        mycursor.execute("""
        SELECT v.title AS Video_Title, SUM(v.likes) AS Total_Likes, SUM(v.dislikes) AS Total_Dislikes
        FROM videos v
        GROUP BY v.title;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["Video Title", "Total Likes", "Total Dislikes"]))
                                
    elif question.startswith("7. What is the total number of views for each channel, and what are their corresponding channel names?"):
        # Query to fetch total views for each channel
        mycursor.execute("""
        SELECT c.channel_Name AS Channel_Name, SUM(v.views) AS Total_Views
        FROM videos v
        INNER JOIN channels c ON v.channel_id = c.channel_id
        GROUP BY c.channel_Name;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["Channel Name", "Total Views"]))

    elif question.startswith("8. What are the names of all the channels that have published videos in the year 2022?"):
        # Query to fetch channels that have published videos in 2022
        mycursor.execute("""
        SELECT DISTINCT c.channel_Name AS Channel_Name
        FROM channels c
        INNER JOIN videos v ON c.channel_id = v.channel_id
        WHERE YEAR(v.Published_Dates) = 2022;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["Channel Name"]))

    elif question.startswith("9. What is the average duration of all videos in each channel, and what are their corresponding channel names?"):
        # Query to fetch the average duration of all videos in each channel
        mycursor.execute("""
        SELECT c.channel_Name AS Channel_Name, AVG(v.duration) AS Average_Duration
        FROM videos v
        INNER JOIN channels c ON v.channel_id = c.channel_id
        GROUP BY c.channel_Name;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["Channel Name", "Average Duration"]))

    elif question.startswith("10. Which videos have the highest number of comments, and what are their corresponding channel names?"):
        # Query to fetch videos with the highest number of comments and their corresponding channel names
        mycursor.execute("""
        SELECT v.title AS Video_Title, comments.Num_Comments, c.channel_Name AS Channel_Name
        FROM videos v
        INNER JOIN channels c ON v.channel_id = c.channel_id
        INNER JOIN (
            SELECT video_id, COUNT(comment_id) AS Num_Comments
            FROM comments
            GROUP BY video_id
        ) AS comments ON v.video_id = comments.video_id
        ORDER BY comments.Num_Comments DESC
        LIMIT 150;
        """)
        data = mycursor.fetchall()
        st.write(pd.DataFrame(data, columns=["Video Title", "Number of Comments", "Channel Name"]))
