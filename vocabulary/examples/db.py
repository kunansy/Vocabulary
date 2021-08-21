import rnc
from sqlalchemy.engine import RowMapping


async def get_corpus_examples(*,
                              mycorp: str,
                              word: str,
                              pages_count: int) -> list[RowMapping]:
    corp = rnc.ParallelCorpus(
        word, pages_count,
        mycorp=rnc.mycorp[mycorp], marker=str.upper
    )
    await corp.request_examples_async()
    return list(corp)