from fbs import platform
from fbs.conf import path, SETTINGS
from glob import glob
from os import makedirs
from os.path import exists, dirname, isfile, join, basename, relpath, splitext
from pathlib import Path
from shutil import copy, copymode

import os

def generate_resources(dest_dir=None, dest_dir_for_base=None, exclude=None):
	if dest_dir is None:
		# Set this default here instead of in the function definition
		# (`def generate_resources(dest_dir=path(...) ...)`) because we can't
		# call path(...) at the module level.
		dest_dir = path('target/resources')
	if dest_dir_for_base is None:
		dest_dir_for_base = dest_dir
	if exclude is None:
		exclude = []
	resources_to_filter = SETTINGS['resources_to_filter']
	kwargs = {'exclude': exclude, 'files_to_filter': resources_to_filter}
	copy_with_filtering(
		path('src/main/resources/base'), dest_dir_for_base, **kwargs
	)
	os_resources_dir = path('src/main/resources/' + platform.name().lower())
	if exists(os_resources_dir):
		copy_with_filtering(os_resources_dir, dest_dir, **kwargs)

def copy_with_filtering(
	src_dir_or_file, dest_dir, replacements=None, files_to_filter=None,
	exclude=None
):
	if replacements is None:
		replacements = SETTINGS
	if files_to_filter is None:
		files_to_filter = []
	if exclude is None:
		exclude = []
	to_copy = _get_files_to_copy(src_dir_or_file, dest_dir, exclude)
	to_filter = _paths(files_to_filter)
	for src, dest in to_copy:
		makedirs(dirname(dest), exist_ok=True)
		if files_to_filter is None or src in to_filter:
			_copy_with_filtering(src, dest, replacements)
		else:
			copy(src, dest)

def get_icons():
	result = {}
	for icons_dir in (
		'src/main/icons/base', 'src/main/icons/' + platform.name().lower()
	):
		for icon_path in glob(path(icons_dir + '/*.png')):
			size = int(splitext(basename(icon_path))[0])
			result[size] = icon_path
	return list(result.items())

def _get_files_to_copy(src_dir_or_file, dest_dir, exclude):
	excludes = _paths(exclude)
	if isfile(src_dir_or_file) and src_dir_or_file not in excludes:
		yield src_dir_or_file, join(dest_dir, basename(src_dir_or_file))
	else:
		for (subdir, _, files) in os.walk(src_dir_or_file):
			dest_subdir = join(dest_dir, relpath(subdir, src_dir_or_file))
			for file_ in files:
				file_path = join(subdir, file_)
				dest_path = join(dest_subdir, file_)
				if file_path not in excludes:
					yield file_path, dest_path

def _copy_with_filtering(
	src_file, dest_file, dict_, place_holder='${%s}', encoding='utf-8'
):
	replacements = []
	for key, value in dict_.items():
		old = (place_holder % key).encode(encoding)
		new = str(value).encode(encoding)
		replacements.append((old, new))
	with open(src_file, 'rb') as open_src_file:
		with open(dest_file, 'wb') as open_dest_file:
			for line in open_src_file:
				new_line = line
				for old, new in replacements:
					new_line = new_line.replace(old, new)
				open_dest_file.write(new_line)
		copymode(src_file, dest_file)

class _paths:
	def __init__(self, paths):
		self._paths = [Path(p).resolve() for p in paths]
	def __contains__(self, item):
		item = Path(item).resolve()
		for p in self._paths:
			if p.samefile(item) or p in item.parents:
				return True
		return False