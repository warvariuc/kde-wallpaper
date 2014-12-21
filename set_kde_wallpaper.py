#!/usr/bin/env python3
"""
There is no API no change the wallpaper, so we do it manually
https://bugs.kde.org/show_bug.cgi?id=217950

"""
__author__ = "Victor Varvariuc <victor.varvariuc@gmail.com>"

import argparse
import os
import sys
import time
import shlex
import subprocess

from distutils import dir_util, file_util
import dbus
from PyKDE4 import kdecore


BASE_DIR = os.path.abspath(os.path.dirname(__file__))


def make_abs_path(file_path):
    file_path = os.path.expanduser(file_path)
    if os.path.isabs(file_path):
        return os.path.normpath(file_path)
    file_path = os.path.join(BASE_DIR, file_path)
    file_path = os.path.abspath(file_path)
    return file_path


def copy_file(src_path, dst_dir_path):
    """Copy a single file to the given directory.

    Args:
        src_path (str): path of the file to copy
        dst_dir_path (str): path of the destination directory
    Returns:
        str: path of the copied file
    """
    src_path = make_abs_path(src_path)
    dst_dir_path = make_abs_path(dst_dir_path)
    print('Copying file %r< to %r.' % (src_path, dst_dir_path))
    file_name = os.path.split(src_path)[1]
    dst_path = os.path.join(dst_dir_path, file_name)
    dir_util.mkpath(dst_dir_path)
    file_util.copy_file(src_path, dst_path)

    return dst_path


def call(command, message):
    """Run a [terminal] command.

    Args:
        command (str, callable): a command to run via subprocess or a callable to call passing
            it main_window as an argument
        message (str): additional text to print before executing the command
    """
    if not command:
        return

    if message:
        print(message)

    if isinstance(command, str):
        command = shlex.split(command)
    else:
        assert isinstance(command, (tuple, list))

    print(" ".join(map(shlex.quote, command)))

    subprocess.call(command)


arg_parser = argparse.ArgumentParser(
    description='Set as wallpaper image with the given path.')
arg_parser.add_argument('path', help='Path to the image')
args = arg_parser.parse_args()

image_path = os.path.join(BASE_DIR, args.path)

if not os.path.isfile(image_path):
    print("File %r does not exist" % image_path)
    sys.exit(1)


# http://api.kde.org/frameworks-api/frameworks5-apidocs/plasma-framework/html/classPlasma_1_1Applet.html
PLASMA_DESKTOP_APPLETSRC_PATH = '~/.kde/share/config/plasma-desktop-appletsrc'

wallpaper_path = copy_file(image_path, '~/.kde/share/wallpapers/')

activity_manager = dbus.SessionBus().get_object(
    'org.kde.ActivityManager', '/ActivityManager/Activities')
current_activity_id = dbus.Interface(
    activity_manager, 'org.kde.ActivityManager.Activities').CurrentActivity()

print('Patching %s' % PLASMA_DESKTOP_APPLETSRC_PATH)
konf_path = make_abs_path(PLASMA_DESKTOP_APPLETSRC_PATH)
# http://api.kde.org/pykde-4.7-api/kdecore/KConfig.html
konf = kdecore.KConfig(konf_path, kdecore.KConfig.SimpleConfig)
containments = konf.group('Containments')
for group_name in containments.groupList():
    group = containments.group(group_name)
    # http://api.kde.org/pykde-4.7-api/kdecore/KConfigGroup.html
    if (group.readEntry('activity') == 'Desktop' and
            group.readEntry('activityId') == current_activity_id):
        group.group('Wallpaper').group('image').writeEntry('wallpaper', wallpaper_path)


call('kquitapp plasma-desktop', 'Stopping Plasma')
time.sleep(2)  # give time for the app to shut down
call('kstart plasma-desktop', 'Starting Plasma')
# plasma = dbus.SessionBus().get_object('org.kde.plasma-desktop', '/MainApplication')
# dbus.Interface(plasma, 'org.kde.KApplication').reparseConfiguration()
