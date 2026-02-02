"""
Mempool Management - Memory Pool for Unconfirmed Transactions
CS 216: Introduction to Blockchain Assignment
"""

from typing import Tuple, List, Optional

# Handle both relative and absolute imports
try:
    from .validator import validate_transaction, get_transaction_fee
except ImportError:
    from validator import validate_transaction, get_transaction_fee


class Mempool:
    """
    Manages the mempool (memory pool) of unconfirmed transactions.
    
    The mempool stores valid transactions that are waiting to be included in a block.
    It tracks which UTXOs are "promised" to be spent by pending transactions.
    """
    
    def __init__(self, max_size: int = 50):
        """
        Initialize the mempool.
        
        Args:
            max_size: Maximum number of transactions the mempool can hold
        """
        self.transactions = []  # List of Transaction objects
        self.spent_utxos = set()  # Set of (tx_id, index) tuples spent in mempool
        self.max_size = max_size
        self.tx_index = {}  # Quick lookup: tx_id -> Transaction
    
    def add_transaction(self, tx, utxo_manager) -> Tuple[bool, str]:
        """
        Validate and add a transaction to the mempool.
        
        Args:
            tx: Transaction object to add
            utxo_manager: UTXOManager instance for validation
        
        Returns:
            Tuple of (success: bool, message: str)
        """
        # Check if mempool is full
        if len(self.transactions) >= self.max_size:
            # Eviction policy: remove lowest-fee transaction if new tx has higher fee
            new_fee = get_transaction_fee(tx, utxo_manager)
            min_fee_tx = min(self.transactions, 
                           key=lambda t: get_transaction_fee(t, utxo_manager))
            min_fee = get_transaction_fee(min_fee_tx, utxo_manager)
            
            if new_fee > min_fee:
                self.remove_transaction(min_fee_tx.tx_id)
                print(f"Evicted low-fee transaction {min_fee_tx.tx_id} to make room")
            else:
                return False, f"Mempool full ({self.max_size} transactions). New tx fee too low."
        
        # Check if transaction already exists
        if tx.tx_id in self.tx_index:
            return False, f"Transaction {tx.tx_id} already in mempool"
        
        # Validate transaction (including mempool conflict check)
        result = validate_transaction(tx, utxo_manager, self.spent_utxos)
        
        if not result.valid:
            return False, result.message
        
        # Add transaction to mempool
        self.transactions.append(tx)
        self.tx_index[tx.tx_id] = tx
        
        # Mark UTXOs as spent in mempool
        for inp in tx.inputs:
            ref = (inp["prev_tx"], inp["index"])
            self.spent_utxos.add(ref)
        
        return True, f"Transaction added to mempool. Fee: {result.fee:.4f} BTC"
    
    def remove_transaction(self, tx_id: str) -> bool:
        """
        Remove a transaction from the mempool (when mined or invalidated).
        
        Args:
            tx_id: ID of the transaction to remove
        
        Returns:
            True if removed, False if not found
        """
        if tx_id not in self.tx_index:
            return False
        
        tx = self.tx_index[tx_id]
        
        # Remove from transactions list
        self.transactions = [t for t in self.transactions if t.tx_id != tx_id]
        
        # Remove from index
        del self.tx_index[tx_id]
        
        # Clear spent UTXOs for this transaction
        for inp in tx.inputs:
            ref = (inp["prev_tx"], inp["index"])
            self.spent_utxos.discard(ref)
        
        return True
    
    def get_transaction(self, tx_id: str) -> Optional[object]:
        """Get a transaction from mempool by ID."""
        return self.tx_index.get(tx_id)
    
    def get_top_transactions(self, n: int, utxo_manager) -> List:
        """
        Return top N transactions by fee (highest first).
        
        Args:
            n: Number of transactions to return
            utxo_manager: UTXOManager for fee calculation
        
        Returns:
            List of Transaction objects sorted by fee (descending)
        """
        # Sort transactions by fee (highest first)
        sorted_txs = sorted(
            self.transactions,
            key=lambda tx: get_transaction_fee(tx, utxo_manager),
            reverse=True
        )
        return sorted_txs[:n]
    
    def get_all_transactions(self) -> List:
        """Get all transactions in the mempool."""
        return self.transactions.copy()
    
    def get_transaction_count(self) -> int:
        """Get number of transactions in mempool."""
        return len(self.transactions)
    
    def is_utxo_spent(self, tx_id: str, index: int) -> bool:
        """Check if a UTXO is already spent in the mempool."""
        return (tx_id, index) in self.spent_utxos
    
    def clear(self) -> None:
        """Clear all transactions from mempool."""
        self.transactions = []
        self.spent_utxos = set()
        self.tx_index = {}
    
    def display(self, utxo_manager) -> None:
        """Display mempool contents in a readable format."""
        print("\n" + "="*70)
        print("MEMPOOL")
        print("="*70)
        print(f"Transactions: {len(self.transactions)} / {self.max_size}")
        print(f"Spent UTXOs tracked: {len(self.spent_utxos)}")
        print("-"*70)
        
        if not self.transactions:
            print("(empty)")
        else:
            print(f"{'TX ID':<30} {'Inputs':<10} {'Outputs':<10} {'Fee (BTC)':<15}")
            print("-"*70)
            
            for tx in self.transactions:
                fee = get_transaction_fee(tx, utxo_manager)
                print(f"{tx.tx_id:<30} {len(tx.inputs):<10} {len(tx.outputs):<10} {fee:<15.4f}")
        
        print("="*70 + "\n")
    
    def display_detailed(self, utxo_manager) -> None:
        """Display detailed mempool contents."""
        print("\n" + "="*70)
        print("MEMPOOL (DETAILED)")
        print("="*70)
        
        if not self.transactions:
            print("(empty)")
        else:
            for i, tx in enumerate(self.transactions):
                fee = get_transaction_fee(tx, utxo_manager)
                print(f"\n[{i+1}] Transaction: {tx.tx_id}")
                print(f"    Fee: {fee:.4f} BTC")
                print("    Inputs:")
                for inp in tx.inputs:
                    print(f"      - ({inp['prev_tx']}, {inp['index']}) from {inp['owner']}")
                print("    Outputs:")
                for out in tx.outputs:
                    print(f"      - {out['amount']:.4f} BTC to {out['address']}")
        
        print("\n" + "="*70 + "\n")
