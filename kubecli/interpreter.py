#!/usr/bin/env python3
from typing import List, Optional
from cmd import Cmd
from kubectl import Kubectl
import readline


class KubeCliInterpreterBase(Cmd):
    doc_header = "Documented internal commands (type /help <topic>):"
    misc_header = "Miscellaneous help topics:"
    undoc_header = "Undocumented internal commands:"

    kubectl_first_commands = []

    def __init__(self, kubectl: Kubectl):
        super().__init__()
        self.kubectl = kubectl
        self._last_command_failed = False
        self.old_delims = None

    def preloop(self) -> None:
        self.old_delims = readline.get_completer_delims()
        readline.set_completer_delims('')

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

    def run_kubectl_command(self, line: str):
        parts = line.split(' ')
        ret = self.kubectl.run(parts)
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
            elif text.startswith('/'):  # Internal command

                if text.count(' ') == 0:
                    self.completion_matches = ["/" + n + " " for n in self.completenames(text[1:])]
                else:
                    cmd, args, _ = self.parseline(text)
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault

                    self.completion_matches = compfunc(text, args)

            else:  # kubectl command

                if text.count(' ') == 0:  # First command
                    self.completion_matches = [n + " " for n in self.kubectl_first_commands if n.startswith(text)]
                else:  # not first command
                    cmd, args, _ = super().parseline(text)  # This is getting out of hand
                    try:
                        compfunc = getattr(self, 'kubectl_complete_' + cmd)
                    except AttributeError:
                        compfunc = self.kubectlcompletedefault

                    self.completion_matches = compfunc(text, args)

        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def completedefault(self, text, args):
        return []

    def kubectlcompletedefault(self, text, args):
        return []

    @property
    def prompt(self) -> str:

        prompt = ""

        if self._last_command_failed:
            prompt += "!"
        else:
            prompt += ""

        ns = self.kubectl.get_current_namespace()
        if ns:
            prompt += f"({ns}) "
        else:
            prompt += "(---) "

        return prompt


class KubeCliInterpreter(KubeCliInterpreterBase):
    kubectl_first_commands = [  # Copied from kubectl help
        'create', 'expose', 'run', 'set', 'explain', 'get', 'edit', 'delete', 'rollout', 'scale', 'autoscale',
        'certificate', 'cluster-info', 'top', 'cordon', 'uncordon', 'drain', 'taint', 'describe', 'logs', 'attach',
        'exec', 'port-forward', 'proxy', 'cp', 'auth', 'diff', 'apply', 'patch', 'replace', 'wait', 'convert',
        'kustomize', 'label', 'annotate', 'completion', 'alpha', 'api-resources', 'api-versions', 'config', 'plugin',
        'version', 'help'
    ]

    def do_setns(self, args):
        'Switch between namesapces'
        if not args:
            print("*** Invalid syntax: a single namespace expected")
        else:
            success = self.kubectl.set_current_namespace(args)
            if not success:
                self._last_command_failed = True

    def do_lsns(self, args):
        'List namespaces'
        namespaces = self.kubectl.get_namespaces()
        for namespace in namespaces:
            print(namespace)

    def complete_setns(self, text, args):
        namespaces = self.kubectl.get_namespaces()

        if args:
            return ["/setns" + ns + " " for ns in namespaces if ns.startswith(args)]
        else:
            return ["/setns" + ns + " " for ns in namespaces]

    def do_exit(self, args):
        'Exit kubecli'
        return True
