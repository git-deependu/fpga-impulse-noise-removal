// =============================================================================
// line_buffer.v
// -------------
// Parameterised single-row line buffer for a streaming 2-D image processor.
//
// Function
// --------
// Accepts one 8-bit pixel per clock cycle in raster-scan order.
// Outputs the delayed pixel that was written exactly IMAGE_WIDTH cycles earlier.
// Two instantiations of this module, together with an input register chain,
// construct the 3×3 sliding window required by the impulse-noise filter.
//
// Interface
// ---------
//  clk        : System clock (rising-edge triggered).
//  rst_n      : Active-low synchronous reset.
//  i_valid    : High when i_pixel carries a valid input pixel.
//  i_pixel    : 8-bit input pixel (current row).
//  o_pixel    : 8-bit output pixel (delayed by exactly IMAGE_WIDTH clock cycles).
//
// Parameters
// ----------
//  IMAGE_WIDTH : Number of pixels per image row (default 64).
//  PIXEL_WIDTH : Bit-width of each pixel (default 8).
// =============================================================================

`timescale 1ns / 1ps

module line_buffer #(
    parameter integer IMAGE_WIDTH = 64,
    parameter integer PIXEL_WIDTH = 8
)(
    input  wire                   clk,
    input  wire                   rst_n,
    input  wire                   i_valid,
    input  wire [PIXEL_WIDTH-1:0] i_pixel,
    output wire [PIXEL_WIDTH-1:0] o_pixel
);

    // -------------------------------------------------------------------------
    // Internal shift-register memory
    // -------------------------------------------------------------------------
    // Stores IMAGE_WIDTH pixels (one complete row).
    reg [PIXEL_WIDTH-1:0] mem [0:IMAGE_WIDTH-1];

    integer k;

    always @(posedge clk) begin
        if (!rst_n) begin
            for (k = 0; k < IMAGE_WIDTH; k = k + 1)
                mem[k] <= {PIXEL_WIDTH{1'b0}};
        end else if (i_valid) begin
            begin : shift_loop
                integer i;
                for (i = IMAGE_WIDTH-1; i > 0; i = i - 1)
                    mem[i] <= mem[i-1];
            end
            mem[0] <= i_pixel;
        end
    end

    // Combinational output from the last shift-register element
    // Total latency through mem[0]..mem[IMAGE_WIDTH-1] is exactly IMAGE_WIDTH cycles.
    assign o_pixel = mem[IMAGE_WIDTH-1];

endmodule
