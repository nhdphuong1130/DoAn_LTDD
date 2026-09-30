from speech import setup_models


def test_existing_snapshot_symlinks_are_materialized_for_onnx(tmp_path, monkeypatch):
    monkeypatch.setattr(setup_models, "CACHE", tmp_path)
    repo = tmp_path / "huggingface/hub/models--example--model"
    blob = repo / "blobs/weights"
    blob.parent.mkdir(parents=True)
    blob.write_bytes(b"model data")
    snapshot = repo / "snapshots/revision/onnx"
    snapshot.mkdir(parents=True)
    target = snapshot / "weights.data"
    target.symlink_to(blob)
    setup_models.materialize_snapshots()
    assert target.read_bytes() == b"model data"
    assert not target.is_symlink()
    assert blob.read_bytes() == b"model data"
    setup_models.materialize_snapshots()
