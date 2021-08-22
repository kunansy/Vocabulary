from typing import Any

import rnc


async def get_corpus_examples(*,
                              mycorp: str,
                              word: str,
                              pages_count: int) -> list[dict[str, Any]]:
    corp = rnc.ParallelCorpus(
        word, pages_count,
        mycorp=rnc.mycorp[mycorp], marker=str.upper
    )
    await corp.request_examples_async()
    return [
        {
            'original': ex.en,
            'native': ex.ru,
            'src': ex.src,
            'ambiguation': ex.ambiguation,
            'doc_url': ex.doc_url,
            'found_wordforms': ex.found_wordforms
         }
        for ex in corp
    ]
