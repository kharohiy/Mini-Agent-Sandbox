import unittest
from project_retrieval import _source_hits


class ExactSourceRetrievalTests(unittest.TestCase):
    def test_exact_source_uses_existing_chunks_in_original_order(self):
        class Collection:
            def get(self, **kwargs):
                self.kwargs = kwargs
                return {'documents': ['second chunk', 'first chunk'],
                        'metadatas': [{'chunk_index': 1}, {'chunk_index': 0}]}
        collection = Collection()
        hits = _source_hits(collection, [{'source': 'app/MainActivity.kt', 'module': ':app', 'sha256': 'a' * 64}], 1)
        self.assertEqual(collection.kwargs['where'], {'source': 'app/MainActivity.kt'})
        self.assertEqual(hits[0]['text'], 'first chunk\nsecond chunk')
        self.assertEqual(hits[0]['scope'], 'project-code')

    def test_missing_indexed_source_does_not_read_source_files(self):
        class Collection:
            def get(self, **kwargs):
                return {'documents': [], 'metadatas': []}
        self.assertEqual(_source_hits(Collection(), [{'source': 'missing/File.kt', 'module': ':app', 'sha256': 'b' * 64}], 1), [])

    def test_source_count_and_text_are_bounded(self):
        class Collection:
            def get(self, **kwargs):
                return {'documents': ['a' * 10000], 'metadatas': [{}]}
        hits = _source_hits(Collection(), [{'source': 'a.kt', 'module': ':', 'sha256': 'c' * 64}, {'source': 'b.kt', 'module': ':', 'sha256': 'd' * 64}], 1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(len(hits[0]['text']), 6000)
