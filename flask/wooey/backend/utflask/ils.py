import os


def find_files(basepath, extension=''):

    found_files = []

    for subdir, dirs, files in os.walk(basepath):
        for file in files:
            if file.endswith(extension):
                file_path = os.path.join(subdir, file)
                found_files.append(file_path)
    return found_files
