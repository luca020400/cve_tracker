#!/usr/bin/python3

import functools
import json
import os
import sys

import utils

from flask import Flask, abort, flash, jsonify, redirect, render_template, request, session
from flask.ext.github import GitHub

configfile = "options.json"
devicefile = "kernels.json"
dbfile = "sqlite.db"

db_version = 3
forceDBUpdate = False

status_ids = {}
allCVEs = {}
kernels = {}

app = Flask(__name__)

if not os.path.isfile(configfile):
  print("Could not find " + configfile + " aborting!")
  sys.exit()

with open(configfile) as config_file:
  config = json.load(config_file)

with open(devicefile) as device_file:
  devices = json.load(device_file)

app.config['GITHUB_CLIENT_ID'] = config['githubclientid']
app.config['GITHUB_CLIENT_SECRET'] = config['githubsecret']
app.secret_key = config['githubsecret']

github = GitHub(app)

def is_authenticated():
  return 'authenticated' in session and session['authenticated'] == True

def authenticated(json_error=False):
  def actual_decorator(fn):
    @functools.wraps(fn)
    def too_deep(*args, **kwargs):
      print(session)
      if not is_authenticated():
        if json_error:
          return jsonify({'error': 'not logged in'})
        return redirect('/login')
      else:
        return fn(*args, **kwargs)
    return too_deep
  return actual_decorator

@app.route("/")
def index():
    return render_template('index.html', kernels = kernels, logged_in = is_authenticated())

@app.route("/<string:k>")
def kernel(k):
    kernel = utils.getKernelByRepo(k)
    if kernel is None:
      abort(404)
    patches = utils.getPatchesByRepo(k)
    patched = utils.getNumberOfPatchedByRepoId(k)
    if k in devices:
      devs = devices[k]
    else:
      devs = ['No officially supported devices!']
    return render_template('kernel.html', kernel = kernel, patched = patched, cves = allCVEs, status_ids = status_ids, patches = patches, devices = devs)

@app.route("/update", methods=['POST'])
@authenticated(json_error=True)
def update():
  r = request.get_json()
  k = r['kernel_id'];
  c = r['cve_id'].split(',');
  s = r['status_id'];
  utils.updatePatchStatus(k, c, s)
  patched = utils.getNumberOfPatchedByRepoId(k)
  return jsonify({'error': 'success', 'patched': patched})

@app.route("/login")
def login():
  return github.authorize(scope='read:org')

@app.route("/logout")
def logout():
    del session['authenticated']
    flash('Logged out!')
    return redirect('/')


@app.route("/callback")
@github.authorized_handler
def authorized(oauth_token):
  if oauth_token is None:
    flash('Failed to log in')
    return redirect('/')

  # hack - github isn't ready for us to use the api yet, but we need it
  github.access_token_getter(lambda:oauth_token)
  orgs = github.get('user/orgs')

  for org in orgs:
    if org['login'] == 'CyanogenMod' or org['login'] == 'LineageOS':
      session['authenticated'] = True
      flash('Logged in! Returning to homepage...')
      return redirect('/')

  flash('Not a member of LineageOS on Github')
  return redirect('/')

if __name__ == "__main__":
  if not os.path.isfile(dbfile):
    print("No database found. Creating one...")
    utils.createDB()

  if utils.getDBVersion() < db_version:
    print("Database version out of date, updating...")
    utils.updateDB()
    utils.getKernelTableFromGithub()

  if "port" in config:
    port=config['port']
  else:
    port=5000

  status_ids = utils.getStatusIDs()
  allCVEs = utils.getCVEs()
  kernels = utils.getKernelsFromDB()

  # TODO: add something to check github every day for new kernel repos and call getKernelTableFromGithub()
  app.run(host="0.0.0.0", debug=True, port=port)
