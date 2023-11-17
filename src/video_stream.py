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

print(
    "Starting video stream... Wait for a few seconds for the stream to the output to start generating."
)
# cap = imageio.get_reader('<video0>')


def zero_shot_prompt(previous=None):
    return f"""
You are a game playing agent I want you to describe interesting things in the environment and your conclusions about the game.
Focus more on what is explorable than details. Feel free to decide nothing in the scene is particularly interesting.
Remember game play information not artistic details.
We will have several sections for you to respond with. Some of these might be empty or unchanged if nothing interesting is happening.
For every observation we will you give the previous result and you can choose to keep the individual parts or not depending on their relevance.
PLEASE ENSURE YOU OUTPUT THE REQUESTED STRUCTURE

Please choose from the following actions to meet your goals:
Interact <entity>
Move <direction>
Move towards <object>
Select <Menu State>
Explore
Equip Object
Grind Area


Give me data in the following format:

Format:
<game>
Name of the game as best as you can tell
</game>
<observation>
A description of the scene and what you think is happening.
</observation>
<world_information>
[New high level information learned about the world in bullet points]
</world_information>
<objects_to_explore>
[Bulleted list of objects to examine in the world]
</objects_to_explore>
<goals>
[Bulleted list of goals based on observations]
</goals>
<action>
[Current action to meet your top goals]
</action>
<reward>
[Reward for past action -1 to 1]
</reward>


"USER:[img-6] Generate data for the image
Previous:
{previous}
ASSISTANT:
 """


def prompt(previous=None):
    return f"""
You are a game playing agent I want you to describe interesting things in the scene and your conclusions about the game.
We will have several sections for you to respond with. Some of these might be empty or unchanged if nothing interesting is happening.
For every observation we will you give the previous result and you can choose to keep the individual parts or not depending on their relevance.
Give me data in the following format:

Format:
<game>
Name of the game as best as you can tell
</game>
<observation>
A description of the scene and what you think is happening.
</observation>
<world_information>
[New high level information learned about the world in bullet points]
</world_information>
<objects_to_explore>
[Bulleted list of objects to examine in the world]
</objects_to_explore>
<goals>
[Bulleted list of goals based on observations]
</goals>

Included are a list of examples but remember that you are doing it based on the game in your observation.

USER:[img-2] Generate data for the image
Previous:
None

ASSISTANT:
<response>
<game>
Mario
</game>
<observation>
* Mario jumps onto a platform and then jumps onto a goomba. There appears to be more to explore to the right.
</observation>
<world_information>
* There are platforms that Mario can jump on.
* Mario can jump on enemies to kill them.
* Goombas are enemies.
* The game moves from left to right.
</world_information>
<objects_to_explore>
* The goomba
* The platform
* Whatever is to the right of the current scene
</objects_to_explore>
<goals>
* Kill enemies
* Move right
</goals>
</response>

"USER:[img-3] Generate data for the image
Previous:
<observation>
* Mario jumps onto a platform and then jumps onto a goomba. There appears to be more to explore to the right.
</observation>
<world_information>
* There are platforms that Mario can jump on.
* Mario can jump on enemies to kill them.
* Goombas are enemies.
* The game moves from left to right.
</world_information>
<objects_to_explore>
* The goomba
* The platform
* Whatever is to the right of the current scene
</objects_to_explore>
<goals>
* Kill enemies
* Move right
</goals>


ASSISTANT:
<response>
<game>
Mario
</game>
<observation>
* Mario now is by a piranha plant and a pipe.
</observation>
<world_information>
* There are platforms that Mario can jump on.
* Mario can jump on enemies to kill them.
* Goombas are enemies.
* The game moves from left to right.
* Piranha plants are enemies.
</world_information>
<objects_to_explore>
* Piranha plants
* Pipes
* Whatever is to the right of the current scene
</objects_to_explore>
<goals>
* Kill enemies and move right
</goals>
</response>

"USER:[img-4] Generate data for the image
Previous:
None

ASSISTANT:
<response>
<game>
Castlevania
</game>
<observation>
* Intro screen not much to go off of yet
</observation>
<world_information>
</world_information>
<objects_to_explore>
</objects_to_explore>
<goals>
</goals>
</response>


"USER:[img-6] Generate data for the image
Previous:
{previous}
ASSISTANT:
<response>
 """


mon = {"left": 1100, "top": 220, "width": 640, "height": 400}

fewshot_file_list = [
    "./fewshot/mario_goomba.png",
    "./fewshot/mario_piranha_plant.png",
    "./fewshot/castlevania_title.png",
]
# fewshot_file_list = ["./fewshot/mario_goomba.png", "./fewshot/zelda.png"]
fewshot_data = []
i = 1
for file in fewshot_file_list:
    i += 1
    with open(file, "rb") as file:
        encoded_string = base64.b64encode(file.read()).decode("utf-8")
        fewshot_data.append({"data": encoded_string, "id": i})

previous = None
with mss() as sct:
    while True:
        screenShot = sct.grab(mon)
        img = Image.frombytes(
            "RGB",
            (screenShot.width, screenShot.height),
            screenShot.rgb,
        )
        # Save the image to a file
        img.save("temp.png")
        # Save the image to a file

        with open("temp.png", "rb") as file:
            encoded_string = base64.b64encode(file.read()).decode("utf-8")

        image_data = [{"data": encoded_string, "id": 6}]

        # print("******PROMPT******")
        # print(f"{prompt(previous)}")
        # other_prompt = lambda x: "USER:[img-1]Describe the image.\nASSISTANT:"
        # data = {"prompt": prompt(previous), "n_predict": 10024, "image_data":  image_data, "stream": True}
        # full_image_data = fewshot_data + image_data
        full_image_data = image_data
        data = {
            "prompt": zero_shot_prompt(previous),
            "n_predict": 10024,
            "image_data": full_image_data,
            "stream": True,
        }

        response = requests.post(url, headers=headers, json=data, stream=True)

        with open("output.txt", "a") as write_file:
            write_file.write("---" * 10 + "\n\n")

        previous = ""
        print("******RESPONSE******")
        for chunk in response.iter_content(chunk_size=128):
            with open("output.txt", "a") as write_file:
                content = chunk.decode()
                print("CONTENT", content)
                content = content.strip().split("\n\n")[0]
                try:
                    # print(content)
                    content_split = content.split("data: ")
                    if len(content_split) > 1:
                        content_json = json.loads(content_split[1])
                        write_file.write(content_json["content"])
                        print(content_json["content"], end="", flush=True)
                        previous += content_json["content"]
                    write_file.flush()  # Save the file after every chunk
                except json.JSONDecodeError:
                    print(
                        "JSONDecodeError: Expecting property name enclosed in double quotes"
                    )

# cap.close()
