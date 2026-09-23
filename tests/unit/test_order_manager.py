"""Test order manager lifecycle."""
from unittest.mock import MagicMock
from agents.execution.order_manager import OrderManager, OrderState
from agents.execution.broker.alpaca import AlpacaOrder

def test_submit_and_poll():
    mock_connector = MagicMock()
    mock_connector.submit_order.return_value = AlpacaOrder(
        id="broker-1", symbol="AAPL", side="buy", qty=10, filled_qty=0, status="submitted"
    )
    mock_connector.get_order.return_value = AlpacaOrder(
        id="broker-1", symbol="AAPL", side="buy", qty=10, filled_qty=10, status="filled", filled_avg_price=150.0
    )

    mgr = OrderManager(connector=mock_connector)
    managed = mgr.submit("int-1", "AAPL", 10, "buy", theoretical_price=149.5)
    assert managed.state == OrderState.SUBMITTED

    mgr.poll("int-1")
    assert mgr.orders["int-1"].state == OrderState.FILLED
    assert mgr.orders["int-1"].actual_fill_price == 150.0

def test_cancel():
    mock_connector = MagicMock()
    mock_connector.submit_order.return_value = AlpacaOrder(
        id="broker-2", symbol="AAPL", side="buy", qty=5, filled_qty=0, status="submitted"
    )
    mgr = OrderManager(connector=mock_connector)
    mgr.submit("int-2", "AAPL", 5, "buy")
    mgr.cancel("int-2")
    assert mgr.orders["int-2"].state == OrderState.CANCELLED
