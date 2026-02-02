# Bitcoin Transaction & UTXO Simulator

## CS 216: Introduction to Blockchain - Coding Assignment

A Python implementation of Bitcoin's UTXO (Unspent Transaction Output) model, demonstrating transaction validation, mempool management, and mining simulation.

---

## Team Information

**Team Name:** Team Punju

**Team Members:**
1. Praneeth - 240008009
2. [Name 2] - [Roll Number]

---

## Features

- ✅ **UTXO Manager**: Track and manage unspent transaction outputs
- ✅ **Transaction Validation**: Implement all 5 validation rules
- ✅ **Mempool Management**: Store and manage pending transactions
- ✅ **Mining Simulation**: Select transactions, update UTXO set, calculate fees
- ✅ **Double-Spending Prevention**: Detect and prevent double-spend attacks
- ✅ **10 Test Scenarios**: All mandatory test cases implemented

---

## Project Structure

```
utxo-simulator/
├── src/
│   ├── __init__.py          # Package initialization
│   ├── main.py              # Main program entry point
│   ├── utxo_manager.py      # UTXO handling class
│   ├── transaction.py       # Transaction class/structure
│   ├── mempool.py           # Mempool management
│   ├── validator.py         # Validation logic
│   └── block.py             # Block/mining logic
├── tests/
│   └── test_scenarios.py    # All 10 test cases
├── requirements.txt         # Dependencies
├── README.md               # This file
└── sample_output.txt       # Demo run output
```

---

## Installation & Running

### Prerequisites
- Python 3.8 or higher
- No external dependencies required (uses standard library only)

### Running the Simulator

```bash
# Navigate to project directory
cd utxo-simulator

# Run the main program
python src/main.py

# Or run tests directly
python tests/test_scenarios.py
```

---

## Usage

### Main Menu Options

```
Main Menu:
  1. Create new transaction
  2. View UTXO set
  3. View mempool
  4. Mine block
  5. Run test scenarios
  6. View blockchain
  7. Check balance
  8. View detailed mempool
  9. Reset simulator
  0. Exit
```

### Example: Creating a Transaction

```
Enter choice: 1

--- Create New Transaction ---
Enter sender name: Alice
Available balance for Alice: 50.0000 BTC
Enter recipient name: Bob
Enter amount (BTC): 10
Enter fee (BTC) [0.001]: 0.001

Creating transaction: Alice -> Bob (10.0000 BTC)...

✓ Transaction valid! Fee: 0.0010 BTC
✓ Transaction ID: tx_1706900000_1234
✓ Transaction added to mempool. Fee: 0.0010 BTC
✓ Mempool now has 1 transactions.
```

### Example: Mining a Block

```
Enter choice: 4

--- Mine Block ---
Enter miner name [Miner1]: Miner1
Max transactions to include [5]: 5

Mining block...
Selected 1 transactions from mempool.
  - Processed tx_1706900000_1234 (fee: 0.0010 BTC)

Coinbase: Miner Miner1 receives 0.0010 BTC in fees

Block block_1706900100_5678 mined successfully!
Total fees: 0.0010 BTC
Removed 1 transactions from mempool.
```

---

## Design Decisions

### 1. Transaction Validation Rules
All 5 rules are implemented:
1. All inputs must exist in UTXO set
2. No double-spending in inputs (same UTXO twice)
3. Sum(inputs) ≥ Sum(outputs)
4. No negative amounts in outputs
5. No conflict with mempool

### 2. Mempool Eviction Policy
When mempool reaches maximum capacity, the lowest-fee transaction is evicted to make room for higher-fee transactions.

### 3. Double-Spend Prevention
- **Within transaction**: Detected by checking for duplicate input references
- **Across mempool**: Tracked using `spent_utxos` set in Mempool class
- **First-seen rule**: First valid transaction is accepted; conflicting transactions rejected

### 4. Unconfirmed Chain (Test 10)
We implement the **simpler approach**: reject spending unconfirmed UTXOs. This means a transaction cannot spend outputs from another transaction that hasn't been mined yet.

### 5. Fork Handling
Basic deterministic rules:
- Block with more transactions wins
- If tied, higher total fees wins
- If still tied, alphabetical by miner name

---

## Test Scenarios

| Test | Description | Expected Result |
|------|-------------|-----------------|
| 1 | Basic Valid Transaction | ACCEPT with change |
| 2 | Multiple Inputs | ACCEPT, aggregates UTXOs |
| 3 | Double-Spend Same TX | REJECT |
| 4 | Mempool Double-Spend | TX1 accepted, TX2 rejected |
| 5 | Insufficient Funds | REJECT |
| 6 | Negative Amount | REJECT |
| 7 | Zero Fee | ACCEPT |
| 8 | Race Attack | First-seen wins |
| 9 | Mining Flow | UTXOs updated, fees collected |
| 10 | Unconfirmed Chain | REJECT (design choice) |

---

## Initial State (Genesis Block)

| Owner   | Amount (BTC) | UTXO Reference |
|---------|--------------|----------------|
| Alice   | 50.0         | (genesis, 0)   |
| Bob     | 30.0         | (genesis, 1)   |
| Charlie | 20.0         | (genesis, 2)   |
| David   | 10.0         | (genesis, 3)   |
| Eve     | 5.0          | (genesis, 4)   |
| **Total** | **115.0**  |                |

---

## Key Classes

### UTXOManager
```python
class UTXOManager:
    def add_utxo(tx_id, index, amount, owner)
    def remove_utxo(tx_id, index)
    def get_balance(owner) -> float
    def exists(tx_id, index) -> bool
    def get_utxos_for_owner(owner) -> list
```

### Transaction
```python
class Transaction:
    def add_input(prev_tx, index, owner)
    def add_output(amount, address)
    def to_dict() -> dict
```

### Mempool
```python
class Mempool:
    def add_transaction(tx, utxo_manager) -> (bool, str)
    def remove_transaction(tx_id)
    def get_top_transactions(n, utxo_manager) -> list
```

### Mining
```python
def mine_block(miner_address, mempool, utxo_manager, blockchain, num_txs)
```

---

## References

- Bitcoin Whitepaper Sections 2, 5, 6
- Course Lecture 3 (L3.pdf) - Pages 7-37
- [Bitcoin UTXO Explained](https://learnmeabitcoin.com/beginners/utxo)
- [Bitcoin Transactions](https://learnmeabitcoin.com/beginners/transactions)

---

## License

This project is for educational purposes as part of CS 216 coursework.
