from app.tools.rag import is_grounded_enough


def test_empty_docs_is_not_grounded():
    assert is_grounded_enough([]) is False


def test_low_similarity_docs_is_not_grounded():
    # Mirrors what a plain top-k cosine search returns for a genuinely
    # off-topic query — it still returns k rows, just weakly related ones.
    docs = [{"similarity": 0.49}, {"similarity": 0.43}, {"similarity": 0.35}]
    assert is_grounded_enough(docs) is False


def test_high_similarity_docs_is_grounded():
    docs = [{"similarity": 0.62}, {"similarity": 0.45}]
    assert is_grounded_enough(docs) is True


def test_borderline_similarity_at_threshold_is_grounded():
    docs = [{"similarity": 0.5}]
    assert is_grounded_enough(docs) is True
