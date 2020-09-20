#!/usr/bin/env python3
from typing import List, Optional
from cmd import Cmd
from kubectl import Kubectl
import readline


class KubeCliInterpreter(Cmd):
    doc_header = "Documented internal commands (type /help <topic>):"
    misc_header = "Miscellaneous help topics:"
    undoc_header = "Undocumented internal commands:"

    kubectl_first_commands = [  # Copied from kubectl help
        'create', 'expose', 'run', 'set', 'explain', 'get', 'edit', 'delete', 'rollout', 'scale', 'autoscale',
        'certificate', 'cluster-info', 'top', 'cordon', 'uncordon', 'drain', 'taint', 'describe', 'logs', 'attach',
        'exec', 'port-forward', 'proxy', 'cp', 'auth', 'diff', 'apply', 'patch', 'replace', 'wait', 'convert',
        'kustomize', 'label', 'annotate', 'completion', 'alpha', 'api-resources', 'api-versions', 'config', 'plugin',
        'version',
    ]

    def __init__(self, kubectl: Kubectl):
        super().__init__()
        self._kubectl = kubectl
        self._last_command_failed = False
        self.old_delims = None

    def preloop(self) -> None:
        self.old_delims = readline.get_completer_delims()
        readline.set_completer_delims(self.old_delims.replace('-', '').replace('/', ''))

    def postloop(self) -> None:
        readline.set_completer_delims(self.old_delims)

    def onecmd(self, line: str) -> bool:
        self._last_command_failed = False

        if line == 'EOF':
            return True
        elif line.startswith('/'):
            return super().onecmd(line)
        else:
            if line:
                self.run_kubectl_command(line)
            else:
                self.emptyline()

    def parseline(self, line):
        return super().parseline(line[1:])  # onecmd ensures that there is a "/"

    def do_setns(self, args):
        'Switch between namesapces'
        if not args:
            print("*** Invalid syntax: a single namespace expected")
        else:
            success = self._kubectl.set_current_namespace(args)
            if not success:
                self._last_command_failed = True

    def run_kubectl_command(self, line: str) -> bool:
        parts = line.split(' ')
        ret = self._kubectl.run(parts)
        if ret != 0:
            self._last_command_failed = True

    def emptyline(self):
        # Do nothing on an empty line
        pass

    def complete(self, text, state):
        # The first iteration should collect possible completions
        if state == 0:

            if text == '':
                self.completion_matches = ["/" + n + " " for n in self.completenames('')]
                self.completion_matches += self.kubectl_first_commands
            elif text.startswith('/'):
                self.completion_matches = ["/" + n + " " for n in self.completenames(text[1:])]
            elif text.count(' ') == 0:  # not starting with slash
                self.completion_matches = [n + " " for n in self.kubectl_first_commands if n.startswith(text)]
            else:  # not first command
                self.completion_matches = []

        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def do_exit(self, args):
        return True

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
