// =============================================================================
// noise_detector.v
// ----------------
// Threshold-based impulse-noise detector for 8-bit grayscale pixels.
//
// Detection criterion
// -------------------
//   A pixel is classified as corrupted (salt or pepper) if and only if:
//     pixel == 8'h00   (pepper / minimum intensity)   OR
//     pixel == 8'hFF   (salt   / maximum intensity)
//
//   This is the simplest and most hardware-efficient noise-detection strategy.
//   It is reliable when the noise model is pure salt-and-pepper (impulse
//   values are always 0 or 255), which matches the project scope.
//
// Interface
// ---------
//   i_pixel    : 8-bit centre pixel from the 3×3 window.
//   o_noisy    : 1 → pixel is classified as corrupted; 0 → pass through.
//
// Note: This is a purely combinational module — no registers.
// =============================================================================

`timescale 1ns / 1ps

module noise_detector #(
    parameter integer PIXEL_WIDTH = 8
)(
    input  wire [PIXEL_WIDTH-1:0] i_pixel,
    output wire                   o_noisy
);

    localparam [PIXEL_WIDTH-1:0] PEPPER = {PIXEL_WIDTH{1'b0}};   // 0x00
    localparam [PIXEL_WIDTH-1:0] SALT   = {PIXEL_WIDTH{1'b1}};   // 0xFF

    assign o_noisy = (i_pixel == PEPPER) | (i_pixel == SALT);

endmodule
