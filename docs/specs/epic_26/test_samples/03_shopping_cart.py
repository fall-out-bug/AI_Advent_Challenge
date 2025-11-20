"""Shopping cart implementation for Test Agent testing."""


class ShoppingCart:
    """Shopping cart implementation.

    Purpose:
        Manages a collection of items with prices and calculates totals.

    Example:
        >>> cart = ShoppingCart()
        >>> cart.add_item({"id": "1", "price": 10.0})
        >>> cart.get_total()
        11.0  # 10.0 + 10% tax
    """

    def __init__(self) -> None:
        """Initialize empty shopping cart."""
        self.items: list[dict] = []

    def add_item(self, item: dict) -> None:
        """Add item to cart.

        Args:
            item: Item dictionary with at least 'id' and 'price' keys.

        Example:
            >>> cart = ShoppingCart()
            >>> cart.add_item({"id": "1", "price": 10.0})
            >>> len(cart.items)
            1
        """
        self.items.append(item)

    def remove_item(self, item_id: str) -> None:
        """Remove item by ID.

        Args:
            item_id: ID of item to remove.

        Example:
            >>> cart = ShoppingCart()
            >>> cart.add_item({"id": "1", "price": 10.0})
            >>> cart.remove_item("1")
            >>> len(cart.items)
            0
        """
        self.items = [item for item in self.items if item.get("id") != item_id]

    def get_total(self, tax_rate: float = 0.1) -> float:
        """Get total with tax.

        Args:
            tax_rate: Tax rate (default: 0.1 = 10%).

        Returns:
            Total price including tax.

        Example:
            >>> cart = ShoppingCart()
            >>> cart.add_item({"id": "1", "price": 10.0})
            >>> cart.get_total()
            11.0
        """
        subtotal = sum(item.get("price", 0) for item in self.items)
        return subtotal * (1 + tax_rate)

    def is_empty(self) -> bool:
        """Check if cart is empty.

        Returns:
            True if cart is empty, False otherwise.

        Example:
            >>> cart = ShoppingCart()
            >>> cart.is_empty()
            True
            >>> cart.add_item({"id": "1", "price": 10.0})
            >>> cart.is_empty()
            False
        """
        return len(self.items) == 0
