import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
import source_expansion as sx


def test_root_url_preserves_scheme_and_host():
    assert sx._root_url("https://icfre.gov.in/recruitments") == "https://icfre.gov.in/"
    assert sx._root_url("http://example.org/a/b?c=1") == "http://example.org/"
    assert sx._root_url("not-a-url") == "not-a-url"
