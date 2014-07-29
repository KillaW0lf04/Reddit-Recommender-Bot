import os
import json


def load_stopwords(path):
    stopwords = set()
    with open(path, 'r') as fp:
        while True:
            line = fp.readline()
            if line:
                stopwords.add(line[:-1])
            else:
                return stopwords


def load_db_params(filename='db.json'):
    """
    Loads database parameters to perform a connection with from a json formatted
    file (by default 'db.json'. The method will search in the current working directory, the
    directories in the current PYTHONPATH and PATH in that order. If no db.json
    file is found, None will be returned.
    """
    params = None
    search_path = [os.getcwd()]
    if 'PYTHONPATH' in os.environ:
        search_path += os.environ['PYTHONPATH'].split(':')

    if 'PATH' in os.environ:
        search_path += os.environ['PATH'].split(':')

    for directory in search_path:
        if filename in os.listdir(directory):
            # DB-Settings for performing a connection
            with open(os.path.join(directory, filename), 'r') as fp:
                params = json.load(fp)
            break

    return params


def to_csv(target_list):
    var_string = u''
    for item in target_list:
        if type(item) in (str, unicode):
            var_string += u'\'%s\',' % item
        else:
            var_string += u'%s,' % item
    return var_string[:-1]


def search_files(path, relative=False):
    for p1 in os.listdir(path):
        abs_path = os.path.join(path, p1)
        if os.path.isdir(abs_path):
            for p2 in search_files(abs_path):
                if relative:
                    yield unicode(os.path.relpath(p2, path))
                else:
                    yield unicode(p2)
        else:
            if relative:
                yield unicode(os.path.relpath(abs_path, path))
            else:
                yield unicode(abs_path)
