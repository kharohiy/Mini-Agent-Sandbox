import os
import argparse
import uuid
import chromadb
from litellm import embedding
import pymupdf4llm
from langchain_text_splitters import MarkdownHeaderTextSplitter, RecursiveCharacterTextSplitter

def get_chroma_client():
    base_dir = "data"
    db_path = os.path.join(base_dir, "chroma_db")
    os.makedirs(db_path, exist_ok=True)
    return chromadb.PersistentClient(path=db_path)

def embed_texts(texts):
    # We use the local Nomic model via Ollama.
    response = embedding(
        model="ollama/nomic-embed-text",
        input=texts,
        api_base="http://localhost:11434"
    )
    return [item["embedding"] for item in response.data]

class LiteLLMEmbeddingFunction(chromadb.api.types.EmbeddingFunction):
    def __call__(self, input: chromadb.api.types.Documents) -> chromadb.api.types.Embeddings:
        return embed_texts(input)

def main():
    parser = argparse.ArgumentParser(description="Ingest PDF book into ChromaDB using Markdown and semantic chunking")
    parser.add_argument("--pdf", type=str, required=True, help="Path to PDF file")
    args = parser.parse_args()
    
    pdf_path = args.pdf
    if not os.path.exists(pdf_path):
        print(f"Error: File '{pdf_path}' not found.")
        return

    print(f"🚀 Parsing PDF to Markdown via PyMuPDF4LLM: {pdf_path} ...")
    try:
        md_text = pymupdf4llm.to_markdown(pdf_path)
    except Exception as e:
        print(f"Error parsing PDF: {e}")
        return
        
    print("✅ PDF successfully converted to Markdown.")

    print("✂️ Semantic chunking using Markdown headers...")
    headers_to_split_on = [
        ("#", "Header 1"),
        ("##", "Header 2"),
        ("###", "Header 3"),
    ]
    markdown_splitter = MarkdownHeaderTextSplitter(headers_to_split_on=headers_to_split_on)
    md_header_splits = markdown_splitter.split_text(md_text)

    # Secondary character split for very long blocks
    chunk_size = 1000
    chunk_overlap = 150
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=chunk_size, chunk_overlap=chunk_overlap
    )

    splits = text_splitter.split_documents(md_header_splits)
    print(f"✅ Total text chunks created: {len(splits)}")

    client = get_chroma_client()
    collection_name = "android_architecture_library"
    print(f"🗄️ Preparing ChromaDB collection: '{collection_name}'...")
    
    emb_fn = LiteLLMEmbeddingFunction()
    collection = client.get_or_create_collection(
        name=collection_name,
        embedding_function=emb_fn
    )

    book_name = os.path.basename(pdf_path)
    batch_size = 50
    total_batches = (len(splits) - 1) // batch_size + 1
    
    print("🧬 Vectorizing and inserting chunks (Ollama/nomic-embed-text) ...")
    for i in range(0, len(splits), batch_size):
        batch = splits[i:i+batch_size]
        
        texts = [doc.page_content for doc in batch]
        metadatas = []
        for doc in batch:
            # Add headers as context if available
            meta = doc.metadata.copy()
            meta["source"] = book_name
            context_str = " | ".join([f"{k}: {v}" for k,v in meta.items() if k != "source"])
            if context_str:
                meta["context"] = context_str
            metadatas.append(meta)
        
        ids = [str(uuid.uuid4()) for _ in batch]
        
        try:
            collection.add(
                documents=texts,
                metadatas=metadatas,
                ids=ids
            )
            print(f"  -> Inserted batch {i//batch_size + 1} / {total_batches}")
        except Exception as e:
            print(f"  -> Error inserting batch {i//batch_size + 1}: {e}")

    print("\n🎉 Knowledge ingestion complete! The book is now available in ChromaDB.")

if __name__ == "__main__":
    main()
