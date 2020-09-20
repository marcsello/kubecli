#!/usr/bin/env python3
from typing import List, Optional
from cmd import Cmd
from kubectl import Kubectl


class KubeCliInterpreter(Cmd):

    def __init__(self, kubectl: Kubectl):
        super().__init__()
        self._kubectl = kubectl

    def onecmd(self, line: str) -> bool:
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
        if not args:
            print("*** Invalid syntax: a single namespace expected")
        else:
            self._kubectl.set_current_namespace(args)

    @property
    def prompt(self) -> str:
        ns = self._kubectl.get_current_namespace()
        if ns:
            return f"({ns}) "
        else:
            return "(---) "
