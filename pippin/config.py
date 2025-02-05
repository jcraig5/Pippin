import configparser
import inspect
import os
import logging
import hashlib
import shutil
import os
import shutil
import stat


def singleton(fn):
    instance = None

    def get(*args, **kwargs):
        nonlocal instance
        if instance is None:
            instance = fn(*args, **kwargs)
        return instance
    return get

@singleton
def get_config():
    filename = os.path.abspath(os.path.dirname(inspect.stack()[0][1]) + "/../cfg.ini")
    config = configparser.ConfigParser()
    config.read(filename)
    return config


def get_output_dir():
    output_dir = get_config()['OUTPUT']['output_dir']
    if output_dir.startswith("$"):
        output_dir = os.path.expandvars(output_dir)
    elif not output_dir.startswith("/"):
        output_dir = os.path.abspath(os.path.dirname(inspect.stack()[0][1]) + "/../" + output_dir)
    return output_dir


def get_output_loc(path):
    if "$" in path:
        path = os.path.expandvars(path)
    if path.startswith("/"):
        return path
    else:
        return os.path.join(get_output_dir(), path)


def get_hash(input_string):
    return hashlib.sha256(input_string.encode('utf-8')).hexdigest()

@singleton
def get_logger():
    return logging.getLogger("pippin")


def mkdirs(path):
    if not os.path.exists(path):
        os.makedirs(path, exist_ok=True, mode=0o775)
        chown_dir(path)


def copytree(src, dst, symlinks=False, ignore=None):
    lst = os.listdir(src)
    if ignore:
        excl = ignore(src, lst)
        lst = [x for x in lst if x not in excl]
    for item in lst:
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if symlinks and os.path.islink(s):
            if os.path.lexists(d):
                os.remove(d)
                os.symlink(os.readlink(s), d)
                try:
                    st = os.lstat(s)
                    mode = stat.S_IMODE(st.st_mode)
                    os.lchmod(d, mode)
                except:
                    pass # lchmod not available
        elif os.path.isdir(s):
            copytree(s, d, symlinks, ignore)
        else:
            shutil.copy2(s, d)


def chown_dir(directory):
    global_config = get_config()
    logger = get_logger()
    try:
        shutil.chown(directory, group=global_config["SNANA"]["group"])
    except Exception as e:
        logger.debug(str(e))
        return
    for root, dirs, files in os.walk(directory):
        for d in dirs:
            try:
                shutil.chown(os.path.join(root, d), group=global_config["SNANA"]["group"])
            except Exception:
                logger.debug(f"Chown error: {os.path.join(root, d)}")
        for f in files:
            try:
                shutil.chown(os.path.join(root, f), group=global_config["SNANA"]["group"])
            except Exception:
                logger.debug(f"Chown error: {os.path.join(root, f)}")


if __name__ == "__main__":
    c = get_config()
    print(c.sections())
    print(c.get("SNANA", "sim_dir"))
    print(c["OUTPUT"].getint("ping_frequency"))
