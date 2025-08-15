from langchain_core.tools import tool


@tool
def add_order_to_sheet(item: str, quantity: int, customer_name: str = "Unknown") -> str:
    """
    Add a new order to the orders spreadsheet

    Args:
        item: The menu item being ordered
        quantity: Number of items
        customer_name: Name of the customer

    Returns:
        Confirmation message
    """
    # TODO: Implement Google Sheets integration
    return f"TODO: Add {quantity}x {item} for {customer_name} to order sheet"


@tool
def check_inventory(item: str) -> str:
    """
    Check if an item is available in inventory

    Args:
        item: The menu item to check

    Returns:
        Availability status
    """
    # TODO: Implement inventory checking
    return f"TODO: Check inventory for {item}"
