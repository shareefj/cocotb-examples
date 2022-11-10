import cocotb
import threading
import logging
import queue
import grpc
import tb_pb2
import tb_pb2_grpc

from cocotb.queue import Queue
from cocotb.clock import Clock
from cocotb.triggers import RisingEdge, ReadOnly
from concurrent import futures
from google.protobuf import text_format

logging.basicConfig(level=logging.INFO)

class GrpcServer():
    class AddNumbersServicer(tb_pb2_grpc.AddNumbersServicer):
        def __init__(self, request_queue, response_queue, *, log):
            self.request_queue = request_queue
            self.response_queue = response_queue
            self.log = log

        def Add(self, request, context):
            self.log.info(f"Add request made, request=> {text_format.MessageToString(request, as_one_line=True)}")
            self.request_queue.put(request)
            response = self.response_queue.get()
            self.log.info(f"Returning response=> {text_format.MessageToString(response, as_one_line=True)}")
            return response

    def __init__(self, log):
        self.request_queue = queue.Queue()
        self.response_queue = queue.Queue()
        self.add_servicer = self.AddNumbersServicer(self.request_queue, self.response_queue, log=log)

    def get_request(self, func):
        try:
            cocotb.function(func)(self.request_queue.get(block=False))
        except queue.Empty:
            cocotb.function(func)(None)

    def put_response(self, item, func):
        self.response_queue.put(item)
        cocotb.function(func)()

    def start(self):
        self.thread = threading.Thread(target=self.serve)
        self.thread.start()

    def serve(self):
        server = grpc.server(futures.ThreadPoolExecutor(max_workers=1))
        tb_pb2_grpc.add_AddNumbersServicer_to_server(self.add_servicer, server)
        server.add_insecure_port("localhost:5000")
        server.start()
        server.wait_for_termination()


class Testbench():
    def __init__(self, dut):
        self.dut = dut
        self.ina = dut.ina
        self.inb = dut.inb
        self.res = dut.res
        self.rst = dut.rst_n
        self.clk = dut.clk
        self.log = dut._log

        self.rst.setimmediatevalue(1)
        self.ina.setimmediatevalue(0)
        self.inb.setimmediatevalue(0)

        self.request_queue = Queue()
        self.response_queue = Queue()
        self.grpc_server = GrpcServer(log=self.log)
        self.grpc_server.start()
        self.trxns = 0

        cocotb.start_soon(Clock(self.clk, 5, units='ns').start())
        cocotb.start_soon(self.request_thread())
        cocotb.start_soon(self.response_thread())
        cocotb.start_soon(self.worker_thread())

    async def push(self, item):
        if item is not None:
            self.request_queue.put_nowait(item)

    async def reset(self):
        self.rst.value = 0
        await RisingEdge(self.clk)
        self.rst.value = 1

    async def cycles(self, count: int):
        for _ in range(count):
            await RisingEdge(self.clk)

    async def add(self, a: int, b:int) -> int:
        self.ina.value = a
        self.inb.value = b
        await RisingEdge(self.clk)
        await ReadOnly()
        return self.res.value.integer

    async def worker_thread(self):
        while True:
            item = await self.request_queue.get()
            self.log.info(f"Driving request to RTL")
            res = await self.add(item.ina, item.inb)
            response = tb_pb2.AddResult(res=res)
            await self.response_queue.put(response)

    async def request_thread(self):
        while True:
            await RisingEdge(self.clk)
            await cocotb.external(self.grpc_server.get_request)(self.push)

    async def response_thread(self):
        while True:
            item = await self.response_queue.get()
            await cocotb.external(self.grpc_server.put_response)(item, self.null)

    async def null(self):
        self.trxns += 1


@cocotb.test()
async def test_remote(dut):
    tb = Testbench(dut)
    await tb.cycles(2)
    await tb.reset()

    while tb.trxns < 10:
        await tb.cycles(1)



