"""Pytest test suite for flux-validator."""
import pytest
from validator import (
    PythonVM, CrossVMValidator, VMStatus, VMResult, TestCase, ValidationResult
)


# ── Fixtures ──

@pytest.fixture
def validator():
    return CrossVMValidator()

@pytest.fixture
def python_vm():
    return PythonVM()


# ── VMStatus ──

class TestVMStatus:
    def test_all_statuses_defined(self):
        expected = {"PASS", "FAIL", "ERROR", "SKIPPED"}
        actual = {s.value for s in VMStatus}
        assert expected == actual


# ── PythonVM ──

class TestPythonVM:
    def test_halt_only(self, python_vm):
        r = python_vm.run([0x00], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 1

    def test_movi(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x00], {})
        assert r.status == VMStatus.PASS
        assert r.registers[0] == 42

    def test_add(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 20, 0x20, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 30

    def test_sub(self, python_vm):
        r = python_vm.run([0x18, 0, 20, 0x18, 1, 8, 0x21, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 12

    def test_mul(self, python_vm):
        r = python_vm.run([0x18, 0, 6, 0x18, 1, 7, 0x22, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 42

    def test_div_normal(self, python_vm):
        r = python_vm.run([0x18, 0, 20, 0x18, 1, 4, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 5

    def test_div_by_zero_no_crash(self, python_vm):
        """Division by zero should not crash the VM."""
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 0, 0x23, 2, 0, 1, 0x00], {})
        assert r.status == VMStatus.PASS

    def test_mod(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 3, 0x24, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_neg(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x0B, 0, 0x00], {})
        assert r.registers[0] == -42

    def test_inc(self, python_vm):
        r = python_vm.run([0x18, 0, 5, 0x08, 0, 0x00], {})
        assert r.registers[0] == 6

    def test_dec(self, python_vm):
        r = python_vm.run([0x18, 0, 5, 0x09, 0, 0x00], {})
        assert r.registers[0] == 4

    def test_push_pop(self, python_vm):
        bc = [0x18, 0, 10, 0x18, 1, 20, 0x0C, 0, 0x0C, 1, 0x0D, 0, 0x0D, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 20
        assert r.registers[1] == 10

    def test_mov(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x3A, 1, 0, 0, 0x00], {})
        assert r.registers[1] == 42

    def test_addi(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x19, 0, 5, 0x00], {})
        assert r.registers[0] == 15

    def test_cmp_eq_true(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x18, 1, 42, 0x2C, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_cmp_eq_false(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x18, 1, 99, 0x2C, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_cmp_lt_true(self, python_vm):
        r = python_vm.run([0x18, 0, 5, 0x18, 1, 10, 0x2D, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_cmp_gt_true(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 5, 0x2E, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_initial_regs(self, python_vm):
        r = python_vm.run([0x20, 2, 0, 1, 0x00], {0: 10, 1: 20})
        assert r.registers[2] == 30

    def test_nop(self, python_vm):
        r = python_vm.run([0x01, 0x01, 0x00], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 3

    def test_empty_bytecode(self, python_vm):
        r = python_vm.run([], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 0

    def test_negative_immediate(self, python_vm):
        r = python_vm.run([0x18, 0, 0xFB, 0x00], {})
        assert r.registers[0] == -5

    def test_vm_name_is_python(self, python_vm):
        r = python_vm.run([0x00], {})
        assert r.vm_name == "python"


# ── CrossVMValidator ──

class TestCrossVMValidator:
    def test_single_test_pass(self, validator):
        validator.add_test("movi_42", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        assert len(results) == 1
        assert results[0].expected_match
        assert results[0].consensus

    def test_add_test(self, validator):
        validator.add_test("add", [0x18, 0, 10, 0x18, 1, 20, 0x20, 2, 0, 1, 0x00], {}, {2: 30})
        results = validator.validate_all()
        assert results[0].expected_match

    def test_factorial(self, validator):
        validator.add_test("factorial_6",
            [0x18, 0, 6, 0x18, 1, 1, 0x22, 1, 1, 0, 0x09, 0, 0x3D, 0, 0xFA, 0, 0x00],
            {}, {1: 720})
        results = validator.validate_all()
        assert results[0].expected_match

    def test_multiple_tests(self, validator):
        validator.add_test("t1", [0x18, 0, 5, 0x00], {}, {0: 5})
        validator.add_test("t2", [0x18, 0, 10, 0x18, 1, 20, 0x20, 2, 0, 1, 0x00], {}, {2: 30})
        results = validator.validate_all()
        assert len(results) == 2
        assert all(r.consensus for r in results)

    def test_vm_count(self, validator):
        validator.add_test("t", [0x00], {}, {})
        results = validator.validate_all()
        assert len(results[0].results) == 8

    def test_all_vm_names_present(self, validator):
        validator.add_test("t", [0x00], {}, {})
        results = validator.validate_all()
        vm_names = {r.vm_name for r in results[0].results}
        assert "python" in vm_names
        assert "c" in vm_names
        assert "rust" in vm_names

    def test_expected_mismatch(self, validator):
        validator.add_test("wrong", [0x18, 0, 42, 0x00], {}, {0: 99})
        results = validator.validate_all()
        assert not results[0].expected_match

    def test_expected_empty_passes(self, validator):
        """No expected values means any result matches."""
        validator.add_test("empty", [0x18, 0, 42, 0x00], {}, {})
        results = validator.validate_all()
        assert results[0].expected_match

    def test_stack_swap(self, validator):
        validator.add_test("swap",
            [0x18, 0, 10, 0x18, 1, 20, 0x0C, 0, 0x0C, 1, 0x0D, 0, 0x0D, 1, 0x00],
            {}, {0: 20, 1: 10})
        results = validator.validate_all()
        assert results[0].expected_match

    def test_loop_program(self, validator):
        """Counter: R0=5, R1=0; loop: INC R1, DEC R0, JNZ R0, -6"""
        bc = [0x18, 0, 5, 0x18, 1, 0, 0x08, 1, 0x09, 0, 0x3D, 0, 0xFC, 0, 0x00]
        validator.add_test("counter", bc, {}, {1: 5})
        results = validator.validate_all()
        assert results[0].expected_match


# ── ValidationResult ──

class TestValidationResult:
    def test_to_markdown_has_vm_names(self, validator):
        validator.add_test("test", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        md = results[0].to_markdown()
        assert "python" in md
        assert "Consensus" in md

    def test_to_markdown_shows_pass(self, validator):
        validator.add_test("test", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        md = results[0].to_markdown()
        assert "PASS" in md

    def test_consensus_all_agree(self, validator):
        validator.add_test("test", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        assert results[0].consensus

    def test_test_name_preserved(self, validator):
        validator.add_test("my_special_test", [0x00], {}, {})
        results = validator.validate_all()
        assert results[0].test_name == "my_special_test"


# ── VMResult ──

class TestVMResult:
    def test_vm_result_fields(self):
        r = VMResult(vm_name="test", status=VMStatus.PASS,
                     registers={0: 42}, cycles=5)
        assert r.vm_name == "test"
        assert r.status == VMStatus.PASS
        assert r.registers[0] == 42
        assert r.cycles == 5
        assert r.error == ""

    def test_vm_result_error(self):
        r = VMResult(vm_name="test", status=VMStatus.ERROR,
                     registers={}, cycles=0, error="out of bounds")
        assert r.error == "out of bounds"
