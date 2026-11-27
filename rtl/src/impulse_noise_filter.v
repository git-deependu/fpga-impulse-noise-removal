// =============================================================================
// impulse_noise_filter.v
// ----------------------
// Top-level FPGA architecture for impulse (salt-and-pepper) noise removal
// from an 8-bit grayscale digital image.
//
// System overview
// ---------------
//
//   i_pixel ──► window_generator ──► noise_detector ──────────────────►─┐
//                    │                     │                              │
//                    │                  o_noisy                    select_mux
//                    │                     │                              │
//                    └──► median_filter ──►─┘                             │
//                               │                                         │
//                           o_median ──────────────────────────────────►─┘
//                                                                         │
//                                                              o_pixel (filtered)
//
// The centre pixel of each 3×3 window is inspected by the noise detector.
//   • If the pixel is NOT noisy → pass the original centre pixel through.
//   • If the pixel IS noisy     → replace it with the computed 3×3 median.
//
// Pipeline management
// -------------------
// The median_filter_3x3 sub-module has a 4-cycle pipeline latency.  The
// centre pixel and the noisy flag are delayed by the same 4 cycles before
// the output multiplexer so that they align with the median output.
//
// Latency  : window_fill_cycles + 4  (median pipeline)
// Throughput: 1 pixel / clock (after pipeline fill)
//
// Parameters
// ----------
//   IMAGE_WIDTH  : Pixels per row (default 64).
//   IMAGE_HEIGHT : Rows per frame (default 64).
//   PIXEL_WIDTH  : Bit-width of each pixel (default 8).
// =============================================================================

`timescale 1ns / 1ps

module impulse_noise_filter #(
    parameter integer IMAGE_WIDTH  = 64,
    parameter integer IMAGE_HEIGHT = 64,
    parameter integer PIXEL_WIDTH  = 8
)(
    input  wire                   clk,
    input  wire                   rst_n,
    // Input stream
    input  wire                   i_valid,
    input  wire [PIXEL_WIDTH-1:0] i_pixel,
    // Output stream
    output wire                   o_valid,
    output wire [PIXEL_WIDTH-1:0] o_pixel
);

    // =========================================================================
    // 1. Window generator
    // =========================================================================
    wire [PIXEL_WIDTH-1:0] win [0:8];
    wire                   win_valid;

    window_generator #(
        .IMAGE_WIDTH (IMAGE_WIDTH),
        .IMAGE_HEIGHT(IMAGE_HEIGHT),
        .PIXEL_WIDTH (PIXEL_WIDTH)
    ) u_win_gen (
        .clk     (clk),
        .rst_n   (rst_n),
        .i_valid (i_valid),
        .i_pixel (i_pixel),
        .o_window(win),
        .o_valid (win_valid)
    );

    // =========================================================================
    // 2. Noise detector (combinational — centre pixel = win[4])
    // =========================================================================
    wire centre_noisy;

    noise_detector #(
        .PIXEL_WIDTH(PIXEL_WIDTH)
    ) u_nd (
        .i_pixel(win[4]),
        .o_noisy(centre_noisy)
    );

    // =========================================================================
    // 3. Median filter (4-cycle pipeline)
    // =========================================================================
    wire [PIXEL_WIDTH-1:0] median_out;
    wire                   median_valid;

    median_filter_3x3 #(
        .PIXEL_WIDTH(PIXEL_WIDTH)
    ) u_med (
        .clk     (clk),
        .rst_n   (rst_n),
        .i_valid (win_valid),
        .i_window(win),
        .o_median(median_out),
        .o_valid (median_valid)
    );

    // =========================================================================
    // 4. Align centre_pixel and noisy flag with median pipeline (5 cycles)
    // =========================================================================
    localparam integer MED_LATENCY = 5;

    reg [PIXEL_WIDTH-1:0] centre_delay [0:MED_LATENCY-1];
    reg                   noisy_delay  [0:MED_LATENCY-1];

    always @(posedge clk) begin : delay_chain
        integer i;
        if (!rst_n) begin
            for (i = 0; i < MED_LATENCY; i = i + 1) begin
                centre_delay[i] <= {PIXEL_WIDTH{1'b0}};
                noisy_delay[i]  <= 1'b0;
            end
        end else begin
            // Always shift — mirrors the always-running median pipeline stages 1-4
            centre_delay[0] <= win[4];
            noisy_delay[0]  <= centre_noisy;
            for (i = 1; i < MED_LATENCY; i = i + 1) begin
                centre_delay[i] <= centre_delay[i-1];
                noisy_delay[i]  <= noisy_delay[i-1];
            end
        end
    end

    // =========================================================================
    // 5. Output multiplexer
    // =========================================================================
    assign o_valid = median_valid;
    assign o_pixel = noisy_delay[MED_LATENCY-1] ? median_out
                                                 : centre_delay[MED_LATENCY-1];

endmodule
