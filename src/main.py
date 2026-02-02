#!/usr/bin/env python3
"""
Bitcoin Transaction & UTXO Simulator
CS 216: Introduction to Blockchain Assignment

Main program entry point with interactive menu interface.
"""

import sys
import os

# Add parent directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)
sys.path.insert(0, current_dir)

from utxo_manager import UTXOManager
from transaction import Transaction, create_simple_transaction, generate_tx_id
from validator import validate_transaction, get_transaction_fee
from mempool import Mempool
from block import Block, Blockchain, mine_block


class BitcoinSimulator:
    """Main simulator class that manages all components."""
    
    def __init__(self):
        """Initialize the simulator with genesis state."""
        self.utxo_manager = UTXOManager()
        self.mempool = Mempool(max_size=50)
        self.blockchain = Blockchain()
        
        # Initialize genesis UTXOs
        self.utxo_manager.initialize_genesis()
    
    def display_welcome(self):
        """Display welcome message and initial state."""
        print("\n" + "="*60)
        print("        BITCOIN TRANSACTION SIMULATOR")
        print("        CS 216: Introduction to Blockchain")
        print("="*60)
        print("\nInitial UTXOs (Genesis Block):")
        print("-"*40)
        print("  - Alice:   50.0 BTC")
        print("  - Bob:     30.0 BTC")
        print("  - Charlie: 20.0 BTC")
        print("  - David:   10.0 BTC")
        print("  - Eve:      5.0 BTC")
        print("-"*40)
        print("  Total:    115.0 BTC")
        print("="*60)
    
    def display_menu(self):
        """Display main menu."""
        print("\nMain Menu:")
        print("  1. Create new transaction")
        print("  2. View UTXO set")
        print("  3. View mempool")
        print("  4. Mine block")
        print("  5. Run test scenarios")
        print("  6. View blockchain")
        print("  7. Check balance")
        print("  8. View detailed mempool")
        print("  9. Reset simulator")
        print("  0. Exit")
    
    def get_input(self, prompt: str, default: str = None) -> str:
        """Get user input with optional default."""
        if default:
            result = input(f"{prompt} [{default}]: ").strip()
            return result if result else default
        return input(f"{prompt}: ").strip()
    
    def get_float_input(self, prompt: str, default: float = None) -> float:
        """Get float input from user."""
        while True:
            try:
                if default is not None:
                    value = input(f"{prompt} [{default}]: ").strip()
                    return float(value) if value else default
                else:
                    return float(input(f"{prompt}: ").strip())
            except ValueError:
                print("Please enter a valid number.")
    
    def create_transaction(self):
        """Interactive transaction creation."""
        print("\n--- Create New Transaction ---")
        
        # Get sender
        sender = self.get_input("Enter sender name")
        
        # Check sender balance
        balance = self.utxo_manager.get_balance(sender)
        if balance <= 0:
            print(f"Error: {sender} has no funds (balance: {balance:.4f} BTC)")
            return
        
        print(f"Available balance for {sender}: {balance:.4f} BTC")
        
        # Show sender's UTXOs
        sender_utxos = self.utxo_manager.get_utxos_for_owner(sender)
        print(f"UTXOs owned by {sender}:")
        for (tx_id, index), data in sender_utxos:
            print(f"  - ({tx_id}, {index}): {data['amount']:.4f} BTC")
        
        # Get recipient
        recipient = self.get_input("Enter recipient name")
        
        # Get amount
        amount = self.get_float_input("Enter amount (BTC)")
        
        # Get fee
        fee = self.get_float_input("Enter fee (BTC)", 0.001)
        
        # Create transaction
        print(f"\nCreating transaction: {sender} -> {recipient} ({amount:.4f} BTC)...")
        
        tx = create_simple_transaction(sender, recipient, amount, self.utxo_manager, fee)
        
        if tx is None:
            print("Failed to create transaction.")
            return
        
        # Validate and add to mempool
        result = validate_transaction(tx, self.utxo_manager, self.mempool.spent_utxos)
        
        if result.valid:
            success, msg = self.mempool.add_transaction(tx, self.utxo_manager)
            if success:
                print(f"\n✓ Transaction valid! Fee: {result.fee:.4f} BTC")
                print(f"✓ Transaction ID: {tx.tx_id}")
                print(f"✓ {msg}")
                print(f"✓ Mempool now has {self.mempool.get_transaction_count()} transactions.")
            else:
                print(f"\n✗ Failed to add to mempool: {msg}")
        else:
            print(f"\n✗ Transaction REJECTED: {result.message}")
    
    def create_custom_transaction(self):
        """Create a transaction with custom inputs/outputs."""
        print("\n--- Create Custom Transaction ---")
        
        tx = Transaction()
        
        # Add inputs
        print("\nAdd inputs (enter empty to finish):")
        while True:
            prev_tx = self.get_input("  Previous TX ID (or empty to finish)")
            if not prev_tx:
                break
            
            try:
                index = int(self.get_input("  Output index"))
            except ValueError:
                print("  Invalid index")
                continue
            
            owner = self.get_input("  Owner name")
            tx.add_input(prev_tx, index, owner)
            print(f"  Added input: ({prev_tx}, {index}) from {owner}")
        
        if not tx.inputs:
            print("No inputs added. Cancelling.")
            return
        
        # Add outputs
        print("\nAdd outputs (enter 0 amount to finish):")
        while True:
            amount = self.get_float_input("  Amount (BTC, 0 to finish)")
            if amount <= 0:
                break
            
            address = self.get_input("  Recipient address")
            tx.add_output(amount, address)
            print(f"  Added output: {amount:.4f} BTC to {address}")
        
        if not tx.outputs:
            print("No outputs added. Cancelling.")
            return
        
        # Validate and add
        print(f"\nTransaction ID: {tx.tx_id}")
        result = validate_transaction(tx, self.utxo_manager, self.mempool.spent_utxos)
        
        if result.valid:
            success, msg = self.mempool.add_transaction(tx, self.utxo_manager)
            print(f"\n✓ Transaction valid! Fee: {result.fee:.4f} BTC")
            print(f"{'✓' if success else '✗'} {msg}")
        else:
            print(f"\n✗ Transaction REJECTED: {result.message}")
    
    def view_utxo_set(self):
        """Display current UTXO set."""
        self.utxo_manager.display_utxo_set()
    
    def view_mempool(self):
        """Display mempool contents."""
        self.mempool.display(self.utxo_manager)
    
    def view_mempool_detailed(self):
        """Display detailed mempool contents."""
        self.mempool.display_detailed(self.utxo_manager)
    
    def mine_block_interactive(self):
        """Interactive block mining."""
        print("\n--- Mine Block ---")
        
        if self.mempool.get_transaction_count() == 0:
            print("No transactions in mempool to mine.")
            return
        
        miner = self.get_input("Enter miner name", "Miner1")
        
        try:
            num_txs = int(self.get_input("Max transactions to include", "5"))
        except ValueError:
            num_txs = 5
        
        block = mine_block(miner, self.mempool, self.utxo_manager, self.blockchain, num_txs)
        
        if block:
            block.display()
    
    def view_blockchain(self):
        """Display blockchain."""
        self.blockchain.display_chain()
    
    def check_balance(self):
        """Check balance for an address."""
        print("\n--- Check Balance ---")
        address = self.get_input("Enter address/name")
        balance = self.utxo_manager.get_balance(address)
        utxos = self.utxo_manager.get_utxos_for_owner(address)
        
        print(f"\nBalance for {address}: {balance:.4f} BTC")
        print(f"Number of UTXOs: {len(utxos)}")
        
        if utxos:
            print("UTXOs:")
            for (tx_id, index), data in utxos:
                print(f"  - ({tx_id}, {index}): {data['amount']:.4f} BTC")
    
    def run_tests(self):
        """Run test scenarios."""
        print("\n--- Test Scenarios ---")
        print("  1. Run all tests")
        print("  2. Test 1: Basic Valid Transaction")
        print("  3. Test 2: Multiple Inputs")
        print("  4. Test 3: Double-Spend (Same TX)")
        print("  5. Test 4: Mempool Double-Spend")
        print("  6. Test 5: Insufficient Funds")
        print("  7. Test 6: Negative Amount")
        print("  8. Test 7: Zero Fee Transaction")
        print("  9. Test 8: Race Attack Simulation")
        print(" 10. Test 9: Complete Mining Flow")
        print(" 11. Test 10: Unconfirmed Chain")
        print("  0. Back to main menu")
        
        try:
            choice = int(input("\nSelect test: "))
        except ValueError:
            return
        
        # Import test module
        sys.path.insert(0, os.path.join(parent_dir, 'tests'))
        from test_scenarios import (
            run_all_tests, run_test_1, run_test_2, run_test_3,
            run_test_4, run_test_5, run_test_6, run_test_7,
            run_test_8, run_test_9, run_test_10
        )
        
        tests = {
            1: run_all_tests,
            2: run_test_1,
            3: run_test_2,
            4: run_test_3,
            5: run_test_4,
            6: run_test_5,
            7: run_test_6,
            8: run_test_7,
            9: run_test_8,
            10: run_test_9,
            11: run_test_10
        }
        
        if choice in tests:
            tests[choice]()
    
    def reset(self):
        """Reset simulator to initial state."""
        confirm = self.get_input("Reset simulator? (yes/no)", "no")
        if confirm.lower() in ["yes", "y"]:
            self.__init__()
            print("Simulator reset to initial state.")
    
    def run(self):
        """Main loop."""
        self.display_welcome()
        
        while True:
            self.display_menu()
            
            try:
                choice = input("\nEnter choice: ").strip()
                
                if choice == "1":
                    self.create_transaction()
                elif choice == "2":
                    self.view_utxo_set()
                elif choice == "3":
                    self.view_mempool()
                elif choice == "4":
                    self.mine_block_interactive()
                elif choice == "5":
                    self.run_tests()
                elif choice == "6":
                    self.view_blockchain()
                elif choice == "7":
                    self.check_balance()
                elif choice == "8":
                    self.view_mempool_detailed()
                elif choice == "9":
                    self.reset()
                elif choice == "0":
                    print("\nExiting Bitcoin Simulator. Goodbye!")
                    break
                else:
                    print("Invalid choice. Please try again.")
                    
            except KeyboardInterrupt:
                print("\n\nExiting...")
                break
            except Exception as e:
                print(f"\nError: {e}")
                print("Please try again.")


def main():
    """Entry point."""
    simulator = BitcoinSimulator()
    simulator.run()


if __name__ == "__main__":
    main()
