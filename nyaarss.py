import os
import re
import sys
import urllib2
import HTMLParser
import subprocess
import time

SCRIPTDIR = os.path.dirname(os.path.realpath(__file__))
g_settings = {}

class RSSParser(HTMLParser.HTMLParser):
    def __init__(self):
        HTMLParser.HTMLParser.__init__(self)
        self.targets = []
        self.in_item = False
        self.in_title = False
        self.in_link = False
        self.cur_title =u""
        self.cur_link = u""

    def handle_charref(self, name):
        self.handle_data(chr(int(name)))


    def handle_starttag(self, tag, attrs):
        if tag == "item":
            self.in_item = True
            self.cur_title = ""
            self.cur_link = ""
        elif self.in_item and tag == "title":
            self.in_title = True
        elif self.in_item and tag == "link":
            self.in_link = True

    def handle_endtag(self, tag):
        if tag == "item":
            self.in_item = False
            if self.cur_title and self.cur_link:
                self.targets.append((self.cur_title, self.cur_link))
        elif tag == "link":
            self.in_link = False
        elif tag == "title":
            self.in_title = False

    def handle_data(self, data):
        if self.in_item:
            if self.in_title:
                self.cur_title = self.cur_title +  data
            elif self.in_link:
                self.cur_link = self.cur_link + data


def load_config(configfile):
    print "config from {}".format(configfile)
    global g_settings
    f = open(configfile, 'rb')
    for line in f:
        if line.strip().startswith("#"): continue
        eq_sign_index = line.find("=")
        key = line[0:eq_sign_index].strip()
        value = line[eq_sign_index+1:].strip()
        if key.endswith('dir') or key.endswith('file'):
            if value.startswith('..'):
                value = value.replace('..', os.path.join(SCRIPTDIR, '..'))
            elif value.startswith('.'): value = value.replace('.', SCRIPTDIR)
        g_settings[key] = value
    f.close()
                
def is_process_running(proc_name):
    if not proc_name: return False
    pids = [pid for pid in os.listdir('/proc') if pid.isdigit()]
    for pid in pids:
        try:
            f = open(os.path.join('/proc', pid, 'cmdline'), 'rb')
            cmdline = f.read()
            f.close()
            if re.search("\A{}".format(proc_name), cmdline, re.I):
                return True
        except IOError:
            continue
    return False

def load_regexes(regex_file):
    regex_list = []
    f = open(regex_file, 'r')
    for line in f:
        if not line.strip(): continue
        elif line.strip().startswith("#"): continue
        regex_list.append(line.strip())
        #print line.strip()
    return regex_list

def grab_rss(url):
    d = urllib2.urlopen(url)
    return d.read()

def match_targets(target_list, regex_list):
    matches = []
    for t in target_list:
        for r in regex_list:
            if re.search(r, t[0], re.I):
                #print "matched\n\t{}\n\t{}".format(t[0], r)
                matches.append(t)
    return matches

def download(targets, actually_download=True):
    global g_settings
    print ""
    print "downloading = {}".format(actually_download)
    t_dir = g_settings['torrent_dir']
    done_dir = g_settings['done_dir']
    for t in targets:
        filename = os.path.join(t_dir, t[0]) + ".torrent"
        done_filename = os.path.join(done_dir, t[0]) + ".torrent"
        if not os.path.exists(done_filename):
            if not os.path.exists(filename):
                print "NEW: " + t[0]
                if actually_download:
                    data = urllib2.urlopen(t[1]).read()
                    f = open(filename, 'w')
                    f.write(data)
                    f.close()
            else:
                # already in todo folder
                print "DOUBLE: " + t[0]
        else:
            # already in done folder
            print "OLD: " + t[0]

def start_oldest_torrent():
    global g_settings
    t_dir = g_settings['torrent_dir']
    lowest_ctime = time.time()
    files = os.listdir(t_dir)
    selected_torrent = ""
    for f in files:
        fullpath = os.path.join(t_dir, f)
        if f.endswith(".torrent"):
            ctime = os.stat(fullpath).st_ctime
            if ctime <= lowest_ctime:
                lowest_ctime = ctime
                selected_torrent = fullpath
    if selected_torrent:
        new_filename = os.path.realpath(os.path.join(g_settings['done_dir'], f))
        os.rename(fullpath, new_filename)
        print "started:\n\t{}".format(f)
        cmd = g_settings['torrent_command'].replace('%f', '"' + new_filename + '"')
        subprocess.call(cmd, shell=True)
            

if __name__ == "__main__":
    try:
        sys.argv.remove("-l")
        actually_download = False
    except ValueError:
        actually_download = True

    for arg in sys.argv[1:]:
        try:
            load_config(arg)
            sys.argv.remove(arg)
            break
        except IOError:
            print "Failed to load config from {}".format(arg)
            sys.argv.remove(arg)
            if len(sys.argv[1:]) == 0: sys.exit(1)
    if len(sys.argv) == 1 and not g_settings:
        # no options, load ./nyaarss.config
        try:
            load_config("nyaarss.config")
        except IOError:
            print "couldn't load nyaarss.config"
            sys.exit(1)

    rss = grab_rss("http://www.nyaa.se/?page=rss&cats=1_37&filter=2")
    regex_list = load_regexes(g_settings['regex_file'])
    parser = RSSParser()
    parser.feed(rss)
    matches = match_targets(parser.targets, regex_list)
    download(matches, actually_download)
    if actually_download and not is_process_running(g_settings['wait_for_process']):
        start_oldest_torrent()
    
