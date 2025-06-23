import json
import glob
import os
import pandas as pd
import re
import subprocess
from subprocess import PIPE, STDOUT

from analyze import Slither


df_columns =['contract', 'ori_or_obf', 'output','valid_format', 'valid_cmpl', 'valid_diff', 'valid_vul', 'valid_func', 'memo']
def main():
    # 1. validate the output format (apply the patch)
    # 2. validate compilable (compile the patch)
    #           !! compile with (solc --asm), and get asm deleting comment in it
    #           !! (for next diff validation)
    # 3. validate difference (get diff original & fixed contracts with asm)
    # 4. validate vulnerability (slither)
    # 5. validate functionality <-- manually.......

    outputs_df = pd.DataFrame(columns=df_columns)

    os.makedirs('temp/', exist_ok=True)
    target_contracts = glob.glob('target_contracts/*/*/')
    for target_contract in target_contracts:
        print(target_contract)
        contract, oriObf = target_contract.split('/')[1:3] 
        # TODO: step or nostep
        # outputs = glob.glob(f'{target_contract}output/output_*_step_2.json')
        outputs = glob.glob(f'{target_contract}output/output_*.json')

        # set compiler version
        cmpl_ver = re.findall('_v(0\.\d+\.\d+)\+commit', target_contract.split('/')[1])[0]
        change_solc_version(cmpl_ver)

        # get contract asm for diff validation
        get_asm(f'{target_contract}vulnerable.sol', 'temp/vul_asm.txt', 'temp/cmpl_error.txt')

        for output in outputs:
            output_num = re.findall('output_(\d+)', output)[-1]

            # if not(valid_format := vld_output_format(target_contract, output_num)):
            #     print(f'{output_num}: format error')
            # elif not(valid_cmpl := vld_compilable(target_contract, output_num)):
            #     print(f'{output_num}: cmpl error')
            # elif not (valid_diff := vld_differencial('temp/vul_asm.txt', 'temp/fixed_asm.txt')):
            #     print(f'{output_num}: diff error')
            # elif not (valid_vul := vld_vulnerability(target_contract, output_num)):
            #     print(f'{output_num}: vul error')

            if not vld_output_format(target_contract, output_num):
                validation_info = pd.Series([contract, oriObf, output.split('/')[-1], False, False, False, False, False, ''], index=df_columns, name=f'{contract}/{oriObf}/{output.split("/")[-1]}')
            elif not vld_compilable(target_contract, output_num):
                validation_info = pd.Series([contract, oriObf, output.split('/')[-1], True, False, False, False, False, ''], index=df_columns, name=f'{contract}/{oriObf}/{output.split("/")[-1]}')
            elif not vld_differencial('temp/vul_asm.txt', 'temp/fixed_asm.txt'):
                validation_info = pd.Series([contract, oriObf, output.split('/')[-1], True, True, False, False, False, ''], index=df_columns, name=f'{contract}/{oriObf}/{output.split("/")[-1]}')
            elif not vld_vulnerability(target_contract, output_num):
                validation_info = pd.Series([contract, oriObf, output.split('/')[-1], True, True, True, False, False, ''], index=df_columns, name=f'{contract}/{oriObf}/{output.split("/")[-1]}')
            else:
                validation_info = pd.Series([contract, oriObf, output.split('/')[-1], True, True, True, True, False, ''], index=df_columns, name=f'{contract}/{oriObf}/{output.split("/")[-1]}')

            # vld_functionality
            outputs_df = pd.concat([outputs_df, validation_info.to_frame().T])

    print(outputs_df)
    # save vulidation info
    outputs_df.to_csv('data/outputs.csv')

    # sum_df = sum_validation_info(outputs_df)
    sum_df = sum_validation_info(pd.read_csv('data/outputs.csv'))
    sum_df.to_csv('data/sum_outputs.csv')



def vld_output_format(contract_dir, output_num):
    # 1. get output with json format
    #    validate format
    try:
        # TODO: step or nostep
        # with open(f'{contract_dir}output/output_{output_num}_step_2.json', 'r') as f:
        with open(f'{contract_dir}output/output_{output_num}.json', 'r') as f:
            patch = json.load(f)
            patch_func = patch['corrected_code'][:-1 if patch['corrected_code'][-1] == '\n' else len(patch['corrected_code'])].split('\n')
    except json.decoder.JSONDecodeError as e:
        print(f'Fail to load output as json.\tFile: {contract_dir}output_{output_num}') 
        print('\t'+str(e))
        return False
    except Exception as e:
        print(f'Error with json decoder\tFile: {contract_dir}output/{output_num}')
        print('\t'+str(type(e))+':\t'+str(e))
        return False

    # 2. Apply patch
    apply_patch(contract_dir, output_num, patch_func)

    return True



def vld_compilable(contract_dir, output_num):
    # solc with option --asm (for validate diff) 
    # return value: True  (compile success)
    #               False (compile fail)
    return get_asm(f'{contract_dir}output/fixed_code_{output_num}.sol', 'temp/fixed_asm.txt', f'{contract_dir}output/cmpl_error_{output_num}.sol')



def vld_differencial(file1, file2):
    with open(file1, 'r') as f:
        text1 = f.read()
    with open(file2, 'r') as f:
        text2 = f.read()

    if text1 == text2:
        return False
    else:
        return True



def vld_vulnerability(contract_dir, output_num):
    option = ['--detect', 'reentrancy-eth']
    contract = f'{contract_dir}output/fixed_code_{output_num}.sol'
    result_json = f'{contract_dir}output/slither_result_{output_num}.json'


    Slither.run_slither(contract, result_json, option)
    return Slither.check_result(result_json)



def apply_patch(contract_dir, output_num, patch_func):
    # 1. get original vulnerable contract
    with open(f'{contract_dir}vulnerable.sol', 'r') as f:
        source_code = f.readlines()

    # 2. get info of vulnerable function (with line number)
    with open(f'{contract_dir}vulnerability_info.json', 'r') as f:
        vul_info = json.load(f)
    vul_func_pos = vul_info['vulnerability_position']
    func_indent = vul_info['vulnerable_function_indent']

    # 3. replace vul_function to patched_function
    patched_code = source_code[:vul_func_pos['start']-1]
    for patch_line in patch_func:
        patched_code.append(func_indent + patch_line + '\n')
    patched_code += source_code[vul_func_pos['end']:]

    # 4, save fixed contract
    with open(f'{contract_dir}output/codellama-13b-instruct/fixed_code_{output_num}.sol', 'w') as f:
        f.writelines(patched_code)
    
    return



def get_asm(source_file, save_file, save_error_file):
    # compile (solc --asm)
    proc = subprocess.run(f'solc --asm {source_file}', shell=True, stdout=PIPE, stderr=PIPE, text=True)

    # INVALID:
    #   Error:
    #     stdout: empty (proc.stdout = '')
    #     stderr: error message
    # 
    # VALID:
    #   Warning:
    #     stdout: asm
    #     stderr: warning message
    #   Success:
    #     stdout: asm
    #     stderr: empty

    if proc.stdout == '':
        with open(save_error_file, 'w') as f:
            f.write(proc.stderr)
        return False

    # remove comment from asm
    asm_with_nocomment = [line for line in proc.stdout.split('\n') if line.strip().startswith('/*')]

    # save asm
    with open(save_file, 'w') as f:
        for line in asm_with_nocomment:
            f.write(line+'\n')

    return True



def change_solc_version(version):
    proc = subprocess.run(f'solc-select use {version}', shell=True, stdout=PIPE, stderr=PIPE, text=True)
    if proc.stderr != '':
        print(version)
        print('Faile to change solc version: ' + proc.stderr)
    # print('solc-select use >> ' + proc.stdout)

    return



def sum_validation_info(outputs_df):
    sum_df = pd.DataFrame(index=['original', 'obfuscated'], columns=['total_C', 'total_P', 'valid_format_C', 'valid_format_P', 'valid_cmpl_C', 'valid_cmpl_P', 'valid_diff_C', 'valid_diff_P', 'valid_vul_C', 'valid_vul_P', 'valid_func_C', 'valid_func_P'])
    org_df = outputs_df[outputs_df['ori_or_obf'] == 'original']
    obf_df = outputs_df[outputs_df['ori_or_obf'] == 'obfuscated']

    # sum per patch
    sum_df.iloc[0, 1::2] = sum_outputs_patch(org_df) # original_P
    sum_df.iloc[1, 1::2] = sum_outputs_patch(obf_df) # obfuscated_P

    # sum per contract
    sum_df.iloc[0, ::2] = sum_outputs_contract(org_df) # original_P
    sum_df.iloc[1, ::2] = sum_outputs_contract(obf_df) # obfuscated_P
    return sum_df



def sum_outputs_patch(df):
    tot = df.shape[0]
    frmt = df[df['valid_format'] == True].shape[0]
    cmpl = df[df['valid_cmpl'] == True].shape[0]
    diff = df[df['valid_diff'] == True].shape[0]
    vul = df[df['valid_vul'] == True].shape[0]
    func = df[df['valid_func'] == True].shape[0]

    return tot, frmt, cmpl, diff, vul, func



def sum_outputs_contract(df):
    # Cの条件は，各条件ごとに　　True抽出 -> 重複削除でコントラクトの数カウント　　すれば良い？
    tot = df.drop_duplicates(subset=['contract', 'ori_or_obf']).shape[0]
    frmt = df[df['valid_format'] == True].drop_duplicates(subset=['contract', 'ori_or_obf']).shape[0]
    cmpl = df[df['valid_cmpl'] == True].drop_duplicates(subset=['contract', 'ori_or_obf']).shape[0]
    diff = df[df['valid_diff'] == True].drop_duplicates(subset=['contract', 'ori_or_obf']).shape[0]
    vul = df[df['valid_vul'] == True].drop_duplicates(subset=['contract', 'ori_or_obf']).shape[0]
    func = df[df['valid_func'] == True].drop_duplicates(subset=['contract', 'ori_or_obf']).shape[0]

    return tot, frmt, cmpl, diff, vul, func



if __name__ == '__main__':
    main()
