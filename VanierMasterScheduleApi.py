# Copyright 2024 Ali Shahrestani
"""
Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated documentation files (the “Software”), to deal in the Software without restriction, including without limitation the rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit persons to whom the Software is furnished to do so, subject to the following conditions:
The above copyright notice and this permission notice shall be included in all copies or substantial portions of the Software.
THE SOFTWARE IS PROVIDED “AS IS”, WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""

import requests
import json
import re

# Need to figure out the base64 encryption of the portal configurations
# https://github.com/Adoxio/xRM-Portals-Community-Edition/blob/master/Framework/Adxstudio.Xrm/Web/UI/ViewLayout.cs
# For now saving one to a file to be used in the api seems to work
from pathlib import Path
base64SecureConfiguration: str
with open(Path(__file__).absolute().parent / "vaniermasterschedule.securekey", "r") as key:
    base64SecureConfiguration = key.read()

class Class():
    ID: str
    teacher: str
    room: str
    time: str
    day: str
    
    attributes: dict = {}
    
    def __init__(self, record: dict):
        if not record['EntityName'] == "vit_meetingtime": 
            raise ValueError("Invalid record passed to Class initializer")
        
        try:
            for attribute in record['Attributes']:
                key = attribute['Name']
                value = attribute['Value']
                if key.startswith("vit_"):
                    self.attributes[key] = value
                    
                    match key:
                        case 'vit_meetingtimeid': 
                            self.ID = value
                        case 'vit_teacher':
                            self.teacher = value
                        case 'vit_room':
                            self.room = value
                        case 'vit_time':
                            self.time = value
                        case 'vit_day':
                            self.day = value
                        case default:
                            pass
        except (KeyError, ValueError):
            raise ValueError("Invalid record passed to Class initializer")
    
    
class Course():
    MS: "MasterSchedule"
    
    ID: str
    section: int
    code: str
    title: str
    program: str
    seats: int
    
    slots: list[Class] = []
    attributes: dict = {}
    
    def __init__(self, MS: "MasterSchedule", record: dict, slots: bool = False):
        self.MS = MS
        if not record['EntityName'] == "vit_courseinfo":
            raise ValueError("Invalid record passed to Course initializer")
        
        try:
            for attribute in record['Attributes']:
                key = attribute['Name']
                value = attribute['Value']
                if key.startswith("vit_"):
                    self.attributes[key] = value
                    
                    match key:
                        case 'vit_courseinfoid': 
                            self.ID = value
                        case 'vit_sec':
                            self.section = int(value)
                        case 'vit_course':
                            self.code = value
                        case 'vit_coursetitle':
                            self.title = value
                        case 'vit_programid':
                            self.program = value
                        case 'vit_availableplaces':
                            self.seats = int(value)
                        case default:
                            pass
        except (KeyError, ValueError):
            raise ValueError("Invalid record passed to Course initializer")

        if slots:
            self.fetch_slots()
    
    def fetch_slots(self): # Fetch course slot details (teacher, day/time, and room)
        data = {
            "entityId": self.ID,
            "entityName": "vit_courseinfo"
        }
        response = self.MS._fetch(data)
        
        if response.status_code == 200 or not response.text.strip():
            self.slots.clear()
            for slot in response.json()['Records']:
                self.slots.append(Class(slot))
        else:
            raise RuntimeError(f"Fetching course slots failed ({response.status_code})")

class MasterSchedule():
    BASE_URL = "https://vanierlivecourseschedule.powerappsportals.com/"
    AUTH = BASE_URL + "_layout/tokenhtml"
    URL = BASE_URL + "_services/entity-grid-data.json/c7a13072-c94f-ed11-bba3-0022486daee2"
    
    BASE_HEADERS = {
        "x-requested-with": "XMLHttpRequest",
        "referrer": "https://vanierlivecourseschedule.powerappsportals.com/",
    }
    
    AUTH_HEADERS = {
        "__requestverificationtoken": "",
        "cookie": "__RequestVerificationToken=",
    }
    
    HEADERS = BASE_HEADERS | AUTH_HEADERS
    
    DATA = {"base64SecureConfiguration" : base64SecureConfiguration}
    
    courses: list[Course] = []
    
    def __init__(self):
        # Create a session to get fresh auth headers
        echo = requests.get(self.AUTH)
        if not echo.status_code == 200:
            raise RuntimeError("Session creation failed")
        token = re.search(r"value=\"(.*)\"", echo.text)
        if not token:
            raise RuntimeError("Session creation failed")
        token = token.group(1)
        cookies = requests.utils.dict_from_cookiejar(echo.cookies)
        token2 = cookies['__RequestVerificationToken']
        self.AUTH_HEADERS['__requestverificationtoken'] = token
        self.AUTH_HEADERS['cookie'] = f"__RequestVerificationToken={token2}"
        self.HEADERS = self.BASE_HEADERS | self.AUTH_HEADERS
    
    def _fetch(self, data: dict): # For internal use
        data = self.DATA | data
        response = requests.post(self.URL, headers=self.HEADERS, json=data)
        return response

    def fetch(self, limit = None, set: bool = True, clear: bool = True): # Fetch courses
        if clear:
            self.courses.clear()
        if not limit:
            more = True
            page = 0
            courses: list[Course] = []
            while more:
                page = page + 1
                response = self._fetch({"search": "", "page": page, "pageSize": 250})
                if not response.status_code == 200 or not response.text.strip():
                    raise RuntimeError(f"Fetch error ({response.status_code})")
                data = response.json()
                if set:
                    for record in data['Records']:
                        self.courses.append(Course(self, record))
                else:
                    for record in data['Records']:
                        courses.append(Course(self, record))
                if not data['MoreRecords']:
                    more = False
            if set:
                return courses
        else:
            if limit <= 250:
                response = self._fetch({"search": "", "page": 1, "pageSize": limit})
                if not response.status_code == 200 or not response.text.strip():
                    raise RuntimeError(f"Fetch error ({response.status_code})")
                data = response.json()
                if set:
                    for record in data['Records']:
                        self.courses.append(Course(self, record))
                else:
                    courses: list[Course] = []
                    for record in data['Records']:
                        courses.append(Course(self, record))
                    return courses
            else:
                left = limit
                page = 0
                courses: list[Course] = []
                while left > 0:
                    page = page + 1
                    response = self._fetch({"search": "", "page": page, "pageSize": 250})
                    if not response.status_code == 200 or not response.text.strip():
                        raise RuntimeError(f"Fetch error ({response.status_code})")
                    data = response.json()
                    if set:
                        for record in data['Records']:
                            self.courses.append(Course(self, record))
                    else:
                        for record in data['Records']:
                            courses.append(Course(self, record))
                    left = left - 250
                    if left > int(data['ItemCount']):
                        left = int(data['ItemCount']) - 250
                if set:
                    return courses

if __name__ == "__main__":
    print("VMS API TEST")
    MS = MasterSchedule()
    MS.fetch()
    print(len(MS.courses))
