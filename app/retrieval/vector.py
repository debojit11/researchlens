from pathlib import Path
from langchain_chroma import Chroma
from langchain_core.embeddings import Embeddings
from langchain_google_genai import GoogleGenerativeAIEmbeddings
from app.config import CHROMA_DIR


COLLECTION_NAME = "researchlens_docs"


class ResearchLensEmbeddings(Embeddings):
    """
    Gemini Embedding 2 wrapper for asymmetric question-answering retrieval.

    Important:
    - Documents are formatted only while generating embeddings.
    - Queries get the question-answering task instruction.
    - Original Document.page_content is not modified.
    """

    def __init__(self):
        self.model = GoogleGenerativeAIEmbeddings(model="gemini-embedding-2")

    @staticmethod
    def _prepare_document(text: str) -> str:
        """
        Format a ResearchLens chunk according to Gemini Embedding 2's
        asymmetric retrieval format.

        Our structured chunks begin with their section heading, so we
        use that first line as the document title.
        """

        stripped = text.strip()

        if not stripped:
            return "title: none | text:"

        parts = stripped.split("\n", maxsplit=1)

        title = parts[0].strip()

        if len(parts) == 2:
            content = parts[1].strip()
        else:
            content = stripped

        if not title:
            title = "none"

        return (
            f"title: {title} | "
            f"text: {content}"
        )



    @staticmethod
    def _prepare_query(query: str) -> str:
        """
        Format a user question for question-answering retrieval.
        """

        return (
            f"task: question answering | "
            f"query: {query.strip()}"
        )

    def embed_documents(self, texts: list[str],) -> list[list[float]]:
        prepared_texts = [self._prepare_document(text) for text in texts]

        return self.model.embed_documents(prepared_texts)


    def embed_query(self, text: str,) -> list[float]:
        prepared_query = self._prepare_query(text)

        return self.model.embed_query(prepared_query)



def get_embeddings():
    return ResearchLensEmbeddings()



def create_vector_store(chunks):
    embeddings = get_embeddings()

    vector_store = Chroma.from_documents(documents=chunks,
        embedding=embeddings,
        collection_name=COLLECTION_NAME,
        persist_directory=str(CHROMA_DIR),
    )

    return vector_store



def load_vector_store():
    embeddings = get_embeddings()

    vector_store = Chroma(collection_name=COLLECTION_NAME,
        embedding_function=embeddings,
        persist_directory=str(CHROMA_DIR),
    )

    return vector_store



def vector_store_exists():
    path = Path(CHROMA_DIR)

    return (path.exists() and any(path.iterdir()))



def vector_search(vector_store, query: str, k: int = 3,):
    return vector_store.similarity_search(
        query,
        k=k,
    )