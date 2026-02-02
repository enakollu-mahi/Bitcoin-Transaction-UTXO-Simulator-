"""
UTXO Manager - Manages Unspent Transaction Outputs
CS 216: Introduction to Blockchain Assignment
"""

class UTXOManager:
    """
    Manages the UTXO (Unspent Transaction Output) set.
    Think of this as Bitcoin's "database" of spendable coins.
    """
    
    def __init__(self):
        # Store UTXOs as dictionary: (tx_id, index) -> {"amount": float, "owner": str}
        self.utxo_set = {}
    
    def add_utxo(self, tx_id: str, index: int, amount: float, owner: str) -> None:
        """
        Add a new UTXO to the set.
        
        Args:
            tx_id: Transaction ID that created this UTXO
            index: Output index within the transaction
            amount: Amount of BTC in this UTXO
            owner: Address/name of the owner
        """
        key = (tx_id, index)
        self.utxo_set[key] = {"amount": amount, "owner": owner}
    
    def remove_utxo(self, tx_id: str, index: int) -> bool:
        """
        Remove a UTXO (when spent).
        
        Args:
            tx_id: Transaction ID of the UTXO
            index: Output index of the UTXO
            
        Returns:
            True if removed successfully, False if UTXO didn't exist
        """
        key = (tx_id, index)
        if key in self.utxo_set:
            del self.utxo_set[key]
            return True
        return False
    
    def get_balance(self, owner: str) -> float:
        """
        Calculate total balance for an address.
        
        Args:
            owner: Address/name to check balance for
            
        Returns:
            Total balance in BTC
        """
        total = 0.0
        for utxo_data in self.utxo_set.values():
            if utxo_data["owner"] == owner:
                total += utxo_data["amount"]
        return total
    
    def exists(self, tx_id: str, index: int) -> bool:
        """
        Check if UTXO exists and is unspent.
        
        Args:
            tx_id: Transaction ID to check
            index: Output index to check
            
        Returns:
            True if UTXO exists, False otherwise
        """
        return (tx_id, index) in self.utxo_set
    
    def get_utxo(self, tx_id: str, index: int) -> dict:
        """
        Get UTXO details.
        
        Args:
            tx_id: Transaction ID
            index: Output index
            
        Returns:
            UTXO data dict or None if not found
        """
        key = (tx_id, index)
        return self.utxo_set.get(key)
    
    def get_utxos_for_owner(self, owner: str) -> list:
        """
        Get all UTXOs owned by an address.
        
        Args:
            owner: Address/name to get UTXOs for
            
        Returns:
            List of tuples: ((tx_id, index), {"amount": float, "owner": str})
        """
        result = []
        for key, utxo_data in self.utxo_set.items():
            if utxo_data["owner"] == owner:
                result.append((key, utxo_data))
        return result
    
    def get_all_utxos(self) -> dict:
        """
        Get all UTXOs in the set.
        
        Returns:
            Copy of the entire UTXO set
        """
        return self.utxo_set.copy()
    
    def display_utxo_set(self) -> None:
        """Display all UTXOs in a readable format."""
        if not self.utxo_set:
            print("UTXO set is empty.")
            return
        
        print("\n" + "="*60)
        print("UTXO SET")
        print("="*60)
        print(f"{'UTXO Reference':<30} {'Owner':<15} {'Amount (BTC)':<15}")
        print("-"*60)
        
        for (tx_id, index), data in sorted(self.utxo_set.items()):
            ref = f"({tx_id}, {index})"
            print(f"{ref:<30} {data['owner']:<15} {data['amount']:<15.4f}")
        
        print("="*60)
        
        # Display balances by owner
        owners = set(data["owner"] for data in self.utxo_set.values())
        print("\nBalances by Owner:")
        for owner in sorted(owners):
            balance = self.get_balance(owner)
            print(f"  {owner}: {balance:.4f} BTC")
        print()
    
    def initialize_genesis(self) -> None:
        """Initialize the genesis UTXOs as specified in the assignment."""
        genesis_utxos = [
            ("genesis", 0, 50.0, "Alice"),
            ("genesis", 1, 30.0, "Bob"),
            ("genesis", 2, 20.0, "Charlie"),
            ("genesis", 3, 10.0, "David"),
            ("genesis", 4, 5.0, "Eve")
        ]
        
        for tx_id, index, amount, owner in genesis_utxos:
            self.add_utxo(tx_id, index, amount, owner)
    
    def clone(self) -> 'UTXOManager':
        """Create a deep copy of this UTXO manager."""
        new_manager = UTXOManager()
        new_manager.utxo_set = self.utxo_set.copy()
        return new_manager
