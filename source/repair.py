
from promptTemplate import PromptTemplate

class Repair:
    def repair(self, model, target_directory, inference_times):
        prompt = PromptTemplate(target_directory)
        prompt.generate_prompt()
        prompt.save_prompt()

        for i in range(inference_times):
            print(f'repair: {i+1} / {inference_times}')

            model.run_inference(prompt.prompt)
            model.save_exectime(f'{target_directory}output/exec_time_{i}.txt')
            model.save_output(f'{target_directory}output/output_{i}.json')

    def step_repair(self, model, target_directory, inference_times):
        prompt = PromptTemplate(target_directory)
        for i in range(inference_times):
            print(f'\nrepair: {i+1} / {inference_times}')
            for step_count in range(3):
                print(f'step: {step_count+1} / {3}')
                prompt.generate_step_prompt(step_count, model.output)
                model.run_inference(prompt.step_prompt[step_count])
                model.save_step_exectime(f'{target_directory}output/step_exec_time_{i}.json')
                model.save_step_output(f'{target_directory}output/output_{i}_step_{step_count}.json', step_count)
            prompt.save_step_prompt(i)
