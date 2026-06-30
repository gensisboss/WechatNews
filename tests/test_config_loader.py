import sys
import tempfile
import textwrap
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from src.config_loader import load_yaml


class ConfigLoaderTests(unittest.TestCase):
    def test_load_yaml_supports_project_config_shape(self):
        with tempfile.TemporaryDirectory() as temp_dir:
            path = Path(temp_dir) / "config.yml"
            path.write_text(
                textwrap.dedent(
                    """
                    title_template: "AI/Game Daily {date}"
                    max_items: 12
                    keywords:
                      - AI
                      - game
                    wechat:
                      create_draft: false
                      author: "Auto"
                    sources:
                      - name: OpenAI
                        url: https://openai.com/news/rss.xml
                        category: ai
                        enabled: true
                    """
                ).strip(),
                encoding="utf-8",
            )

            data = load_yaml(path)

        self.assertEqual(data["title_template"], "AI/Game Daily {date}")
        self.assertEqual(data["max_items"], 12)
        self.assertEqual(data["keywords"], ["AI", "game"])
        self.assertEqual(data["wechat"]["create_draft"], False)
        self.assertEqual(data["sources"][0]["enabled"], True)


if __name__ == "__main__":
    unittest.main()
