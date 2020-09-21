#!/usr/bin/env python3
from typing import List, Optional
from cmd import Cmd
from kubectl import Kubectl
import readline
import os
import os.path


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
        readline.set_completer_delims(self.old_delims.replace('/', '').replace('-', ''))

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
        # this function fails silently
        # The first iteration should collect possible completions
        if state == 0:

            origline = readline.get_line_buffer()
            line = origline.lstrip()

            if line == '':
                self.completion_matches = ["/" + n + " " for n in self.completenames('')]
                self.completion_matches += self.kubectl_first_commands
            elif line.startswith('/'):  # Internal command

                if line.count(' ') == 0:
                    self.completion_matches = ["/" + n + " " for n in self.completenames(line[1:])]
                else:
                    cmd, args, _ = self.parseline(line)  # This parseline handles leading slash
                    try:
                        compfunc = getattr(self, 'complete_' + cmd)
                    except AttributeError:
                        compfunc = self.completedefault

                    self.completion_matches = compfunc(text, line, args)

            else:  # kubectl command

                if line.count(' ') == 0:  # First command
                    self.completion_matches = [n + " " for n in self.kubectl_first_commands if n.startswith(line)]
                else:  # not first command
                    cmd, args, _ = super().parseline(line)  # this does not  # This is getting out of hand
                    try:
                        compfunc = getattr(self, 'kubectl_complete_' + cmd)
                    except AttributeError:
                        compfunc = self.kubectlcompletedefault

                    self.completion_matches = compfunc(text, line, args)

        try:
            return self.completion_matches[state]
        except IndexError:
            return None

    def completedefault(self, text, line, args):
        return []

    def kubectlcompletedefault(self, text, line, args):
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

    def do_setns(self, args: str):
        'Switch between namesapces'
        if not args:
            print("*** Invalid syntax: a single namespace expected")
        else:
            success = self.kubectl.set_current_namespace(args)
            if not success:
                self._last_command_failed = True

    def do_lsns(self, args: str):
        'List namespaces'
        namespaces = self.kubectl.list_resource_of_type('namespace')
        for namespace in namespaces:
            print(namespace)

    def complete_setns(self, text: str, line: str, args: str) -> List[str]:
        # This function is only called to complete the args
        namespaces = self.kubectl.list_resource_of_type('namespace')

        if text != args:  # Ensure that we only check the first argument
            return []

        if text:
            return [ns for ns in namespaces if ns.startswith(args) if ns != text]
        else:
            return namespaces

    def _handle_api_resource_type_as_next(self, prefix: str) -> List[str]:
        available_api_resources = self.kubectl.get_available_api_resource_types()

        if prefix:
            return [ns + " " for ns in available_api_resources if ns.startswith(prefix) if ns != prefix]
        else:
            return [ns + " " for ns in available_api_resources]

    def _handle_api_resource_as_next(self, type_: str, prefix: str) -> List[str]:
        available_api_resources = self.kubectl.list_resource_of_type(type_)

        if prefix:
            return [ns for ns in available_api_resources if ns.startswith(prefix) if ns != prefix]
        else:
            return available_api_resources

    def _handle_basic_api_resource_completion(self, text: str, line: str, args: str) -> List[str]:
        argv = args.split(' ')
        if line[-1] == ' ':
            argv.append('')  # ugly hax ftw

        if len(argv) == 1:
            return self._handle_api_resource_type_as_next(text)
        elif len(argv) == 2:
            return self._handle_api_resource_as_next(argv[0], text)

    def _handle_file_completion(self, text: str) -> List[str]:
        dirname = os.path.dirname(text)
        searchdir = dirname if dirname else '.'

        files = os.listdir(searchdir)

        suggestions = []
        for f in files:
            full_path = os.path.join(dirname, f)
            if os.path.isdir(full_path):
                full_path += '/'

            if full_path.startswith(text):
                suggestions.append(full_path)

        return suggestions

    def kubectl_complete_get(self, text: str, line: str, args: str) -> List[str]:
        return self._handle_basic_api_resource_completion(text, line, args)

    def kubectl_complete_delete(self, text: str, line: str, args: str) -> List[str]:
        argv = args.split(' ')
        if (line[-1] == ' ' and argv[-1] == '-f') or (argv[-2] == '-f' and line[-1] != ' '):
            return self._handle_file_completion(text)
        else:  # not entering a filename
            return self._handle_basic_api_resource_completion(text, line, args)

    def kubectl_complete_describe(self, text: str, line: str, args: str) -> List[str]:
        return self._handle_basic_api_resource_completion(text, line, args)

    def kubectl_complete_logs(self, text: str, line: str, args: str) -> List[str]:

        if text != args:  # Ensure that we only check the first argument
            return []

        return self._handle_api_resource_as_next("pod", text)

    def kubectl_complete_drain(self, text: str, line: str, args: str) -> List[str]:

        if text != args:  # Ensure that we only check the first argument
            return []

        return self._handle_api_resource_as_next("node", text)

    def kubectl_complete_cordon(self, text: str, line: str, args: str) -> List[str]:

        if text != args:  # Ensure that we only check the first argument
            return []

        return self._handle_api_resource_as_next("node", text)

    def kubectl_complete_uncordon(self, text: str, line: str, args: str) -> List[str]:

        if text != args:  # Ensure that we only check the first argument
            return []

        return self._handle_api_resource_as_next("node", text)

    def kubectl_complete_apply(self, text: str, line: str, args: str) -> List[str]:
        argv = args.split(' ')
        # about to enter filename or currently entering one
        if (line[-1] == ' ' and argv[-1] == '-f') or (argv[-2] == '-f' and line[-1] != ' '):
            return self._handle_file_completion(text)

    def kubectl_complete_create(self, text: str, line: str, args: str) -> List[str]:
        argv = args.split(' ')
        # about to enter filename or currently entering one
        if (line[-1] == ' ' and argv[-1] == '-f') or (argv[-2] == '-f' and line[-1] != ' '):
            return self._handle_file_completion(text)

    def do_exit(self, args: str) -> bool:
        'Exit kubecli'
        return True
