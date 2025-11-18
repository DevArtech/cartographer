import os
import pathlib
import subprocess
from typing import Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel
import json


router = APIRouter()


class MapperResponse(BaseModel):
	content: str
	script_exit_code: int
	network_map_path: Optional[str] = None


def _project_root() -> pathlib.Path:
	# backend/app/routers -> repo root at ../../..
	return pathlib.Path(__file__).resolve().parents[3]


def _script_path() -> pathlib.Path:
	return _project_root() / "lan_mapper.sh"


def _network_map_candidates() -> list[pathlib.Path]:
	root = _project_root()
	return [
		root / "network_map.txt",
		root / "output" / "network_map.txt",
	]


@router.post("/run-mapper", response_model=MapperResponse)
def run_mapper() -> MapperResponse:
	script = _script_path()
	if not script.exists():
		raise HTTPException(status_code=404, detail=f"lan_mapper.sh not found at {script}")
	if not os.access(script, os.X_OK):
		# Try to run with /bin/bash even if not executable
		cmd = ["/bin/bash", str(script)]
	else:
		cmd = [str(script)]

	try:
		# Run from repo root to keep relative paths consistent
		proc = subprocess.run(
			cmd,
			cwd=str(_project_root()),
			stdout=subprocess.PIPE,
			stderr=subprocess.PIPE,
			text=True,
			timeout=300,
		)
	except subprocess.TimeoutExpired:
		raise HTTPException(status_code=504, detail="lan_mapper.sh timed out after 300s")
	except Exception as exc:  # pragma: no cover
		raise HTTPException(status_code=500, detail=f"Failed to run lan_mapper.sh: {exc}")

	# Prefer an actual file artifact if present
	content: Optional[str] = None
	map_path: Optional[str] = None
	for candidate in _network_map_candidates():
		if candidate.exists():
			try:
				content = candidate.read_text()
				map_path = str(candidate)
				break
			except Exception:
				pass

	# Fallback to stdout
	if content is None:
		content = proc.stdout.strip()

	if not content:
		# Provide stderr context for easier debugging
		raise HTTPException(
			status_code=500,
			detail=f"No network_map.txt content produced. stderr: {proc.stderr.strip()}",
		)

	return MapperResponse(
		content=content,
		script_exit_code=proc.returncode,
		network_map_path=map_path,
	)

def _sse_event(event: str, data: str) -> str:
	# Basic SSE formatting; split multi-line payloads
	lines = data.splitlines() or [""]
	chunks = [f"event: {event}"]
	for line in lines:
		chunks.append(f"data: {line}")
	chunks.append("")  # end of message
	return "\n".join(chunks) + "\n"


@router.get("/run-mapper/stream")
def run_mapper_stream():
	script = _script_path()
	if not script.exists():
		raise HTTPException(status_code=404, detail=f"lan_mapper.sh not found at {script}")

	def event_gen():
		# Try to execute with bash to avoid exec perm issues
		cmd = ["/bin/bash", str(script)] if not os.access(script, os.X_OK) else [str(script)]
		try:
			proc = subprocess.Popen(
				cmd,
				cwd=str(_project_root()),
				stdout=subprocess.PIPE,
				stderr=subprocess.PIPE,
				text=True,
				bufsize=1,
				universal_newlines=True,
			)
		except Exception as exc:
			yield _sse_event("log", f"ERROR: failed to start lan_mapper.sh: {exc}")
			yield _sse_event("done", "exit=-1")
			return

		# Stream stdout
		if proc.stdout:
			for line in proc.stdout:
				yield _sse_event("log", line.rstrip("\n"))
		# Drain stderr afterwards (some scripts only write stderr)
		if proc.stderr:
			for line in proc.stderr:
				yield _sse_event("log", f"STDERR: {line.rstrip('\n')}")

		exit_code = proc.wait()

		# Attempt to read produced file
		result_payload = {"content": "", "script_exit_code": exit_code, "network_map_path": None}
		for candidate in _network_map_candidates():
			if candidate.exists():
				try:
					result_payload["content"] = candidate.read_text()
					result_payload["network_map_path"] = str(candidate)
					break
				except Exception as exc:
					yield _sse_event("log", f"ERROR: could not read {candidate}: {exc}")

		# If no file, try to provide a minimal result from stdout (already streamed)
		if not result_payload["content"]:
			result_payload["content"] = ""

		yield _sse_event("result", json.dumps(result_payload))
		yield _sse_event("done", f"exit={exit_code}")

	return StreamingResponse(event_gen(), media_type="text/event-stream")


