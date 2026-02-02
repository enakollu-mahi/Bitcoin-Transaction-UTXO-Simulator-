"""
Block and Mining Simulation
CS 216: Introduction to Blockchain Assignment
"""

import time
import random
from typing import List, Optional

# Handle both relative and absolute imports
try:
    from .validator import get_transaction_fee
except ImportError:
    from validator import get_transaction_fee


class Block:
    """
    Represents a block in the blockchain.
    
    A block contains confirmed transactions and links to the previous block.
    """
    
    def __init__(self, block_id: str = None, prev_block_id: str = None, miner: str = None):
        """
        Initialize a new block.
        
        Args:
            block_id: Unique block identifier (auto-generated if not provided)
            prev_block_id: ID of the previous block (None for genesis)
            miner: Address of the miner who created this block
        """
        self.block_id = block_id if block_id else f"block_{int(time.time())}_{random.randint(1000, 9999)}"
        self.prev_block_id = prev_block_id
        self.miner = miner
        self.transactions = []  # List of Transaction objects
        self.timestamp = time.time()
        self.total_fees = 0.0
    
    def add_transaction(self, tx, fee: float) -> None:
        """Add a transaction to the block."""
        self.transactions.append(tx)
        self.total_fees += fee
    
    def get_transaction_count(self) -> int:
        """Get number of transactions in block."""
        return len(self.transactions)
    
    def display(self) -> None:
        """Display block information."""
        print(f"\n{'='*60}")
        print(f"BLOCK: {self.block_id}")
        print(f"{'='*60}")
        print(f"Previous Block: {self.prev_block_id or 'Genesis'}")
        print(f"Miner: {self.miner}")
        print(f"Timestamp: {time.ctime(self.timestamp)}")
        print(f"Transactions: {len(self.transactions)}")
        print(f"Total Fees: {self.total_fees:.4f} BTC")
        print(f"{'-'*60}")
        
        for i, tx in enumerate(self.transactions):
            print(f"  [{i+1}] {tx.tx_id}")
        
        print(f"{'='*60}\n")


class Blockchain:
    """
    Simple blockchain implementation for managing the chain of blocks.
    """
    
    def __init__(self):
        """Initialize the blockchain."""
        self.blocks = []  # List of Block objects (main chain)
        self.orphaned_blocks = []  # Blocks not in main chain
    
    def add_block(self, block: Block) -> bool:
        """
        Add a block to the blockchain.
        
        Args:
            block: Block to add
        
        Returns:
            True if added successfully
        """
        # Verify chain linkage
        if self.blocks:
            if block.prev_block_id != self.blocks[-1].block_id:
                print(f"Warning: Block doesn't link to current tip")
                self.orphaned_blocks.append(block)
                return False
        
        self.blocks.append(block)
        return True
    
    def get_latest_block(self) -> Optional[Block]:
        """Get the most recent block."""
        return self.blocks[-1] if self.blocks else None
    
    def get_chain_length(self) -> int:
        """Get the length of the main chain."""
        return len(self.blocks)
    
    def display_chain(self) -> None:
        """Display the entire blockchain."""
        print("\n" + "="*70)
        print("BLOCKCHAIN")
        print("="*70)
        print(f"Chain Length: {len(self.blocks)} blocks")
        print(f"Orphaned Blocks: {len(self.orphaned_blocks)}")
        print("-"*70)
        
        for i, block in enumerate(self.blocks):
            print(f"\n[Block {i}] {block.block_id}")
            print(f"  Miner: {block.miner}")
            print(f"  Transactions: {len(block.transactions)}")
            print(f"  Fees: {block.total_fees:.4f} BTC")
        
        print("\n" + "="*70 + "\n")


def mine_block(miner_address: str, mempool, utxo_manager, 
               blockchain: Blockchain = None, num_txs: int = 5) -> Optional[Block]:
    """
    Simulate mining a block.
    
    Steps:
    1. Select top transactions from mempool (by fee)
    2. Update UTXO set (remove inputs, add outputs)
    3. Add miner fee as special UTXO (coinbase)
    4. Remove mined transactions from mempool
    
    Args:
        miner_address: Address of the miner to receive fees
        mempool: Mempool instance
        utxo_manager: UTXOManager instance
        blockchain: Optional Blockchain instance to add block to
        num_txs: Maximum number of transactions to include
    
    Returns:
        Block object if successful, None if mempool is empty
    """
    # Get top transactions by fee
    transactions = mempool.get_top_transactions(num_txs, utxo_manager)
    
    if not transactions:
        print("No transactions in mempool to mine.")
        return None
    
    # Create new block
    prev_block_id = None
    if blockchain and blockchain.blocks:
        prev_block_id = blockchain.get_latest_block().block_id
    
    block = Block(prev_block_id=prev_block_id, miner=miner_address)
    
    total_fees = 0.0
    mined_tx_ids = []
    
    print(f"\nMining block...")
    print(f"Selected {len(transactions)} transactions from mempool.")
    
    # Process each transaction
    for tx in transactions:
        fee = get_transaction_fee(tx, utxo_manager)
        
        # Update UTXO set: remove spent inputs
        for inp in tx.inputs:
            utxo_manager.remove_utxo(inp["prev_tx"], inp["index"])
        
        # Update UTXO set: add new outputs
        for i, out in enumerate(tx.outputs):
            utxo_manager.add_utxo(tx.tx_id, i, out["amount"], out["address"])
        
        # Add to block
        block.add_transaction(tx, fee)
        total_fees += fee
        mined_tx_ids.append(tx.tx_id)
        
        print(f"  - Processed {tx.tx_id} (fee: {fee:.4f} BTC)")
    
    # Create coinbase UTXO for miner (fees only in this simulation)
    if total_fees > 0:
        coinbase_tx_id = f"coinbase_{block.block_id}"
        utxo_manager.add_utxo(coinbase_tx_id, 0, total_fees, miner_address)
        print(f"\nCoinbase: Miner {miner_address} receives {total_fees:.4f} BTC in fees")
    
    # Remove mined transactions from mempool
    for tx_id in mined_tx_ids:
        mempool.remove_transaction(tx_id)
    
    # Add block to blockchain if provided
    if blockchain:
        blockchain.add_block(block)
    
    print(f"\nBlock {block.block_id} mined successfully!")
    print(f"Total fees: {total_fees:.4f} BTC")
    print(f"Removed {len(mined_tx_ids)} transactions from mempool.")
    print(f"Mempool now has {mempool.get_transaction_count()} transactions.\n")
    
    return block


def simulate_fork(blockchain: Blockchain, competing_blocks: List[Block]) -> Block:
    """
    Simulate fork resolution with multiple competing blocks.
    
    Deterministic rules for block selection:
    1. Block with more transactions wins
    2. If tied, block with higher total fees wins
    3. If still tied, choose alphabetically by miner name
    
    Args:
        blockchain: Current blockchain
        competing_blocks: List of blocks competing for the same position
    
    Returns:
        The winning block
    """
    if not competing_blocks:
        return None
    
    if len(competing_blocks) == 1:
        return competing_blocks[0]
    
    # Sort by: (num_transactions DESC, total_fees DESC, miner ASC)
    def block_sort_key(block):
        return (-len(block.transactions), -block.total_fees, block.miner)
    
    sorted_blocks = sorted(competing_blocks, key=block_sort_key)
    winner = sorted_blocks[0]
    
    print(f"\nFork Resolution:")
    print(f"  {len(competing_blocks)} competing blocks")
    print(f"  Winner: {winner.block_id} (miner: {winner.miner})")
    
    # Add losers to orphaned blocks
    for block in sorted_blocks[1:]:
        blockchain.orphaned_blocks.append(block)
        print(f"  Orphaned: {block.block_id}")
    
    return winner
