#!/usr/bin/env python3

from datetime import datetime, timedelta
from math import floor
import requests
import sqlite3
import json

from global_config import DATABASE
from config_mgr import ConfigMGR

# from users import conf_file_name, cache_file_name
"""
Canvas Manager

Contact with canvas.
"""


class CanvasMGR:
    g_out = ""
    g_tformat = "relative"
    usercheck = []
    bid = ""
    ucommand = {}
    url = ""

    def __init__(self, username: str) -> None:
        self.username = username
        self.config_mgr = ConfigMGR()
        self.config = self.config_mgr.get_conf(username)
        if self.config is None:
            raise Exception(f"No configuration found for user: {username}")
        self.reset()

    def reset(self):
        self.g_out = ""
        self.g_tformat = "relative"
        self.ucommand = self.config

        self.url = self.ucommand["url"]
        self.bid = self.ucommand["bid"]
        if self.url[-1] == "/":
            self.url = self.url[:-1]
        if self.url[:4] != "http":
            raise Exception("Invalid url")

        if "checks" in self.ucommand:
            self.usercheck = self.ucommand["checks"]

        if "timeformat" in self.ucommand:
            self.g_tformat = self.ucommand["timeformat"]

    def write_cache(self):
        html = self.g_out[:-1]
        with sqlite3.connect(DATABASE) as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT id FROM users WHERE username = ?",
                           (self.username, ))
            user_id = cursor.fetchone()[0]
            cursor.execute(
                """
                INSERT OR REPLACE INTO user_cache (user_id, html) VALUES (?, ?)
                """,
                (user_id, html),
            )
            conn.commit()
            return html

    def print_own(self, mystr):
        """
        Change the value of self.g_out
        """
        self.g_out += mystr + "\n"

    def get_response(self):
        self.reset()
        self.now = datetime.now()

        if "courses" not in self.ucommand:
            return "<p>No course found!</p>"
        courses = self.ucommand["courses"]
        allc = []

        try:
            for course in courses:
                allc.append(
                    apilink(
                        course,
                        self.bid,
                        self.url,
                        self.usercheck,
                        g_tformat=self.g_tformat,
                    ))
        except Exception as e:
            raise Exception("invalid course", e)

        now_root = self.now.replace(hour=0, minute=0, second=0, microsecond=0)

        sem_begin = datetime.strptime(self.ucommand["semester_begin"],
                                      "%Y-%m-%d")

        bdays = (now_root - sem_begin).days
        bweeks = floor(bdays / 7) + 1

        if "title" in self.ucommand:
            self.print_own(
                f"<h1>{self.ucommand['title']} - Week {bweeks}</h1>")
        else:
            self.print_own(f"<h1>Canvas Dashboard - Week {bweeks}</h1>")

        for i in allc:
            try:
                i.run()
            except Exception as e:
                print(e)
                self.print_own(f"<h2>{i.cname} - Error</h2>\n{i.raw}")

        for i in allc:
            self.print_own(i.print_out())

        return self.write_cache()


class apilink:

    def __init__(self,
                 course: dict,
                 bid: str,
                 url: str,
                 user_check,
                 g_tformat="relative") -> None:
        self.headers = {"Authorization": f"Bearer {bid}"}

        self.course = course["course_id"]
        self.cname = course["course_name"]
        self.course_type = course["type"]
        self.assignment = f"{url}/api/v1/courses/{self.course}/assignment_groups?include[]=assignments&include[]=discussion_topic&exclude_response_fields[]=description&exclude_response_fields[]=rubric&override_assignment_dates=true"
        self.announcement = f"{url}/api/v1/courses/{self.course}/discussion_topics?only_announcements=true"
        self.discussion = f"{url}/api/v1/courses/{self.course}/discussion_topics?plain_messages=true&exclude_assignment_descriptions=true&exclude_context_module_locked_topics=true&order_by=recent_activity&include=all_dates&per_page=50"
        self.other = course
        self.output = ""
        self.now = datetime.now()
        self.g_tformat = g_tformat
        self.usercheck = user_check

    def dump_span(self, style, item_id, text, url: str = ""):
        if style == 1:
            # Positive
            return f'<div class="single"><span class="checkbox positive" id="{item_id}"></span><span class="label" url="{url}">{text}</span></div>\n'
        elif style == 2:
            # wrong
            return f'<div class="single"><span class="checkbox negative" id="{item_id}"></span><span class="label" url="{url}">{text}</span></div>\n'
        elif style == 3:
            # important
            return f'<div class="single"><span class="checkbox important" id="{item_id}"></span><span class="label" url="{url}">{text}</span></div>\n'
        else:
            # Not checked
            return f'<div class="single"><span class="checkbox" id="{item_id}"></span><span class="label" url="{url}">{text}</span></div>\n'

    def num2ch(self, f: int):
        s = ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]
        return s[f] + "."

    def time_format_control(self, rtime: datetime, format):
        if rtime < self.now:
            return "Expired"
        if format == "relative":
            return self.relative_date(rtime)
        elif format == "origin":
            return rtime
        else:
            # Fallback
            return rtime.strftime(format)

    def get_check_status(self, item_id):
        # Return type
        for i in self.usercheck:
            if i["item_id"] == item_id:
                return i["type"]
        return 0

    def relative_date(self, rtime: datetime):
        # Generate relative date
        delta = rtime.replace(hour=0, minute=0, second=0,
                              microsecond=0) - self.now.replace(
                                  hour=0, minute=0, second=0, microsecond=0)
        wp = int((delta.days + self.now.weekday()) / 7)
        if wp == 0:
            # Current week
            if delta.days == 0:
                return f"Today {rtime.strftime('%H:%M:%S')}"
            elif delta.days == 1:
                return f"Tomorrow {rtime.strftime('%H:%M:%S')}"
            elif delta.days == 2:
                return f"The day after tomorrow {rtime.strftime('%H:%M:%S')}"
            else:
                return f"{self.num2ch(rtime.weekday())} {rtime.strftime('%H:%M:%S')}"
        elif wp == 1:
            if delta.days == 1:
                return f"Tomorrow {rtime.strftime('%H:%M:%S')}"
            elif delta.days == 2:
                return f"The day after tomorrow {rtime.strftime('%H:%M:%S')}"
            return (
                f"Next week {self.num2ch(rtime.weekday())} {rtime.strftime('%H:%M:%S')}"
            )
        elif wp == 2:
            return f"The week after next week {self.num2ch(rtime.weekday())} {rtime.strftime('%H:%M:%S')}"
        else:
            return f"{rtime}"

    def send(self, url):
        return requests.get(url, headers=self.headers).content.decode(
            encoding="utf-8", errors="ignore")

    def _cmp_ass(self, el):
        if el["due_at"]:
            return el["due_at"]
        else:
            return el["updated_at"]

    def run(self):
        t = self.course_type
        if t == 0:
            self.collect_assignment()
        elif t == 1:
            self.collect_announcement()
        elif t == 2:
            self.collect_discussion()
        else:
            raise Exception(
                f"invalid show type {self.course_type} (only support 0, 1, 2)")
        self.add_custom_info()

    def add_custom_info(self):
        if "msg" in self.other and self.other["msg"] != "":
            # Add custom message
            self.output += f'<p>{self.other["msg"]}</p>\n'

    def collect_assignment(self):
        self.cstate = "Assignment"
        asr = self.send(self.assignment)
        self.raw = asr
        self.ass_data = []
        asr = json.loads(asr)
        for big in asr:
            a = big["assignments"]
            if a:
                for k in a:
                    if k["due_at"]:
                        dttime = datetime.strptime(
                            k["due_at"],
                            "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
                        if dttime < self.now:
                            continue
                        self.ass_data.append(k)
                    elif k["updated_at"]:
                        # Fallback to updated
                        self.ass_data.append(k)
        self.ass_data.sort(key=self._cmp_ass, reverse=True)
        self.output = f"<h2>{self.cname}: Homework</h2>\n"
        maxnum = 10000
        if "maxshow" in self.other:
            maxnum = int(self.other["maxshow"])
            if maxnum == -1:
                maxnum = 10000
        if len(self.ass_data) == 0 or maxnum <= 0:
            self.output += "None\n"
            return
        if "order" in self.other and self.other["order"] == "reverse":
            self.ass_data.reverse()
        for ass in self.ass_data:
            if maxnum == 0:
                break
            maxnum -= 1
            submit_msg = ""
            if ("has_submitted_submissions"
                    in ass) and ass["has_submitted_submissions"]:
                submit_msg = "(Submittable)"
            if ass["due_at"]:
                dttime = datetime.strptime(
                    ass["due_at"], "%Y-%m-%dT%H:%M:%SZ") + timedelta(hours=8)
                tformat = self.g_tformat
                if "timeformat" in self.other:
                    tformat = self.other["timeformat"]
                dttime = self.time_format_control(dttime, tformat)
                check_type = self.get_check_status(ass["id"])
                # "ass" returend from canvas, so 'id' instead of 'item_id'
                self.output += self.dump_span(
                    check_type,
                    ass["id"],
                    f"{ass['name']}, Due: <b>{dttime}{submit_msg}</b>",
                    ass["html_url"],
                )
            else:
                # No due date homework
                check_type = self.get_check_status(ass["id"])
                self.output += self.dump_span(
                    check_type,
                    ass["id"],
                    f"{ass['name']}{submit_msg}",
                    ass["html_url"],
                )

    def collect_announcement(self):
        self.cstate = "Announcement"
        anr = self.send(self.announcement)
        self.raw = anr
        anr = json.loads(anr)
        self.ann_data = anr
        self.output = f"<h2>{self.cname}: Announcements</h2>\n"
        maxnum = 10000
        if "maxshow" in self.other:
            maxnum = int(self.other["maxshow"])
            if maxnum == -1:
                maxnum = 10000
        if len(anr) == 0 or maxnum <= 0:
            self.output += "None.\n"
            return
        if "order" in self.other and self.other["order"] == "reverse":
            self.ann_data.reverse()
        for an in self.ann_data:
            if maxnum == 0:
                break
            maxnum -= 1
            check_type = self.get_check_status(an["id"])
            self.output += self.dump_span(check_type, an["id"], an["title"],
                                          an["html_url"])

    def collect_discussion(self):
        self.cstate = "Discussion"
        dis = self.send(self.discussion)
        self.raw = dis
        dis = json.loads(dis)
        self.dis_data = []
        self.output = f"<h2>{self.cname}: Discussions</h2>\n"
        for d in dis:
            if d["locked"]:
                continue
            self.dis_data.append(d)
        maxnum = 10000
        if "maxshow" in self.other:
            maxnum = int(self.other["maxshow"])

            if maxnum == -1:
                maxnum = 10000
        if len(self.dis_data) == 0 or maxnum <= 0:
            self.output += "None.\n"
            return
        if "order" in self.other and self.other["order"] == "reverse":
            self.dis_data.reverse()
        for d in self.dis_data:
            if maxnum == 0:
                break
            maxnum -= 1
            check_type = self.get_check_status(d["id"])
            self.output += self.dump_span(check_type, d["id"], d["title"],
                                          d["html_url"])

    def print_out(self):
        if self.output:
            return self.output
        else:
            return (
                f"<p>Warning: no output for course {self.cname} (id: {self.course})</p>"
            )


if __name__ == "__main__":
    # TEST
    cmgr = CanvasMGR()
    print(cmgr.get_response())
