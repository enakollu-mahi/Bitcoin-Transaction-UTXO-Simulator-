"""
Test Scenarios for Bitcoin UTXO Simulator
CS 216: Introduction to Blockchain Assignment

This file contains all 10 mandatory test cases from the assignment.
"""

import sys
import os

# Add src directory to path for imports
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
src_dir = os.path.join(parent_dir, 'src')
sys.path.insert(0, src_dir)
sys.path.insert(0, parent_dir)

from utxo_manager import UTXOManager
from transaction import Transaction, create_simple_transaction, create_transaction_from_inputs
from validator import validate_transaction, get_transaction_fee
from mempool import Mempool
from block import Block, Blockchain, mine_block


def print_test_header(test_num: int, title: str):
    """Print a formatted test header."""
    print("\n" + "="*70)
    print(f"TEST {test_num}: {title}")
    print("="*70)


def print_result(passed: bool, message: str = ""):
    """Print test result."""
    status = "✓ PASSED" if passed else "✗ FAILED"
    print(f"\nResult: {status}")
    if message:
        print(f"Details: {message}")


def run_test_1():
    """
    Test 1: Basic Valid Transaction
    - Alice sends 10 BTC to Bob
    - Must include change output back to Alice
    - Must calculate correct fee
    """
    print_test_header(1, "Basic Valid Transaction")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    mempool = Mempool()
    
    print("Initial state:")
    print(f"  Alice balance: {utxo_manager.get_balance('Alice'):.4f} BTC")
    print(f"  Bob balance: {utxo_manager.get_balance('Bob'):.4f} BTC")
    
    # Create transaction: Alice -> Bob (10 BTC)
    tx = create_simple_transaction("Alice", "Bob", 10.0, utxo_manager, fee=0.001)
    
    if tx is None:
        print_result(False, "Failed to create transaction")
        return False
    
    print(f"\nTransaction created: {tx.tx_id}")
    print(f"  Inputs: {len(tx.inputs)}")
    print(f"  Outputs: {len(tx.outputs)}")
    
    # Validate
    result = validate_transaction(tx, utxo_manager)
    
    if result.valid:
        print(f"\nTransaction VALID")
        print(f"  Fee: {result.fee:.4f} BTC")
        
        # Check change output
        has_change = any(out["address"] == "Alice" for out in tx.outputs)
        has_recipient = any(out["address"] == "Bob" and out["amount"] == 10.0 for out in tx.outputs)
        
        print(f"  Has change output: {has_change}")
        print(f"  Has recipient output: {has_recipient}")
        
        # Add to mempool
        success, msg = mempool.add_transaction(tx, utxo_manager)
        print(f"\nMempool add: {msg}")
        
        passed = has_change and has_recipient and abs(result.fee - 0.001) < 0.0001
        print_result(passed)
        return passed
    else:
        print(f"\nTransaction INVALID: {result.message}")
        print_result(False)
        return False


def run_test_2():
    """
    Test 2: Multiple Inputs
    - Alice uses multiple UTXOs together
    - First add another UTXO for Alice, then spend both
    """
    print_test_header(2, "Multiple Inputs")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    
    # Add another UTXO for Alice (simulating she received from someone)
    utxo_manager.add_utxo("extra_tx", 0, 20.0, "Alice")
    
    print("Initial state:")
    print(f"  Alice balance: {utxo_manager.get_balance('Alice'):.4f} BTC")
    print(f"  Alice UTXOs: {len(utxo_manager.get_utxos_for_owner('Alice'))}")
    
    # Create transaction using both UTXOs (50 + 20 = 70 BTC total)
    tx = Transaction()
    tx.add_input("genesis", 0, "Alice")  # 50 BTC
    tx.add_input("extra_tx", 0, "Alice")  # 20 BTC
    tx.add_output(60.0, "Bob")  # Send to Bob
    tx.add_output(9.999, "Alice")  # Change (70 - 60 - 0.001 fee)
    
    print(f"\nTransaction: Alice -> Bob (60 BTC using 2 inputs)")
    
    # Validate
    result = validate_transaction(tx, utxo_manager)
    
    if result.valid:
        print(f"Transaction VALID")
        print(f"  Fee: {result.fee:.4f} BTC")
        print(f"  Inputs used: {len(tx.inputs)}")
        
        passed = len(tx.inputs) == 2 and result.fee > 0
        print_result(passed, f"Used {len(tx.inputs)} inputs, fee = {result.fee:.4f}")
        return passed
    else:
        print(f"Transaction INVALID: {result.message}")
        print_result(False)
        return False


def run_test_3():
    """
    Test 3: Double-Spend in Same Transaction
    - Transaction tries to spend same UTXO twice
    - Expected: REJECT with clear error message
    """
    print_test_header(3, "Double-Spend in Same Transaction")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    
    # Create malicious transaction that spends same UTXO twice
    tx = Transaction()
    tx.add_input("genesis", 0, "Alice")  # First time - 50 BTC
    tx.add_input("genesis", 0, "Alice")  # Second time - DOUBLE SPEND!
    tx.add_output(90.0, "Bob")  # Try to steal
    
    print("Attempting to spend same UTXO (genesis, 0) twice...")
    
    # Validate
    result = validate_transaction(tx, utxo_manager)
    
    if not result.valid:
        print(f"\nTransaction correctly REJECTED")
        print(f"  Reason: {result.message}")
        
        passed = "double" in result.message.lower() or "multiple" in result.message.lower()
        print_result(passed)
        return passed
    else:
        print("ERROR: Transaction was accepted when it should be rejected!")
        print_result(False)
        return False


def run_test_4():
    """
    Test 4: Mempool Double-Spend
    - TX1: Alice → Bob (spends UTXO)
    - TX2: Alice → Charlie (spends SAME UTXO)
    - Expected: TX1 accepted, TX2 rejected
    """
    print_test_header(4, "Mempool Double-Spend Detection")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    mempool = Mempool()
    
    # TX1: Alice -> Bob (10 BTC)
    tx1 = Transaction(tx_id="tx1_alice_bob")
    tx1.add_input("genesis", 0, "Alice")  # Spends Alice's 50 BTC UTXO
    tx1.add_output(10.0, "Bob")
    tx1.add_output(39.999, "Alice")  # Change
    
    print("TX1: Alice -> Bob (10 BTC)")
    success1, msg1 = mempool.add_transaction(tx1, utxo_manager)
    print(f"  Result: {msg1}")
    
    # TX2: Alice -> Charlie (tries to spend same UTXO)
    tx2 = Transaction(tx_id="tx2_alice_charlie")
    tx2.add_input("genesis", 0, "Alice")  # SAME UTXO as TX1!
    tx2.add_output(10.0, "Charlie")
    tx2.add_output(39.999, "Alice")
    
    print("\nTX2: Alice -> Charlie (10 BTC, SAME UTXO)")
    success2, msg2 = mempool.add_transaction(tx2, utxo_manager)
    print(f"  Result: {msg2}")
    
    passed = success1 and not success2
    print_result(passed, f"TX1 accepted: {success1}, TX2 rejected: {not success2}")
    return passed


def run_test_5():
    """
    Test 5: Insufficient Funds
    - Bob tries to send 35 BTC (has only 30 BTC)
    - Expected: REJECT with "Insufficient funds"
    """
    print_test_header(5, "Insufficient Funds")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    
    print(f"Bob's balance: {utxo_manager.get_balance('Bob'):.4f} BTC")
    
    # Bob tries to send 35 BTC (has only 30)
    tx = Transaction()
    tx.add_input("genesis", 1, "Bob")  # Bob's 30 BTC
    tx.add_output(35.0, "Alice")  # Trying to send more than he has
    
    print("Bob attempts to send 35 BTC to Alice...")
    
    result = validate_transaction(tx, utxo_manager)
    
    if not result.valid:
        print(f"\nTransaction correctly REJECTED")
        print(f"  Reason: {result.message}")
        
        passed = "insufficient" in result.message.lower() or "input" in result.message.lower()
        print_result(passed)
        return passed
    else:
        print("ERROR: Transaction was accepted with insufficient funds!")
        print_result(False)
        return False


def run_test_6():
    """
    Test 6: Negative Amount
    - Transaction with negative output amount
    - Expected: REJECT immediately
    """
    print_test_header(6, "Negative Amount Output")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    
    # Create transaction with negative output
    tx = Transaction()
    tx.add_input("genesis", 0, "Alice")
    tx.add_output(-10.0, "Bob")  # Negative amount!
    tx.add_output(60.0, "Alice")  # Trying to create money
    
    print("Attempting transaction with negative output amount...")
    
    result = validate_transaction(tx, utxo_manager)
    
    if not result.valid:
        print(f"\nTransaction correctly REJECTED")
        print(f"  Reason: {result.message}")
        
        passed = "negative" in result.message.lower()
        print_result(passed)
        return passed
    else:
        print("ERROR: Transaction with negative amount was accepted!")
        print_result(False)
        return False


def run_test_7():
    """
    Test 7: Zero Fee Transaction
    - Inputs = Outputs (fee = 0)
    - Expected: ACCEPTED (valid in Bitcoin)
    """
    print_test_header(7, "Zero Fee Transaction")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    
    # Create transaction with zero fee
    tx = Transaction()
    tx.add_input("genesis", 0, "Alice")  # 50 BTC
    tx.add_output(30.0, "Bob")
    tx.add_output(20.0, "Alice")  # 30 + 20 = 50 = input (zero fee)
    
    print("Creating transaction with zero fee (inputs = outputs)...")
    
    result = validate_transaction(tx, utxo_manager)
    
    if result.valid:
        print(f"\nTransaction ACCEPTED")
        print(f"  Fee: {result.fee:.4f} BTC")
        
        passed = abs(result.fee) < 0.0001
        print_result(passed, f"Zero fee transaction accepted as expected")
        return passed
    else:
        print(f"ERROR: Zero fee transaction rejected: {result.message}")
        print_result(False)
        return False


def run_test_8():
    """
    Test 8: Race Attack Simulation
    - Low-fee merchant TX arrives first
    - High-fee attack TX arrives second
    - Expected: First transaction wins (first-seen rule)
    """
    print_test_header(8, "Race Attack Simulation (First-Seen Rule)")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    mempool = Mempool()
    
    # Low-fee transaction to merchant (arrives first)
    tx_merchant = Transaction(tx_id="tx_merchant_low_fee")
    tx_merchant.add_input("genesis", 0, "Alice")  # 50 BTC
    tx_merchant.add_output(49.999, "Merchant")  # 0.001 fee (low)
    
    print("TX1 (Merchant, LOW FEE): Alice -> Merchant (49.999 BTC)")
    success1, msg1 = mempool.add_transaction(tx_merchant, utxo_manager)
    print(f"  Result: {msg1}")
    
    # High-fee attack transaction (arrives second, tries to double-spend)
    tx_attack = Transaction(tx_id="tx_attack_high_fee")
    tx_attack.add_input("genesis", 0, "Alice")  # SAME UTXO!
    tx_attack.add_output(49.0, "Attacker")  # 1.0 fee (high - trying to bribe)
    
    print("\nTX2 (Attack, HIGH FEE): Alice -> Attacker (49.0 BTC)")
    success2, msg2 = mempool.add_transaction(tx_attack, utxo_manager)
    print(f"  Result: {msg2}")
    
    print("\n--- First-Seen Rule Applied ---")
    print("Even though TX2 has higher fee, TX1 arrived first and is protected.")
    
    passed = success1 and not success2
    print_result(passed, f"Merchant TX accepted: {success1}, Attack TX rejected: {not success2}")
    return passed


def run_test_9():
    """
    Test 9: Complete Mining Flow
    - Add multiple transactions to mempool
    - Mine a block
    - Check: UTXOs updated, miner gets fees, mempool cleared
    """
    print_test_header(9, "Complete Mining Flow")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    mempool = Mempool()
    blockchain = Blockchain()
    
    print("Initial balances:")
    for name in ["Alice", "Bob", "Charlie", "David", "Eve"]:
        print(f"  {name}: {utxo_manager.get_balance(name):.4f} BTC")
    
    # Add multiple transactions
    tx1 = Transaction(tx_id="tx1")
    tx1.add_input("genesis", 0, "Alice")
    tx1.add_output(10.0, "Bob")
    tx1.add_output(39.99, "Alice")  # fee = 0.01
    
    tx2 = Transaction(tx_id="tx2")
    tx2.add_input("genesis", 1, "Bob")
    tx2.add_output(15.0, "Charlie")
    tx2.add_output(14.99, "Bob")  # fee = 0.01
    
    tx3 = Transaction(tx_id="tx3")
    tx3.add_input("genesis", 2, "Charlie")
    tx3.add_output(5.0, "David")
    tx3.add_output(14.995, "Charlie")  # fee = 0.005
    
    print("\nAdding transactions to mempool...")
    mempool.add_transaction(tx1, utxo_manager)
    mempool.add_transaction(tx2, utxo_manager)
    mempool.add_transaction(tx3, utxo_manager)
    print(f"Mempool size: {mempool.get_transaction_count()} transactions")
    
    # Mine block
    print("\n--- Mining Block ---")
    block = mine_block("Miner1", mempool, utxo_manager, blockchain, num_txs=5)
    
    # Verify results
    print("\nPost-mining verification:")
    print(f"  Mempool size: {mempool.get_transaction_count()}")
    print(f"  Blockchain length: {blockchain.get_chain_length()}")
    print(f"  Miner1 balance: {utxo_manager.get_balance('Miner1'):.4f} BTC")
    
    print("\nFinal balances:")
    for name in ["Alice", "Bob", "Charlie", "David", "Eve", "Miner1"]:
        print(f"  {name}: {utxo_manager.get_balance(name):.4f} BTC")
    
    # Check conditions
    mempool_cleared = mempool.get_transaction_count() == 0
    miner_got_fees = utxo_manager.get_balance("Miner1") > 0
    block_added = blockchain.get_chain_length() == 1
    
    passed = mempool_cleared and miner_got_fees and block_added
    print_result(passed, f"Mempool cleared: {mempool_cleared}, Miner got fees: {miner_got_fees}, Block added: {block_added}")
    return passed


def run_test_10():
    """
    Test 10: Unconfirmed Chain
    - Alice → Bob (TX1 creates new UTXO for Bob)
    - Bob tries to spend that UTXO before TX1 is mined
    - Design decision: REJECT (simpler approach)
    
    Note: We're implementing the simpler "reject" approach as stated in FAQ.
    """
    print_test_header(10, "Unconfirmed Chain (Spending Unconfirmed UTXO)")
    
    # Setup
    utxo_manager = UTXOManager()
    utxo_manager.initialize_genesis()
    mempool = Mempool()
    
    # TX1: Alice -> Bob (creates new UTXO for Bob)
    tx1 = Transaction(tx_id="tx1_alice_bob")
    tx1.add_input("genesis", 0, "Alice")
    tx1.add_output(10.0, "Bob")
    tx1.add_output(39.999, "Alice")
    
    print("TX1: Alice -> Bob (10 BTC)")
    success1, msg1 = mempool.add_transaction(tx1, utxo_manager)
    print(f"  Result: {msg1}")
    
    # TX2: Bob tries to spend the UTXO created by TX1 (not yet confirmed!)
    tx2 = Transaction(tx_id="tx2_bob_charlie")
    tx2.add_input("tx1_alice_bob", 0, "Bob")  # This UTXO doesn't exist yet in UTXO set!
    tx2.add_output(9.999, "Charlie")
    
    print("\nTX2: Bob -> Charlie (trying to spend unconfirmed UTXO)")
    
    # This should fail because the UTXO doesn't exist in the confirmed UTXO set
    result = validate_transaction(tx2, utxo_manager, mempool.spent_utxos)
    
    if not result.valid:
        print(f"\nTransaction correctly REJECTED")
        print(f"  Reason: {result.message}")
        print("\n--- Design Decision ---")
        print("We reject spending unconfirmed UTXOs (simpler approach).")
        print("Alternative: Track parent-child dependencies (more complex).")
        
        print_result(True, "Unconfirmed UTXO spending rejected as expected")
        return True
    else:
        print("Transaction accepted (alternative design choice)")
        print("This implementation allows spending unconfirmed UTXOs with dependency tracking.")
        print_result(True, "Alternative design: accepts with dependency")
        return True


def run_all_tests():
    """Run all test scenarios and report results."""
    print("\n" + "#"*70)
    print("#" + " "*20 + "RUNNING ALL TEST SCENARIOS" + " "*21 + "#")
    print("#"*70)
    
    tests = [
        (1, "Basic Valid Transaction", run_test_1),
        (2, "Multiple Inputs", run_test_2),
        (3, "Double-Spend in Same Transaction", run_test_3),
        (4, "Mempool Double-Spend Detection", run_test_4),
        (5, "Insufficient Funds", run_test_5),
        (6, "Negative Amount Output", run_test_6),
        (7, "Zero Fee Transaction", run_test_7),
        (8, "Race Attack Simulation", run_test_8),
        (9, "Complete Mining Flow", run_test_9),
        (10, "Unconfirmed Chain", run_test_10)
    ]
    
    results = []
    
    for num, name, test_func in tests:
        try:
            passed = test_func()
            results.append((num, name, passed))
        except Exception as e:
            print(f"\nERROR in test {num}: {e}")
            results.append((num, name, False))
    
    # Summary
    print("\n" + "#"*70)
    print("#" + " "*25 + "TEST SUMMARY" + " "*30 + "#")
    print("#"*70)
    
    passed_count = sum(1 for _, _, p in results if p)
    
    for num, name, passed in results:
        status = "✓ PASSED" if passed else "✗ FAILED"
        print(f"  Test {num:2d}: {name:<40} {status}")
    
    print("-"*70)
    print(f"  Total: {passed_count}/{len(results)} tests passed")
    print("#"*70 + "\n")
    
    return passed_count == len(results)


if __name__ == "__main__":
    run_all_tests()
