import re
import json
import glob

REENTRANCY_CAUSE_DSCR = ['External calls', 'External calls sending eth', 'State variables written after the call(s)']

def main():
    
    contracts = glob.glob('../../target_contracts/*/*/')

    for contract in contracts:
        with open(f'{contract}resultSlither.txt', 'r') as f:
            result_lns = f.readlines()

        vul, vul_pos, vul_file = get_vul_info(result_lns[0])
       
        adjust_result = adjust_slither_result(vul, vul_pos, vul_file, result_lns)
        with open(f'{contract}adjustResultSlither.txt', 'w') as f:
            for ln in adjust_result:
                f.write(ln)

        function_indent = extract_vul_function(contract, vul_pos)
        save_vul_info(vul, vul_pos, vul_file, function_indent, contract)


def get_vul_info(info_line):
    print('\n\nGet vul info')
    name = re.search('\w*', info_line).group()
    print('Vul type: ' + name)

    # vul_pos = [xxx, yyy],  There is a vulnerability in xxx-yyy.
    position = [int(s) for s in re.findall('\d+', re.findall(r'#\d+-\d+', info_line)[-1])]
    print(f'Vul position: {position[0]} - {position[1]}')

    file_name = re.findall('\s\((.*)#\d+-\d+\):', info_line)[0]
    print(f'Vul file: {file_name}')
 
    return name, position, file_name



def adjust_slither_result(vul, pos, file, result_lns):
    print('Adjust Slither result')
    new_result = [f'{vul} is in the code.\n']

    cause_count = 0
    for result_ln in result_lns[1:]:
        if result_ln.startswith('\t- '):
            cause_ln = int(result_ln.split(f'{file}#')[1][:-2])
            new_result.append(result_ln.replace(f'({file}#{cause_ln})\n','') + f'(in line {cause_ln-pos[0]+1})\n')
        elif result_ln.startswith('\t\t'):
            # description for sub-cause 
            # i.e.: the cause line in the called function (different with vulnerable function)
            continue
        elif result_ln[1:-2] in REENTRANCY_CAUSE_DSCR:
            new_result.append(result_ln)
            cause_count += 1
            continue
        else:
            # ex. xxx can be used in cross function reentrancy ?
            print('further possibility: ')
            print(result_ln)
            break

    return new_result



def extract_vul_function(contract, pos):
    print('Extract vul function from source code')
    # open sol file
    with open(f'{contract}vulnerable.sol', 'r') as f:
        vul_source = f.readlines()

    # extract only function following vul position
    vul_func = vul_source[pos[0]-1: pos[1]]

    # get function indent
    idx = vul_func[0].find('f') # get 1st char of function
    func_idt = vul_func[0][0:idx] 

    # save the function to new file
    with open(f'{contract}vulnerable_function.sol', 'w') as f:
        for ln in vul_func:
            # remove indent from all lines
            f.write(ln.removeprefix(func_idt))

    return func_idt



def save_vul_info(vul, pos, file, func_indent, contract_dir):
    vul_info = {
        'vulnerability': vul,
        'vulnerability_position': {'start': pos[0], 'end': pos[1]},
        'vulnreable_file_path': file,
        'vulnerable_function_indent': func_indent
    }
    with open(f'{contract_dir}vulnerability_info.json', 'wt') as f:
        json.dump(vul_info, f, ensure_ascii=False, indent=4)

    return



if __name__ == '__main__':
    main()
