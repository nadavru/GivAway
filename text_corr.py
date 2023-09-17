from sentence_transformers import SentenceTransformer, util

class TextCorrelate():
    def __init__(self):
        self.model_embedder = SentenceTransformer('sentence-transformers/msmarco-distilbert-base-tas-b')
    
    def correlate(self, text, queries):
 
        text_emb = self.model_embedder.encode(text)
        queries_emb = self.model_embedder.encode(queries)

        scores = util.dot_score(text_emb, queries_emb)[0].cpu().tolist()

        query_score_pairs = list(zip(queries, scores))

        #Sort by decreasing score
        query_score_pairs = sorted(query_score_pairs, key=lambda x: x[1], reverse=True)

        best_query = query_score_pairs[0][0]

        return best_query