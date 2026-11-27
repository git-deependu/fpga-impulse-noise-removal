// =============================================================================
// tb_impulse_noise_filter.v
// -------------------------
// Self-checking testbench for the impulse_noise_filter top-level module.
// =============================================================================

`timescale 1ns / 1ps

module tb_impulse_noise_filter;

    // ── Parameters ────────────────────────────────────────────────────────────
    parameter integer IMAGE_WIDTH   = 64;
    parameter integer IMAGE_HEIGHT  = 64;
    parameter integer PIXEL_WIDTH   = 8;
    parameter integer CLK_PERIOD_NS = 10;

    localparam integer N_PIXELS    = IMAGE_WIDTH * IMAGE_HEIGHT;   // 4096
    localparam integer DRAIN_EXTRA = IMAGE_WIDTH + 30;

    // ── File paths (relative to rtl/tb/) ─────────────────────────────────────
    `define INPUT_FILE    "../../software_model/results/synthetic_noisy_10pct.raw"
    `define EXPECTED_FILE "../../software_model/results/synthetic_hw_ref_10pct.raw"
    `define OUTPUT_FILE   "../sim_out/dut_output.raw"

    // ── DUT signals ───────────────────────────────────────────────────────────
    reg                    clk     = 0;
    reg                    rst_n   = 0;
    reg                    i_valid = 0;
    reg  [PIXEL_WIDTH-1:0] i_pixel = 0;
    wire                   o_valid;
    wire [PIXEL_WIDTH-1:0] o_pixel;

    // ── DUT instantiation ─────────────────────────────────────────────────────
    impulse_noise_filter #(
        .IMAGE_WIDTH (IMAGE_WIDTH),
        .IMAGE_HEIGHT(IMAGE_HEIGHT),
        .PIXEL_WIDTH (PIXEL_WIDTH)
    ) dut (
        .clk    (clk),
        .rst_n  (rst_n),
        .i_valid(i_valid),
        .i_pixel(i_pixel),
        .o_valid(o_valid),
        .o_pixel(o_pixel)
    );

    // ── Clock generation (100 MHz) ───────────────────────────────────────────
    always #(CLK_PERIOD_NS / 2) clk = ~clk;

    // ── Image memories ────────────────────────────────────────────────────────
    reg [PIXEL_WIDTH-1:0] input_mem    [0:N_PIXELS-1];
    reg [PIXEL_WIDTH-1:0] expected_mem [0:N_PIXELS-1];
    reg [PIXEL_WIDTH-1:0] output_mem   [0:N_PIXELS-1];

    // ── Output collector ──────────────────────────────────────────────────────
    integer out_idx = 0;
    always @(negedge clk) begin
        if (o_valid && out_idx < N_PIXELS) begin
            output_mem[out_idx] = o_pixel;
            out_idx = out_idx + 1;
        end
    end

    // ── VCD dump for GTKWave ──────────────────────────────────────────────────
    initial begin
        $dumpfile("../sim_out/tb_impulse_noise_filter.vcd");
        $dumpvars(0, tb_impulse_noise_filter);
    end

    // ── Main stimulus ─────────────────────────────────────────────────────────
    integer in_idx;
    integer mismatch_count;
    integer i;
    integer fd;
    reg [1023:0] input_file;
    reg [1023:0] expected_file;
    reg [1023:0] output_file;

    initial begin
        if (!$value$plusargs("INPUT_FILE=%s", input_file))
            input_file = `INPUT_FILE;
        if (!$value$plusargs("EXPECTED_FILE=%s", expected_file))
            expected_file = `EXPECTED_FILE;
        if (!$value$plusargs("OUTPUT_FILE=%s", output_file))
            output_file = `OUTPUT_FILE;

        // Load files
        $readmemh(input_file,    input_mem);
        $readmemh(expected_file, expected_mem);

        $display("==========================================================");
        $display("  tb_impulse_noise_filter: RTL Verification");
        $display("  Resolution : %0d x %0d  (%0d pixels)", IMAGE_WIDTH, IMAGE_HEIGHT, N_PIXELS);
        $display("  Input File : %0s", input_file);
        $display("  Golden Ref : %0s", expected_file);
        $display("==========================================================");

        // ── Reset ─────────────────────────────────────────────────────────────
        rst_n   = 0;
        i_valid = 0;
        i_pixel = 0;
        repeat(4) @(posedge clk);
        @(negedge clk);
        rst_n   = 1;

        // ── Stream all input pixels ───────────────────────────────────────────
        for (in_idx = 0; in_idx < N_PIXELS; in_idx = in_idx + 1) begin
            @(negedge clk);
            i_valid = 1;
            i_pixel = input_mem[in_idx];
        end

        // Stream dummy pixels to drain the line buffer pipeline completely
        for (in_idx = 0; in_idx < IMAGE_WIDTH + 15; in_idx = in_idx + 1) begin
            @(negedge clk);
            i_pixel = 0;
        end
        @(negedge clk);
        i_valid = 0;

        repeat(DRAIN_EXTRA) @(posedge clk);

        $display("  Output pixels collected : %0d / %0d", out_idx, N_PIXELS);

        // ── Pixel-by-pixel comparison against golden reference ────────────────
        mismatch_count = 0;
        for (i = 0; i < N_PIXELS; i = i + 1) begin
            if (output_mem[i] !== expected_mem[i]) begin
                if (mismatch_count < 20)
                    $display("  MISMATCH @ pixel[%04d]  got=0x%02h  exp=0x%02h",
                             i, output_mem[i], expected_mem[i]);
                mismatch_count = mismatch_count + 1;
            end
        end

        // ── Save DUT output ───────────────────────────────────────────────────
        fd = $fopen(output_file, "w");
        if (fd != 0) begin
            for (i = 0; i < N_PIXELS; i = i + 1)
                $fwrite(fd, "%02h\n", output_mem[i]);
            $fclose(fd);
            $display("  DUT output saved to %0s", output_file);
        end

        // ── Result Summary ────────────────────────────────────────────────────
        $display("==========================================================");
        if (out_idx < N_PIXELS) begin
            $display("  RESULT : INCOMPLETE — only %0d of %0d pixels received.",
                     out_idx, N_PIXELS);
        end else if (mismatch_count == 0) begin
            $display("  RESULT : PASS  -- 100%% BIT-EXACT MATCH!");
            $display("  All %0d pixels match the software golden reference.", N_PIXELS);
        end else begin
            $display("  RESULT : FAIL  -- %0d / %0d pixels differ.",
                     mismatch_count, N_PIXELS);
        end
        $display("==========================================================");

        $finish;
    end

endmodule
