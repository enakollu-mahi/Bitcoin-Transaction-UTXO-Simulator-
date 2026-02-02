"""
Transaction Validator - Validates transactions according to Bitcoin rules
CS 216: Introduction to Blockchain Assignment
"""

from typing import Tuple, Set


class ValidationResult:
    """Represents the result of a transaction validation."""
    
    def __init__(self, valid: bool, message: str = "", fee: float = 0.0):
        self.valid = valid
        self.message = message
        self.fee = fee
    
    def __bool__(self) -> bool:
        return self.valid
    
    def __str__(self) -> str:
        if self.valid:
            return f"VALID (fee: {self.fee:.4f} BTC)"
        return f"INVALID: {self.message}"


def validate_transaction(tx, utxo_manager, mempool_spent_utxos: Set[tuple] = None) -> ValidationResult:
    """
    Validate a transaction according to Bitcoin rules.
    
    Validation Rules:
    1. All inputs must exist in UTXO set
    2. No double-spending in inputs (same UTXO twice in same transaction)
    3. Sum(inputs) >= Sum(outputs) (difference = fee)
    4. No negative amounts in outputs
    5. No conflict with mempool (UTXO not already spent in unconfirmed tx)
    
    Args:
        tx: Transaction object to validate
        utxo_manager: UTXOManager instance with current UTXO set
        mempool_spent_utxos: Set of (tx_id, index) tuples already spent in mempool
    
    Returns:
        ValidationResult object
    """
    if mempool_spent_utxos is None:
        mempool_spent_utxos = set()
    
    # Rule 4: Check for negative amounts in outputs (check first for quick fail)
    for i, output in enumerate(tx.outputs):
        if output["amount"] < 0:
            return ValidationResult(
                False, 
                f"Output {i} has negative amount: {output['amount']} BTC"
            )
    
    # Rule 1 & 2: Check inputs exist and no duplicates
    input_refs = set()
    total_input = 0.0
    
    for i, inp in enumerate(tx.inputs):
        prev_tx = inp["prev_tx"]
        index = inp["index"]
        owner = inp["owner"]
        ref = (prev_tx, index)
        
        # Rule 2: Check for duplicate inputs (double-spend in same transaction)
        if ref in input_refs:
            return ValidationResult(
                False,
                f"Double-spend detected: UTXO ({prev_tx}, {index}) used multiple times in same transaction"
            )
        input_refs.add(ref)
        
        # Rule 1: Check if UTXO exists
        utxo = utxo_manager.get_utxo(prev_tx, index)
        if utxo is None:
            return ValidationResult(
                False,
                f"Input {i}: UTXO ({prev_tx}, {index}) does not exist"
            )
        
        # Verify owner (simulates signature verification)
        if utxo["owner"] != owner:
            return ValidationResult(
                False,
                f"Input {i}: Owner mismatch. Expected {utxo['owner']}, got {owner}"
            )
        
        # Rule 5: Check for mempool conflicts
        if ref in mempool_spent_utxos:
            return ValidationResult(
                False,
                f"UTXO ({prev_tx}, {index}) already spent in mempool (pending transaction)"
            )
        
        total_input += utxo["amount"]
    
    # Calculate total output
    total_output = sum(out["amount"] for out in tx.outputs)
    
    # Rule 3: Check inputs >= outputs
    if total_input < total_output:
        return ValidationResult(
            False,
            f"Insufficient input: {total_input:.4f} BTC < {total_output:.4f} BTC output"
        )
    
    # Calculate fee
    fee = total_input - total_output
    
    return ValidationResult(True, "Transaction valid", fee)


def get_transaction_fee(tx, utxo_manager) -> float:
    """
    Calculate the fee for a transaction.
    
    Args:
        tx: Transaction object
        utxo_manager: UTXOManager instance
    
    Returns:
        Transaction fee in BTC, or -1 if invalid
    """
    total_input = 0.0
    
    for inp in tx.inputs:
        utxo = utxo_manager.get_utxo(inp["prev_tx"], inp["index"])
        if utxo is None:
            return -1
        total_input += utxo["amount"]
    
    total_output = sum(out["amount"] for out in tx.outputs)
    
    return total_input - total_output


def validate_inputs_exist(tx, utxo_manager) -> Tuple[bool, str]:
    """Check if all transaction inputs exist in UTXO set."""
    for inp in tx.inputs:
        if not utxo_manager.exists(inp["prev_tx"], inp["index"]):
            return False, f"UTXO ({inp['prev_tx']}, {inp['index']}) does not exist"
    return True, "All inputs exist"


def validate_no_double_spend_internal(tx) -> Tuple[bool, str]:
    """Check for double-spending within the same transaction."""
    refs = set()
    for inp in tx.inputs:
        ref = (inp["prev_tx"], inp["index"])
        if ref in refs:
            return False, f"UTXO ({inp['prev_tx']}, {inp['index']}) used multiple times"
        refs.add(ref)
    return True, "No internal double-spending"


def validate_amounts(tx, utxo_manager) -> Tuple[bool, str, float]:
    """Validate that inputs cover outputs and calculate fee."""
    total_input = 0.0
    
    for inp in tx.inputs:
        utxo = utxo_manager.get_utxo(inp["prev_tx"], inp["index"])
        if utxo:
            total_input += utxo["amount"]
    
    total_output = sum(out["amount"] for out in tx.outputs)
    
    if total_input < total_output:
        return False, f"Insufficient funds: {total_input:.4f} < {total_output:.4f}", 0.0
    
    fee = total_input - total_output
    return True, "Amounts valid", fee


def validate_no_negative_outputs(tx) -> Tuple[bool, str]:
    """Check for negative output amounts."""
    for i, out in enumerate(tx.outputs):
        if out["amount"] < 0:
            return False, f"Output {i} has negative amount: {out['amount']}"
    return True, "No negative outputs"
