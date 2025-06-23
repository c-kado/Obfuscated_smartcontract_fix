import glob
import json
import re


def main():
    # project_dir <-- run script here
    #  |
    #  + source
    #  |  |
    #  |  + postprocessing
    #  |     |
    #  |     + apply_patch.py
    #  |
    #  + target_contracts

    contracts = glob.glob('target_contracts/*/*/')
    
    for contract in contracts:
        print('\n\n')
        outputs = glob.glob(f'{contract}output/output_[0-9].txt')

        for output in outputs:

            # 1. get fixed_function
            try:
                with open(output, 'r') as f:
                    patch = json.load(f)
                    patch_func = patch['corrected_code'][:-1 if patch['corrected_code'][-1] == '\n' else len(patch['corrected_code'])].split('\n')
            except json.decoder.JSONDecodeError as e:
                print('Fail to load output as json.\nFile: '+output) 
                with open(f'{output}_error.txt', 'w') as f:
                    f.write('Error: '+ str(e))
                continue
            except Exception as e:
                print('other ERRORRRROROROROR')
                with open('error.txt', 'a') as f:
                    f.write(f'{type(e)}: {e}\n')
                continue

            # 2. get original vulnerable contract
            with open(f'{contract}vulnerable.sol', 'r') as f:
                source_code = f.readlines()

            # 3. get position of vulnerable function (with line number)
            with open(f'{contract}vulnerability_info.json', 'r') as f:
                vul_info = json.load(f)
            vul_func_pos = vul_info['vulnerability_position']

            # 4. add the code before vulnerable function
            patched_code = source_code[:vul_func_pos['start']-1]

            # 5. get indent of vulnerable function
            func_indent = vul_info['vulnerable_function_indent']

            # 6. add the fixed function with proper indent
            for patch_line in patch_func:
                patched_code.append(func_indent + patch_line + '\n')

            # 7. add the code after vulnerable function
            patched_code += source_code[vul_func_pos['end']:]


            output_num = re.findall('output_(\d+).txt', output)[0]
            with open(f'{contract}output/fixed_contract_{output_num}.sol', 'w') as f:
                f.writelines(patched_code)
            


if __name__ == '__main__':
    main()
