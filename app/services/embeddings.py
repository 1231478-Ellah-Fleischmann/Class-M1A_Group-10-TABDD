import os
from functools import lru_cache

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    """Carrega o modelo de embeddings. Só carrega da primeira vez; depois reutiliza."""
    print(f"A carregar o modelo '{EMBEDDING_MODEL}'...")
    return SentenceTransformer(EMBEDDING_MODEL)


def embed_texts(texts: list[str]) -> list[list[float]]:
    """Transforma uma lista de textos numa lista de vetores (normalizados)."""
    vectors = get_model().encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_text(text: str) -> list[float]:
    """Transforma um único texto num vetor."""
    return embed_texts([text])[0]

@lru_cache(maxsize=1)
def get_dimension() -> int:
    """Devolve o número de dimensões dos vetores gerados pelo modelo."""
    return len(embed_text("teste"))

if __name__ == "__main__":
    frases = [
        "Praia calma para famílias",
        "Praia sossegada, boa para ir com crianças",
        "Discoteca com música alta até de madrugada",
    ]

    vetores = embed_texts(frases)

    print("Número de vetores:", len(vetores))
    print("Dimensão de cada vetor:", len(vetores[0]))
    print("Primeiros 5 números do 1.º vetor:", [round(x, 3) for x in vetores[0][:5]])

    def cosseno(a: list[float], b: list[float]) -> float:
        # Como os vetores estão normalizados, o cosseno é só o produto escalar
        return sum(x * y for x, y in zip(a, b))

    print()
    print("Semelhança entre frase 1 e frase 2:", round(cosseno(vetores[0], vetores[1]), 3))
    print("Semelhança entre frase 1 e frase 3:", round(cosseno(vetores[0], vetores[2]), 3))