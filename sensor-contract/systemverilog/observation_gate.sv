module apolo_observation_gate(
  input  logic valid_record,
  input  logic valid_name,
  input  logic valid_value,
  input  logic allowed_origin,
  input  logic valid_source,
  input  logic valid_timestamp,
  output logic accepted
);
  always_comb accepted = valid_record && valid_name && valid_value &&
                         allowed_origin && valid_source && valid_timestamp;
endmodule

module tb;
  logic valid_record, valid_name, valid_value, allowed_origin, valid_source, valid_timestamp;
  logic accepted;
  apolo_observation_gate dut(.*);
  initial begin
    valid_record=1; valid_name=1; valid_value=1; allowed_origin=1; valid_source=1; valid_timestamp=1;
    #1; if (!accepted) $fatal(1, "valid observation rejected");
    allowed_origin=0;
    #1; if (accepted) $fatal(1, "test/unknown origin accepted");
    $display("SYSTEMVERILOG_GATE_PASS");
    $finish;
  end
endmodule
