# =============================================================================
# Makefile — FPGA Impulse Noise Removal Project
# =============================================================================
# Targets:
#   make software      → run Python reference model (evaluate.py)
#   make export        → export PNGs to raw hex for $readmemh
#   make sim           → compile and simulate RTL with Icarus Verilog
#   make wave          → open GTKWave with the VCD dump
#   make clean         → remove generated files
#   make all           → software + export + sim
# =============================================================================

PYTHON    := python
IVERILOG  := iverilog
VVP       := vvp
GTKWAVE   := gtkwave

SW_DIR    := software_model
RTL_SRC   := rtl/src
RTL_TB    := rtl/tb
SIM_OUT   := rtl/sim_out

# ── Software reference model ─────────────────────────────────────────────────
.PHONY: software
software:
	cd $(SW_DIR) && $(PYTHON) evaluate.py

# ── Export PNGs to raw hex files for testbench ───────────────────────────────
.PHONY: export
export:
	cd $(SW_DIR) && $(PYTHON) export_raw.py --dir results/

# ── RTL simulation ───────────────────────────────────────────────────────────
RTL_SRCS = $(RTL_SRC)/line_buffer.v \
           $(RTL_SRC)/window_generator.v \
           $(RTL_SRC)/noise_detector.v \
           $(RTL_SRC)/median_filter_3x3.v \
           $(RTL_SRC)/impulse_noise_filter.v \
           $(RTL_TB)/tb_impulse_noise_filter.v

SIM_EXE   = $(SIM_OUT)/sim_impulse_noise.vvp
VCD_FILE  = $(SIM_OUT)/tb_impulse_noise_filter.vcd

.PHONY: sim
sim: $(SIM_OUT)
	$(IVERILOG) -g2012 -o $(SIM_EXE) $(RTL_SRCS)
	$(VVP) $(SIM_EXE)

$(SIM_OUT):
	mkdir -p $(SIM_OUT)

# ── GTKWave ──────────────────────────────────────────────────────────────────
.PHONY: wave
wave:
	$(GTKWAVE) $(VCD_FILE) &

# ── Clean ─────────────────────────────────────────────────────────────────────
.PHONY: clean
clean:
	rm -f $(SIM_OUT)/*.vvp $(SIM_OUT)/*.vcd $(SIM_OUT)/*.raw
	rm -f $(SW_DIR)/results/*.raw
	rm -f $(SW_DIR)/results/*.png
	rm -f $(SW_DIR)/results/*.csv

# ── All ───────────────────────────────────────────────────────────────────────
.PHONY: all
all: software export sim
