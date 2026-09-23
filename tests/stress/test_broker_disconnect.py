"""Stress test: broker disconnect handling."""
from unittest.mock import MagicMock
from agents.execution.order_manager import OrderManager, OrderState

def test_submit_fails_gracefully():
    mock = MagicMock()
    mock.submit_order.side_effect = ConnectionError("Broker disconnected")
    mgr = OrderManager(connector=mock)
    managed = mgr.submit("fail-1", "AAPL", 10, "buy")
    assert managed.state == OrderState.FAILED

def test_poll_handles_error():
    mock = MagicMock()
    from agents.execution.broker.alpaca import AlpacaOrder
    mock.submit_order.return_value = AlpacaOrder("b-1","AAPL","buy",10,0,"submitted")
    mock.get_order.side_effect = ConnectionError("Broker disconnected")
    mgr = OrderManager(connector=mock)
    mgr.submit("fail-2", "AAPL", 10, "buy")
    result = mgr.poll("fail-2")
    assert result.state == OrderState.SUBMITTED  # stays in submitted, doesn't crash
