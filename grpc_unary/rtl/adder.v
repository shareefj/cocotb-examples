// ----------------------------------------------------------------------
// Copyright 2022 IDEX ASA. All Rights Reserved. www.idexbiometrics.com
//
//
// IDEX ASA is the owner of this RTL and all intellectual property rights
// in and to the RTL. The RTL may only be used together with IDEX
// fingerprint sensors, unless otherwise permitted by IDEX ASA in writing.
//
//
// This copyright notice must not be altered or removed from the RTL.
//
//
// DISCLAIMER OF WARRANTY/LIMITATION OF REMEDIES: unless otherwise agreed, IDEX
// ASA has no obligation to support this RTL, and the RTL is provided
// "AS IS", with no express or implied warranties of any kind, and IDEX ASA is
// not to be liable for any damages, any relief, or for any claim by any third
// party, arising from use of this RTL.
//
// Image capture and processing logic is defined and controlled by IDEX ASA in
// order to maximize FAR/FRR performance.
// ----------------------------------------------------------------------


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

// Local Variables:
// verilog-library-directories:(".")
// End:
