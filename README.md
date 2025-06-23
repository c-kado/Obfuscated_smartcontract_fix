# Obfuscated_smartcontract_fix

## setup

Make directories for the contracts to be fixed, 'target_contracts/{contract_address}_{compiler_version}/{original or obfuscated}/'.
Make files in the directories, 'vulnerable.sol', 'resultSlither.txt'.

- runllm_aws.py
  The main file of fixing contracts.
  ```python runllm_aws.py```

- preprocessing/adjustResultSlither.py  
  Simplify the result by Slither and extract the vulenrable function from the source code.


