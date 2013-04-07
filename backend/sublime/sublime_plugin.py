import os
import os.path
import inspect
import traceback
import imp
import sublime
import sys
import importlib

sublime.OP_EQUAL = 0
sublime.OP_NOT_EQUAL = 1
sublime.OP_REGEX_MATCH = 2
sublime.OP_NOT_REGEX_MATCH = 3
sublime.OP_REGEX_CONTAINS = 4
sublime.OP_NOT_REGEX_CONTAINS = 5
def __hack(a, b):
    print "set_timeout not implemented"
sublime.set_timeout = __hack

class Command(object):
    def is_enabled(self, args=None):
        return True

    def is_visible(self, args=None):
        return True

class ApplicationCommand(Command):
    pass

class WindowCommand(Command):
    def __init__(self, wnd):
        self.window = wnd

    def run_(self, kwargs):
        if kwargs and 'event' in kwargs:
            del kwargs['event']

        if kwargs:
            self.run(**kwargs)
        else:
            self.run()

class TextCommand(Command):
    def __init__(self, view):
        self.view = view

    def run__(self, edit_token, kwargs):
        if kwargs and 'event' in kwargs:
            del kwargs['event']

        if kwargs:
            self.run(edit_token, **kwargs)
        else:
            self.run(edit_token)

class EventListener(object):
    pass


def fn(fullname):
    paths = fullname.split(".")
    paths = "/".join(paths)
    for p in sys.path:
        f = os.path.join(p, paths)
        if os.path.exists(f):
            return f
        f += ".py"
        if os.path.exists(f):
            return f
    return None

class __myfinder:
    class myloader(object):
        def load_module(self, fullname):
            if fullname in sys.modules:
                return sys.modules[fullname]
            f = fn(fullname)
            if not f.endswith(".py"):
                m = imp.new_module(fullname)
                m.__path__ = f
                sys.modules[fullname] = m
                return m
            return imp.load_source(fullname, f)

    def find_module(self, fullname, path=None):
        f = fn(fullname)
        if f != None:
            return self.myloader()

sys.meta_path = [__myfinder()]

def reload_plugin(module):
    def cmdname(name):
        if name.endswith("Command"):
            name = name[:-7]
        ret = ""
        for c in name:
            l = c.lower()
            if c != l and len(ret) > 0:
                ret += "_"
            ret += l
        return ret
    print "Loading plugin %s" % module
    try:
        module = importlib.import_module(module)
        for item in inspect.getmembers(module):
            if type(EventListener) != type(item[1]):
                continue

            try:
                cmd = cmdname(item[0])
                if issubclass(item[1], EventListener):
                    inst = item[1]()
                    toadd = getattr(inst, "on_query_context", None)
                    if toadd:
                        sublime.OnQueryContextGlue(toadd)
                elif issubclass(item[1], TextCommand):
                    sublime.register(cmd, sublime.TextCommandGlue(item[1]))
                elif issubclass(item[1], WindowCommand):
                    sublime.register(cmd, sublime.WindowCommandGlue(item[1]))
                elif issubclass(item[1], ApplicationCommand):
                    sublime.register(cmd, sublime.ApplicationCommandGlue(item[1]))
            except:
                print "Skipping registering %s: %s" % (cmd, sys.exc_info()[1])
        if "plugin_loaded" in dir(module):
            module.plugin_loaded()
    except:
        traceback.print_exc()


class MyLogger:
    def write(self, data):
        v = sublime.console()
        try:
            e = v.begin_edit()
            v.insert(e, v.size(), data)
        finally:
            v.end_edit(e)

sys.stdout = sys.stderr = MyLogger()