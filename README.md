# FLUX Cross-VM Validator

Run same bytecodes across 8 language implementations and compare results.

## Features
- Reference Python VM built-in
- 8-VM comparison matrix (python, c, cpp, go, rust, zig, js, java)
- Consensus detection — all VMs must agree
- Expected value matching
- Markdown test reports

## Usage
```python
from validator import CrossVMValidator
v = CrossVMValidator()
v.add_test("factorial", [0x18,0,6, 0x18,1,1, 0x22,1,1,0, 0x09,0, 0x3D,0,0xFA,0, 0x00], {}, {1: 720})
results = v.validate_all()
print(results[0].to_markdown())
```

8 tests passing.
