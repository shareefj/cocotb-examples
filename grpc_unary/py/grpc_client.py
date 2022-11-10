#!/usr/bin/env python3

import grpc
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'proto'))

import tb_pb2
import tb_pb2_grpc

def main(args):
    with grpc.insecure_channel("localhost:5000") as channel:
        stub = tb_pb2_grpc.AddNumbersStub(channel)
        add_request = tb_pb2.AddOperands(ina=args.operand_a, inb=args.operand_b)
        add_response = stub.Add(add_request)
        print(add_response)

if __name__ == "__main__":

    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument("operand_a", type=int, help="operands to add")
    parser.add_argument("operand_b", type=int, help="operands to add")
    args = parser.parse_args()

    main(args)