#!/usr/bin/env python3
from typing import List, Optional
from cmd import Cmd
from kubectl import Kubectl


class KubeCliInterpreter(Cmd):

    def __init__(self, kubectl: Kubectl):
        super().__init__()
        self._kubectl = kubectl

    @property
    def prompt(self) -> str:
        ns = self._kubectl.get_current_namespace()
        return f"({ns}) "
