#!/usr/bin/env python3
# vim: set ai et ts=4 sw=4:

import requests
import getpass
import html
import sys
import re

headers = {}
headers['user-agent'] = u'Mozilla/5.0 (compatible; MSIE 9.0; Windows NT 6.0; Trident/5.0;  Trident/5.0)'

def eprint(msg):
    print(msg, file=sys.stderr)
    sys.exit(1)

if False: # auth code could be used in the future
    if len(sys.argv) < 2:
        print("Usage: " + sys.argv[0] + " <your login in the commitfest app>")
        print("Example: " + sys.argv[0] + " a.alekseev")
        sys.exit(1)

    login = sys.argv[1]
    password = getpass.getpass("{}'s password: ".format(login))

    res = requests.get("https://commitfest.postgresql.org/account/login/?next=/", headers=headers, allow_redirects=True)
    m = re.search("""(?s)<form.*?name='csrfmiddlewaretoken'\s+value='([^']+)'.*?name="next"\s+value="([^"]+)".*?</form>""", res.text)
    [form_csrf_token, form_next] = [ m.group(i+1) for i in range(2) ]
    data = {
        "csrfmiddlewaretoken": form_csrf_token,
        "username": login,
        "password": password,
        "this_is_the_login_form": "1",
        "next": form_next
    }

    headers['referer'] = res.url # to bypass CSRF checks
    res = requests.post(res.url, headers=headers, cookies=res.cookies, allow_redirects=True, data=data)
    headers.pop('referer')
    cookies = res.history[2].cookies # save cookies for the domain commitfest.postgresql.org

    res = requests.get("https://commitfest.postgresql.org/", headers=headers, cookies=cookies)

    if not re.search("""/account/logout/""", res.text):
        eprint("Login failed!")

res = requests.get("https://commitfest.postgresql.org/", headers=headers)

curr_cf_id = 0
curr_cf_date = ''
for m in re.finditer("""<li><a href="/([0-9]+)/">([^<]+)</a> \((Closed|In Progress|Open|Future) -[^<]+</li>""", res.text):
    [cf_id, cf_date, cf_status] = [ m.group(i+1) for i in range(3) ]
    # print("Id: {}, Date: {}, Status: {}".format(cf_id, cf_date, cf_status))
    if cf_status == 'In Progress':
        (curr_cf_id, curr_cf_date) = (cf_id, cf_date)
        break

if curr_cf_id == 0:
    eprint("Unable to determine current commitfest id")
        
print("Current commitfest id: {}".format(curr_cf_id))

res = requests.get("https://commitfest.postgresql.org/{}/".format(curr_cf_id), headers=headers)

needs_review = {} # id -> title
for m in re.finditer("""(?s)<tr>\s+<td><a href="([0-9]+)/?">([^<]+)</a></td>\s+<td><span[^>]*>([^<]+)</span></td>""", res.text):
    [p_id, p_title, p_status] = [ m.group(i+1) for i in range(3) ]
    p_title = html.unescape(p_title)
    # print("Id: {}, Title: '{}', Status: {}".format(p_id, p_title, p_status))
    if p_status == 'Needs review':
        needs_review[p_id] = p_title

#print("Needs review (total {}):".format(len(needs_review)))
#for p_id, p_title in needs_review.items():
#    print("Id: {}, Title: '{}'".format(p_id, p_title))

res = requests.get("http://commitfest.cputube.org/", headers=headers)
[cnt_ok, cnt_apply_failed, cnt_build_failed] = [ 0 for _ in range(3) ]
[lst_ok, lst_apply_failed, lst_build_failed] = [ [] for _ in range(3) ]
collect_emails_queue = []

for m in re.finditer("""(?s)<tr>\s+<td>#([0-9]+)</td>.*?apply-(passing|failing)\.svg"(.*?)</tr>""", res.text):
    [p_id, p_apply, p_therest] = [ m.group(i+1) for i in range(3) ]
    if not needs_review.get(p_id):
        continue
    p_build = 'failing'
    m_url = re.search("""<img src="(https://travis-ci\.org/[^"]+)""""", p_therest)
    if m_url is not None:
        p_build_url = m_url.group(1)
        print("Fetching {} ...".format(p_build_url))
        svg = requests.get(p_build_url, headers=headers)
        m_svg = re.search("""<text[^>]*>build</text><text[^>]*>(passing|failing)</text>""", svg.text)
        p_build = m_svg.group(1)
    # print("Id: {}, Apply: '{}', Build: {}".format(p_id, p_apply, p_build))
    url = "https://commitfest.postgresql.org/{}/{}/".format(curr_cf_id, p_id)
    obj = { "id": p_id, "title": needs_review[p_id], "url": url }
    if p_apply == 'passing' and p_build == 'passing':
        cnt_ok += 1
        lst_ok += [ obj ]
    elif p_apply == 'passing':
        cnt_build_failed += 1
        lst_build_failed += [ obj ]
        collect_emails_queue += [ url ]
    else:
        cnt_apply_failed += 1
        lst_apply_failed += [ obj ]
        collect_emails_queue += [ url ]

cc_set = set()
url_to_authors = {}
for url in collect_emails_queue:
    print("Fetching {} ...".format(url))
    res = requests.get(url, headers=headers)
    url_to_authors[url] = set()
    for m in re.finditer("""<dt><a href="(https://www.postgresql.org/message-id/[^"]+)""", res.text):
        msg_url = m.group(1)
        print("Fetching {} ...".format(msg_url))
        msg_res = requests.get(msg_url, headers=headers)
        msg_from = re.search("""(?s)<th>From:</th>\s+<td>([^>]+)</td>""", msg_res.text).group(1)
        msg_from = html.unescape(msg_from).replace("(dot)", ".").replace("(at)", "@")
        url_to_authors[url].add(msg_from)
        cc_set.add(msg_from)

#print("\n=== OK: {} ===".format(cnt_ok))
#for obj in lst_ok:
#    print("{} ({})".format(obj["url"], obj["title"]))

print("\n=== Apply Failed: {} ===".format(cnt_apply_failed))
for obj in lst_apply_failed:
    end = "s" if len(url_to_authors[obj["url"]]) > 1 else ""
    print("Title: {1}\nAuthor{3}: {2}\nURL: {0}\n".format(
        obj["url"], obj["title"], ", ".join(url_to_authors[obj["url"]]), end))

print("\n=== Build Failed: {} ===".format(cnt_build_failed))
for obj in lst_build_failed:
    end = "s" if len(url_to_authors[obj["url"]]) > 1 else ""
    print("Title: {1}\nAuthor{3}: {2}\nURL: {0}\n".format(
        obj["url"], obj["title"], ", ".join(url_to_authors[obj["url"]]), end))

failed_total = cnt_build_failed + cnt_apply_failed
print("Needs Review Total: {}".format(len(needs_review)))
print("Failed Total: {} ({:.2f} %)".format(failed_total, failed_total * 100.0 / len(needs_review)))

cc_lst = list(cc_set)
cc_lst.sort()
print("\nCC ({}): {}".format(len(cc_lst), ", ".join(cc_lst)))
