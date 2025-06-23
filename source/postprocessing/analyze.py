import subprocess
from subprocess import PIPE, STDOUT
import json

class Slither:

    def run_slither(contract, output_json, option):
        opt_str = ' '.join(option)
        proc = subprocess.run(f'slither {opt_str} {contract} --json {output_json}', shell=True, stdout=PIPE, stderr=PIPE, text=True)

        return


    def check_result(result_json_file):
        with open(result_json_file, 'r') as f:
            result_json = json.load(f)
        if not result_json['success']:
            print('Execution of slither is failed. ' + contract)
            return False

        # in this time, only detect reentrancy-eth
        # -> if no result[detectors], no reentrancy-eth
        return not 'detectors' in result_json['results'].keys()

