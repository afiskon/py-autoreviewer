#!/usr/bin/env python3
# vim: set ai et ts=4 sw=4:

import requests
import sys
import os
import re

if len(sys.argv) < 2:
    print("Usage: {} <commitfest-url>".format(sys.argv[0]))
    print("Example: {} https://commitfest.postgresql.org/17/".format(sys.argv[0]))
    sys.exit(1)

cfurl = sys.argv[1]
if not cfurl.endswith("/"):
    cfurl = cfurl + "/"

print("Processing {}...".format(cfurl))

headers = {}
headers['user-agent'] = u'Mozilla/5.0 (compatible; MSIE 9.0; ' + \
  u'Windows NT 6.0; Trident/5.0;  Trident/5.0)'

res = requests.get(cfurl, headers = headers)
body = res.text

re_str = "(?is)<tr>\s*" + ("(<td[^>]*>(.*?)</td>\s*)"*7) + "\s*</tr>"
counter = 0

print("""
CREATE TABLE IF NOT EXISTS commitfest
(url text, title text, status text, authors text, reviewers text, committer text,
latest_activity timestamp, latest_mail timestamp);
""")

for fi in re.finditer(re_str, body):
    counter += 1
    if counter == 1:
        continue # skip table header
    [url_title, status, authors, reviewers, committer, latest_activity, latest_mail] = \
        [fi.group(i) for i in range(2,16,2) ]
    m = re.search('(?is)<a href="([^"]+)">([^<]+)</a>', url_title)
    url = cfurl + m.group(1)
    title = m.group(2)
    status = re.sub("</?span[^>]*>", "", status)
    latest_activity = latest_activity.replace("<br/>", " ")
    latest_mail = latest_mail.replace("<br/>", " ")
    print(
    ("""
    INSERT INTO commitfest 
    (url, title, status, authors, reviewers, committer, latest_activity, latest_mail) VALUES
    (""" + ( ",".join(["'{}'"] * 8) ) + """);"""
    ).format(url, title.replace("'", "\\'").replace("&quot;", '"'),
             status, authors, reviewers, committer, latest_activity, latest_mail))
