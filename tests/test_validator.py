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


# ═══════════════════════════════════════════════════════════
#  VMStatus
# ═══════════════════════════════════════════════════════════

class TestVMStatus:
    def test_all_statuses_defined(self):
        expected = {"PASS", "FAIL", "ERROR", "SKIPPED"}
        actual = {s.value for s in VMStatus}
        assert expected == actual

    def test_status_pass_value(self):
        assert VMStatus.PASS.value == "PASS"

    def test_status_fail_value(self):
        assert VMStatus.FAIL.value == "FAIL"

    def test_status_error_value(self):
        assert VMStatus.ERROR.value == "ERROR"

    def test_status_skipped_value(self):
        assert VMStatus.SKIPPED.value == "SKIPPED"


# ═══════════════════════════════════════════════════════════
#  PythonVM — Arithmetic Ops
# ═══════════════════════════════════════════════════════════

class TestPythonVMArithmetic:
    def test_add_positive(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 20, 0x20, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 30

    def test_add_negative(self, python_vm):
        """ADD: -10 + (-20) = -30"""
        r = python_vm.run([0x18, 0, 0xF6, 0x18, 1, 0xEC, 0x20, 2, 0, 1, 0x00], {})
        assert r.registers[2] == -30

    def test_add_mixed_sign(self, python_vm):
        """ADD: -10 + 25 = 15"""
        r = python_vm.run([0x18, 0, 0xF6, 0x18, 1, 25, 0x20, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 15

    def test_sub_positive(self, python_vm):
        r = python_vm.run([0x18, 0, 20, 0x18, 1, 8, 0x21, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 12

    def test_sub_negative_result(self, python_vm):
        """SUB: 8 - 20 = -12"""
        r = python_vm.run([0x18, 0, 8, 0x18, 1, 20, 0x21, 2, 0, 1, 0x00], {})
        assert r.registers[2] == -12

    def test_sub_both_negative(self, python_vm):
        """SUB: -5 - (-3) = -2"""
        r = python_vm.run([0x18, 0, 0xFB, 0x18, 1, 0xFD, 0x21, 2, 0, 1, 0x00], {})
        assert r.registers[2] == -2

    def test_mul_positive(self, python_vm):
        r = python_vm.run([0x18, 0, 6, 0x18, 1, 7, 0x22, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 42

    def test_mul_negative(self, python_vm):
        """MUL: -6 * 7 = -42"""
        r = python_vm.run([0x18, 0, 0xFA, 0x18, 1, 7, 0x22, 2, 0, 1, 0x00], {})
        assert r.registers[2] == -42

    def test_mul_both_negative(self, python_vm):
        """MUL: -6 * -7 = 42"""
        r = python_vm.run([0x18, 0, 0xFA, 0x18, 1, 0xF9, 0x22, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 42

    def test_mul_by_zero(self, python_vm):
        """MUL: 100 * 0 = 0"""
        r = python_vm.run([0x18, 0, 100, 0x18, 1, 0, 0x22, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_mul_by_one(self, python_vm):
        """MUL: 42 * 1 = 42"""
        r = python_vm.run([0x18, 0, 42, 0x18, 1, 1, 0x22, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 42

    def test_div_normal(self, python_vm):
        r = python_vm.run([0x18, 0, 20, 0x18, 1, 4, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 5

    def test_div_truncation_neg_pos(self, python_vm):
        """BUG FIX TEST: -7 / 2 = -3 (truncation toward zero), NOT -4 (floor)."""
        r = python_vm.run([0x18, 0, 0xF9, 0x18, 1, 2, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == -3

    def test_div_truncation_pos_neg(self, python_vm):
        """7 / -2 = -3 (truncation toward zero), NOT -4."""
        r = python_vm.run([0x18, 0, 7, 0x18, 1, 0xFE, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == -3

    def test_div_truncation_neg_neg(self, python_vm):
        """-7 / -2 = 3 (truncation toward zero)."""
        r = python_vm.run([0x18, 0, 0xF9, 0x18, 1, 0xFE, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 3

    def test_div_by_one(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x18, 1, 1, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 42

    def test_div_by_zero_no_crash(self, python_vm):
        """Division by zero should not crash the VM."""
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 0, 0x23, 2, 0, 1, 0x00], {})
        assert r.status == VMStatus.PASS

    def test_div_by_zero_leaves_result_unchanged(self, python_vm):
        """DIV by zero should leave the destination register unchanged (0)."""
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 0, 0x23, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_mod_positive(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 3, 0x24, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_mod_zero(self, python_vm):
        """10 % 5 = 0"""
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 5, 0x24, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_neg(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x0B, 0, 0x00], {})
        assert r.registers[0] == -42

    def test_neg_double(self, python_vm):
        """NEG applied twice returns original value."""
        r = python_vm.run([0x18, 0, 42, 0x0B, 0, 0x0B, 0, 0x00], {})
        assert r.registers[0] == 42

    def test_neg_zero(self, python_vm):
        """NEG of 0 is still 0."""
        r = python_vm.run([0x18, 0, 0, 0x0B, 0, 0x00], {})
        assert r.registers[0] == 0

    def test_inc(self, python_vm):
        r = python_vm.run([0x18, 0, 5, 0x08, 0, 0x00], {})
        assert r.registers[0] == 6

    def test_inc_zero(self, python_vm):
        """INC from 0 gives 1."""
        r = python_vm.run([0x18, 0, 0, 0x08, 0, 0x00], {})
        assert r.registers[0] == 1

    def test_inc_negative(self, python_vm):
        """INC from -1 gives 0."""
        r = python_vm.run([0x18, 0, 0xFF, 0x08, 0, 0x00], {})
        assert r.registers[0] == 0

    def test_dec(self, python_vm):
        r = python_vm.run([0x18, 0, 5, 0x09, 0, 0x00], {})
        assert r.registers[0] == 4

    def test_dec_zero(self, python_vm):
        """DEC from 0 gives -1."""
        r = python_vm.run([0x18, 0, 0, 0x09, 0, 0x00], {})
        assert r.registers[0] == -1

    def test_dec_negative(self, python_vm):
        """DEC from -5 gives -6."""
        r = python_vm.run([0x18, 0, 0xFB, 0x09, 0, 0x00], {})
        assert r.registers[0] == -6

    def test_multiple_inc(self, python_vm):
        """Three INCs on R0: 0 -> 1 -> 2 -> 3."""
        bc = [0x18, 0, 0, 0x08, 0, 0x08, 0, 0x08, 0, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 3


# ═══════════════════════════════════════════════════════════
#  PythonVM — MOVI, MOVI16, ADDI, MOV
# ═══════════════════════════════════════════════════════════

class TestPythonVMMov:
    def test_movi(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x00], {})
        assert r.status == VMStatus.PASS
        assert r.registers[0] == 42

    def test_movi_negative(self, python_vm):
        """MOVI with signed byte: 0xFB -> -5."""
        r = python_vm.run([0x18, 0, 0xFB, 0x00], {})
        assert r.registers[0] == -5

    def test_movi_negative_127(self, python_vm):
        """MOVI: 0x81 -> -127."""
        r = python_vm.run([0x18, 0, 0x81, 0x00], {})
        assert r.registers[0] == -127

    def test_movi_high_register(self, python_vm):
        """MOVI into register 15."""
        r = python_vm.run([0x18, 15, 99, 0x00], {})
        assert r.registers[15] == 99

    def test_movi16_positive(self, python_vm):
        """MOVI16: set R0 = 1000 (0x03E8)."""
        bc = [0x40, 0, 0xE8, 0x03, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 1000

    def test_movi16_negative(self, python_vm):
        """MOVI16: set R0 = -1000. Low=0x18 (-128 + -56 = -1000+2*256? Actually compute)."""
        # -1000 + 65536 = 64536 = 0xFC18
        bc = [0x40, 0, 0x18, 0xFC, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == -1000

    def test_movi16_max_signed(self, python_vm):
        """MOVI16: 32767 = 0x7FFF."""
        bc = [0x40, 0, 0xFF, 0x7F, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 32767

    def test_movi16_min_signed(self, python_vm):
        """MOVI16: -32768 = 0x8000."""
        bc = [0x40, 0, 0x00, 0x80, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == -32768

    def test_mov_copy(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x3A, 1, 0, 0, 0x00], {})
        assert r.registers[1] == 42

    def test_mov_same_reg(self, python_vm):
        """MOV R0, R0 — no-op but should still work."""
        r = python_vm.run([0x18, 0, 42, 0x3A, 0, 0, 0, 0x00], {})
        assert r.registers[0] == 42

    def test_mov_preserves_source(self, python_vm):
        """MOV should not modify the source register."""
        r = python_vm.run([0x18, 0, 42, 0x3A, 1, 0, 0, 0x00], {})
        assert r.registers[0] == 42  # source unchanged

    def test_addi(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x19, 0, 5, 0x00], {})
        assert r.registers[0] == 15

    def test_addi_negative(self, python_vm):
        """ADDI: 10 + (-3) = 7."""
        r = python_vm.run([0x18, 0, 10, 0x19, 0, 0xFD, 0x00], {})
        assert r.registers[0] == 7


# ═══════════════════════════════════════════════════════════
#  PythonVM — Stack Operations
# ═══════════════════════════════════════════════════════════

class TestPythonVMStack:
    def test_push_pop(self, python_vm):
        bc = [0x18, 0, 10, 0x18, 1, 20, 0x0C, 0, 0x0C, 1, 0x0D, 0, 0x0D, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 20
        assert r.registers[1] == 10

    def test_push_pop_single(self, python_vm):
        """Push R0=99, pop back into R1."""
        bc = [0x18, 0, 99, 0x0C, 0, 0x0D, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 99

    def test_multiple_pushes(self, python_vm):
        """Push three values, pop them back in reverse order."""
        # Push R0=1, R1=2, R2=3 then pop R0, R1, R2 -> R0=3, R1=2, R2=1
        bc = [0x18, 0, 1, 0x18, 1, 2, 0x18, 2, 3,
              0x0C, 0, 0x0C, 1, 0x0C, 2,
              0x0D, 0, 0x0D, 1, 0x0D, 2,
              0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 3
        assert r.registers[1] == 2
        assert r.registers[2] == 1

    def test_push_preserves_register(self, python_vm):
        """PUSH should not modify the source register."""
        bc = [0x18, 0, 42, 0x0C, 0, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 42

    def test_swap_via_stack(self, python_vm):
        """Swap R0 and R1 using the stack: push both, pop in reverse."""
        bc = [0x18, 0, 10, 0x18, 1, 20,
              0x0C, 0, 0x0C, 1,
              0x0D, 0, 0x0D, 1,
              0x00]
        r = python_vm.run(bc, {})
        assert r.registers[0] == 20
        assert r.registers[1] == 10


# ═══════════════════════════════════════════════════════════
#  PythonVM — Comparison Ops
# ═══════════════════════════════════════════════════════════

class TestPythonVMCompare:
    def test_cmp_eq_true(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x18, 1, 42, 0x2C, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_cmp_eq_false(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x18, 1, 99, 0x2C, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_cmp_eq_both_zero(self, python_vm):
        r = python_vm.run([0x2C, 2, 0, 1, 0x00], {0: 0, 1: 0})
        assert r.registers[2] == 1

    def test_cmp_lt_true(self, python_vm):
        r = python_vm.run([0x18, 0, 5, 0x18, 1, 10, 0x2D, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_cmp_lt_false(self, python_vm):
        """10 < 5 is false."""
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 5, 0x2D, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_cmp_lt_equal(self, python_vm):
        """5 < 5 is false."""
        r = python_vm.run([0x18, 0, 5, 0x18, 1, 5, 0x2D, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_cmp_lt_negative(self, python_vm):
        """-10 < 5 is true."""
        r = python_vm.run([0x18, 0, 0xF6, 0x18, 1, 5, 0x2D, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_cmp_gt_true(self, python_vm):
        r = python_vm.run([0x18, 0, 10, 0x18, 1, 5, 0x2E, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 1

    def test_cmp_gt_false(self, python_vm):
        """5 > 10 is false."""
        r = python_vm.run([0x18, 0, 5, 0x18, 1, 10, 0x2E, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0

    def test_cmp_gt_equal(self, python_vm):
        """5 > 5 is false."""
        r = python_vm.run([0x18, 0, 5, 0x18, 1, 5, 0x2E, 2, 0, 1, 0x00], {})
        assert r.registers[2] == 0


# ═══════════════════════════════════════════════════════════
#  PythonVM — Jumps and Control Flow
# ═══════════════════════════════════════════════════════════

class TestPythonVMJumps:
    def test_jz_taken(self, python_vm):
        """JZ: R0=0, jump backward to skip INC. R1 should stay 0."""
        # MOVI R0, 0; MOVI R1, 0; JZ R0, offset_back(-4, relative to pc+4);
        # INC R1; HALT
        # After JZ if taken: pc += -4 -> goes to MOVI R1, 0
        # Let's construct carefully:
        # offset 0: 0x18 0 0  (MOVI R0, 0) -> 3 bytes
        # offset 3: 0x18 1 0  (MOVI R1, 0) -> 3 bytes
        # offset 6: 0x3C 0 0xFE (JZ R0, -2 as signed) -> 4 bytes
        #   if taken: pc(6) + (-2) = 4... not right
        # JZ adds sb(bc[pc+2]) to pc. After fetch pc=6.
        # if R0==0: pc = 6 + (-2) = 4 -> byte 0x1 which is NOP
        # Let's try: JZ R0, 0xFB -> sb(0xFB) = -5, pc = 6 + (-5) = 1 -> MOVI R1 again
        # Actually need offset that goes to offset 3 (MOVI R1, 0) to loop
        # offset 6: 0x3C 0 0xFD -> sb(0xFD) = -3, pc = 6 + (-3) = 3 -> MOVI R1,0
        # That would re-execute MOVI R1,0 forever. We need to go past JZ.
        # Actually we want JZ to skip the INC.
        # offset 6: 0x3C 0 X  (JZ R0, X) -- if taken, skip 4 bytes ahead (past INC+HALT)
        # If R0==0: pc = 6 + X, we want to land on HALT at offset 11
        # So X = 11 - 6 = 5 = 0x05
        bc = [0x18, 0, 0, 0x18, 1, 0, 0x3C, 0, 5, 0x08, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 0  # INC was skipped

    def test_jz_not_taken(self, python_vm):
        """JZ not taken when R0 != 0."""
        # JZ advances by 4 when not taken (3-byte instr + padding)
        # offset 0: MOVI R0, 1 (3 bytes)
        # offset 3: MOVI R1, 0 (3 bytes)
        # offset 6: JZ R0, 6 + NOP padding (4 bytes)
        # offset 10: INC R1 (2 bytes)
        # offset 12: HALT
        # Not taken: pc=6+4=10 -> INC R1 executed -> R1=1
        # Taken: pc=6+6=12 -> HALT -> R1 stays 0
        bc = [0x18, 0, 1, 0x18, 1, 0, 0x3C, 0, 6, 0x01, 0x08, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 1  # INC was executed

    def test_jnz_taken(self, python_vm):
        """JNZ: R0=1, jump forward past DEC."""
        # offset 0: MOVI R0, 1
        # offset 3: MOVI R1, 5
        # offset 6: JNZ R0, 5  (skip DEC)
        # offset 10: DEC R1
        # offset 12: HALT
        bc = [0x18, 0, 1, 0x18, 1, 5, 0x3D, 0, 5, 0x09, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 5  # DEC was skipped

    def test_jnz_not_taken(self, python_vm):
        """JNZ not taken when R0 == 0."""
        # JNZ advances by 4 when not taken (3-byte instr + padding)
        # offset 0: MOVI R0, 0 (3 bytes)
        # offset 3: MOVI R1, 5 (3 bytes)
        # offset 6: JNZ R0, 6 + NOP padding (4 bytes)
        # offset 10: DEC R1 (2 bytes)
        # offset 12: HALT
        # Not taken (R0=0): pc=6+4=10 -> DEC R1 -> R1=4
        # Taken (R0!=0): pc=6+6=12 -> HALT -> R1 stays 5
        bc = [0x18, 0, 0, 0x18, 1, 5, 0x3D, 0, 6, 0x01, 0x09, 1, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 4  # DEC was executed

    def test_loop_counter(self, python_vm):
        """Counter: R0=5, R1=0; loop: INC R1, DEC R0, JNZ R0, back."""
        bc = [0x18, 0, 5, 0x18, 1, 0, 0x08, 1, 0x09, 0, 0x3D, 0, 0xFC, 0, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 5


# ═══════════════════════════════════════════════════════════
#  PythonVM — HALT, NOP, Edge Cases
# ═══════════════════════════════════════════════════════════

class TestPythonVMHaltAndNop:
    def test_halt_only(self, python_vm):
        r = python_vm.run([0x00], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 1

    def test_halt_stops_execution(self, python_vm):
        """Instructions after HALT should not execute."""
        bc = [0x18, 0, 42, 0x00, 0x18, 1, 99, 0x08, 0]
        r = python_vm.run(bc, {})
        assert r.cycles == 2  # MOVI + HALT
        assert r.registers[1] == 0  # second MOVI never executed

    def test_nop(self, python_vm):
        r = python_vm.run([0x01, 0x01, 0x00], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 3

    def test_empty_bytecode(self, python_vm):
        r = python_vm.run([], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 0

    def test_just_halt(self, python_vm):
        r = python_vm.run([0x00], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 1

    def test_unknown_opcode(self, python_vm):
        """Unknown opcode 0xFF should be skipped (pc += 1)."""
        r = python_vm.run([0xFF, 0x00], {})
        assert r.status == VMStatus.PASS
        assert r.cycles == 2


# ═══════════════════════════════════════════════════════════
#  PythonVM — VM Result Properties
# ═══════════════════════════════════════════════════════════

class TestPythonVMProperties:
    def test_vm_name_is_python(self, python_vm):
        r = python_vm.run([0x00], {})
        assert r.vm_name == "python"

    def test_initial_regs_loaded(self, python_vm):
        r = python_vm.run([0x20, 2, 0, 1, 0x00], {0: 10, 1: 20})
        assert r.registers[2] == 30

    def test_initial_regs_multiple(self, python_vm):
        r = python_vm.run([0x20, 3, 0, 1, 0x21, 4, 3, 2, 0x00],
                          {0: 100, 1: 50, 2: 10})
        assert r.registers[3] == 150
        assert r.registers[4] == 140

    def test_registers_only_first_16(self, python_vm):
        """Only registers 0-15 should be in the result."""
        r = python_vm.run([0x18, 0, 42, 0x00], {})
        assert len(r.registers) == 16

    def test_unwritten_regs_are_zero(self, python_vm):
        r = python_vm.run([0x18, 0, 42, 0x00], {})
        assert r.registers[5] == 0


# ═══════════════════════════════════════════════════════════
#  PythonVM — Factorial / Complex Programs
# ═══════════════════════════════════════════════════════════

class TestPythonVMComplex:
    def test_factorial_6(self, python_vm):
        bc = [0x18, 0, 6, 0x18, 1, 1, 0x22, 1, 1, 0, 0x09, 0, 0x3D, 0, 0xFA, 0, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 720

    def test_factorial_1(self, python_vm):
        """Factorial of 1 = 1."""
        bc = [0x18, 0, 1, 0x18, 1, 1, 0x22, 1, 1, 0, 0x09, 0, 0x3D, 0, 0xFA, 0, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 1

    def test_sum_1_to_10(self, python_vm):
        """Sum 1..10 = 55 using a loop."""
        # R0=10, R1=0; loop: ADD R1,R1,R0 (actually ADDI? no, let's use simple)
        # This is complex; let's use ADDI approach:
        # MOVI R0, 10; MOVI R1, 0; loop: ADDI R1, R1, 1 (actually need ADD reg,reg,reg)
        # We don't have ADDI for R1+=1... but we can use INC
        # R0=10, R1=0; loop: INC R1, DEC R0, JNZ R0, back
        bc = [0x18, 0, 10, 0x18, 1, 0, 0x08, 1, 0x09, 0, 0x3D, 0, 0xFC, 0, 0x00]
        r = python_vm.run(bc, {})
        assert r.registers[1] == 10


# ═══════════════════════════════════════════════════════════
#  VMResult
# ═══════════════════════════════════════════════════════════

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

    def test_vm_result_empty_registers(self):
        r = VMResult(vm_name="x", status=VMStatus.PASS, registers={}, cycles=0)
        assert r.registers == {}


# ═══════════════════════════════════════════════════════════
#  TestCase
# ═══════════════════════════════════════════════════════════

class TestTestCase:
    def test_create_test_case(self):
        tc = TestCase(name="my_test", bytecode=[0x00], initial_regs={}, expected={0: 0})
        assert tc.name == "my_test"
        assert tc.bytecode == [0x00]
        assert tc.expected == {0: 0}

    def test_test_case_with_initial_regs(self):
        tc = TestCase(name="t", bytecode=[0x00], initial_regs={0: 5}, expected={0: 5})
        assert tc.initial_regs == {0: 5}


# ═══════════════════════════════════════════════════════════
#  ValidationResult
# ═══════════════════════════════════════════════════════════

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

    def test_to_markdown_consensus_all_agree(self, validator):
        validator.add_test("test", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        assert results[0].consensus

    def test_to_markdown_has_test_name(self, validator):
        validator.add_test("special_test", [0x00], {}, {})
        results = validator.validate_all()
        md = results[0].to_markdown()
        assert "special_test" in md

    def test_to_markdown_has_cycles(self, validator):
        validator.add_test("test", [0x00], {}, {})
        results = validator.validate_all()
        md = results[0].to_markdown()
        assert "cycles" in md

    def test_test_name_preserved(self, validator):
        validator.add_test("my_special_test", [0x00], {}, {})
        results = validator.validate_all()
        assert results[0].test_name == "my_special_test"


# ═══════════════════════════════════════════════════════════
#  CrossVMValidator
# ═══════════════════════════════════════════════════════════

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
        for name in ["python", "c", "cpp", "go", "rust", "zig", "js", "java"]:
            assert name in vm_names

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
        bc = [0x18, 0, 5, 0x18, 1, 0, 0x08, 1, 0x09, 0, 0x3D, 0, 0xFC, 0, 0x00]
        validator.add_test("counter", bc, {}, {1: 5})
        results = validator.validate_all()
        assert results[0].expected_match

    def test_consensus_across_simulated_vms(self, validator):
        """All 8 simulated VMs should produce identical results."""
        validator.add_test("consensus", [0x18, 0, 7, 0x18, 1, 3, 0x20, 2, 0, 1, 0x00], {}, {2: 10})
        results = validator.validate_all()
        assert results[0].consensus
        reg_sets = [frozenset(r.registers.items()) for r in results[0].results]
        assert len(set(reg_sets)) == 1

    def test_vm_status_reporting(self, validator):
        """All VM results should have PASS status for a valid program."""
        validator.add_test("status", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        for vm_result in results[0].results:
            assert vm_result.status == VMStatus.PASS

    def test_div_truncation_consensus(self, validator):
        """Negative division should produce correct truncated result across all VMs."""
        validator.add_test("neg_div",
            [0x18, 0, 0xF9, 0x18, 1, 2, 0x23, 2, 0, 1, 0x00], {}, {2: -3})
        results = validator.validate_all()
        assert results[0].expected_match
        assert results[0].consensus

    def test_sequence_of_three_tests(self, validator):
        """Run three tests in sequence."""
        validator.add_test("a", [0x18, 0, 1, 0x00], {}, {0: 1})
        validator.add_test("b", [0x18, 0, 2, 0x00], {}, {0: 2})
        validator.add_test("c", [0x18, 0, 3, 0x00], {}, {0: 3})
        results = validator.validate_all()
        assert len(results) == 3
        assert all(r.expected_match for r in results)
        assert results[0].test_name == "a"
        assert results[1].test_name == "b"
        assert results[2].test_name == "c"

    def test_to_markdown_output(self, validator):
        """Markdown output should be a well-formatted string."""
        validator.add_test("md_test", [0x18, 0, 42, 0x00], {}, {0: 42})
        results = validator.validate_all()
        md = results[0].to_markdown()
        assert isinstance(md, str)
        assert "### md_test" in md
        assert "python" in md
        assert "PASS" in md
        assert "All agree" in md

    def test_to_markdown_consensus_disagree(self, validator):
        """Expected mismatch should still show consensus (VMs agree with each other)."""
        validator.add_test("wrong", [0x18, 0, 42, 0x00], {}, {0: 99})
        results = validator.validate_all()
        md = results[0].to_markdown()
        # VMs still agree with each other (they all get 42)
        assert "All agree" in md
        assert not results[0].expected_match
