#!/usr/bin/env python3
from interpreter import KubeCliInterpreter
from kubectl import Kubectl


def main():
    i = KubeCliInterpreter(Kubectl())
    i.cmdloop()


if __name__ == '__main__':
    main()
