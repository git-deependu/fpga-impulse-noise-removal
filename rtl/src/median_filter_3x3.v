// =============================================================================
// median_filter_3x3.v
// --------------------
// Hardware-optimised 3×3 median computation for 8-bit grayscale pixels.
//
// Algorithm — Partial-order comparator network (Batcher-style)
// -------------------------------------------------------------
// Pipelined network of compare-and-swap (CAS) operations across 4 stages.
//
// Pipeline stages
// ---------------
//   Stage 0 : Inputs latched into s0 (window pixels)
//   Stage 1 : First 12 CAS pairs
//   Stage 2 : Next 8 CAS pairs
//   Stage 3 : Next 4 CAS pairs
//   Stage 4 : Final 1 CAS pair — median available on o_median
//
// Interface
// ---------
//   clk        : System clock.
//   rst_n      : Active-low synchronous reset.
//   i_valid    : Input window is valid.
//   i_window   : 9 pixels × PIXEL_WIDTH bits (row-major, centre = [4]).
//   o_median   : Computed median pixel value (PIXEL_WIDTH bits).
//   o_valid    : Asserted with pipeline latency = 5 cycles.
// =============================================================================

`timescale 1ns / 1ps

module median_filter_3x3 #(
    parameter integer PIXEL_WIDTH = 8
)(
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   i_valid,
    input  wire [PIXEL_WIDTH-1:0] i_window [0:8],
    output reg  [PIXEL_WIDTH-1:0] o_median,
    output reg                    o_valid
);

    // -------------------------------------------------------------------------
    // Safe Compare-and-Swap macro with temporary variable
    // Ensures (lo <= hi) without destroying values on blocking assignment
    // -------------------------------------------------------------------------
    `define CAS(a, b) \
        if (t[a] > t[b]) begin \
            cas_tmp = t[a]; \
            t[a] = t[b]; \
            t[b] = cas_tmp; \
        end

    // -------------------------------------------------------------------------
    // Pipeline registers (5 stages × 9 pixels)
    // -------------------------------------------------------------------------
    reg [PIXEL_WIDTH-1:0] s0 [0:8];
    reg [PIXEL_WIDTH-1:0] s1 [0:8];
    reg [PIXEL_WIDTH-1:0] s2 [0:8];
    reg [PIXEL_WIDTH-1:0] s3 [0:8];
    reg [PIXEL_WIDTH-1:0] s4 [0:8];

    // Valid pipeline (5 cycles total latency from i_valid to o_valid)
    reg [3:0] valid_pipe;

    // -------------------------------------------------------------------------
    // Stage 0 — Input latch (Cycle 1)
    // -------------------------------------------------------------------------
    always @(posedge clk) begin : stage0
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) s0[i] <= {PIXEL_WIDTH{1'b0}};
        end else begin
            for (i = 0; i < 9; i = i + 1) s0[i] <= i_window[i];
        end
    end

    // -------------------------------------------------------------------------
    // Stage 1 — First 12 CAS pairs (Cycle 2)
    // -------------------------------------------------------------------------
    always @(posedge clk) begin : stage1
        reg [PIXEL_WIDTH-1:0] t [0:8];
        reg [PIXEL_WIDTH-1:0] cas_tmp;
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) s1[i] <= {PIXEL_WIDTH{1'b0}};
        end else begin
            for (i = 0; i < 9; i = i + 1) t[i] = s0[i];

            `CAS(0, 1);
            `CAS(3, 4);
            `CAS(6, 7);
            `CAS(1, 2);
            `CAS(4, 5);
            `CAS(7, 8);
            `CAS(0, 1);
            `CAS(3, 4);
            `CAS(6, 7);
            `CAS(0, 3);
            `CAS(3, 6);
            `CAS(0, 3);

            for (i = 0; i < 9; i = i + 1) s1[i] <= t[i];
        end
    end

    // -------------------------------------------------------------------------
    // Stage 2 — Next 8 CAS pairs (Cycle 3)
    // -------------------------------------------------------------------------
    always @(posedge clk) begin : stage2
        reg [PIXEL_WIDTH-1:0] t [0:8];
        reg [PIXEL_WIDTH-1:0] cas_tmp;
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) s2[i] <= {PIXEL_WIDTH{1'b0}};
        end else begin
            for (i = 0; i < 9; i = i + 1) t[i] = s1[i];

            `CAS(1, 4);
            `CAS(4, 7);
            `CAS(1, 4);
            `CAS(2, 5);
            `CAS(5, 8);
            `CAS(2, 5);
            `CAS(2, 4);
            `CAS(4, 6);

            for (i = 0; i < 9; i = i + 1) s2[i] <= t[i];
        end
    end

    // -------------------------------------------------------------------------
    // Stage 3 — Next 4 CAS pairs (Cycle 4)
    // -------------------------------------------------------------------------
    always @(posedge clk) begin : stage3
        reg [PIXEL_WIDTH-1:0] t [0:8];
        reg [PIXEL_WIDTH-1:0] cas_tmp;
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) s3[i] <= {PIXEL_WIDTH{1'b0}};
        end else begin
            for (i = 0; i < 9; i = i + 1) t[i] = s2[i];

            `CAS(2, 4);
            `CAS(3, 4);
            `CAS(4, 5);
            `CAS(4, 6);

            for (i = 0; i < 9; i = i + 1) s3[i] <= t[i];
        end
    end

    // -------------------------------------------------------------------------
    // Stage 4 — Final comparison; median is at t[4] (Cycle 5)
    // -------------------------------------------------------------------------
    always @(posedge clk) begin : stage4
        reg [PIXEL_WIDTH-1:0] t [0:8];
        reg [PIXEL_WIDTH-1:0] cas_tmp;
        integer i;
        if (!rst_n) begin
            for (i = 0; i < 9; i = i + 1) s4[i] <= {PIXEL_WIDTH{1'b0}};
            o_median <= {PIXEL_WIDTH{1'b0}};
        end else begin
            for (i = 0; i < 9; i = i + 1) t[i] = s3[i];

            `CAS(3, 4);

            for (i = 0; i < 9; i = i + 1) s4[i] <= t[i];
            o_median <= t[4];   // Median output
        end
    end

    // -------------------------------------------------------------------------
    // Valid shift register (pipeline latency = 5 cycles from i_valid)
    // -------------------------------------------------------------------------
    always @(posedge clk) begin
        if (!rst_n) begin
            valid_pipe <= 4'b0;
            o_valid    <= 1'b0;
        end else begin
            valid_pipe <= {valid_pipe[2:0], i_valid};
            o_valid    <= valid_pipe[3];
        end
    end

    `undef CAS

endmodule
