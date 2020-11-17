import json
import requests
import pymysql
from datetime import datetime
from urllib.parse import urlencode
import urllib3
from typing import Tuple, List, Dict
import os
from user_management import *
from knowledge_base_management import *
from dialog_management import *
import constant

dialogDBHost = constant.dialogDBHost
dialogDBPort = constant.dialogDBPort
dialogDBUserName = constant.dialogDBUserName
dialogDBPassword = constant.dialogDBPassword
dialogDBDatabase = constant.dialogDBDatabase
dialogDBCharset = constant.dialogDBCharset

HOME_DIRECTORY = constant.HOME_DIRECTORY
DOCKER_EXEC_PREFIX = constant.DOCKER_EXEC_PREFIX

TARGET_DB = constant.TARGET_DB
headers = constant.headers

def query(query):
    conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
                           db=dialogDBDatabase,
                           charset=dialogDBCharset)
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = query
    print(sql)
    try:
        curs.execute(sql)

        result = curs.fetchall()

    except Exception as e:
        print(e)

    curs.close()
    conn.commit()
    conn.close()

    return result

#
# def DescribeTable(table_name):
#     conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
#                            db=dialogDBDatabase,
#                            charset=dialogDBCharset)
#     curs = conn.cursor(pymysql.cursors.DictCursor)
#     sql = 'desc {}'.format(table_name)
#
#     try:
#         curs.execute(sql)
#         result = curs.fetchall()
#
#     except:
#         print('error in DescribeTable')
#
#     curs.close()
#     conn.close()
#     return result

#
# def LookUpTables():
#     conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
#                            db=dialogDBDatabase,
#                            charset=dialogDBCharset)
#     curs = conn.cursor(pymysql.cursors.DictCursor)
#     sql = 'show tables'
#
#     try:
#         curs.execute(sql)
#         result = curs.fetchall()
#
#     except Exception as e:
#         print(e)
#
#     curs.close()
#     conn.close()
#     return result


#
# def CreateNewTable(table_name,column_list):
# 	conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword, db=dialogDBDatabase,
# 						   charset=dialogDBCharset)
# 	curs = conn.cursor()
#
# 	data = column_list
# 	temp = '{} int auto_increment'.format(table_name+'_id')
# 	for item in data.items():
# 		temp = temp + ',' + item[0] + ' '+ item[1]
#
#
# 	sql = "CREATE TABLE {}({},PRIMARY KEY({}))".format(table_name,temp,table_name+'_id')
#
# 	print(sql)
# 	try:
# 		curs.execute(sql)
#
# 	except Exception as e:
# 		print(e)
#
# 	curs.close()
# 	conn.commit()
# 	conn.close()


def getUtteranceWithKnowledgeBySessionID(session_id):
    conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
                           db=dialogDBDatabase,
                           charset=dialogDBCharset)
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = "select u.utterance_id, u.utterance, u.speaker, u.turn_id, u.query_id, u.intent_req, u.session_id, l.subject, l.property, l.object, l.userKB_log_id, l.kv_module_score from UTTERANCE u left outer join USERKB_LOG l on u.utterance_id=l.utterance_id where u.session_id={}".format(session_id)

    try:
        curs.execute(sql)
        result = curs.fetchall()

    except Exception as e:
        print(e)
    curs.close()
    conn.close()
    if len(result) > 0:
        answer = {'utterances': result}
    else:
        answer = None
    print(answer)
    return answer


def getEntityListWithUserID(user_id=None):
    conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
                           db=dialogDBDatabase,
                           charset=dialogDBCharset)
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT e.text, e.entity_uri, e.entity_ne_type, e.score, e.confidence FROM USER u, SESSION s, UTTERANCE d, UTTERANCE_ENTITY e WHERE u.user_id={} and s.user_id=u.user_id and s.session_id=d.session_id and d.utterance_id=e.utterance_id".format(user_id)

    try:
        curs.execute(sql)
        result = curs.fetchall()

    except Exception as e:
        print(e)
    curs.close()
    conn.close()
    if len(result) > 0:
        answer = result
    else:
        answer = None
    return answer


def getFrameQuestionByUtteranceID(utterance_id):
    conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
                           db=dialogDBDatabase,
                           charset=dialogDBCharset)
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT * FROM FRAME_QUESTION WHERE utterance_id={}".format(utterance_id)

    try:
        curs.execute(sql)
        result = curs.fetchall()

    except Exception as e:
        print(e)
    curs.close()
    conn.close()
    if len(result) > 0:
        answer = result[0]
    else:
        answer = None
    return answer


def getFrameLogWithFrameLogID(frame_log_id):
    conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
                           db=dialogDBDatabase,
                           charset=dialogDBCharset)
    curs = conn.cursor(pymysql.cursors.DictCursor)

    sql = "SELECT * FROM FRAME_LOG WHERE frame_log_id={}".format(frame_log_id)

    try:
        curs.execute(sql)
        result = curs.fetchall()

    except Exception as e:
        print(e)
    curs.close()
    conn.close()
    if len(result) > 0:
        answer = result[0]
    else:
        answer = None
    return answer


def InsertDataToTable(table_name, data_list):
    conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword,
                           db=dialogDBDatabase,
                           charset=dialogDBCharset)
    curs = conn.cursor()

    for data in data_list:
        keys = ''
        values = ''

        for item in data.items():
            keys = keys + ',' + item[0]
            if str(type(item[1])) == "<class 'str'>":
                text = item[1].replace("'", "''")
                values = values + ",'" + text + "'"
            elif str(type(item[1])) == "<class 'int'>" or str(type(item[1])) == "<class 'float'>":
                values = values + "," + str(item[1])
            else:
                values = values + "," + item[1]

        keys = keys[1:]
        values = values[1:]
        sql = "INSERT INTO {}({}) VALUES({})".format(table_name, keys, values)

        try:
            curs.execute(sql)

        except Exception as e:
            print(e)

        sql = "SELECT LAST_INSERT_ID()"
        try:
            curs.execute(sql)
            result = curs.fetchall()

        except Exception as e:
            print(e)
    curs.close()
    conn.commit()
    conn.close()
    return result[0][0]


def save_entity_info(entities, utterance_id):
    print(entities)
    for entity in entities:
        datalist = []
        datadict = {
            'utterance_id': utterance_id,
            'text': entity['text'],
            'entity_uri': entity['uri'],
            'entity_ne_type': entity['ne_type'],
            'score': entity['score'],
            'confidence': entity['confidence'],
            'start_offset': entity['start_offset'],
            'end_offset': entity['end_offset']
        }
        datalist.append(datadict)
    last_entity_id = InsertDataToTable('UTTERANCE_ENTITY', datalist)



# def UserDBaccess(userDB_json):
# 	userID = userDB_json['userID']
# 	command = userDB_json['command']
# 	targetURL = "http://kbox.kaist.ac.kr:6121/flagship"
# 	requestJson = {
# 		'user_id': userID,
# 		'command': command,
# 	}
# 	headers = {'Content-Type': 'application/json; charset=utf-8'}
#
# 	if command == 'QUERY':
# 		requestJson['query'] = userDB_json['query']
# 	elif command == 'REGISTER':
# 		requestJson['triple'] = userDB_json['triple']
#
# 	print(requestJson)
# 	response = requests.post(targetURL, headers=headers, data=json.dumps(requestJson))
# 	print("[responseCode] " + str(response.status_code))
# 	if command == 'REGISTER':
# 		result = None
# 	else:
# 		result = response.json()
#
# 	return result


# def UserLogin(user_name):
# 	conn = pymysql.connect(host=dialogDBHost, port=dialogDBPort, user=dialogDBUserName, passwd=dialogDBPassword, db=dialogDBDatabase,
# 						   charset=dialogDBCharset)
# 	curs = conn.cursor(pymysql.cursors.DictCursor)

# 	sql = "SELECT * FROM USER WHERE user_name = '{}'".format(user_name)
# 	print(sql)
# 	try:
# 		curs.execute(sql)

# 		result = curs.fetchall()

# 	except Exception as e:
# 		print(e)

# 	if len(result)>0:## login User
# 		user_id = result[0]['user_id']
# 		user_name = result[0]['user_name']
# 		print(result)

# 	else:## 유저 없어서 추가해줘야함
# 		AddNewUser(user_name)
# 		print('New user')
# 	curs.close()	
# 	conn.commit()
# 	conn.close()


# if __name__ == "__main__":

# print(MasterDBaccess('SELECT * WHERE { <http://ko.dbpedia.org/resource/김연아> rdf:type ?o . }'))
# conn = ConnectDatabase()
# AddNewUser('')
# ret = LookUpUsers()


# temp=[{
# 	'utterance':'실험을 해보는 중',
# 	'date_time':'2020-01-08 09:11:11',
# 	'speaker':'user',
# 	'user_id':5
# }]

# table_temp = {
# 	'test' : 'int',
# 	'test1' : 'varchar(100)'
# }

# InsertDataToTable('DIALOG',temp)
# print(GetUtteranceByUser('용빈'))
# print(CreateNewTable('test_table',table_temp))
# UserKBLogin('ybjeongasdasdsa')
