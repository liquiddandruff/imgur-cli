#!/usr/bin/env python
# -*- coding: utf-8 -*-

import urllib2
import json
from base64 import b64encode
from urllib import urlencode
from cookielib import CookieJar
from os.path import expanduser, exists
from pprint import pprint
from collections import OrderedDict
from argparse import ArgumentParser

USERNAME = ""
PASSWORD = ""
APIKEY_AUTH = "acfe292a432ded08e576f019fb4e34d104df16436"
APIKEY_ANON = "641ff5860e0a7e26e97e48d8ee80d162"
DEBUG = False


class ImgurError(Exception):
    pass


class Imgur(object):
    """
    This class can be used to upload images and manage an account on imgur.com
    """

    base = "api.imgur.com"
    connected = False
    urls = {
            # Anon
            "upload": "/2/upload",
            "image": "/2/image/%s",
            "delete": "/2/delete/%s",
            # Auth
            "signin": "/2/signin",
            "account": "/2/account",
            "account_images": "/2/account/images",
            "account_images_hash": "/2/account/images/%s",
            "account_images_count": "/2/account/images_count",
            "albums": "/2/account/albums",
            "album": "/2/account/albums/%s",
            # Other
            "stats": "/2/stats",
            "credits": "/2/credits",
           }
    
    def __init__(self, apikey_auth=None, apikey_anon=None, print_results=True):
        self.apikey_auth = apikey_auth
        self.apikey_anon = apikey_anon
        self.print_results = print_results
        self.cj = CookieJar()

    def _handle_response(fun):
        def new_f(self, *args, **kwargs):
            try:
                resp = fun(self, *args, **kwargs)
            except urllib2.HTTPError, err:
                raise ImgurError(err)
            else:
                if self.print_results:
                    content = resp.read()
                    try:
                        #pprint(json.loads(content))
                        json_print(json.loads(content))
                    except:
                        pprint(content)
                return resp
        return new_f

    def connection_required(fun):
        """ A decorator that checks if the user is authentified """
        def new_f(self, *args, **kwargs):
            if not self.connected:
                raise ImgurError("You must be connected to perform this"
                        "operation")
            return fun(self, *args, **kwargs)
        return new_f

    def connect(self, username=None, password=None):
        """
        A cookie is created for the authentification
        """
        response = self.request("POST", "signin",
                username=username, password=password)
        debug("Connected.")
        self.connected = True

    def _json(self, data):
        try:
            return json.loads(data)
        except ValueError:
            raise ImgurError("Invalid data")

    @_handle_response
    @connection_required
    def _account(self):
        return self.request("GET", "account")

    @_handle_response
    def _upload(self, filename, url, name, title, caption):
        if filename:
            with open(expanduser(filename), "rb") as f:
                img = b64encode(f.read())
            t = "base64"
        else:
            img = url
            t = "url"
        url = "account_images" if self.connected else "upload"
        return self.request("POST", url, image=img,
                type=t, name=name, title=title, caption=caption)

    @_handle_response
    @connection_required
    def _imgedit(self, hash, title="", caption=""):
        url = self.urls["account_images_hash"] % hash
        return self.request("POST", url=url, title=title, caption=caption)

    @_handle_response
    def _imginfos(self, hash):
        c = self.connected
        url = self.urls["account_images_hash" if c else "image"] % hash
        return self.request("GET", url=url)

    @_handle_response
    def _imgdelete(self, hash):
        c = self.connected
        url = self.urls["account_images_hash" if c else "delete"] % hash
        return self.request("DELETE", url=url)

    @_handle_response
    @connection_required
    def _imgcount(self):
        return self.request("GET", "account_images_count")

    @_handle_response
    @connection_required
    def _list(self):
        return self.request("GET", "account_images")

    @_handle_response
    @connection_required
    def _albums(self, title="", description="", privacy="", layout="",
            count="", page="", create=True):
        if create:
            return self.request("POST", "albums", title=title,
                    description=description, privacy=privacy, layout=layout)
        else:
            return self.request("GET", "albums", count=count, page=page)

    @_handle_response
    @connection_required
    def _albmlist(self, album_id):
        url = self.urls["album"] % album_id
        return self.request("GET", url=url)

    @_handle_response
    @connection_required
    def _albmdelete(self, album_id):
        url = self.urls["album"] % album_id
        return self.request("DELETE", url=url)

    @_handle_response
    @connection_required
    def _albmedit(self, album_id, title="", description="", cover="",
            privacy="", layout="", images="", add_images="", del_images=""):
        url = self.urls["album"] % album_id
        datas = {}
        for k in ("url", "title", "description", "cover", "privacy", "layout",
                "images", "add_images", "del_images"):
            datas[k] = locals()[k]
        return self.request("POST", **datas)

    @_handle_response
    def _limits(self):
        return self.request("GET", "credits")

    def _stats(self, view):
        return self.request("GET", "stats", view=view)

    def request(self, method, key="", url="", headers=None, **params):
        # Send an http request.
        # if key is set, use the url from self.urls[key]
        # else use 'url'
        if not headers:
            headers = {}
        url = "http://" + self.base + (self.urls[key] if key else url) + ".json"
        params["key"] = self.apikey_auth if self.connected else self.apikey_anon
        data = None
        if method in ("POST", "DELETE"):
            for k in params.keys():
                if not params[k]:
                    del params[k]
            data = urlencode(params)
        elif method in ("GET", "DELETE"):
            url = "%s?%s" % (url, urlencode(params))

        opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(self.cj))
        urllib2.install_opener(opener)
        req = urllib2.Request(url, data, headers)
        if not method in ("POST", "GET"):
            req.get_method = lambda: method
        return urllib2.urlopen(req)
    
    def _get_json(self, fun_name, *args, **kwargs):
        return self._json(getattr(self, fun_name)(*args, **kwargs).read())

    def upload_image(self, image="", name="", title="", caption=""):
        """
        Upload an image
        'image' can be a path or an url
        """
        url, file = "", ""
        if not exists(image):
            url = image
        else:
            file = image
        datas = self._get_json("_upload", file, url, name, title, caption)
        return dict_print(datas["images" if self.connected else
            "upload"]["links"])

    def account(self):
        """ Get account infos """
        datas = self._get_json("_account")
        return dict_print(datas["account"])

    def _infos(self, img):
        """ Print the infos of an image """
        return dict_print(OrderedDict(img["image"].items() +
                img["links"].items()))

    def list_image(self):
        """ List all images in account """
        datas = self._get_json("_list")
        imgs = (self._infos(img) for img in datas["images"])
        return "\n *** \n".join(imgs)

    def infos_image(self, hash):
        """ Retrieve informations from an image """
        datas = self._get_json("_imginfos", hash)
        return self._infos(datas["images" if self.connected else "image"])

    def delete_image(self, hash):
        """ Delete an image """
        datas = self._get_json("_imgdelete", hash)
        return datas["images"]["message"] if self.connected else ""

    def edit_image(self, hash, new_title="", new_caption=""):
        """ Edit an image """
        datas = self._get_json("_imgedit", hash, new_title, new_caption)
        return self._infos(datas["images"])

    def count_image(self):
        """ Count all images in the account """
        return self._get_json("_imgcount")["images_count"]["count"]

    def list_albums(self, count=30, page=1):
        """
        List all albums in the account
        """
        datas = self._get_json("_albums", count=count, page=page,
                create=False)
        return "\n *** \n".join(dict_print(alb) for alb in datas["albums"])

    def create_album(self, title="", description="", privacy="", layout=""):
        """
        All values are optional.
        privacy: public/hidden/secret
        layout: blog/horizontal/vertical/grid
        """
        datas = self._get_json("_albums", title, description, privacy, layout)
        return dict_print(datas["albums"])

    def list_album(self, album_id):
        """ List all images in an album """
        datas = self._get_json("_albmlist", album_id)
        imgs = (self._infos(img) for img in datas["albums"])
        return "\n *** \n".join(imgs)

    def delete_album(self, album_id):
        """ Delete an album """
        datas = self._get_json("_albmdelete", album_id)
        return datas["albums"]["message"]

    def edit_album(self, album_id, title="", description="", cover="",
            privacy="", layout="", images="", add_images="", del_images=""):
        """
        Edit an album
        privacy: public/hidden/secret
        layout: blog/horizontal/vertical/grid
        cover: a hash of an image in the account
        'images' replaces all images in the album

        images, add_images and del_images must be a list of hashes,
            or a string formatted like (hash1,hash2,...)
        """
        for k in ("images", "add_images", "del_images"):
            if isinstance(locals()[k], (list, tuple)):
                locals()[k] = "(%s)" % (",".join(str(e) for e in locals()[k]))
        datas = self._get_json("_albmedit", album_id, title, description,
                cover, privacy, layout, images, add_images, del_images)
        imgs = (self._infos(img) for img in datas["albums"])
        return "\n *** \n".join(imgs)

    def stats(self, view="month"):
        """
        View imgur's stats
        view: today|week|month
        """
        return dict_print(self._get_json("_stats", view)["stats"])


def debug(*datas):
    if DEBUG:
        print "DEBUG:", ", ".join(str(d) for d in datas)

def json_print(data, tab=0):
    if isinstance(data, (list, tuple)):
        print
        for elem in data:
            json_print(elem, tab)
            print
    elif isinstance(data, dict):
        print
        for e, d in data.items():
            print "\t"*tab, e,
            json_print(d, tab+1)
    else:
        print "\t"*tab, data 

def dict_print(data):
    def align(l, r, w=80):
        return "%s: %s%s" % (l, (w-len(l))* " ", r)
    w = max(len(e) for e in data.keys())
    return "\n".join(align(k, v, w) for k, v in data.items())

def main():
    i = Imgur(APIKEY_AUTH, APIKEY_ANON, False)

    # Parser definition
    parser = ArgumentParser(description="A command-line utility for imgur.com")
    parser.add_argument("--user")
    parser.add_argument("--password")
    parser.add_argument("--anon", action="store_true", default=False,
            help="Do not authentificate.")
    sparsers = parser.add_subparsers(metavar="ACTION", dest='sp_name', 
            help="Use '%(prog)s action -h' for more help")
    
    up_parser = sparsers.add_parser("upload", help="Upload a file or an url")
    up_parser.add_argument("image", help="A path or an url")
    up_parser.add_argument("-t", "--title")
    up_parser.add_argument("-n", "--name")
    up_parser.add_argument("-c", "--caption")

    imgd_parser = sparsers.add_parser("delete", help="Delete an image")
    imgd_parser.add_argument("hash")

    imgi_parser = sparsers.add_parser("infos", help="Get infos on the image")
    imgi_parser.add_argument("hash")

    imge_parser = sparsers.add_parser("edit", help="Edit an image")
    imge_parser.add_argument("hash")
    imge_parser.add_argument("-t", "--title")
    imge_parser.add_argument("-c", "--caption")

    list_parser = sparsers.add_parser("list", help="List all your images")

    acc_parser = sparsers.add_parser("account", help="Account infos")

    albc_parser = sparsers.add_parser("create-album", help="Create a new album")
    albc_parser.add_argument("-t", "--title")
    albc_parser.add_argument("-d", "--description")
    albc_parser.add_argument("-p", "--privacy", choices=["public", "hidden",
        "secret"])
    albc_parser.add_argument("-l", "--layout", choices=["blog", "horizontal",
        "vertical", "grid"])

    albl_parser = sparsers.add_parser("list-album",
            help="List all albums or all images in an album")
    albl_parser.add_argument("id", nargs="?")

    albd_parser = sparsers.add_parser("delete-album", help="Delete an album")
    albd_parser.add_argument("id")

    stats_parser = sparsers.add_parser("stats", help="Imgur statistics")
    stats_parser.add_argument("-v", "--view",
            choices=["today", "month", "week"])

    # Authentification
    args = parser.parse_args()
    u, p = args.user, args.password
    if u or p:
        if u and not p:
            i.connect(u, PASSWORD)
        elif p and not u:
            i.connect(USERNAME, p)
        else:
            i.connect(u, p)
    elif USERNAME and PASSWORD and not args.anon:
        i.connect(USERNAME, PASSWORD)
    
    # Preparation
    opts = vars(args)
    del opts["user"], opts["password"], opts["anon"]
    if args.sp_name in ("upload", "infos", "delete", "edit", "list", "count"):
        fun = getattr(Imgur, args.sp_name+"_image")
    elif args.sp_name.endswith("album"):
        fun_name = args.sp_name.replace("-", "_")
        if args.sp_name.startswith("list") and not args.id:
            del opts["id"]
            fun_name += "s"
        fun = getattr(Imgur, fun_name)
    else:
        fun = getattr(Imgur, args.sp_name)
    del opts["sp_name"]
    
    # And action.
    print fun(i, **opts)

if __name__ == "__main__":
    main()

