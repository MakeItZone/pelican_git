#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Test pelican-git
=================

Unit testing for pelican_git

"""

from __future__ import unicode_literals
import os

from pelican_git import plugin as gitplugin
from mock import patch
import requests.models
from bs4 import BeautifulSoup

TEST_REPO = 'minhhh/wiki'
TEST_FILENAME = 'sample.md'
TEST_BRANCH = 'develop'
TEST_HASH = '08dab572cd'
# https://github.com/minhhh/wiki/blob/master/sample.md
# https://github.com/minhhh/wiki/blob/08dab572cd/sample.md
# https://raw.githubusercontent.com/minhhh/wiki/08dab572cdb5085f252baba51e55904c5381d86d/sample.md
# https://raw.githubusercontent.com/minhhh/wiki/master/sample.md


def test_git_url():
    repo = TEST_REPO
    filename = TEST_FILENAME
    hash = TEST_HASH

    # Test without a branch or hash
    url = gitplugin.git_url(**{'repo': repo, 'filename': filename})
    assert filename in url

    # Test with a branch
    url = gitplugin.git_url(**{'repo': repo, 'filename': filename, 'branch': 'develop'})
    assert url.endswith(filename)
    assert 'develop' in url

    # Test with a hash
    url = gitplugin.git_url(**{'repo': TEST_REPO, 'filename': filename, 'hash': hash})
    assert url.endswith(filename)
    assert hash in url


def test_cache_filename():
    repo = TEST_REPO
    filename = TEST_FILENAME
    path_base = '/tmp'

    # Test without a branch
    path = gitplugin.cache_filename(path_base, repo, filename)
    assert path.startswith(path_base)
    assert path.endswith('.cache')

    # Test with branch
    path = gitplugin.cache_filename(path_base, repo, filename, 'develop')
    assert path.startswith(path_base)
    assert path.endswith('.cache')


def test_set_get_cache():
    repo = TEST_REPO
    filename = TEST_FILENAME
    path_base = '/tmp'
    body = """Some gist body"""

    # Make sure there is no cache
    for f in (gitplugin.cache_filename(path_base, repo, filename), ):
        if os.path.exists(f):
            os.remove(f)

    # Get an empty cache
    cache_file = gitplugin.get_cache(path_base, repo, filename)
    assert cache_file is None

    # Set a cache file
    gitplugin.set_cache(path_base, repo, filename, body=body)

    # Fetch the same file
    cached = gitplugin.get_cache(path_base, repo, filename)
    assert cached == body


def test_regex():
    content = '[git:repo=minhhh/wiki,file=sample.md]'

    matches = gitplugin.git_regex.findall(content)
    match = matches[0]
    assert match[1] == 'minhhh/wiki'
    assert match[3] == 'sample.md'


def test_fetch_git():
    """Ensure fetch_gist returns the response content as a string."""
    repo = TEST_REPO
    filename = TEST_FILENAME
    CODE_BODY = "code"
    with patch('requests.get') as get:
        return_response = requests.models.Response()
        return_response.status_code = 200
        return_response._content = CODE_BODY.encode()
        get.return_value = return_response
        assert gitplugin.fetch_git(repo, filename) == CODE_BODY


def test_get_body():
    res = """<div class="file">
    <div class="meta clearfix">
    <div class="info file-name">
    <span>
        22 lines (15 sloc)
    </span>
    <span class="meta-divider">
    </span>
    <span>
        0.308 kb
    </span>
    </div>
    <div class="actions">
    <div class="button-group">
        <a class="minibutton " href="/minhhh/wiki/raw/master/sample.md" id="raw-url">
        Raw
        </a>
        <a class="minibutton js-update-url-with-hash" href="/minhhh/wiki/blame/master/sample.md">
        Blame
        </a>
        <a class="minibutton " href="/minhhh/wiki/commits/master/sample.md" rel="nofollow">
        History
        </a>
    </div>
    <!-- /.button-group -->
    <a aria-label="You must be signed in to make or propose changes" class="octicon-button disabled tooltipped tooltipped-w" href="#">
        <span class="octicon octicon-pencil">
        </span>
    </a>
    <a aria-label="You must be signed in to make or propose changes" class="octicon-button danger disabled tooltipped tooltipped-w" href="#">
        <span class="octicon octicon-trashcan">
        </span>
    </a>
    </div>
    <!-- /.actions -->
    </div>
    <div class="blob instapaper_body" id="readme">
    <article class="markdown-body entry-content" itemprop="mainContentOfPage">
    <h1>
        <a aria-hidden="true" class="anchor" href="#first-level-title" name="user-content-first-level-title">
        <span class="octicon octicon-link">
        </span>
        </a>
        First level title
    </h1>
    <p>
        Notes from
        <a href="https://github.com/minhhh/wiki">
        link
        </a>
        .
    </p>
    <h2>
        <a aria-hidden="true" class="anchor" href="#second-level-title" name="user-content-second-level-title">
        <span class="octicon octicon-link">
        </span>
        </a>
        Second level title
    </h2>
    <p>
        Quote some code with correct syntax highlight
    </p>
    <div class="highlight highlight-python">
        <pre><span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="p">[</span><span class="mi">0</span><span class="p">,</span> <span class="mi">1</span><span class="p">,</span> <span class="mi">2</span><span class="p">,</span> <span class="mi">3</span><span class="p">,</span> <span class="mi">4</span><span class="p">,</span> <span class="mi">5</span><span class="p">]:</span>
        <span class="k">print</span> <span class="n">i</span><span class="o">**</span><span class="mi">2</span>

    <span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="nb">range</span><span class="p">(</span><span class="mi">6</span><span class="p">):</span>
        <span class="k">print</span> <span class="n">i</span><span class="o">**</span><span class="mi">2</span>
    </pre>
    </div>
    <h3>
        <a aria-hidden="true" class="anchor" href="#third-level-title" name="user-content-third-level-title">
        <span class="octicon octicon-link">
        </span>
        </a>
        Third level title
    </h3>
    <div class="highlight highlight-python">
        <pre><span class="k">for</span> <span class="n">i</span> <span class="ow">in</span> <span class="nb">xrange</span><span class="p">(</span><span class="mi">6</span><span class="p">):</span>
        <span class="k">print</span> <span class="n">i</span><span class="o">**</span><span class="mi">2</span>
    </pre>
    </div>
    </article>
    </div>
    </div>
    """
    body = gitplugin.get_body(res)
    assert body is not None


def test_fetch_git_sample():
    """Ensure fetch_gist returns the response content as a string."""
    repo = TEST_REPO
    filename = TEST_FILENAME

    response = gitplugin.fetch_git(repo, filename)
    soup = BeautifulSoup(response, "html.parser")
    res = soup.find('div', 'file')
    assert res is not None

