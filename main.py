#  _____
# |  ___|_ _ ___ _ __ ___    __ _  __ _
# | |_ / _` / __| '_ ` _ \  / _` |/ _` |
# |  _| (_| \__ \ | | | | || (_| | (_| |
# |_|  \__,_|___/_| |_| |_(_)__, |\__,_|
#                           |___/

# © 2020-today Fasm.ga
# Protected by Apache License.
# https://github.com/fasm-ga/redirects

############################### Packages

from flask import Flask, make_response, redirect, render_template, request, send_from_directory
import hashlib, pymongo, ssl
import gevent.pywsgi

############################### Setting up basic things

app = Flask("redirects")

database = pymongo.MongoClient("<REDACTED>", ssl_cert_reqs = ssl.CERT_NONE)
db = database["fasmga"]
urls = db["urls"]

############################### Functions

def getLang():
    if request.cookies.get("lang"):
        import json
        try:
            with open(app.root_path + "/translations/" + request.cookies.get("lang") + ".json", "r") as file:
                translation = json.load(file)
                return translation
        except:
            with open(app.root_path + "/translations/en.json", "r") as file:
                translation = json.load(file)
                return translation
    else:
        import json
        with open(app.root_path + "/translations/en.json", "r") as file:
            translation = json.load(file)
            return translation

def getError(error):
    translations = getLang()
    return translations["errors"][str(error)]

############################### Settings

@app.route("/settings", methods = ["POST", "GET"], strict_slashes = False)
def settings():
	if request.method == "GET":
		return render_template("settings.html", lang = getLang())
	elif request.method == "POST":
		if not request.form["language"]: return "nope"
		if not request.form["language"] in ["en", "it", "pl"]: return "nope"
		response = make_response(redirect("/settings"))
		response.set_cookie("lang", request.form["language"], 15780000)
		return response

############################### Pages

@app.route("/")
def main():
	return redirect("https://www.fasmga.org")

@app.route('/<id>', strict_slashes = False)
def redirectURL(id):
	try:
		url = urls.find_one({ "ID": id })
		redirectURL = url["redirect_url"]
		password = url["password"]
		nsfw = url["nsfw"]
		clicks = url["clicks"]
		if redirectURL:
			if password != "":
				return render_template("password.html", id = id, lang = getLang())
			else:
				if request.args.get("nsfwConsent"):
					if request.args.get("nsfwConsent") == "yes":
						urls.find_one_and_update({ "ID": id }, { "$set": { "clicks": clicks + 1 }})
						return redirect(redirectURL, 302)
					else:
						if nsfw == False:
							urls.find_one_and_update({ "ID": id }, { "$set": { "clicks": clicks + 1 }})
							return redirect(redirectURL, 302)
						else:
							return render_template("nsfw.html", lang = getLang(), url = id)
				else:
					if nsfw == False:
						urls.find_one_and_update({ "ID": id }, { "$set": { "clicks": clicks + 1 }})
						return redirect(redirectURL, 302)
					else:
						return render_template("nsfw.html", lang = getLang(), url = id)
		else:
			return render_template("error.html", code = "404", error = getError(802), lang = getLang())
	except:
		return render_template("error.html", code = "404", error = getError(802), lang = getLang())

@app.route("/check_password", methods = ["POST"], strict_slashes = False)
def check_password():
	if not request.form["id"]: return redirect("/")
	if not request.form["password"]: return redirect("/")
	url = urls.find_one({ "ID": request.form["id"] })
	if not url: return redirect("/")
	if not hashlib.sha512(request.form["password"].encode()).hexdigest() == url["password"]: return render_template("error.html", lang = getLang(), code = "401", error = getError(801))
	urls.find_one_and_update({ "ID": request.form["id"] }, { "$set": { "clicks": url["clicks"] + 1 }})
	if url["nsfw"] == False:
		return redirect(url["redirect_url"])
	else:
		return render_template("nsfw_password.html", lang = getLang(), url = url["redirect_url"])

############################### Assets

@app.route("/favicon.ico", strict_slashes = False)
def favicon():
	return send_from_directory(app.root_path + "/assets", "favicon.ico")

@app.route("/robots.txt", strict_slashes = False)
def robots():
	return send_from_directory(app.root_path + "/assets", "robots.txt")

############################### Errors

@app.errorhandler(404)
def error_404(error):
	return render_template("error.html", lang = getLang(), code = "404", error = getError(404))

@app.errorhandler(405)
def error_405(error):
	return render_template("error.html", lang = getLang(), code = "405", error = getError(405))

@app.errorhandler(500)
def error_500(error):
	return render_template("error.html", lang = getLang(), code = "500", error = getError(500))

############################### Running the application

http_server = gevent.pywsgi.WSGIServer(('0.0.0.0', 2001), app, certfile = "<REDACTED>", keyfile = "<REDACTED>")
http_server.serve_forever()
