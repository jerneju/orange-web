# Regex objects for browser OS detection
import re

from django.conf import settings
from django.core.urlresolvers import reverse
from django.http import HttpResponse
from django.shortcuts import render
from os import path

p_win = re.compile(r'.*[Ww]in.*')
p_mac = re.compile(r'^(?!.*(iPhone|iPad)).*[Mm]ac.*')
p_linux = re.compile(r'.*[Ll]inux.*')
VERSION_RE = re.compile(r"Orange3-([\d\.]+)\.")

TABS = [
    dict(icon="windows", title="Windows", os="windows"),
    dict(icon="apple", title="macOS", os="macos"),
    dict(icon="linux", title="Linux / Source", os="linux"),
]


class OS:
    windows = "windows"
    macos = "macos"
    linux = "linux"
    unknown = ""


def detect_os(user_agent):
    if re.match(p_win, user_agent):
        return OS.windows
    elif re.match(p_mac, user_agent):
        return OS.macos
    elif re.match(p_linux, user_agent):
        return OS.linux
    else:
        return ''


def download(request):
    title = "Download"
    os = detect_os(request.META.get('HTTP_USER_AGENT', ''))

    if os == OS.macos:
        return download_macos(request, title)
    elif os == OS.linux:
        return download_linux(request, title)
    else:
        return download_windows(request, title)


def download_windows(request, title=None):
    if title is None:
        title = "Download for Windows"

    return render(request, "download/windows.html", dict(
        title=title,
        tabs=TABS,
        os=OS.windows,
        classic=_get_download("orange3-win32-installer"),
        standalone=_get_download("orange3-win32-installer-standallone"),
    ))


def download_macos(request, title=None):
    if title is None:
        title = "Download for macOS"

    return render(request, "download/macos.html", dict(
        title=title,
        tabs=TABS,
        os=OS.macos,
        bundle=_get_download("bundle-orange3")
    ))


def download_linux(request, title=None):
    if title is None:
        title = "Download for GNU/Linux"

    return render(request, "download/linux.html", dict(
        title=title,
        tabs=TABS,
        os=OS.linux,
    ))


def _get_version(filename):
    try:
        return VERSION_RE.findall(filename)[0]
    except IndexError:
        return "(unknown version)"


def _get_download(key):
    downloads = _download_choices()
    filename = downloads[key]
    return dict(
        filename=filename,
        url=reverse('download') + 'files/' + filename,
        version=_get_version(filename)
    )


def _download_choices(os=None):
    downloads = {}

    for key, value in _download_set_patterns("win"):
        if key == 'WIN_SNAPSHOT':
            downloads['win27'] = '{0}-py2.7.exe'.format(value)
            downloads['date'] = value[-10:]
        elif key == 'WIN_PYTHON_SNAPSHOT':
            downloads['winw27'] = '{0}-py2.7.exe'.format(value)
        elif key == 'ADDON_BIOINFORMATICS_SNAPSHOT':
            downloads['bio27'] = '{0}-py2.7.exe'.format(value)
        elif key == 'ADDON_TEXT_SNAPSHOT':
            downloads['text27'] = '{0}-py2.7.exe'.format(value)
        elif key == 'SOURCE_SNAPSHOT':
            downloads['source'] = value

    for key, value in _download_set_patterns(None):
        if key == "WIN32_ORANGE3_DAILY":
            downloads["orange3-win32-installer"] = value
        elif key == "WIN32_ORANGE3_STANDALONE_DAILY":
            downloads["orange3-win32-installer-standallone"] = value

    for key, value in _download_set_patterns("mac"):
        if key == 'MAC_DAILY':
            downloads['mac'] = value
        if key == 'MAC_ORANGE3_DAILY':
            downloads['bundle-orange3'] = value
            try:
                downloads['version'] = \
                    re.findall("Orange3-(.*)\.dmg", value)[0]
            except IndexError:
                downloads['version'] = 'unknown'

    return downloads


def _download_set_patterns(os=None):
    if path.isdir(settings.DOWNLOAD_DIR):
        if os is None:
            filename = path.join(settings.DOWNLOAD_DIR, "filenames.set")
        else:
            filename = settings.DOWNLOAD_SET_PATTERN % os

        if not path.isfile(filename):
            return

        with open(filename, 'rt') as f:
            for line in f:
                key, value = line.split('=', 1)
                yield key.strip(), value.strip()


def latest_version(request):
    version = _download_choices('mac').get('version', '')
    return HttpResponse(version, content_type="text/plain")
