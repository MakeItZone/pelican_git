#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Git embedding plugin for Pelican
=================================

This plugin allows you to embbed `git` file into your posts.

"""

from __future__ import unicode_literals
import os, re, logging, hashlib, codecs, copy
from bs4 import BeautifulSoup
import collections
import jinja2
import requests
g_jinja2 = jinja2.Environment(loader=jinja2.PackageLoader('pelican_git', 'templates'))
from pelican_git import __url__

logger = logging.getLogger(__name__)
git_regex = re.compile(r'(\[git:repo\=([^,]+)(:?,file\=([^,]+))(:?,type\=([^,]+))?(:?,branch\=([^,]+))?(:?,hash\=([^,]+))?\])')

gist_template = """<div class="gist">
    {{code}}
</div>"""

GIT_TEMPLATE = 'git.jinja.html'

def git_url(repo, filename, branch="master", githash=None):
    url = "https://github.com/{}/blob/{}{}/{}".format(repo, "" if githash else branch, "" if not githash else githash, filename)
    return url

def rawgit_url(repo, filename, branch="master", githash=None):
    url = "https://raw.githubusercontent.com/{}/{}{}/{}".format(repo, "" if githash else branch, "" if not githash else githash, filename)
    return url

def cache_filename(base, repo, filename, branch="master", githash=None):
    h = hashlib.md5()
    h.update(str(repo).encode())
    h.update(str(filename).encode())
    if githash is not None:
        h.update(githash.encode())
    else:
        h.update(branch.encode())
    return os.path.join(base, '{}.cache'.format(h.hexdigest()))


def get_cache(base, repo, filename, branch="master", githash=None):
    cache_file = cache_filename(base, repo, filename, branch="master", githash=None)
    if not os.path.exists(cache_file):
        return None
    with codecs.open(cache_file, 'rb') as f:
        return f.read().decode('utf-8')


def set_cache(base, repo, filename, branch="master", githash=None, body=""):
    with codecs.open(cache_filename(base, repo, filename, branch, githash), 'wb') as f:
        f.write(body.encode('utf-8'))


def fetch_rawgit(repo, filename, branch="master", githash=None):
    """Fetch the raw content of a file and return it as a string."""
    url = rawgit_url(repo, filename, branch, githash)
    response = requests.get(url)

    if response.status_code != 200:
        raise Exception('Got a bad status looking up gist.')
    body = response.text
    if not body:
        raise Exception('Unable to get the gist contents.')

    return body


def setup_git(pelican):
    """Setup the default settings."""
    pelican.settings.setdefault('GIT_CACHE_ENABLED', False)
    pelican.settings.setdefault('GIT_CACHE_LOCATION',
                                '/tmp/git-cache')

    # Make sure the cache directory exists
    cache_base = pelican.settings.get('GIT_CACHE_LOCATION')
    if not os.path.exists(cache_base):
        os.makedirs(cache_base)


def get_body(res):
    return res


def replace_git_url(generator):
    """Replace gist tags in the article content."""
    template = g_jinja2.get_template(GIT_TEMPLATE)

    should_cache = generator.context.get('GIT_CACHE_ENABLED')
    cache_location = generator.context.get('GIT_CACHE_LOCATION')

    for article in generator.articles:
        for match in git_regex.findall(article._content):
            params = collections.defaultdict(str)
            repo = match[1]
            filename = match[3]
            filetype = match[5] if match[5] else "text"
            branch = match[7]
            githash = match[9]

            params['repo'] = repo
            params['filename'] = filename
            if branch:
                params['branch'] = branch
            if githash:
                params['githash'] = githash

            logger.info('[git]: Found repo {}, filename {}, filetype {}, branch {} and hash {}'.format(repo, filename, filetype, branch, githash))
            logger.info('[git]: {}'.format(params))

            body = None if not should_cache else get_cache(cache_location, **params)

            # Fetch the git
            if not body:
                logger.info('[git]: Git did not exist in cache, fetching...')
                response = fetch_rawgit(**params)
                body = get_body(response)

                if should_cache:
                    logger.info('[git]: Saving git to cache...')
                    cache_params = copy.copy(params)
                    cache_params['body'] = body
                    set_cache(cache_location, **cache_params)
            else:
                logger.info('[git]: Found git in cache.')

            # Create a context to render with
            context = generator.context.copy()
            context.update({
                'code': body,
                'footer': 'full',
                'base': __url__,
                'filename': filename,
                'filetype': filetype,
                'url': git_url(**params)
            })
            replacement = template.render(context)
            article._content = article._content.replace(match[0], replacement)


def register():
    """Plugin registration."""
    from pelican import signals

    signals.initialized.connect(setup_git)

    signals.article_generator_finalized.connect(replace_git_url)
