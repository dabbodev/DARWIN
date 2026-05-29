from darwin.auth.symbolic import SymbolicAuthState


def test_symbolic_auth_state_can_model_failure():
    auth = SymbolicAuthState(rolling_proof_valid=False)
    assert not auth.all_valid
