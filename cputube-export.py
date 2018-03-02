#!/usr/bin/env python3
# vim: set ai et ts=4 sw=4:

import requests
import sys
import os
import re

cputube_url = 'http://commitfest.cputube.org/';
commitfest_url = 'https://commitfest.postgresql.org/';

headers = {}
headers['user-agent'] = u'Mozilla/5.0 (compatible; MSIE 9.0; ' + \
  u'Windows NT 6.0; Trident/5.0;  Trident/5.0)'

body = requests.get(cputube_url, headers = headers).text

print("""
DROP TABLE IF EXISTS cputube;
CREATE TABLE cputube (url text, apply_passing bool, build_passing bool);
""");
sys.stdout.flush()

re_str = "(?is)<tr>\s*(<td>(\d+/\d+)</td>)\s*" + ("(<td[^>]*>(.*?)</td>\s*?)"*5) + "(<td>[^>]+</td>)?\s*</tr>"
for fi in re.finditer(re_str, body):
    [pid, apply_passing, build_passing] = [fi.group(i) for i in [2, 10, 12]]
    url = commitfest_url + pid + "/";
    apply_passing = (apply_passing.find("apply-passing.svg") > 0)
    if not apply_passing:
        build_passing = False
    else:
        m = re.search('(?i)<img src="(https?://travis-ci.org/[^"]+.svg[^"]+)"', build_passing)
        img_url = m.group(1)
        # print("-- Fetching {}...".format(img_url))
        img_content = requests.get(img_url, headers = headers).text
        build_passing = (img_content.find(">passing</text>") > 0)
    print("""
    INSERT INTO cputube (url, apply_passing, build_passing) VALUES('{}', '{}', '{}');
    """.format(url, 't' if apply_passing else 'f', 't' if build_passing else 'f'))
    sys.stdout.flush()
 
