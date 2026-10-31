import os
from functools import lru_cache

from dotenv import load_dotenv
from sentence_transformers import SentenceTransformer

load_dotenv()

EMBEDDING_MODEL = os.getenv("EMBEDDING_MODEL", "paraphrase-multilingual-MiniLM-L12-v2")

# Prefixos exigidos por alguns modelos: (prefixo das pesquisas, prefixo dos documentos).
# Modelos que não estão aqui não usam prefixos.
PREFIXOS_POR_MODELO = {
    "intfloat/multilingual-e5-small": ("query: ", "passage: "),
}


def get_prefixos(model_name: str = EMBEDDING_MODEL) -> tuple[str, str]:
    """Devolve (prefixo das pesquisas, prefixo dos documentos) para o modelo."""
    return PREFIXOS_POR_MODELO.get(model_name, ("", ""))

@lru_cache(maxsize=4)
def get_model(model_name: str = EMBEDDING_MODEL) -> SentenceTransformer:
    """Carrega um modelo de embeddings. Cada modelo só é carregado uma vez."""
    print(f"A carregar o modelo '{model_name}'...")
    return SentenceTransformer(model_name)


def embed_texts(texts: list[str], model_name: str = EMBEDDING_MODEL) -> list[list[float]]:
    """Transforma uma lista de textos numa lista de vetores (normalizados)."""
    vectors = get_model(model_name).encode(texts, normalize_embeddings=True)
    return vectors.tolist()


def embed_text(text: str, model_name: str = EMBEDDING_MODEL) -> list[float]:
    """Transforma um único texto num vetor."""
    return embed_texts([text], model_name)[0]


@lru_cache(maxsize=4)
def get_dimension(model_name: str = EMBEDDING_MODEL) -> int:
    """Devolve o número de dimensões dos vetores gerados pelo modelo."""
    return len(embed_text("teste", model_name))


def embed_query(text: str, model_name: str = EMBEDDING_MODEL) -> list[float]:
    """Vetor de uma PESQUISA de um utilizador (com o prefixo de pesquisa, se o modelo o exigir)."""
    prefixo_pesquisa, _ = get_prefixos(model_name)
    return embed_text(prefixo_pesquisa + text, model_name)


def embed_documents(texts: list[str], model_name: str = EMBEDDING_MODEL) -> list[list[float]]:
    """Vetores dos TEXTOS dos POIs (com o prefixo de documento, se o modelo o exigir)."""
    _, prefixo_documento = get_prefixos(model_name)
    return embed_texts([prefixo_documento + t for t in texts], model_name)

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