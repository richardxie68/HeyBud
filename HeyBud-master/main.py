#!/usr/bin/env python
#
# Copyright 2007 Google Inc.
#
# Licensed under the Apache License, Version 2.0 (the "License");
# you may not use this file except in compliance with the License.
# You may obtain a copy of the License at
#
#     http://www.apache.org/licenses/LICENSE-2.0
#
# Unless required by applicable law or agreed to in writing, software
# distributed under the License is distributed on an "AS IS" BASIS,
# WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
# See the License for the specific language governing permissions and
# limitations under the License.
#
import webapp2
import json
import logging
import jinja2
import os
from google.appengine.ext import ndb
from google.appengine.api import users

jinja_environment = jinja2.Environment(
    loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

login_dict = {"header": None}
notes_dict = {"notes": []}


# DataStore Entity Class to store user information
class UserProperties(ndb.Model):
    username = ndb.StringProperty()
    notes = ndb.StringProperty()


# UserLogin function to be run on every page, so user can be logged in on every page
# and be able to add bookmarks and log out
def UserLogin(user_notes_dict=notes_dict):
    user = users.get_current_user()
    # if the user is logged in
    if user:
        nickname = user.nickname()
        global nickname
        # HTML to display username and sign out button
        logout_url = users.create_logout_url("/")
        greeting = "<p id='username' >Welcome, {}! <a id='login_link' href='{}'>Sign Out</a></p>".format(nickname, logout_url)
        # search DataStore for specific user, to see if this is their first login
        user_entity_query = UserProperties.query(UserProperties.username == nickname).fetch()
        # if list of user entities returned by query is empty (current user doesn"t exist), make new user entity
        if user_entity_query == []:
            # bookmarks made before logging in are added to the user"s list of bookmarks
            user_notes_dict_json = json.dumps(user_notes_dict)
            new_user = UserProperties(username=nickname, notes=user_notes_dict_json)
            new_user.put()
    # if no user logged in
    else:
        # HTML to display sign in button
        login_url = users.create_login_url("/")
        greeting = "<a id='login_link' href='{}'>Log in to save your Notes!</a>.".format(login_url)
    # Dictionary to pass to template to display log in/out url
    login_dict = {"header": greeting}
    return login_dict


# Function to add new bookmark to user"s bookmarks property
def AddUserNote(self, note, rendered_dict):
    if users.get_current_user():
        # Get user"s notes property, then add bookmark to user_notes_dict, then update user"s bookmark property
        user_notes_dict = LoadUserNotes()
        # user_notes_dict = AddToBookmarkDict(self, user_notes_dict)
        user_notes_dict["notes"].append(note)
        DumpUserNotes(self, user_notes_dict)
    # if user not logged in
    else:
        # add bookmark without Load/Dump user entity json
        # AddToNotesDict(self)
        notes_dict["notes"].append(note)


# def AddToNotesDict(self, note):
#     note = self.request.get("note")
#     notes_dict.append(note)


def DeleteUserNote(self, rendered_dict):
    if users.get_current_user():
        user_notes_dict = LoadUsernotes()
        user_notes_dict = DeleteFromBookmarkDict(self, user_notes_dict)
        DumpUsernotes(self, user_notes_dict)
        rendered_dict["notes_dict"] = user_notes_dict
    else:
        notes_dict = DeleteFromBookmarkDict(self)


# Load user"s notes dictionary
def LoadUserNotes():
    # fetch user"s notes via username
    user_entity_query = UserProperties.query(UserProperties.username == nickname).get()
    user_notes_dict_json = user_entity_query.notes
    user_notes_dict = json.loads(user_notes_dict_json)
    return user_notes_dict


# Dump user  user's notes dictionary
def DumpUserNotes(self, user_notes_dict=notes_dict):
    user_entity = UserProperties.query(UserProperties.username == nickname).get()
    user_notes_dict_json = json.dumps(user_notes_dict)
    user_entity.notes = user_notes_dict_json
    user_entity.put()


def DeleteFromNotesDict(self, deleted_note, notes_dict):
    for note in notes_dict["notes"]:
        if deleted_note == note:
            notes_dict["notes"].remove(note)
            break


class HomePageHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("/templates/index.html")
        login_dict = UserLogin()
        self.response.write(template.render(login_dict))


class MapMarkersHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("/templates/map_markers.html")
        login_dict = UserLogin()
        self.response.write(template.render())


class ChatboxHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("/templates/chatbox2.html")
        login_dict = UserLogin()
        self.response.write(template.render())


class TextSpeechHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("/templates/opposite.html")
        login_dict = UserLogin()
        self.response.write(template.render())


class SpeechTextHandler(webapp2.RequestHandler):
    def get(self):
        template = jinja_environment.get_template("/templates/speech-text.html")
        login_dict = UserLogin()
        rendered_dict = {"login_dict": login_dict, "notes_dict": notes_dict}
        if users.get_current_user():
            user_notes_dict = LoadUserNotes()
            rendered_dict["notes_dict"] = user_notes_dict
        self.response.write(template.render(rendered_dict))

    def post(self):
        template = jinja_environment.get_template("/templates/speech-text.html")
        login_dict = UserLogin()
        logging.info(notes_dict)
        note = self.request.get("note")
        rendered_dict = {"login_dict": login_dict, "notes_dict": notes_dict}
        # if users.get_current_user():
        #     user_notes_dict = LoadUserBookmarks()
        #     rendered_dict["notes_dict"] = user_notes_dict
        if note == "delete":
            deleted = self.request.get("to_be_deleted")
            if users.get_current_user():
                user_notes_dict = LoadUserNotes()
                DeleteFromNotesDict(self, deleted, user_notes_dict)
                DumpUserNotes(self, user_notes_dict)
                rendered_dict["notes_dict"] = user_notes_dict
            else:
                DeleteFromNotesDict(self, deleted, notes_dict)
        else:
            logging.info(notes_dict["notes"])
            # AddUserNote(self, note, rendered_dict)
            if users.get_current_user():
                user_notes_dict = LoadUserNotes()
                user_notes_dict["notes"].append(note)
                DumpUserNotes(self, user_notes_dict)
                rendered_dict["notes_dict"] = user_notes_dict
            else:
                notes_dict["notes"].append(note)

        self.response.write(template.render(rendered_dict))

app = webapp2.WSGIApplication([
    ('/', HomePageHandler),
    ('/map', MapMarkersHandler),
    ('/speechtext', SpeechTextHandler),
    ('/chatbox', ChatboxHandler),
    ('/textspeech', TextSpeechHandler)
], debug=True)
