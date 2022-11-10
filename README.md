# cocotb-examples

This is a collection of Cocotb examples.

## grpc_unary

This example uses a unary gRPC service to send addition operands to a Cocotb testbench.  The
testbench drives the operands to the DUT and gets the result of the addition which it then
sends back as a response.

### Running the testbench

```
. sourceme
cd grpc_unary
make
```

Then in a separate terminal:

```
. sourceme
grpc_unary/py/grpc_client.py <opa> <opb>
```