// =============================================================================
// window_generator.v
// ------------------
// Generates a streaming 3×3 pixel window for a raster-scan image.
//
// Architecture
// ------------
//   Input pixel stream (row-major, left-to-right, top-to-bottom)
//        │
//        ├─── row_reg[0..2]   : Horizontal shift register for current row
//        │
//        │    line_buffer_0   : Delays by IMAGE_WIDTH cycles → previous row
//        │         │
//        │    row_reg[3..5]   : Horizontal shift register for row-1
//        │         │
//        │    line_buffer_1   : Delays by IMAGE_WIDTH cycles → two rows ago
//        │         │
//        │    row_reg[6..8]   : Horizontal shift register for row-2
//        │
//        └─── o_window[8:0][7:0] : Nine pixels, row-major, centre = [4]
//
// Window layout (o_window indices)
// ---------------------------------
//   [0][1][2]   ← oldest row (row n-2)
//   [3][4][5]   ← middle row (row n-1)  ← [4] is the centre pixel
//   [6][7][8]   ← current row (row n)
//
// Valid signal
// ------------
//   o_valid is asserted once the pipeline is filled (2×IMAGE_WIDTH + 2 cycles
//   after the first valid input pixel on a fresh frame).
//   It follows i_valid exactly after that point.
//
// Parameters
// ----------
//   IMAGE_WIDTH  : Pixels per row (default 64).
//   IMAGE_HEIGHT : Rows per frame (default 64).
//   PIXEL_WIDTH  : Bit-width of each pixel (default 8).
// =============================================================================

`timescale 1ns / 1ps

module window_generator #(
    parameter integer IMAGE_WIDTH  = 64,
    parameter integer IMAGE_HEIGHT = 64,
    parameter integer PIXEL_WIDTH  = 8
)(
    input  wire                          clk,
    input  wire                          rst_n,
    // Input pixel stream
    input  wire                          i_valid,
    input  wire [PIXEL_WIDTH-1:0]        i_pixel,
    // 3×3 window output (9 pixels × PIXEL_WIDTH bits each)
    output wire [PIXEL_WIDTH-1:0]        o_window [0:8],
    output wire                          o_valid
);

    // -------------------------------------------------------------------------
    // Line-buffer outputs (one-row and two-row delayed pixels)
    // -------------------------------------------------------------------------
    wire [PIXEL_WIDTH-1:0] lb0_out;   // pixel delayed by IMAGE_WIDTH (row n-1)
    wire [PIXEL_WIDTH-1:0] lb1_out;   // pixel delayed by 2×IMAGE_WIDTH (row n-2)

    line_buffer #(
        .IMAGE_WIDTH(IMAGE_WIDTH),
        .PIXEL_WIDTH(PIXEL_WIDTH)
    ) u_lb0 (
        .clk    (clk),
        .rst_n  (rst_n),
        .i_valid(i_valid),
        .i_pixel(i_pixel),
        .o_pixel(lb0_out)
    );

    line_buffer #(
        .IMAGE_WIDTH(IMAGE_WIDTH),
        .PIXEL_WIDTH(PIXEL_WIDTH)
    ) u_lb1 (
        .clk    (clk),
        .rst_n  (rst_n),
        .i_valid(i_valid),
        .i_pixel(lb0_out),
        .o_pixel(lb1_out)
    );

    // -------------------------------------------------------------------------
    // Three horizontal shift registers — one per buffered row
    // Row 2 (current):  row_r[0..2], row_r[2] is the rightmost (newest)
    // Row 1 (previous): row_m[0..2]
    // Row 0 (oldest):   row_t[0..2]
    // -------------------------------------------------------------------------
    reg [PIXEL_WIDTH-1:0] row_r [0:2];   // current row
    reg [PIXEL_WIDTH-1:0] row_m [0:2];   // row n-1
    reg [PIXEL_WIDTH-1:0] row_t [0:2];   // row n-2

    always @(posedge clk) begin
        if (!rst_n) begin : rst_block
            integer i;
            for (i = 0; i < 3; i = i + 1) begin
                row_r[i] <= {PIXEL_WIDTH{1'b0}};
                row_m[i] <= {PIXEL_WIDTH{1'b0}};
                row_t[i] <= {PIXEL_WIDTH{1'b0}};
            end
        end else if (i_valid) begin
            // Shift current-row pixels left (oldest at index 0)
            row_r[0] <= row_r[1];
            row_r[1] <= row_r[2];
            row_r[2] <= i_pixel;

            row_m[0] <= row_m[1];
            row_m[1] <= row_m[2];
            row_m[2] <= lb0_out;

            row_t[0] <= row_t[1];
            row_t[1] <= row_t[2];
            row_t[2] <= lb1_out;
        end
    end

    // -------------------------------------------------------------------------
    // Window output mapping
    // [0][1][2]  ←  top    row (n-2)
    // [3][4][5]  ←  middle row (n-1),  [4] = centre pixel
    // [6][7][8]  ←  bottom row (n)
    // -------------------------------------------------------------------------
    assign o_window[0] = row_t[0];
    assign o_window[1] = row_t[1];
    assign o_window[2] = row_t[2];
    assign o_window[3] = row_m[0];
    assign o_window[4] = row_m[1];   // ← centre pixel
    assign o_window[5] = row_m[2];
    assign o_window[6] = row_r[0];
    assign o_window[7] = row_r[1];
    assign o_window[8] = row_r[2];

    // -------------------------------------------------------------------------
    // Valid signal generation
    // o_valid is asserted once pixel (0,0) reaches the centre position win[4].
    // Latency to centre position = IMAGE_WIDTH + 2 clock cycles.
    // -------------------------------------------------------------------------
    localparam integer FILL_LATENCY = IMAGE_WIDTH + 2;

    reg [$clog2(FILL_LATENCY+1)-1:0] fill_cnt;
    reg                               pipeline_filled;

    always @(posedge clk) begin
        if (!rst_n) begin
            fill_cnt        <= 0;
            pipeline_filled <= 1'b0;
        end else begin
            if (!pipeline_filled && i_valid) begin
                if (fill_cnt == FILL_LATENCY - 1) begin
                    pipeline_filled <= 1'b1;
                end else begin
                    fill_cnt <= fill_cnt + 1;
                end
            end
        end
    end

    assign o_valid = pipeline_filled & i_valid;

endmodule
