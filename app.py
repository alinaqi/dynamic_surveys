#dynamic survey proof of concept 
#generate questions on the fly based on user input 
#this is just a poc

import os
import string
import requests

import openai
from flask import Flask, redirect, render_template, request, url_for, session
import random
from flask_sqlalchemy import SQLAlchemy
from flask_session import Session
from datetime import timedelta
import time

random.seed(time.clock())

app = Flask(__name__)

app.config['SECRET_KEY'] = 'Pz3X0FPfX09q0F5X9q5b0HDxX9q5VU2WYzOI'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///db.sqlite3'
app.config['SESSION_TYPE'] = 'sqlalchemy'
app.secret_key = "fX9q5b0Hz3Pz3X0FPfX9q5b0U2WYzDxVOIDxVVU2WYz"

db = SQLAlchemy(app)
app.config['SESSION_SQLALCHEMY'] = db
sess = Session(app)


DIR_DATA_FOLDER = "user_data" + os.path.sep
DIR_PATH_SUMMARY = os.path.sep + "summary.txt"
DIR_PATH_CONVERSATION = os.path.sep + "conversation.txt"
DIR_PATH_CONVERSATION_SUMMARY = os.path.sep + "conversation_summary.txt"
DIR_PATH_SURVEY = os.path.sep + "survey.txt"

COUNTER = 0




TOUCHPOINT_OPTIONS = [
    "Left website without purchasing",
    "has Completed transaction",
    "is Dissatisfied customer",
    "is Satisfied customer",
    "has Placed a new order (renewal)",
    "has Requested a claim (insurance)"
]

default_api_key = 'default api key here'
openai.api_key = default_api_key

api_keys = ["list of keys here"]

query_default_alpha = """Suggest technical support for {}(Company) providing {}S related to these keywords({}) .

Human: I recieved the damaged package. what should I do now?
AI: I apologize for the inconvenience. Please provide me with your order number, so I can look into this issue. We may be able to replace the shirt or offer a refund as a result of our quality assurance policy. Please let me know if there is any other way I can be of assistance in this matter.
Human: order no is this
AI: I apologize for the inconvenience and escalated the issue to the customer service team, they will be in contact with you soon. 
AI: Is there anything else we can do to make sure you are satisfied with your experience?"""
query_default_beta = """Suggest technical support for #@ store related to these #@
Human: I recieved the damaged package. what should I do now?\nAI: I apologize for the inconvenience. Please provide me with your order number, so I can look into this issue. We may be able to replace the shirt or offer a refund as a result of our quality assurance policy. Please let me know if there is any other way I can be of assistance in this matter.\nHuman: order no is this\nAI: I apologize for the inconvenience and escalated the issue to the customer service team, they will be in contact with you soon. \nAI: Is there anything else we can do to make sure you are satisfied with your experience?"""


def current_milli_time():
    return round(time.time() * 1000)
    

def setup_db(app):
    db.app = app
    db.init_app(app)
    with app.app_context():
        db.create_all()



def id_generator(size=6, chars=string.ascii_uppercase + string.digits + string.ascii_lowercase):
    return ''.join(random.choice(chars) for _ in range(size))

def create_directories():
    Username = session.get("Username")

    if not os.path.isdir(DIR_DATA_FOLDER +Username):
        os.makedirs(DIR_DATA_FOLDER +Username)
        open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, "w")
        open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION_SUMMARY, "w")
        open(DIR_DATA_FOLDER + Username + DIR_PATH_SUMMARY, "w")
        open(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY, "w")



def get_api_key():
    k = random.randrange(len(api_keys))

    return api_keys[k]


def initiate_prompt(company='AXA', keywords='shirts'):
    global query_default_alpha
    query_default_alpha = query_default_alpha.replace('#1', company)
    query_default_alpha = query_default_alpha.replace('#2', keywords)
    return query_default_alpha


def generate_summary(conversation):
    response = openai.Completion.create(
        model="text-davinci-003",
        prompt="""Write summary of following conversation: \n{}""".format(conversation),
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    return response.choices[0].text


def toggled_status():
    current_status = request.args.get('status')
    session['toggle'] = current_status
   
    return 'PRODUCT' if current_status == 'SERVICE' else 'SERVICE'


@app.route('/setsession')
def setsession():
    session.permanent = True
    app.permanent_session_lifetime = timedelta(minutes=30)
    session.modified = True
    
    mtime = current_milli_time()
    global COUNTER
    Username = id_generator(size=3) + str(COUNTER) + str(mtime) + id_generator(size=3)
    COUNTER = COUNTER + 1
    session['Username'] = Username
    session['is_key_generated'] = False
    session['api_key'] = get_api_key()
    session['toggle'] = "PRODUCT"
    session["survey_questions"] = []
    session["question_no"] = 1
    session["generate_survey_toggle"] = False
    session["answers_list"] = []
    session['survey_answers'] = []
    session["context"] = ''
    session['touchpoint'] = ''
    session['companyname'] = ''
    session['keywords'] = ''
    session['query'] = ''
    session['feedback_toggle'] = 0
    session['current_milli_time'] = mtime

    return f"The session has been Set: " + session.get("Username") + " - \n milli_time 1: " + str(session.get("current_milli_time")) + " - \n milli_time 2: " + str(mtime)


@app.route('/popsession')	
def popsession():	
    mUser = session.get("Username")	
    clear_session()	
    return "Session Deleted: " + mUser	
    
    
def clear_session():	
    mUser = session.get("Username")	
	
    session.pop('Username', None)	
    session.pop('is_key_generated', None)
    session.pop('api_key', None)	
    session.pop('toggle', None)
    session.pop('survey_questions', None)
    session.pop('question_no', None)	
    session.pop('generate_survey_toggle', None)
    session.pop('answers_list', None)	
    session.pop('survey_answers', None)
    session.pop('context', None)	
    session.pop('touchpoint', None)
    session.pop('companyname', None)	
    session.pop('keywords', None)
    session.pop('query', None)	
    session.pop('feedback_toggle', None)
	
	
    
    return "Session Deleted"


@app.route('/touchpoint_select')
def touchpoint_select():

    create_directories()

    session['touchpoint'] = request.args.get('status')
    session['companyname'] = request.args.get('companyname')
    session['keywords'] = request.args.get('keywords')

    touchpoint = session.get('touchpoint')
    companyname = session.get('companyname')
    keywordsname = session.get('keywords')

    usecase = TOUCHPOINT_OPTIONS[int(touchpoint) - 1]

    if session['is_key_generated'] == False:
        openai.api_key = session.get('api_key')
        session['is_key_generated'] = True
    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt="""Ask for feedback as a bot for a user of {} for {}. 
            Specific use case is that customer {}.""".format(companyname, keywordsname, usecase),
            temperature=0.9,
            max_tokens=150,
            top_p=1,
            presence_penalty=0.6,
            stop=[" Human:", " AI:"]
        )
    except:
        return ["Something went wrong. Please try again later.", [], 500]
    toggle_val = session.get('toggle')

    session['feedback_toggle'] = 1

    list_prompt = [
        f"What five specific feedback questions should be shown to the customer in number list format as chatbot helper? Specific use case is that customer {usecase} {toggle_val.lower()}: {keywordsname}.",
        f"What five specific queries should be shown to the customer in number list format as chatbot helper? Specific use case is that customer {usecase} with {companyname} for {toggle_val.lower()}: {keywordsname}.",
        f"What five specific queries should be shown to the customer in number list format as chatbot helper? Specific use case is that customer is not satisfied with his/her experience from {companyname} for {toggle_val.lower()}: {keywordsname}.",
        f"What five specific queries should be shown to the customer in number list format as chatbot helper? Specific use case is that customer is satisfied with his/her experience from {companyname} for {toggle_val.lower()}: {keywordsname}.",
        f"What five specific queries should be shown to the customer in number list format as chatbot helper? Specific use case is that customer has placed a new order for {companyname} for {toggle_val.lower()}: {keywordsname}."
    ]
    
    select_prompt = ''
    if int(touchpoint)==1:
        select_prompt = list_prompt[0]
    elif int(touchpoint)==2:
        select_prompt = list_prompt[1]
    elif int(touchpoint)==3:
        select_prompt = list_prompt[2]
    elif int(touchpoint)==4:
        select_prompt = list_prompt[3]
    elif int(touchpoint)==5:
        select_prompt = list_prompt[4]
    else:
        select_prompt = list_prompt[1]
    response2 = openai.Completion.create(
        model="text-davinci-003",
        prompt="""What 5 specific feedback questions should be shown to the user in number list format as chatbot helper? Specific use case is that customer {} while purchasing {}.""".format(
            usecase, keywordsname),
        temperature=0.9,
        max_tokens=150,
        top_p=1,
        presence_penalty=0.6,
        stop=[" Human:", " AI:"]
    )
    session["context"] = {"response1": response.choices[0].text, "response2": response2.choices[0].text}

    add_conversation(f'{companyname} Customer Experience Team: \n"Please choose from the following:\n'+ response2.choices[
                         0].text.strip())
    return {"response1": response.choices[0].text,
            "response2": "Please choose from the following: " + response2.choices[0].text}


@app.route("/")
def home():
    Username = session.get("Username")
    if Username != None:
        if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION):
            open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'w').close()
    return render_template("index.html")


@app.route('/get_toggled_status')
def change_status():
    toggled_status()
    return session.get("toggle")


@app.route('/refresh')
def refresh():
    Username = session.get("Username")
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_SUMMARY):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_SUMMARY, 'w').close()
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'w').close()
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION_SUMMARY):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION_SUMMARY, 'w').close()
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY, 'w').close()

    clear_session()
    return render_template("index.html")

def reload_conversation():
    Username = session.get("Username")
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_SUMMARY):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_SUMMARY, 'w').close()
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'w').close()
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION_SUMMARY):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION_SUMMARY, 'w').close()
    if os.path.exists(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY):
        open(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY, 'w').close()
    session['survey_questions'] = []
    session['answers_list'] = []
    session["question_no"] = 1    

    return render_template("index.html")



@app.route("/get", methods=["POST"])
def chatbot_response():

    create_directories()

    session['query'] = request.form["messageText"]
    session['companyname'] = request.form['companyname']
    session['keywords'] =  request.form['keywords']

    query = session.get('query')
    companyname = session.get('companyname')
    keywordsname = session.get('keywords')

    if session['is_key_generated'] == False:
        openai.api_key = session.get('api_key')
        global query_default_beta
        query_default_beta = generate_prompt(query, company=companyname, keywords=keywordsname)
        session['is_key_generated'] = True

    survey_questions_list = session['survey_questions']

    question_no = session.get("question_no")
    generate_survey_toggle = session.get("generate_survey_toggle")
    answers_list = session['answers_list']
    survey_answers_list = session['survey_answers']
    survey_questions_list = session['survey_questions']

    if (generate_survey_toggle == True and question_no < len(survey_questions_list)):

        question_no += 1
        session['question_no']  = question_no
        answers_list.append(query)
        session['answers_list'] = answers_list
        return [survey_questions_list[question_no - 1], survey_answers_list[question_no - 1]]
    elif (generate_survey_toggle == True and question_no >= len(survey_questions_list)):
        answers_list.append(query)
        session['answers_list'] = answers_list

        generate_survey_toggle = False
        session['generate_survey_toggle'] = False
        Username = session.get("Username")
        f = open(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY, "w")

        for i in range(len(survey_questions_list)):
            if i <= len(answers_list):
                f.write("Question: " + survey_questions_list[i] + '\n\n')
                f.write('Answer: ' + answers_list[i] + '\n\n')
        f.close()


        with open(DIR_DATA_FOLDER + Username + DIR_PATH_SURVEY, 'r') as f, open(DIR_DATA_FOLDER + Username + DIR_PATH_SUMMARY, 'w') as f1:

            file_content = f.read()

            summary_prompt = "Generate the summary of this survey:\n\n"

            summary_prompt = summary_prompt + file_content
            try:
                response2 = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=summary_prompt,
                    temperature=0.9,
                    max_tokens=150,
                    top_p=1,
                    presence_penalty=0.6,

                )
            except:
                return ["Something went wrong. Please try again later.", [], 500]
            f1.write(response2.choices[0].text)

        return '\t**Survey Completed**\n\n' + response2.choices[0].text.strip()


    if ( session['feedback_toggle'] > 2):

        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f'Act as a {companyname} Customer Experience Team bot. End the conversation in PROFESSIONAL MANNER since you have all information needed',
                temperature=0.9,
                max_tokens=150,
                top_p=1,
                presence_penalty=0.6,

            )
        except:
            return ["Something went wrong. Please try again later.", [], 500]


        Username = session.get("Username")
        with open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'r')as f, open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION_SUMMARY, 'w')as f1:
            conversation_temp = f.read()
            summary_prompt = "summarize the responses to all questions, as follows, and suggest action to be taken:\n\n"

            summary_prompt = summary_prompt + conversation_temp
            try:
                response2 = openai.Completion.create(
                    model="text-davinci-003",
                    prompt=summary_prompt,
                    temperature=0.9,
                    max_tokens=150,
                    top_p=1,
                    presence_penalty=0.6,

                )
            except:
                return ["Something went wrong. Please try again later.", [], 500]
            f1.write(response2.choices[0].text.split('\n')[-1])

        return response.choices[0].text.strip() + '\n\n' + '**Conversation Ended**\n\n' + \
               response2.choices[0].text.split('\n')[-1].strip()

    if(session['feedback_toggle']==1):
        Username = session.get("Username")
        with open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'r') as f:
            context_file = f.read()
            choices_given = context_file.strip().split('\n')
            try:
                response = openai.Completion.create(
                model="text-davinci-003",
                prompt=f'Choose from the following choices: {context_file}. \n\nUser Answer: \"{query}\"',
                temperature=0.9,
                max_tokens=150,
                top_p=1,
                presence_penalty=0.6,
                stop=[" Human:", " AI:"]
                )
            except:
                return ["Something went wrong. Please try again later.", [], 500]
            f.close()
            
            choice = select_option(choices_given, choice=int(query))
            try:

                response = openai.Completion.create(
                model="text-davinci-003",
                prompt=generate_prompt(choice, company=companyname, keywords=keywordsname),
                temperature=0.9,
                max_tokens=150,
                top_p=1,
                presence_penalty=0.6,
                stop=[" Human:", " AI:"]
                )
            except:
                return ["Something went wrong. Please try again later.", [], 500]
            session['feedback_toggle'] += 1
          
            add_conversation('\n' + 'User Answer: \"' + query + '\"\n\n' + f"{companyname} Customer Experience Team: \"" +(response.choices[0].text) + '\"\n\n')
           
            return response.choices[0].text



    else:
        try:
            response = openai.Completion.create(
                model="text-davinci-003",
                prompt=generate_prompt(query, company=companyname, keywords=keywordsname),
                temperature=0.9,
                max_tokens=150,
                top_p=1,
                presence_penalty=0.6,
                stop=[" Human:", " AI:"]
            )
        except:
            return ["Something went wrong. Please try again later.", [], 500]
       
        session['feedback_toggle'] += 1
        
        add_conversation('\n' + 'User Answer: \"' + query + '\"\n\n' + f"{companyname} Customer Experience Team: \"" +(response.choices[0].text) + '\"\n')

        return retrieve_question(response.choices[0].text.strip('\n'))#.split('?')[0]+'?'


def select_option(list_choices, choice):
    if (str(choice) in list_choices[choice].split()):
        return list_choices[choice]
    else:
        for i in list_choices:
            if str(choice) in i:
                return i
                
                
def retrieve_question(content):
    content = content.replace('"', '').replace('.', '').replace('\n\n', '\n')
    for i in content.split('\n'):
        if '?' in i:
            return i
        else:
            return False


def add_conversation(text):
    Username = session.get("Username")
    f = open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, "a")
    f.write(text)
    f.close()


def generate_prompt_choice(query, company, keywords):
    Username = session.get("Username")
    with open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'r') as f:

        context_file = f.read()
    if session.get("toggle") == 'PRODUCT':
                    
        return f"Ask one question acting as {company} Customer Support Assistant regarding customer's response: {query} based on {keywords} according to this conversation: {context_file}"

    else:
                return f"Ask one question acting as {company} Customer Support Assistant regarding customer's response: {query} based on {keywords} according to this conversation: {context_file}"


def generate_prompt(query, company, keywords):
    Username = session.get("Username")
    touchpoint = session.get('touchpoint')
    usecase = TOUCHPOINT_OPTIONS[int(touchpoint) - 1]
    with open(DIR_DATA_FOLDER + Username + DIR_PATH_CONVERSATION, 'r') as f:

        context_file = f.read()
    if session.get("toggle") == 'PRODUCT':
        return f"###\n{context_file} \nUser Answer: \"{query}\" \n###\nAsk one question acting as {company} Customer Support Assistant regarding customer's answer.Do not include \"{company} Customer Experience Team\"."# based on {usecase}"
    else:
        return f"###\n{context_file}\nUser Answer: {query} \n###\nAsk one question acting as {company} Customer Support Assistant regarding customer's answer.Do not include \"{company} Customer Experience Team\"." # based on {usecase}"



class QA:
    def __init__(self, question, answers_list):
        self.question = question
        self.answers_list = answers_list

def parse_QA(text):
    if(len(text.split('?'))>1):
        question = text.split('?')[0]
        answer = text.split('?')[1]

    return question, answer.split('\n')[1:]

@app.route('/generate_survey')
def generate_survey():

    create_directories()
    reload_conversation()
    session["generate_survey_toggle"] = True

    session['touchpoint'] = request.args.get('touchpoint')
    session['companyname'] = request.args.get('companyname')
    session['keywords'] = request.args.get('keywords')
    toggle_val = session.get('toggle')
    touchpoint = session.get('touchpoint')
    companyname = session.get('companyname')
    keywordsname = session.get('keywords')
    usecase = TOUCHPOINT_OPTIONS[int(touchpoint)]
    list_prompt = [
        f"Generate survey of three questions in number list format for {companyname} for {keywordsname} {toggle_val.lower()} for the case when customer {usecase}. Ask three questions why customer {usecase}. For each question, always add atleast four answer options in alphabetic multiple choice inline format and do not add numbering at start of question. Add # before each question. Add @ before each answer options.",
        """Generate customer satisfaction survey of three questions for {} for {} {} for the case when customer {}. Include NPS questions in number list format. For each question, always add atleast four answer options in alphabetic multiple choice inline format and do not add numbering at start of question. Add # before each question. Add @ before each answer options.""".format(
        companyname, keywordsname, (toggle_val.lower()), usecase)
    ]
    
    select_prompt = ''
    if int(touchpoint)==0:
        select_prompt = list_prompt[0]
    else:
        select_prompt = list_prompt[1]
    response = ''

    try:
        response = openai.Completion.create(
            model="text-davinci-003",
            prompt=select_prompt,
            temperature=0.7,
            max_tokens=250,
            top_p=1,
            presence_penalty=0.6
            
        )
    except:

        return ["Something went wrong. Please try again later.", [], 500]
    
  
    
    survey_questions_list = session['survey_questions']
    survey_answers_list = session['survey_answers']
   
    response_text = response.choices[0].text

    
    qa_seperated = response_text.strip().split("#")
    for i in qa_seperated:
        if(i=='' or i=='\n' or i=='\n\n'):
            qa_seperated.remove(i)
        else:
            i.strip()
    questions_list = []
    answers_options = []
    for j in qa_seperated:
        answers_options.append(j.split("@")[1:])
        questions_list.append(j.split("@")[0])
    session['survey_questions'] = questions_list
    session['survey_answers'] = answers_options 


    return [questions_list[0], answers_options[0]]


@app.route('/fetch_logo')
def fetch_logo():

    session['touchpoint'] = request.args.get('touchpoint')
    session['companyname'] = request.args.get('companyname')
    session['keywords'] = request.args.get('keywords')

    touchpoint = session.get('touchpoint')
    companyname = session.get('companyname')
    keywordsname = session.get('keywords')

    r = requests.get("https://api.qwant.com/v3/search/images",
                     params={
                         'count': 5,
                         'q': companyname,
                         't': 'images',
                         'safesearch': 1,
                         'locale': 'en_US',
                         'offset': 0,
                         'device': 'desktop'
                     },
                     headers={
                         'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/56.0.2924.87 Safari/537.36'
                     }
                     )

    response = r.json().get('data').get('result').get('items')
    urls = [r.get('media') for r in response]
    for i in range(len(urls)):
        print("URL : ", str(i) + " -- " + urls[i])
    if(len(urls) > 0):
        return urls[0]
    else:
        return "../static/icons/bot.png"
        
        

if __name__ == "__main__":
    setup_db(app)
    app.run(threaded=True)
