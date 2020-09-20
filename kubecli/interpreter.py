#!/usr/bin/env python3
from typing import List, Optional
from cmd import Cmd
from kubectl import Kubectl


class KubeCliInterpreter(Cmd):

    def __init__(self, kubectl: Kubectl):
        super().__init__()
        self._kubectl = kubectl
        self._last_command_failed = False

    def onecmd(self, line: str) -> bool:
        self._last_command_failed = False
        if line.startswith('/'):
            return self._process_internal_command(line)
        else:
            return super().onecmd(line)

    def _process_internal_command(self, line: str) -> bool:
        cmd, arg, line = self.parseline(line[1:])
        if cmd:
            try:
                func = getattr(self, 'internal_' + cmd)
            except AttributeError:
                print(f"*** Unknown internal command: {cmd}")
                return False
            return func(arg)
        else:
            print("*** Invalid syntax: internal command expected")
            return False

    def internal_setns(self, args):
        'Switch between namesapces'
        if not args:
            print("*** Invalid syntax: a single namespace expected")
        else:
            success = self._kubectl.set_current_namespace(args)
            if not success:
                self._last_command_failed = True

    def internal_help(self, arg):
        'List available internal commands with "/help" or detailed help with "/help cmd".'
        if arg:
            # XXX check arg syntax
            try:
                doc = getattr(self, 'internal_' + arg).__doc__
                if doc:
                    self.stdout.write("%s\n" % str(doc))
                    return
            except AttributeError:
                pass
            self.stdout.write("%s\n" % str(self.nohelp % (arg,)))
            return
        else:
            names = [a for a in self.get_names() if a.startswith('internal_')]
            cmds_doc = []
            cmds_undoc = []
            for name in names:
                cmd = name[9:]
                if getattr(self, name).__doc__:
                    cmds_doc.append(cmd)
                else:
                    cmds_undoc.append(cmd)
            self.stdout.write("%s\n" % str(self.doc_leader))
            self.print_topics("Documented internal commands (type /? <topic>):", cmds_doc, 15, 80)
            self.print_topics("Undocumented internal commands:", cmds_undoc, 15, 80)

    def complete_internal_names(self, text, *ignored):
        internaltext = 'internal_' + text
        return ['/' + a[9:] for a in self.get_names() if a.startswith(internaltext)]

    def do_help(self, arg: str):
        if arg:
            self.default('help')
        else:
            self.default('help ' + arg)

    def default(self, line: str) -> bool:
        parts = line.split(' ')
        ret = self._kubectl.run(parts)
        if ret != 0:
            self._last_command_failed = True

    def emptyline(self):
        # Do nothing on an empty line
        pass

    @property
    def prompt(self) -> str:

        prompt = ""

        if self._last_command_failed:
            prompt += "!"
        else:
            prompt += ""

        ns = self._kubectl.get_current_namespace()
        if ns:
            prompt += f"({ns}) "
        else:
            prompt += "(---) "

        return prompt
