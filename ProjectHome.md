imgur-cli is a python script that allows you to upload images and manage your account from a shell.

It can also be used as a module for a graphical app, or anything.

## Download ##

Just download the script from the repository and it's ready to go :
```bash

svn checkout http://imgur-cli.googlecode.com/svn/trunk/ imgur-cli
mv imgur-cli/imgur.py ~/bin/imgur
chmod +x !$
rmdir imgur-cli```


---


## Usage ##

Basically, you type `imgur action arguments` and that's all.
`imgur -h` gives you a list of actions, and `imgur action -h` gives you a list of arguments.
### Anonymous ###

You can upload and delete an image anonymously :

#### upload ####

```
imgur upload <path> -t title -n name -c caption
imgur upload <url> ...
```

#### delete ####
```
imgur delete <hash>
```
where `hash` is the delete hash given when you uploaded the image (a link of the form http://imgur.com/delete/hash).

#### informations of an image ####
```
imgur infos <hash>
```

### Authentication ###

If you have an account on imgur, you can either put your name and password at the beginning of the script
```
USERNAME = "foo"
PASSWORD = "bar"
```
or you can use arguments `--user` and `--password`. If you don't like to give your password in plain text, which is understandable, you can use `--ask-pass`.

When you have your login in the script and you want to upload something anonymously, use `--anon`.

You can then manage your images with `upload`, `delete`, `edit`, `list` and your albums with `create-album`, `edit-album`, `delete-album`, `list-album`, `list-albums`.

There is not much more to say, see the help for more informations.


---


## Known bugs ##

### Delete ###

You can't delete a picture when authentified, by using `imgur delete hash` (it raises a HTTP 500 error). I don't know why and how to fix it now, so you have to use `imgur --anon delete <delete_hash>` instead. (delete\_hash can be found with `imgur infos`.

### Order ###

Ordering albums or images in an album (order-album and order-albums) with a list of hashes or id raises a Bad Request error.
I don't know how to fix it but I'm working on it, sort of :/