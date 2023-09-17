from flask import Flask, render_template, request, session, redirect, url_for
from flask_socketio import join_room, leave_room, send, SocketIO
import random
from string import ascii_uppercase

import torch
from PIL import Image
from io import BytesIO
import base64
import numpy as np

from sentiment import SentimentClassifier
#from voice import SpeakText
from voice import speak
from listen import Listener
from q_a import QuestionAnswering
from text_corr import TextCorrelate
from replace_with import replace_with
from pdf import data2pdf
from image import Damage_detection
from image import Clip
import time
from gpt_covered import ChatGPTWrapper

from parameters import Parameters

import threading

def read_text(text):
    # Start the function in a new thread
    t = threading.Thread(target=speak, args=(text,))
    t.start()


#from image import Damage_detection

app = Flask(__name__)
app.config["SECRET_KEY"] = "af34hbesrjh2435b23uoi"
socketio = SocketIO(app)

rooms = {}

def generate_unique_code(length):
    while True:
        code = ""
        for _ in range(length):
            code += random.choice(ascii_uppercase)
        
        if code not in rooms:
            break
    
    return code

@app.route("/", methods=["POST", "GET"])
def home():
    session.clear()
    if request.method == "POST":
        name = request.form.get("name")
        id = request.form.get("id")
        parameters.name = name
        parameters.id = id
        login = request.form.get("login", False)

        if not name:
            return render_template("home.html", error="Please enter a name.", code=code, name=name)
        
        room = id
        rooms[room] = {"members": 0, "messages": []}
        session["room"] = room
        session["name"] = name
        return redirect(url_for("room"))

    return render_template("home.html")

@app.route("/room")
def room():
    room = session.get("room")
    name = session.get("name")
    if room is None or session.get("name") is None or room not in rooms:
        return redirect(url_for("home"))

    return render_template("room.html", name=name, room=room, messages=rooms[room]["messages"])


# New SocketIO event for image transfer
@socketio.on('send_image')
def handle_image(data):
    room = session.get("room")
    if room not in rooms:
        return 
    
    image_data = data['image_data']  # Base64 encoded image data
    print('im here 2')
    send({'type': 'image', 'message': image_data,"name": session.get("name")}, room=room)
    # DUMMY FOR IMAGES
    image, text = get_answer(image_data,"image")
    content = {
        'type': 'image',
        "name":  'Admin',
        'message': image}
    rooms[room]["messages"].append(content)
    send(content, to=room)
    
    content = {
        'type': 'text',
        "name":  'Admin',
        'message': text}
    rooms[room]["messages"].append(content)
    read_text(text)
    send(content, to=room)


# Update the existing send method to handle both text and image messages
@socketio.on('message')
def handle_message(msg):
    room = session.get("room")
    
    if room not in rooms:
        return
    
    if 'image_data'  in msg.keys() :  # If it's an image
        send({'type': 'image', 'message': msg['image_data'],"name": session.get("name")}, room=room)
    else:  # If it's text
        content = {'type': 'text', 'message': msg['data'],"name": session.get("name")}
        send(content, room=room)
        rooms[room]["messages"].append(content)
        # dummy for text
        content = {
            'type': 'text',
            "name":  'Admin',
            'message': get_answer(content['message'],content['type'])}
        rooms[room]["messages"].append(content)
        read_text(content["message"])
        #speaker.speak(content["message"])
        send(content, to=room)


@socketio.on('start_recording')
def handle_start_recording():
    text = listener.listen()
    handle_message({"data": text})
    '''room = session.get("room")
    content = {'type': 'text', 'message': text, "name": session.get("name")}
    send(content, room=room)
    rooms[room]["messages"].append(content)'''
    print('start recording')

@socketio.on('stop_recording')
def handle_stop_recording():
    print('stop recording')

@socketio.on("connect")
def connect(auth):
    room = session.get("room")
    name = session.get("name")
    if not room or not name:
        return
    if room not in rooms:
        leave_room(room)
        return
    
    join_room(room)
    send({"name": name, "message": "has entered the room"}, to=room)
    content = {
        'type': 'text',
        "name":  'Admin',
        'message': 'Good morning Sir, how can I help you?'}
    rooms[room]["messages"].append(content)
    read_text(content["message"])
    #speaker.speak(content["message"])
    
    send(content, to=room)
    rooms[room]["members"] += 1
    print(f"{name} joined room {room}")

@socketio.on("disconnect")
def disconnect():
    room = session.get("room")
    name = session.get("name")
    leave_room(room)

    if room in rooms:
        rooms[room]["members"] -= 1
        if rooms[room]["members"] <= 0:
            del rooms[room]
    
    send({"name": name, "message": "has left the room"}, to=room)
    print(f"{name} has left the room {room}")

def base64_to_pil(image_base64):
    image_data = base64.b64decode(image_base64.split(',')[1])  # You may not need to split by ',' depending on your data
    image = Image.open(BytesIO(image_data))
    return image


def np_to_base64(img_np, format='JPEG'):
    # Convert NumPy array to PIL Image
    img_pil = Image.fromarray((img_np).astype(np.uint8))
    # Resize the image
    new_dim = (img_np.shape[1]*2, img_np.shape[0]*2)
    resized_image_pil = img_pil.resize(new_dim, Image.ANTIALIAS)
    # Create a Bytes buffer
    buffer = BytesIO()
    # Save the PIL Image to the Bytes buffer
    resized_image_pil.save(buffer, format=format)
    # Convert to Base64
    img_base64 = base64.b64encode(buffer.getvalue()).decode()
    
    return 'data:image/jpeg;base64,' + img_base64


def get_answer(data, type):
    if type == "image":
        image = base64_to_pil(data)
        parameters.image_before = image
        parameters.image_after = Image.fromarray(seg_image)
        seg_image = damage_model.segment_damage(image)

        probs_dict = clip_model.get_probabilities_from_image(image)
        labels_probs = [(label, prob) for label, prob in probs_dict.items()]
        max_label_prob = max(labels_probs, key=lambda x:x[1])
        max_label = max_label_prob[0]
        if max_label == "high damage and wrecked":
            max_label = "high damage"
        parameters.damage = max_label

        returned_message = f"This is the segmentation of the damage I detected. I see that the car has {max_label}. "
        if len(parameters.unanswered_questions)>0:
            returned_message += "\n\nI just have a few more questions.\n\n"
            returned_message += parameters.unanswered_questions[parameters.unanswered_ind]
        else:
            returned_message += "\n\nThank you for your answers. Based on the information you provided, your policy covers the damage. You will be notified with the details."
            data2pdf(parameters.q2a, question2category, categories, parameters.name, parameters.id, parameters.image_before, parameters.image_after, parameters.damage)
        return np_to_base64(seg_image), returned_message
    elif type == 'text':
        ## In the end, call gpt_model.is_he_coverd() with the data and policies (we did that in advance)!
        if parameters.stage==1:
            best_query = text_correlate.correlate(data, queries)
            returned_message = f"I understand you've been through a {best_query}, and I'm here to help. First, let's ensure you're safe. Are you okay? Your safety is our top priority."
            parameters.stage += 1
        
        elif parameters.stage==2:
            is_ok = question_answering.ask("Am I okay?", data)[0]
            is_ok = sentiment_classifier.classify(is_ok)

            if is_ok:
                returned_message = "I'm glad to hear that you're safe. We're here to guide you through the process. Can you please tell me what happened?"
            else:
                returned_message = "I'm really sorry to hear that. Your health is the most important thing right now. Please call 911 or seek medical help right away. Once you've done that or if you've already received medical attention, please let me know, and we can start the claims process."
            parameters.stage += 1
        
        elif parameters.stage==3:
            transformed_questions = [replace_with(question, [["you", "I"], ["your", "my"]]) for question in questions]
            answers = question_answering.ask(transformed_questions, data)

            for question, answer in zip(questions, answers):
                if answer is None:
                    parameters.unanswered_questions.append(question)
                else:
                    final_answer = replace_with(answer, replaces)
                    parameters.q2a[question] = final_answer
            
            returned_message = "Great, thank you for the information. Can you please send an image of the damage?"
            parameters.stage += 1
        
        elif parameters.stage==4:
            parameters.q2a[parameters.unanswered_questions[parameters.unanswered_ind]] = data
            parameters.unanswered_ind += 1
            if parameters.unanswered_ind>=len(parameters.unanswered_questions):
                parameters.stage += 1
                returned_message = "Thank you for your answers. Based on the information you provided, your policy covers the damage. You will be notified with the details."
                data2pdf(parameters.q2a, question2category, categories, parameters.name, parameters.id, parameters.image_before, parameters.image_after, parameters.damage)
                '''for question, answer in parameters.q2a.items():
                    print(f"Q: {question}")
                    print(f"A: {answer}")
                    print("")'''
            else:
                returned_message = parameters.unanswered_questions[parameters.unanswered_ind]
            
        return returned_message

if __name__ == "__main__":

    ##############################################

    question2category = {
        "When did the accident occur?": "The Incident",
        "where did the accident occur?": "The Incident", 

        "Were you injured in the accident?": "Injuries", 
        "Were there any passengers in your vehicle at the time of the accident?": "Injuries", 
        "Were any passengers injured in the accident?": "Injuries", 
        
        "Was the accident caused by you or the other party?": "Accident Details", 
        "Who was driving the vehicle at the time of the accident?": "Accident Details", 
        "Were you abiding by all traffic laws and speed limits?": "Accident Details"
    }
    categories = ["The Incident", "Injuries", "Accident Details"]
    
    questions = question2category.keys()

    queries = ["car accident", "motorcycle accident", "traveling accident"]

    score_threshold = 0.1 # above it, consider answered the question

    male_voice = False # woman

    replaces = [] #[["i", "he"], ["my", "his"], ["me", "him"]]

    gpt_api_key = "###################" # insert here the api key

    ##############################################

    question_answering = QuestionAnswering(score_threshold)

    text_correlate = TextCorrelate()

    sentiment_classifier = SentimentClassifier()

    #speaker = SpeakText(male_voice)

    listener = Listener()

    parameters = Parameters()

    device = torch.device("cuda") if torch.cuda.is_available() else torch.device("cpu")
    print('device: ', device)

    seg_model_path = 'models/Car_damage_detection.pth'
    damage_model = Damage_detection(seg_model_path, device)

    gpt_model = ChatGPTWrapper(gpt_api_key)

    clip_model = Clip()

    socketio.run(app, debug=True)
    # send first message 