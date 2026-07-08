import urllib.error
from pathlib import Path

import backend.detect_ai_apis as scanner


def test_suggest_models_filters_by_task_and_sorts_by_downloads_then_likes(tmp_path, monkeypatch):
    def fake_urlopen(*args, **kwargs):
        raise urllib.error.URLError("disable live API during test")

    monkeypatch.setattr(scanner.urllib.request, "urlopen", fake_urlopen)

    fallback = tmp_path / "models_sample.json"
    fallback.write_text(
        """
[
  {
    "id": "wrong-task-popular",
    "task": "image-classification",
    "downloads": 1000000,
    "likes": 100000,
    "description": "Popular but wrong task"
  },
  {
    "id": "text-generation-low-downloads",
    "task": "text-generation",
    "downloads": 100,
    "likes": 1000,
    "description": "Correct task but low downloads"
  },
  {
    "id": "text-generation-high-downloads-low-likes",
    "task": "text-generation",
    "downloads": 100000,
    "likes": 10,
    "description": "Correct task, high downloads, lower likes"
  },
  {
    "id": "text-generation-high-downloads-high-likes",
    "task": "text-generation",
    "downloads": 100000,
    "likes": 500,
    "description": "Correct task, high downloads, higher likes"
  }
]
"""
    )

    results = scanner.suggest_models("text-generation", fallback)

    assert [model.id for model in results] == [
        "text-generation-high-downloads-high-likes",
        "text-generation-high-downloads-low-likes",
        "text-generation-low-downloads",
    ]

    assert all(model.task == "text-generation" for model in results)
    assert all(model.source == "local_cache" for model in results)
