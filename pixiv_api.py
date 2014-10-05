import urllib
import urllib2
import re
import csv
import random

base_url = "http://spapi.pixiv.net/"
work_attributes = ['id', 'artist_id', 'format', 'title', 'img_folder', 'artist_name',
            'thumbnail_url', '', '', 'preview_url', '', '', 'upload_time', 'tags',
            'application', 'ratings', 'total_rating', 'views', 'description',
            'novel_pages', '', '', '', '', 'artist_nickname', '', '', '',
            '', 'artist_avatar_url', '']

artist_attributes = ['', 'artist_id', '', '', '', 'artist_name', 'artist_avatar_url',
            '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '', '',
            'artist_nickname', '', '']

class Work:
    def __init__(self, line):
        self.line = line
        for i in range(len(line)):
            if work_attributes[i]=='' : continue
            else: setattr(self, work_attributes[i], line[i])
        self.img_folder = self.img_folder.zfill(2)

    def get_full_url(self, page=None):
        single_fmt = "http://i{}.pixiv.net/img{}/img/{}/{}.{}"
        ugoira_fmt = "http://i{}.pixiv.net/img-zip-ugoira/img/{}/{}/{}/{}/{}/{}/{}_ugoira1920x1080.zip"
        if int(self.id) > 46270952:  # ID 46270953 uses new URL, 46270952 uses old URL.
            single_fmt = "http://i{}.pixiv.net/img-original/img/{}/{}/{}/{}/{}/{}/{}_p0.{}"
            novel_fmt = "http://i{}.pixiv.net/img-original/img/{}/{}/{}/{}/{}/{}/{}_p{}.{}"

        elif int(self.id) > 11320000:  # ID 11320066 uses new URL, 11319887 uses old URL, 11319948 uses old URL, but site thinks it uses new URL.
            novel_fmt = "http://i{}.pixiv.net/img{}/img/{}/{}_big_p{}.{}"
        else:
            novel_fmt = "http://i{}.pixiv.net/img{}/img/{}/{}_p{}.{}"
        if len(self.preview_url.split('/')[-1].split('_'))==3:
            private_salt=self.preview_url.split('/')[-1].split('_')[1]
            work_id = "{}_{}".format(self.id,private_salt)
        else:
            work_id = self.id
        date_arr = re.split('[- :]', self.upload_time)
        uri_arr = self.preview_url.split('/')
        if len(uri_arr) > 11:
            date_arr = uri_arr[7:13]
        if page==None:
            if int(self.id) > 46270952:
                img_url = single_fmt.format(random.choice([1,2]),date_arr[0],date_arr[1],date_arr[2],
                                            date_arr[3],date_arr[4],date_arr[5],work_id,self.format)
            else:
                img_url = single_fmt.format(random.choice([1,2]),self.img_folder,self.artist_nickname,work_id,self.format)
            try:  #We perform a HEAD GET on the single illust file to check if it is an Ugoira.
                request = urllib2.Request(img_url,headers={'Referer': "http://www.pixiv.net/"})
                request.get_method = lambda: 'HEAD'
                response = urllib2.urlopen(request)
            except urllib2.HTTPError as e:
                img_url = ugoira_fmt.format(random.choice([1,2]),date_arr[0],date_arr[1],date_arr[2],
                                            date_arr[3],date_arr[4],date_arr[5],work_id)
            return img_url
        else:
            if int(self.id) > 46270952:
                return novel_fmt.format(random.choice([1,2]),date_arr[0],date_arr[1],date_arr[2],
                                        date_arr[3],date_arr[4],date_arr[5],work_id,page,self.format)
            else:
                return novel_fmt.format(random.choice([1,2]),self.img_folder,self.artist_nickname,work_id,page,self.format)

    def get_files(self):
        files = []
        if self.novel_pages=='':
            request = urllib2.Request(self.get_full_url(), headers={'Referer': "http://www.pixiv.net/"})
            files.append(request)
        else:
            for i in range(int(self.novel_pages)):
                request = urllib2.Request(self.get_full_url(i), headers={'Referer': "http://www.pixiv.net/"})
                files.append(request)
        return files

class Artist:
    def __init__(self, line):
        self.line = line
        for i in range(len(line)):
            if artist_attributes[i]=='' : continue
            else: setattr(self, artist_attributes[i], line[i])

class Pixiv:
    FEED_URI = "/iphone/new_illust.php"
    BOOKMARK_FEED_URI = "iphone/bookmark_user_new_illust.php"
    ARTIST_URI = "iphone/member_illust.php"
    TAG_URI = "iphone/tags.php"
    ARTIST_BOOKMARK_URI = "/iphone/bookmark_user_all.php"


    def __init__(self, session_id=''):
        self.set_session_id(session_id)

    def set_session_id(self, session_id=''):
        self.session_id = session_id

    def make_request(self, url, query={}):
        query['PHPSESSID'] = self.session_id
        query_string = urllib.urlencode(query)
        url = base_url+url+"?"+query_string
        return urllib2.urlopen(url)

    def get_page(self, request_uri, query={}):
        try:
            data = self.make_request(request_uri, query)
            lines = csv.reader(data)
        except urllib2.HTTPError as e:
            error_string = "Failed to get " + query + " from " + request_uri + "with return " + e.code
            print error_string
            return ''
        works = []
        for line in lines:
            works.append(Work(line))
        return works

    def get_pages(self, request_uri, query={}, start_page=1, end_page=''):
        page = start_page
        works = []
        while True:
            query['p'] = page
            current_works = self.get_page(request_uri, query)
            if end_page and page > end_page: break
            if len(current_works)==0: break
            works.extend(current_works)
            page += 1
        return works

    def get_pages_id(self, request_uri, last_id, query={}):
        page = 1
        works = []
        while True:
            query['p'] = page
            current_works = self.get_page(request_uri, query)
            if len(current_works)==0: break
            for current_work in current_works:
                if int(current_work.id) < last_id: return works
                works.append(current_work)
            page += 1
        return works

    def get_works_id(self, member_id, last_id):
        query = {
            'id': member_id
        }
        works = self.get_pages_id(self.ARTIST_URI, last_id, query)
        return works

    def get_works_all(self, member_id):
        query = {
            'id': member_id
        }
        works = self.get_pages(self.ARTIST_URI, query)
        return works

    def get_feed_pages(self, start_page, end_page):
        works = self.get_pages(self.BOOKMARK_FEED_URI, {}, start_page, end_page)
        return works

    def get_feed_all(self):
        works = self.get_pages(self.BOOKMARK_FEED_URI)
        return works

    def get_tag_all(self, tag):
        query = {
            'tag': tag,
        }
        works = self.get_pages(self.TAG_URI, query)
        return works

    def get_artists_page(self, page=1, private_query='show'):
        query = {
            'rest': private_query,
            'p': page,
        }
        try:
            data = self.make_request("/iphone/bookmark_user_all.php", query)
            lines = csv.reader(data)
        except urllib2.HTTPError as e:
            return ''
        artists = []
        for line in lines:
            artists.append(Artist(line))
        return artists

    def get_artists_all(self, private_query='show'):
        page = 1
        artists = []
        while True:
            current_artists = self.get_artists_page(page, private_query)
            if len(current_artists)==0: break
            artists.extend(current_artists)
            page += 1
        return artists