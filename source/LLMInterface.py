import torch
from torch import cuda,bfloat16
from transformers import AutoTokenizer,AutoModelForCausalLM
import transformers
import json


import datetime

class CodeLlama:

    def __init__(self):
        self.output = ''

    def install_model(self):
        # 修正指示を与えるために，Code LLama -Instruction- を使用
        # model_id = "codellama/CodeLlama-7b-Instruct-hf"
        model_id = "codellama/CodeLlama-13b-Instruct-hf"
        # model_id = "codellama/CodeLlama-34b-Instruct-hf"

        print('quantize')
        # 量子化？
        quant_config = transformers.BitsAndBytesConfig(
            load_in_4bit=True,
            bnb_4bit_quant_type='nf4',
            bnb_4bit_use_double_quant=True,
            bnb_4bit_compute_dtype=bfloat16
        )

        print('download model from_pretrained')
        # GPUを使用していない場合，quant_configの指定によりエラー発生
        self.model = AutoModelForCausalLM.from_pretrained(
            model_id,
            trust_remote_code=True,
            quantization_config=quant_config,
            device_map="auto"
        )

        print('download tokenizer from_pretrained')
        self.tokenizer = AutoTokenizer.from_pretrained(model_id)

        #print('save model & tokenizer')
        # 新しくモデルを読み込んだ場合は，モデルのダウンロードに時間がかかるため，セーブ
        #self.model.save_pretrained(save_directory)
        #self.tokenizer.save_pretrained(save_directory)

        return 


    def load_model(self, save_directory):
        print('ここでも量子化を指定？')
        # self.model = AutoModelForCausalLM.from_pretrained(save_directory)
        # self.tokenizer = AutoTOkenizer.from_pretrained(save_directory)


    def run_inference(self, prompt):
        # TODO: プロンプトの長さ考える
        # 元のコードの長さ + α
        prompt_length = len(prompt)

        pipeline = transformers.pipeline(
            task = "text-generation",
            model = self.model,
            tokenizer = self.tokenizer
        )

        start_dt = datetime.datetime.now() + datetime.timedelta(hours=9)
        print('\tinference start: ' + start_dt.strftime('%m/%d %X'))

        sequences = pipeline(
            prompt,
            do_sample=True,
            temperature=0.2,
            top_p=0.95,
            eos_token_id=self.tokenizer.eos_token_id,
            truncation=True,
            max_length=prompt_length,
        )

        end_dt = datetime.datetime.now() + datetime.timedelta(hours=9)
        self.exec_time = str(end_dt - start_dt)[:-7]
        self.output = sequences[0]['generated_text'][prompt_length:]
        print('\texec time: '+ self.exec_time)

        # 推論で使用したRAM領域を解放
        # del pipeline
        # torch.cuda.empty_cache()
    

    def save_exectime(self, save_file):
        with open(save_file, 'w') as f:
            f.write(self.exec_time)

    def save_step_exectime(self, save_file):
        with open(save_file, 'a') as f:
            f.write(self.exec_time+'\n')
    
    def save_output(self, save_file):
        with open(save_file, 'w') as f:
            f.write(self.output)

    def save_step_output(self, save_file, step_count):
        if step_count == 0:
            d = {'Cause of Reentrancy': self.output}
            with open(save_file, 'w') as f:
                json.dump(d, f)
        elif step_count == 1:
            d = {'How to fix': self.output}
            with open(save_file, 'w') as f:
                json.dump(d, f)
        elif step_count == 2:
            self.save_output(save_file)
