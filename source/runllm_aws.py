# pip install transformers sentencepiece accelerate bitsandbytes scipy


import glob
import os
import datetime
import argparse
import sys
import traceback

# reference functions in the other files
# from promptTemplate import PromptTemplate
from LLMInterface import CodeLlama
from repair import Repair


def main(model):
    target_contracts = get_target_contracts()
    inference_times = set_inference_times()
    target_count = 1

    for target_directory in target_contracts:
        print(f'\n{target_count}/{len(target_contracts)}\n{target_directory}')

        r = Repair()
        r.step_repair(model, target_directory, inference_times)
        

        with open('fixed_completed_contracts.txt', 'a') as f:
            f.write(target_directory+'\n')

        target_count += 1
    
    print('Finis running llm')
    os.remove('fixed_completed_contracts.txt')
    # __name__ の部分は，コマンドラインからファイルが実行された場合は__main__ になってるけど，
    # 別ファイルからインポートされた場合はモジュール名（.pyを除いたファイル名）になるらしい

    

def get_target_contracts():
    # 修正が終了しているものを除外
    completed_contracts = []
    if os.path.isfile('fixed_completed_contracts.txt'):
        with open('fixed_completed_contracts.txt', 'r') as f:
            completed_contracts = f.read().split('\n')[:-1]

    target_contracts = glob.glob('target_contracts/*/*/')

    return [contract for contract in target_contracts if not contract in completed_contracts]


def set_inference_times():
    # set default 5
    # TODO: change inference times with argument
    return 10


def argument_processing(args):
    if args.load_localmodel is None:
        print('Download a model')
        model = CodeLlama()
        model.install_model()
    else:
        try:
            print('Load a model')
            save_directory = args.load_localmodel
            # save_directory = '/content/drive/MyDrive/forAPR/CodeLlama-7b-Instruct-hf'
            model = CodeLlama()
            model.load_model(save_directory)
        except Exception as e:
            print('\nError in loading model')
            print(str(e) + '\n')
            raise

    return model


def get_args():
    parser = argparse.ArgumentParser()
    parser.add_argument('--load-localmodel')
    args = parser.parse_args()

    return args


if __name__ == '__main__':
    try:
        model = argument_processing(get_args())
        main(model)
    except Exception as e:
        print('An error has occured. Exit the program.\n')
        print('Traceback:')
        etype, value, tb = sys.exc_info()
        traceback.print_tb(tb)

        print(str(e))

