import os
# Change paht to ffmpeg if needed
# os.environ["IMAGEIO_FFMPEG_EXE"] = "/path_to/ffmpeg"


import requests
import time
from PIL import Image
import base64
import io
import imageio
import json
from mss import mss

url = "http://localhost:8080/completion"
headers = {"Content-Type": "application/json"}

print("Starting video stream... Wait for a few seconds for the stream to the output to start generating.")
# cap = imageio.get_reader('<video0>')

mon = {'left': 1100, 'top': 220, 'width': 640, 'height': 400}

with mss() as sct:
    while True:
        screenShot = sct.grab(mon)
        img = Image.frombytes(
            'RGB', 
            (screenShot.width, screenShot.height), 
            screenShot.rgb, 
        )
        # Save the image to a file
        img.save('temp.png')
        # Save the image to a file
        with open('temp.png', 'rb') as file:
            encoded_string = base64.b64encode(file.read()).decode('utf-8')

        image_data = [{"data": encoded_string, "id": 12}]

        data = {"prompt": "USER:[img-12]You are a game playing agent I want you to describe interesting things in the scene and your conclusions about the game.\nASSISTANT:", "n_predict": 128, "image_data": image_data, "stream": True}

        response = requests.post(url, headers=headers, json=data, stream=True)

        with open("output.txt", "a") as write_file:
            write_file.write("---"*10 + "\n\n")
        
        for chunk in response.iter_content(chunk_size=128):
            with open("output.txt", "a") as write_file:
                content = chunk.decode().strip().split('\n\n')[0]
                try:
                    content_split = content.split('data: ')
                    if len(content_split) > 1:
                        content_json = json.loads(content_split[1])
                        write_file.write(content_json["content"])
                        print(content_json["content"], end='', flush=True)
                    write_file.flush()  # Save the file after every chunk
                except json.JSONDecodeError:
                    print("JSONDecodeError: Expecting property name enclosed in double quotes")

cap.close()
