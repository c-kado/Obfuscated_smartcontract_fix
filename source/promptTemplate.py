'''
Code Llama - Instructionのプロンプトテンプレート
https://www.llama.com/docs/model-cards-and-prompt-formats/meta-code-llama/

<s>[INST] <<SYS>>
{{ system_prompt }}
<</SYS>>

{{ user_message_1 }} [/INST] {{ model_answer_1 }} </s>
<s>[INST] {{ user_message_2 }} [/INST]
'''

import json
import textwrap

class PromptTemplate:

    def __init__(self, target_directory):
        self.target_directory = target_directory
        self.step_prompt = ['', '', '']
        with open(self.target_directory+'vulnerable_function.sol', 'r') as f:
            self.vul_code = f.read()


    def generate_role_prompt(self):
        system_instruction = 'You are an expert in solidity smart contract security and vulnerability fixing.'
        return f'<s>[INST] <<SYS>>\n{system_instruction}\n<</SYS>>\n\n'
    
    def generate_task_prompt(self):
        with open(self.target_directory+'adjustResultSlither.txt', 'r') as f:
            analysis_result = f.read()
       
        task_prompt = textwrap.dedent(f"""
                Task: Fix the reentrancy vulnerability in a code.
                The code and the result of reentrancy analysis are the following.

                {{
                    "Vulnerable code": {json.dumps(self.vul_code)},
                    "Analysis result": {json.dumps(analysis_result)} 
                }}

                Address the cause above and provide the corrected Solidity code.
                Follow these three steps to fix it:
                Step 1. Understand the cause described above.
                Step 2. Figure out how to fix the vulnerability by applying the 'Checks-Effects-Interactions' pattern.
                Step 3. Fix the vulnerability and output the corrected code.

                Expected Output: Fill in the blank of the format described below and output the corrected Solidity code.
                Output Format: {{
                    "cause of Reentrancy": "   ",
                    "how to fix": "   ",
                    "corrected_code": "   "
                }}
                """)[1:]

        return f'{task_prompt}[/INST]'

    def generate_task_prompt_understanding(self):
        # コードとslither与えて，
        # 原因を解釈して，文章(sentence)のみで説明してください
        with open(self.target_directory+'adjustResultSlither.txt', 'r') as f:
            analysis_result = f.read()

        task_prompt = textwrap.dedent(f"""
                Task: Understand the cause of the vulnerability based on the analysis results provided below for the vulnerable Solidity code.
                The analysis results indicate the cause of the vulnerability and the corresponding lines of vulnerable code.
                Then, explain the cause in your own words using written format only.
                The vulnerable Solidity code and its analysis results are shown below.

                {{
                    "Vulnerable code": {json.dumps(self.vul_code)},
                    "Analysis result": {json.dumps(analysis_result)} 
                }}
                """)[1:]

        return f'{task_prompt}[/INST]'

 

    def generate_task_prompt_figureout(self, cause_description):
        # 原因の文章とコード与えて
        # 脆弱性の原因に対処して，脆弱性にパッチを当てる方法を文章のみで説明してください
        task_prompt = textwrap.dedent(f"""
                Task: Refer to the cause provided below and consider how to fix the vulnerability in the Solidity code by applying the 'Checks-Effects-Interactions' pattern.
                Explain the fix you came up with using written format only.
                The vulnerable Solidity code and the cause of the vulnerability are shown below.

                {{
                    "Vulnerable code": {json.dumps(self.vul_code)},
                    "Cause of the vulnerability": {json.dumps(cause_description)}
                }}
                """)[1:]

        return f'{task_prompt}[/INST]'



    def generate_task_genpatch(self, fixing_method):
        # パッチの当て方の文章とコード与えて
        # パッチを当てたコードのみを出力
        task_prompt = textwrap.dedent(f"""
                Task: Fix the vulnerability in the Solidity code shown below, and output only the corrected Solidity code.
                Follow the method provided below to apply the fix.
                The vulnerable Solidity code and the method for fixing it are shown below.

                {{
                    "Vulnerable code": {json.dumps(self.vul_code)},
                    "Fixing method": {json.dumps(fixing_method)} 
                }}

                Expected Output: Fill in the blank in the format below and output the corrected Solidity code.
                Output Format: {{
                    "corrected_code": "   "
                }}
                """)[1:]

        return f'{task_prompt}[/INST]'




    def generate_prompt(self):
        self.prompt = self.generate_role_prompt() + self.generate_task_prompt()



    def generate_step_prompt(self, step_count, previous_step_output):
        # 0: understanding, 1: how to gen patch, 2: generate patch 
        if step_count == 0:
            self.step_prompt[0] = self.generate_role_prompt() + self.generate_task_prompt_understanding()
        elif step_count == 1:
            self.step_prompt[1] = self.generate_role_prompt() + self.generate_task_prompt_figureout(previous_step_output)
        elif step_count == 2:
            self.step_prompt[2] = self.generate_role_prompt() + self.generate_task_genpatch(previous_step_output)
        else:
            print('Invalid step count number!!')



    def save_prompt(self):
        with open(f'{self.target_directory}prompt.txt', 'w') as f:
            f.write(self.prompt)
        return



    def save_step_prompt(self, inference_time):
        with open(f'{self.target_directory}step_prompt_{inference_time}.txt', 'w') as f:
            for step_count in range(3):
                f.write(self.step_prompt[step_count]+'\n\n')
        return
