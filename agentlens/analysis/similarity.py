from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


_model = SentenceTransformer(
    "all-MiniLM-L6-v2"
)


def semantic_similarity(
    text_a: str,
    text_b: str,
) -> float:

    embeddings = _model.encode(
        [text_a, text_b]
    )

    return float(
        cosine_similarity(
            [embeddings[0]],
            [embeddings[1]],
        )[0][0]
    )
