import faiss

# Load the FAISS index
index = faiss.read_index("faiss_index_finetuned.bin")

# Check the number of stored embeddings
num_vectors = index.ntotal
print(f"FAISS index contains {num_vectors} embeddings.")

# Ensure the index is using INNER_PRODUCT (cosine similarity)
metric = index.metric_type
metric_name = "INNER_PRODUCT" if metric == faiss.METRIC_INNER_PRODUCT else "UNKNOWN"
print(f"FAISS index metric: {metric_name}")
