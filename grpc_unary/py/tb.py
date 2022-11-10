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
    """ This class wraps the gRPC server such that we can interface with a Cocotb testbench.
    
    The server must be run in a separate thread and we make use of the cocotb.external and
    cocotb.function decorators. 

    https://docs.cocotb.org/en/stable/library_reference.html?highlight=external#cocotb.external

    """
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
        """ Get a gRPC request if there is one available.
        
        This method must be called as a cocotb.external decorated function. It then passes control
        back to Cocotb by calling the callback `func` using the cocotb.function decorator.

        If there is a valid request in the queue we return that otherwise None.  We can't block 
        here as simulation time will not continue.

        Args:
          func: a callback function that accepts a request item
        
        """
        try:
            cocotb.function(func)(self.request_queue.get(block=False))
        except queue.Empty:
            cocotb.function(func)(None)

    def put_response(self, response, func):
        """ Puts a gRPC response.

        This method appends the gRPC response onto the internal queue and then calls the callback
        `func` with no arguments.  This callback must be called in order to return control back to
        the Cocotb thread but it doesn't have do anything.
        
        """
        self.response_queue.put(response)
        cocotb.function(func)()

    def start(self):
        """ Creates a new thread from which to start the gRPC server. 
        
        """
        self.thread = threading.Thread(target=self.serve)
        self.thread.start()

    def serve(self):
        """ Start the gRPC server.

        This is taken directly from the gRPC examples.

        """
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

        self.log.info("Starting gRPC server")
        self.request_queue = Queue()
        self.response_queue = Queue()
        self.grpc_server = GrpcServer(log=self.log)
        self.grpc_server.start()
        self.trxns = 0

        cocotb.start_soon(Clock(self.clk, 5, units='ns').start())
        cocotb.start_soon(self.request_thread())
        cocotb.start_soon(self.response_thread())
        cocotb.start_soon(self.worker_thread())

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
        """ Drives transaction to DUT.
        
        This coroutines sits and waits for new requests to arrive and then drives them to the
        DUT. In this simple example the response is available one cycle later and can be pushed
        onto the response queue ready to be passed back to the gRPC server.

        Note that the request/response types are tb_pb2.AddOperands/tb_pb2.AddResult respectively.

        """
        while True:
            request = await self.request_queue.get()
            self.log.info(f"Driving request to RTL")
            res = await self.add(request.ina, request.inb)
            response = tb_pb2.AddResult(res=res)
            await self.response_queue.put(response)

    async def request_thread(self):
        """ Gets requests from the gRPC server.

        This coroutine polls the server every cycle for new requests and if one is available, it
        is returned via the get_request_cb callback.

        """
        while True:
            await RisingEdge(self.clk)
            await cocotb.external(self.grpc_server.get_request)(self.get_request_cb)

    async def response_thread(self):
        """ Returns responses to the gRPC server. 
        
        This coroutine pops responses from the respone_queue and pushes them to the server. The
        put_response_cb callback doesn't do anything but is required to enable control to be returned
        to Cocotb using a cocotb.function decorator.

        """
        while True:
            response = await self.response_queue.get()
            await cocotb.external(self.grpc_server.put_response)(response, self.put_response_cb)

    async def get_request_cb(self, request):
        """ Callback function.
        
        Called by the gRPC server in response to a call to grpc_server.get_request. If a valid
        `request` is passed in, it is pushed onto the local queue.

        """
        if request is not None:
            self.request_queue.put_nowait(request)

    async def put_response_cb(self):
        """ Callback function.
        
        Called by the gRPC server after a response has been accepted.

        """
        self.trxns += 1


@cocotb.test()
async def test_remote(dut):
    tb = Testbench(dut)
    await tb.cycles(2)
    await tb.reset()

    tb.log.info("Waiting for transactions...")
    while tb.trxns < 10:
        await tb.cycles(1)



