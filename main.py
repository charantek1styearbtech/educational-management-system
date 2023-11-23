from twilio.rest import Client
from flask import Flask, request, session
from twilio.twiml.messaging_response import MessagingResponse
from flask_session import Session
import sqlite3
import time
import os
import requests
import waitress as serve
#userdata dictonary to store user data
user_data={}
app = Flask(__name__)
#handle in coming messages
@app.route('/wasms', methods=['POST'])
def recive_msg():
    #extract the senders number
    no = request.values.get('From')[12:]
    #if userdata found saving it to user_info or create a userdata
    try :
        user_info=user_data[no]
    except:
        user_data[no] = {
            'pageroute': 0,
            'second_found': '',
            'list_students': []
        }
        user_info = user_data[no]
     #user message
    rply_from_user = request.form.get('Body').upper()
    #media url if send
    media_url=request.form.get('MediaUrl0')
    if media_url is not None:
        for x in user_info['list_students']:
            reply_media(media_url,x[0])
    #handle exit command
    if rply_from_user=='EXIT':
        user_info={
            'pageroute':0,
            'list_students':[],
            'section_found':''
        }
        user_data[no]=user_info
        reply("THANKS FOR USING ME PRESS HI TO USE AGAIN",no)
        return None
    #logic start from here handling start from here
    if  user_info['pageroute']== 0:
        #checking if registered
        is_registered = get_person_info(no)
        #registering command
        if is_registered==0:
            user_info['pageroute']=1
            reply("""REGISTER AS
1. TEACHER
2. STUDENT""", no)
            return None
        #found as student
        elif is_registered == 2:
            user_info['pageroute']= 1.1
            reply("""HERE IS THE MENU:
1. TIMETABLE
2. ASSIGNMENTS
3. UPCOMING EXAMS
4. PREVIOUS PAPERS
ENTER EXIT TO CLOSE""", no)
            return None
        #found as teacher
        elif is_registered == 1:
            user_info['pageroute']=1.2
            reply("""HERE IS THE MENU:
1. GET DETAILS ABOUT STUDENT
2. SEND ANNOUNCEMENT, MATERIALS
3. ADD ASSIGNMENT
4. ADD UPCOMING EXAM
ENTER EXIT TO CLOSE""", no)
            return None
        #registering and taking input data from the user
    if(user_info['pageroute']==1):
        if(rply_from_user=="1"):
            user_info['pageroute']=0.1
            reply("""ENTER THE DETAILS IN THIS FORMAT:
NAME,SECTIONS YOU TEACH WITH SUBJECTS (SEPARATED BY COMMAS)
EXAMPLE:
SECTION: 2EEB:"SUBJECT" 2->YEAR EE->DEPT B->SECTION""",no)
            return None
        if(rply_from_user=="2"):
            user_info['pageroute']=0.2
            reply("""ENTER THE DETAILS IN THIS FORMAT:
NAME,ROLL NO,SECTION
SECTION: 2EEB 2->YEAR EE->DEPT B->SECTION""",no)
            return None
    #adding data to taecher database
    if(user_info['pageroute']==0.1):
        newuser_info=rply_from_user.split(',')
        ans=''
        for x in range(1,len(newuser_info)):
            ans+=newuser_info[x]+','
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO teacher_info(name, phone_number,sections) VALUES (?, ?, ?)",
                       (newuser_info[0],no,ans))
        conn.commit()
        conn.close()
        reply("SUCCESSFULLY REGISTERED",no)
        user_info['pageroute']=1.2
        reply("""
HERE IS THE MENU:
1.GET DETAILS ABOUT STUDENT
2.SEND ANNOUNCEMENT,MARKS,MATERIALS
3.ADD ASSIGNMENT
4.ADD UPCOMING EXAM
ENTER EXIT TO CLOSE
""", no)
        return None
    #adding data to student database
    if (user_info['pageroute']==0.2):
        newuser_info = rply_from_user.split(',')
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute("INSERT INTO NITW(name, id, phone_number, section) VALUES (?, ?, ?, ?)",
                       (newuser_info[0], newuser_info[1], no, newuser_info[2],))
        conn.commit()
        conn.close()
        reply("SUCCESSFULLY REGISTERED",no)
        user['pageroute'] = 1.1
        reply("""HERE IS THE MENU:
1.TIMETABLE
2.ASSIGNMENTS
3.UPCOMING EXAMS
4.PREVIOUS PAPERS
ENTER EXIT TO CLOSE""", no)
        return None
    #student menu
    if(user_info['pageroute']==1.1):
        #timetable
        if(rply_from_user=="1"):
            current_time = time.localtime()
            day=current_time.tm_wday
            hour=current_time.tm_hour
            if(hour>=18):
                day=(day+1)%6
            ans=''
            if(day==0):
                ans='sunday'
            if(day==1):
                ans='monday'
            if(day==2):
                ans='tuesday'
            if(day==3):
                ans='wednesday'
            if(day==4):
                ans='thursday'
            if(day==5):
                ans='friday'
            if(day==6):
                ans='saturday'
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT section FROM NITW WHERE phone_number=?",(no,))
            section1= cursor.fetchone()
            conn.commit()
            conn.close()
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT {ans} FROM section_data WHERE section=?",(section1[0],))
            result = cursor.fetchone()
            conn.commit()
            conn.close()
            message=result[0]
            msg=message.split('\n')
            timetable=''
            for x in msg:
                timetable+=x+'\n'
            reply(timetable,no)
            user_info['pageroute']=1
            return None
        #checking assignments
        if(rply_from_user=="2"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT section FROM NITW WHERE phone_number={no}")
            section = cursor.fetchone()
            cursor.execute(f"SELECT assignments FROM section_data WHERE section=?",(section[0],))
            assignment=cursor.fetchone()
            conn.commit()
            conn.close()
            reply(assignment,no)
            user_info['pageroute']=1
            return None
        #checking upcomingexams
        if(rply_from_user=="3"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT section FROM NITW WHERE phone_number={no}")
            section = cursor.fetchone()
            cursor.execute(f"SELECT upcomig_exams FROM section_data WHERE section=?",(section[0],))
            upcoming_exam = cursor.fetchone()
            conn.commit()
            conn.close()
            reply(upcoming_exam,no)
            user_info['pageroute'] = 1
            return None
        #google drive links for materials and previous year papers
        if(rply_from_user=="4"):
            reply("""SELECT THE SUBJECT
1.ELECTRICAL-MACHINES-1
2.PYTHON-PROGRAMMING
3.POWER-SYSTEMS-1
4.DSA
5.ANALOG-ELECTRONICS
6.MATHEMATICS-3
ENTER EXIT TO CLOSE""",no)
            user_info['pageroute']=1.4
            return None
    #teacher menu
    if(user_info['pageroute']==1.2):
        #searching student from database based on roll,name,phone number
        if (rply_from_user == "1"):
            reply("""COMMANDS FOR SEARCHING:
/r: TO SEARCH BY ROLLNO
/p: TO SEARCH BY PHONR NUMBER
/n: TO SEARCH BY NAME
/o: TO SEARCH OTHER NO
FORMAT
COMMAND:ROLLNO/PHONENUMBER/NAME
ENTER EXIT TO CLOSE""",no)
            user_info['pageroute']=1.21
            return None
        #send announcemts or material
        if (rply_from_user == "2"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT sections FROM teacher_info WHERE phone_number={no}")
            section = cursor.fetchone()
            message = "SELECT THE SECTION\n"
            ans=section[0]
            section_list=ans.split(',')
            for x in range(0,len(section_list)-1):
                if section_list[x] is not None:
                    message+=str(x+1)+'.'+section_list[x]+'\n'
            conn.close()
            reply(message,no)
            user_info['pageroute']=1.22
            return None
        #add assignments to students
        if (rply_from_user == "3"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT sections FROM teacher_info WHERE phone_number={no}")
            section = cursor.fetchone()
            message = "SELECT THE SECTION\n"
            ans = section[0]
            section_list = ans.split(',')
            for x in range(0, len(section_list) - 1):
                if section_list[x] is not None:
                    message += str(x + 1) + '.' + section_list[x] + '\n'
            conn.close()
            reply(message, no)
            user_info['pageroute'] = 1.24
            return None
        #add upcoming exam to students
        if (rply_from_user == "4"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT sections FROM teacher_info WHERE phone_number={no}")
            section = cursor.fetchone()
            message = "SELECT THE SECTION\n"
            ans = section[0]
            section_list = ans.split(',')
            for x in range(0, len(section_list) - 1):
                if section_list[x] is not None:
                    message += str(x + 1) + '.' + section_list[x] + '\n'
            conn.close()
            reply(message, no)
            user_info['pageroute'] = 1.25
            return None
    #inmplenting the logic of searching
    elif(user_info['pageroute']==1.21):
        search=rply_from_user.split(':')
        if(rply_from_user[1]=="R"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM NITW WHERE id=?",(" "+search[1],))
            person_info = cursor.fetchall()
            conn.close()
            for x in person_info:
                reply(f"Name:{x[0]}, RollNO:{x[1]}, PhoneNumber:{x[2]}, Section:{x[3]}",no)
            return None
        elif (rply_from_user[1] == "P"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM NITW WHERE phone_number=?",(search[1],))
            person_info = cursor.fetchall()
            conn.close()
            for x in person_info:
                reply(f"Name:{x[0]}, RollNO:{x[1]}, PhoneNumber:{x[2]}, Section:{x[3]}", no)
            return None
        elif (rply_from_user[1] == "N"):
            conn = sqlite3.connect('project_data.db')
            cursor = conn.cursor()
            cursor.execute(f"SELECT * FROM NITW WHERE name=?",(search[1],))
            person_info = cursor.fetchall()
            conn.close()
            for x in person_info:
                reply(f"Name:{x[0]}, RollNO:{x[1]}, PhoneNumber:{x[2]}, Section:{x[3]}", no)
            return None
        elif (rply_from_user[1] == "o"):
            user_info['pageroute']=1.21
            return None
        else:
            user_info['pageroute']=1.2
            return None
    #implenting logic of sending material and announcements
    elif(user_info['pageroute']==1.22):
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT sections FROM teacher_info WHERE phone_number={no}")
        section = cursor.fetchone()
        ans=section[0]
        section_list=ans.split(',')
        target_section=section_list[int(rply_from_user)-1]
        user_info['section_found']=target_section
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT phone_number FROM NITW WHERE section=?",(user_info['section_found'][0:4],))
        user_info['list_students'] = cursor.fetchall()
        reply("""ENTER THE ANNOUNCEMENT OR IF YOU WANT TO SEND FILE SEND IT""",no)
        user_info['pageroute']=1.23
        return None
    elif (user_info['pageroute']==1.23):
        for x in user_info['list_students']:
            reply(rply_from_user+"FROM "+user_info['section_found'][5:]+" "+"INSTRUCTOR",x[0])
            return None
    #implementing the logic of adding assingments to students
    elif(user_info['pageroute']==1.24):
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT sections FROM teacher_info WHERE phone_number={no}")
        section = cursor.fetchone()
        ans = section[0]
        section_list = ans.split(',')
        user_info['second_found']=section_list[int(rply_from_user) - 1]
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT phone_number FROM NITW WHERE section=?",(user_info['second_found'][0:4],))
        user_info['list_students'] = cursor.fetchall()
        reply("""ENTER THE ASSIGNMENT WITH SUBMISSION DATA IN (DD/MM/YYYY)""", no)
        user_info['pageroute'] = 1.241
        return None
    #implenting the logic of adding upcoming exams to students
    elif(user_info['pageroute']==1.25):
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT sections FROM teacher_info WHERE phone_number={no}")
        section = cursor.fetchone()
        ans = section[0]
        section_list = ans.split(',')
        user_info['second_found'] = section_list[int(rply_from_user) - 1]
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute(f"SELECT phone_number FROM NITW WHERE section=?",(user_info['second_found'][0:4],))
        user_info['list_students'] = cursor.fetchall()
        reply("""ENTER THE EXAM WITH DATE IN (DD/MM/YYYY)""", no)
        user_info['pageroute'] = 1.251
        return None
    #implenting logic of sending assignments to students
    elif(user_info['pageroute']==1.241):
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT assignments FROM section_data WHERE section=?",(user_info['second_found'][0:4],))
        ans=cursor.fetchone()
        rply_from_user=ans[0]+rply_from_user
        cursor.execute("UPDATE section_data SET assignments = ? WHERE section = ?",
                       (rply_from_user + ',', user_info['second_found'][0:4]))
        conn.commit()
        conn.close()
        rply_from_user=f"WE HAVE A ASSIGNMENT GIVEN BY {user_info['second_found'][5:]} INSTRUCTOR\n"+rply_from_user
        for x in user_info['list_students']:
            reply(rply_from_user, x[0])
        return None
    # implenting logic of sending upcoming exams to students
    elif(user_info['pageroute']==1.251):
        conn = sqlite3.connect('project_data.db')
        cursor = conn.cursor()
        cursor.execute("SELECT upcoming_exams FROM section_data WHERE section=?", (user_info['second_found'][0:4],))
        ans = cursor.fetchone()
        rply_from_user = ans[0] + rply_from_user
        conn = sqlite3.connect('project_data.db')
        cursor.execute("UPDATE section_data SET upcoming_exams = ? WHERE section =?", (rply_from_user+',',user_info['second_found'][0:4]))
        cursor = conn.cursor()
        conn.commit()
        conn.close()
        rply_from_user = f"WE HAVE AN EXAM SCHEDULED BY {user_info['second_found'][5:]} INSTRUCTOR \n" + rply_from_user
        for x in user_info['list_students']:
            reply(rply_from_user, x[0])
            return None
    #implenting logic of links of material and papers for students menu
    elif user_info['pageroute']==1.4:
        search_index=''
        if(rply_from_user=="1"):
            search_index='ELECTRICALMACHINES_1'
        elif rply_from_user=="2":
            search_index='PYTHON_PROGRAMMING'
        elif user_info['pageroute']=='3':
            search_index='POWERSYSTEMS_I'
        elif user_info['pageroute']=='4':
            search_index='DSA'
        elif user_info['pageroute']=='5':
            search_index='ANALOG_ELECTRONICS'
        elif user_info['pageroute']=='6':
            search_index='MATHEMATICS_3'
        conn=sqlite3.connect('project_data.db')
        cursor=conn.cursor()
        cursor.execute(f"SELECT {search_index} FROM material_links")
        link=cursor.fetchone()
        reply(link[0],no)
        user_info['pageroute']=1.1
        return None
#checking func to check if user exits in database
def get_person_info(no):
    conn = sqlite3.connect('project_data.db')
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM NITW WHERE phone_number=?",(no,))
    person_info = cursor.fetchone()
    cursor.execute("SELECT * FROM teacher_info WHERE phone_number=?",(no,))
    teacher_info=cursor.fetchone()
    conn.close()
    if person_info is None and teacher_info is None:
        reply(f"""NO DATA ABOUT {no} FOUND
PLEASE REGISTER""",no)
        return 0
    elif person_info is None:
        return 1
    else:
        return 2
#sending replies to user
def reply(msg,no):
    account_sid = 'AC25b3d457e76640fef28cb485566362a7'
    auth_token = '34c7b478e18195768a6660bab067d4ef'
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        body=f'{msg}',
        from_='whatsapp:+14155238886',
        to=f'whatsapp:+91{no}'
        )
    return str(message.sid)
#sending media replies to user
def reply_media(path, no):
    account_sid = 'AC25b3d457e76640fef28cb485566362a7'
    auth_token = '34c7b478e18195768a6660bab067d4ef'
    client = Client(account_sid, auth_token)
    message = client.messages.create(
        media_url=path,
        from_='whatsapp:+14155238886',
        to=f'whatsapp:+91{no}'
    )
    return str(message.sid)
#implenting production server to handle multiple requests to max of 5 users at a time
if __name__ == '__main__':
    from waitress import serve
    serve(app, host='0.0.0.0', port=5000, threads=5)
