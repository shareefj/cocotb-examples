// Copyright IDEX Biometrics
// Licensed under the MIT License, see LICENSE
// SPDX-License-Identifier: MIT

module adder (
  input wire         clk,
  input wire         rst_n,
  input wire [31:0]  ina,
  input wire [31:0]  inb,
  output wire [31:0] res,
  output wire        ovfl
);

// ----------------------------------------------------------------------
// Logic Declarations
// ----------------------------------------------------------------------

reg [32:0] add_q;
wire [32:0] add_d;

// ----------------------------------------------------------------------
// 32-bit unsigned counter
// ----------------------------------------------------------------------

assign add_d = ina + inb;

always @(posedge clk or negedge rst_n) begin
  if (!rst_n) begin
    add_q <= '0;
  end else begin
    add_q <= add_d;
  end
end

assign res = add_q[31:0];
assign ovfl = add_q[32];

initial begin
  $dumpfile("waves.vcd");
  $dumpvars(0,adder);
end

endmodule
