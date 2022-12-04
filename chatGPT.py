import requests
import json
import uuid
import moviepy.editor as mp
import boto3

class Chatbot:
    config: json
    conversation_id: str
    parent_id: str

    def __init__(self, config, conversation_id=None):
        self.config = config
        self.conversation_id = conversation_id
        self.parent_id = self.generate_uuid()

    def generate_uuid(self):
        uid = str(uuid.uuid4())
        return uid

    def get_chat_response(self, prompt):
        Authorization = self.config["Authorization"]
        headers = {
            "Accept": "application/json",
            "Authorization": "Bearer " + Authorization,
            "Content-Type": "application/json"
        }
        data = {
            "action": "next",
            "messages": [
                {"id": str(self.generate_uuid()),
                 "role": "user",
                 "content": {"content_type": "text", "parts": [prompt]}
                 }],
            "conversation_id": self.conversation_id,
            "parent_message_id": self.parent_id,
            "model": "text-davinci-002-render"
        }
        response = requests.post(
            "https://chat.openai.com/backend-api/conversation", headers=headers, data=json.dumps(data))
        try:
            response = response.text.splitlines()[-4]
        except:
            print(response.text)
            return ValueError("Error: Response is not a text/event-stream")
        try:
            response = response[6:]
        except:
            print(response.text)
            return ValueError("Response is not in the correct format")
        response = json.loads(response)
        self.parent_id = response["message"]["id"]
        self.conversation_id = response["conversation_id"]
        message = response["message"]["content"]["parts"][0]
        return {'message': message}


def ttsToMp3(text):
    # aws polly use arthur voice from english british
    polly = boto3.client('polly', region_name='us-east-1')
    response = polly.synthesize_speech(VoiceId='Arthur', OutputFormat='mp3', Text=text, Engine='neural')
    file = open('data/audio.mp3', 'wb')
    file.write(response['AudioStream'].read())
    file.close()
    return 'data/audio.mp3'

def createVideo(text, mp3):
    video = mp.VideoFileClip('data/video.mp4', audio=False)
    w, h = video.size
    text = mp.TextClip(text, font='Amiri-regular', color='white', fontsize=40, stroke_color='grey', stroke_width=1, kerning=0, interline=1, size=(w, h), method='caption')
    text = text.set_pos('center').set_duration(video.duration)
    video = mp.CompositeVideoClip([video, text])
    audio = mp.AudioFileClip(mp3)
    video = video.set_audio(audio)
    video.write_videofile('data/final.mp4', fps=24, codec='libx264', audio_codec='aac')
    # if video is not None:
    #     uploadVideoToTikTok(video)

def uploadVideoToTikTok(video):
    video = mp.VideoFileClip(video, audio=True)
    video.write_videofile('data/final.mp4', codec='libx264', audio_codec='aac')
    video = open('data/video.mp4', 'rb')
    files = {'video': video}
    data = {
        'open_id': 'open_id',
        'access_token': 'access_token',
    }
    response = requests.post('https://open-api.tiktok.com/share/video/upload/', files=files, data=data)
    print(response.text)


if __name__ == "__main__":
    print("Type '!exit' to exit")
    with open("config.json", "r") as f:
        config = json.load(f)
    chatbot = Chatbot(config)
    keep: str = ''
    while True:
        prompt = input("You: ")
        if prompt == "!exit":
            break
        if prompt == "!accept":
            ttsFile = ttsToMp3(keep)
            createVideo(keep, ttsFile)
            break
        try:
            response = chatbot.get_chat_response(prompt)
            if prompt != "!accept":
                keep = response['message']
        except Exception as e:
            print("Something went wrong!")
            print(e)
            continue
        print("\n")
        print("Chatbot:", response['message'])
        print("\n")