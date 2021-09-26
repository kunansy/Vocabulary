from typing import Any

import rnc

from vocabulary.common import settings
from vocabulary.common.log import logger


async def get_corpus_examples(*,
                              mycorp: str,
                              word: str,
                              pages_count: int) -> list[dict[str, Any]]:
    corp = rnc.ParallelCorpus(
        word, pages_count,
        mycorp=rnc.mycorp[mycorp],
        marker=settings.CORPUS_EXAMPLES_MARKER
    )
    logger.info("Requesting corpus examples")
    await corp.request_examples_async()
    logger.info("%s corpus examples got", len(corp))

    return [
        {
            'original': getattr(ex, mycorp),
            'native': ex.ru,
            'src': ex.src,
            'ambiguation': ex.ambiguation,
            'doc_url': ex.doc_url,
            'found_wordforms': ex.found_wordforms
         }
        for ex in corp
    ]
