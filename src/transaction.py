"""
Transaction Structure and Creation
CS 216: Introduction to Blockchain Assignment
"""

import time
import random


def generate_tx_id() -> str:
    """Generate a unique transaction ID."""
    return f"tx_{int(time.time())}_{random.randint(1000, 9999)}"


class Transaction:
    """
    Represents a Bitcoin transaction.
    
    A transaction transfers value from inputs (existing UTXOs) to outputs (new UTXOs).
    Formula: Sum(inputs) = Sum(outputs) + fee
    """
    
    def __init__(self, tx_id: str = None):
        """
        Initialize a new transaction.
        
        Args:
            tx_id: Transaction ID (auto-generated if not provided)
        """
        self.tx_id = tx_id if tx_id else generate_tx_id()
        self.inputs = []   # List of input references
        self.outputs = []  # List of output definitions
    
    def add_input(self, prev_tx: str, index: int, owner: str) -> None:
        """
        Add an input to the transaction.
        
        Args:
            prev_tx: Previous transaction ID containing the UTXO
            index: Output index in the previous transaction
            owner: Owner of the UTXO (simulates signature verification)
        """
        self.inputs.append({
            "prev_tx": prev_tx,
            "index": index,
            "owner": owner
        })
    
    def add_output(self, amount: float, address: str) -> None:
        """
        Add an output to the transaction.
        
        Args:
            amount: Amount of BTC for this output
            address: Recipient address
        """
        self.outputs.append({
            "amount": amount,
            "address": address
        })
    
    def to_dict(self) -> dict:
        """Convert transaction to dictionary format."""
        return {
            "tx_id": self.tx_id,
            "inputs": self.inputs.copy(),
            "outputs": self.outputs.copy()
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Transaction':
        """Create a Transaction from dictionary format."""
        tx = cls(tx_id=data.get("tx_id"))
        tx.inputs = data.get("inputs", []).copy()
        tx.outputs = data.get("outputs", []).copy()
        return tx
    
    def get_input_refs(self) -> list:
        """Get list of (prev_tx, index) tuples for all inputs."""
        return [(inp["prev_tx"], inp["index"]) for inp in self.inputs]
    
    def calculate_output_sum(self) -> float:
        """Calculate total output amount."""
        return sum(out["amount"] for out in self.outputs)
    
    def display(self) -> None:
        """Display transaction in a readable format."""
        print(f"\nTransaction ID: {self.tx_id}")
        print("-" * 40)
        
        print("Inputs:")
        if not self.inputs:
            print("  (no inputs)")
        for i, inp in enumerate(self.inputs):
            print(f"  [{i}] From: ({inp['prev_tx']}, {inp['index']}) - Owner: {inp['owner']}")
        
        print("Outputs:")
        if not self.outputs:
            print("  (no outputs)")
        for i, out in enumerate(self.outputs):
            print(f"  [{i}] To: {out['address']} - Amount: {out['amount']:.4f} BTC")
        print()
    
    def __str__(self) -> str:
        """String representation of the transaction."""
        return f"Transaction({self.tx_id}, inputs={len(self.inputs)}, outputs={len(self.outputs)})"
    
    def __repr__(self) -> str:
        return self.__str__()


def create_simple_transaction(sender: str, recipient: str, amount: float, 
                               utxo_manager, fee: float = 0.001) -> Transaction:
    """
    Create a simple transaction from sender to recipient.
    
    This is a helper function that:
    1. Finds suitable UTXOs from the sender
    2. Creates inputs from those UTXOs
    3. Creates output for recipient
    4. Creates change output back to sender (if needed)
    
    Args:
        sender: Address of the sender
        recipient: Address of the recipient
        amount: Amount to send
        utxo_manager: UTXOManager instance to query UTXOs
        fee: Transaction fee (default 0.001 BTC)
    
    Returns:
        Transaction object or None if insufficient funds
    """
    # Get sender's UTXOs
    sender_utxos = utxo_manager.get_utxos_for_owner(sender)
    
    if not sender_utxos:
        print(f"Error: {sender} has no UTXOs")
        return None
    
    # Calculate total needed
    total_needed = amount + fee
    
    # Select UTXOs (simple strategy: use UTXOs until we have enough)
    selected_utxos = []
    total_input = 0.0
    
    for (tx_id, index), utxo_data in sender_utxos:
        selected_utxos.append(((tx_id, index), utxo_data))
        total_input += utxo_data["amount"]
        if total_input >= total_needed:
            break
    
    if total_input < total_needed:
        print(f"Error: Insufficient funds. {sender} has {total_input:.4f} BTC, needs {total_needed:.4f} BTC")
        return None
    
    # Create transaction
    tx = Transaction()
    
    # Add inputs
    for (tx_id, index), utxo_data in selected_utxos:
        tx.add_input(tx_id, index, sender)
    
    # Add output for recipient
    tx.add_output(amount, recipient)
    
    # Add change output back to sender (if any)
    change = total_input - amount - fee
    if change > 0:
        tx.add_output(change, sender)
    
    return tx


def create_transaction_from_inputs(inputs: list, outputs: list, tx_id: str = None) -> Transaction:
    """
    Create a transaction with explicit inputs and outputs.
    
    Args:
        inputs: List of dicts with {"prev_tx", "index", "owner"}
        outputs: List of dicts with {"amount", "address"}
        tx_id: Optional transaction ID
    
    Returns:
        Transaction object
    """
    tx = Transaction(tx_id)
    tx.inputs = inputs.copy()
    tx.outputs = outputs.copy()
    return tx
