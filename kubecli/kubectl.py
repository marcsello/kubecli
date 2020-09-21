#!/usr/bin/env python3
from typing import List, Optional

import subprocess
import json


class Kubectl:

    def __init__(self, kubectl_path="/usr/bin/kubectl"):
        self._kubectl_path = kubectl_path

    def _inner_run_json(self, args: list) -> dict:
        result = subprocess.run([self._kubectl_path, *args, '-o', 'json'], capture_output=True, check=True)
        if result.stderr:
            print(result.stderr)
        return json.loads(result.stdout)

    def _inner_run_name(self, args: list) -> List[str]:
        result = subprocess.run([self._kubectl_path, *args, '-o', 'name'], capture_output=True, check=True)
        if result.stderr:
            print(result.stderr)
        return list(filter(None, result.stdout.decode('utf-8').split('\n')))

    ### Public stuff ###
    def run(self, args: list) -> int:
        result = subprocess.run([self._kubectl_path, *args])
        return result.returncode

    def get_current_namespace(self) -> Optional[str]:
        config = self._inner_run_json(['config', 'view'])

        if config['contexts']:
            return config['contexts'][0]['context']['namespace']
        else:
            return None

    def set_current_namespace(self, namespace: str) -> bool:
        return self.run(['config', 'set-context', '--current', f'--namespace={namespace}']) == 0

    def get_available_api_resource_types(self) -> List[str]:
        return self._inner_run_name(['api-resources'])

    def list_resource_of_type(self, type_: str) -> List[str]:
        resources = self._inner_run_name(['get', type_])
        return [res.split('/')[-1] for res in resources]
