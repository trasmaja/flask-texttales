#!/usr/bin/env python
# encoding: utf-8
from flask import Flask, jsonify, request, send_file
app = Flask(__name__)

import os
# import gnews
import openai # added
from langchain.chat_models import ChatOpenAI
from dotenv import load_dotenv
# from datetime import datetime
# import requests
# import datetime
load_dotenv()
from pydrive.auth import GoogleAuth 
from pydrive.drive import GoogleDrive
from moviepy.editor import concatenate_audioclips, AudioFileClip
import uuid
# from elevenlabs import voices, generate, play, save

openai.api_key = os.getenv("OPENAI_API_KEY")
weather_api_key = os.getenv("WEATHER_API_KEY")
ELEVEN_API_KEY = os.getenv("ELEVEN_API_KEY")
# # Initialize chat model
chat_model = ChatOpenAI(model_name='gpt-3.5-turbo-16k')  # Make sure to set the API key as an environment variable


class Podcast:
    def __init__(self, user_prompt, num_minutes, category):
        self.ID = generate_name()
        self.user_prompt = user_prompt
        self.num_minutes = int(num_minutes)
        self.num_words = int(num_minutes) * 135
        self.category = category
        self.text_list = []
        self.sound_file_name = self.ID + ".wav"
        self.drive_name = ""

    def get_ID(self):
        return self.ID

    def get_drive_name(self):
        return self.drive_name
    
    def gen_story_podcast(self):
        
        if self.num_words < 1000:
            prompt = "Create a story about '{}'. The story should be approximately {} number of words".format(self.user_prompt, self.num_words)
            self.text_list = [chat_model.predict(prompt)]
            print("--------")
            print(self.text_list)
        else:
            chapters = int(self.num_words / 300)
            prompt = "Create a detailed outline for a story about '{}' with {} scenes. Return your answer in the following format:".format(self.user_prompt, str(chapters*3))
            for i in range(1, 3*chapters+1):
                prompt += "\nScene {}:".format(str(i))

            outline = chat_model.predict(prompt)
            scene_list = []
            for i in range(1, chapters*3+1):
                scene_before_index = outline.index("Scene {}".format(str(i)))
                if i < chapters*3:
                    scene_after_index = outline.index("Scene {}".format(str(i+1)))
                    scene = outline[scene_before_index:scene_after_index]
                else:
                    scene = outline[scene_before_index:]
                scene_list.append(scene)

            prompt = "Specify the characters and in what scene they enter the story based on this outline:\n{}\n\nReturn in the format:\nName of character - Description - Scene Number".format(outline)
            characters = chat_model.predict(prompt)
            extended_scenes = []

            for i in range(chapters):
                number_of_scenes = 3
                response_format = "Return in the format:\nPart {}:\nPart {}:\nPart {}:".format(str(i*3+1), str(i*3+2), str(i*3+3))
                scenes = scene_list[i*3] + "\n" + scene_list[i*3+1] + "\n" + scene_list[i*3+2]
                if i < chapters - 1:
                        scenes += "\n" + scene_list[i*3+3]
                        response_format += "\nPart {}:".format(str(i*3+4))
                        number_of_scenes = 4
                
                #prompt = "Turn these {} scenes into storytelling format, add details, return just the text:\n{}\n\nHere is a list of characters and in what scene they will or have been introduced:\n{}\n\n{}".format(str(number_of_scenes), scenes, characters, response_format)
                prompt = "Here are the story's characters and in what scenes they appear:\n{}\n\nRewrite the following scenes into a plain text story that can written in a book. Add unnecessary details so the story feels more alive:\n{}\n\n{}".format(characters, scenes, response_format)
                response = chat_model.predict(prompt)

                k = 0
                for j in range(i*3+1,i*3+number_of_scenes+1):
                    k += 1
                    scene_before_index = response.lower().index("part {}".format(str(j)))
                    if j < i*3+number_of_scenes:
                        scene_after_index = response.lower().index("part {}".format(str(j+1)))
                        scene = response[scene_before_index:scene_after_index]
                    else:
                        scene = response[scene_before_index:]
                    
                    if k < 4:
                        extended_scenes.append(scene)

            cleaned_text = []
            for row in extended_scenes:
                split_row = row.split("\n")[1:]  # Remove the first element
                restored_row = "\n".join(split_row)  # Join the remaining elements with newline
                restored_row = restored_row.strip("\n")
                cleaned_text.append(restored_row)

            self.text_list = cleaned_text
            print("--------")
            print(self.text_list)

    def audiofy_story(self, voice="Adam", sound_effect_name="fairytale"):

        if not os.path.exists("story_audio"):
            os.makedirs("story_audio")
        
        
        file_names = []
        # for i in range(len(self.text_list)):
        #     audio = generate(text=self.text_list[i], voice=voice, model="eleven_monolingual_v1", api_key=ELEVEN_API_KEY)
        #     save(audio, "./story_audio/story_{}_{}.wav".format(self.ID, str(i)))

        #     file_names.append("./story_audio/story_{}_{}.wav".format(self.ID, str(i)))
        #     file_names.append("./sound_effects/{}.wav".format(sound_effect_name))
        

        # file_names = ["./sound_effects/fairytale.wav","./sound_effects/fairytale.wav"]
        file_names = ["./sound_effects/original_transition.wav","./sound_effects/original_transition.wav"]
        concatenate_audio_moviepy(file_names, "./story_audio/{}".format(self.sound_file_name))

    def upload_wav_file_and_get_ID(self):
        print(777777)
        gauth = GoogleAuth()

        # Try to load saved client credentials
        gauth.LoadCredentialsFile("mycreds.txt")

        if gauth.credentials is None:
            # Authenticate if they're not there
            gauth.GetFlow()
            gauth.flow.params.update({'access_type': 'offline'})
            gauth.flow.params.update({'approval_prompt': 'force'})
            gauth.LocalWebserverAuth()
        elif gauth.access_token_expired:
            # Refresh them if expired
            gauth.Refresh()
        else:
            # Initialize the saved creds
            gauth.Authorize()

        # Save the current credentials to a file
        gauth.SaveCredentialsFile("mycreds.txt")  

        drive = GoogleDrive(gauth)

        title = generate_name() + ".txt"
        team_drive_id = '1WdeZhQ_vegXPMA-JeoM0pldAOKbCCVcx'
        parent_folder_id = '1TtWk3uo0jTC0BR2CAlaH8DgcRtp0hDCb'
        f = drive.CreateFile({
            'title': title,
            'parents': [{
                'kind': 'drive#fileLink',
                'teamDriveId': team_drive_id,
                'id': parent_folder_id
            }]
        })
        f.SetContentFile("./story_audio/" + self.sound_file_name)
        f.Upload(param={'supportsTeamDrives': True})

        files = drive.ListFile({"q": "'" + parent_folder_id + "' in parents and mimeType!='application/vnd.google-apps.folder'"}).GetList()

        name = ""
        for file in files:
            if file['title'] == title:
                name = file['id']

        self.drive_name = name
    
    def list_to_text(self):
        text = ""
        for row in self.text_list:
            text += row + "\n"
        return text


def generate_name():
    # Generate a unique ID
    unique_id = str(uuid.uuid4())
    return unique_id

def concatenate_audio_moviepy(audio_clip_paths, output_path):
        """Concatenates several audio files into one audio file using MoviePy
        and save it to `output_path`. Note that extension (mp3, etc.) must be added to `output_path`"""
        clips = [AudioFileClip(c) for c in audio_clip_paths]
        final_clip = concatenate_audioclips(clips)
        final_clip.write_audiofile(output_path)


@app.route('/')
def home():
    return 'Hello, World adam!'

@app.route('/about')
def about():
    return 'adam test'


@app.route('/create')
def get_create():
    print(00000)
    
    # Argument fetched from url params
    user_prompt = request.args.get('topic') # User input can be any string
    num_minutes = request.args.get('min') # Time [0-5, 5-10, 10-15]
    podcast_type = request.args.get("style") # style ["NEWS", "STORY"]
    # num_words = int(num_minutes)*135

    # Pausar detta för tillfället
    # prompt = "Can you create a documentary/news broadcast/podcast/fantasy story about this input? Respond only by returning 'YES' or explain why it does not work. Input = {}".format(user_prompt)
    # response = chat_model.predict(prompt)
    # if "YES" != response:
    #     return print(response)

    new_podcast = Podcast(user_prompt, num_minutes, podcast_type)
    
    if podcast_type == "NEWS":
        # Todo fix
        print("IN NEWS")
        podcast_name = temp_gen()
        data = {'text': "TODO", 'name': podcast_name}
        return jsonify(data)
    elif podcast_type == "STORY":
        new_podcast.gen_story_podcast()
        new_podcast.audiofy_story()
        new_podcast.upload_wav_file_and_get_ID()


    data = {'text': new_podcast.list_to_text(), 'name': new_podcast.get_drive_name()}
    
    return jsonify(data)