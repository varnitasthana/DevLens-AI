import re
from typing import Protocol

import httpx
from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.models.repository import Repository
from app.schemas.dashboard import GitHubImportRequest, GitHubImportResponse


class GitHubClient(Protocol):
    def repository(self, owner: str, name: str) -> dict[str, object]:
        ...


class HttpGitHubClient:
    def __init__(self, token: str | None = None, transport: httpx.BaseTransport | None = None) -> None:
        self.token = token
        self.transport = transport

    def repository(self, owner: str, name: str) -> dict[str, object]:
        headers = {"Accept": "application/vnd.github+json"}
        if self.token:
            headers["Authorization"] = f"Bearer {self.token}"
        with httpx.Client(transport=self.transport, timeout=15, headers=headers) as client:
            response = client.get(f"https://api.github.com/repos/{owner}/{name}")
            if response.status_code == 404:
                raise HTTPException(status_code=404, detail="GitHub repository not found")
            if response.status_code in (401, 403):
                raise HTTPException(status_code=403, detail="GitHub repository access denied")
            response.raise_for_status()
            return response.json()


class GitHubImportService:
    pattern = re.compile(r"^https?://github\.com/([^/]+)/([^/#]+?)(?:\.git)?/?$")

    def __init__(self, session: Session, client: GitHubClient) -> None:
        self.session = session
        self.client = client

    def import_repository(self, request: GitHubImportRequest) -> GitHubImportResponse:
        match = self.pattern.fullmatch(request.url.strip())
        if not match:
            raise HTTPException(status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, detail="Invalid GitHub repository URL")
        owner, name = match.groups()
        metadata = self.client.repository(owner, name)
        source_url = str(metadata["html_url"])
        existing = self.session.query(Repository).filter_by(source_url=source_url).first()
        if existing:
            return GitHubImportResponse.model_validate(existing)
        repository = Repository(
            name=str(metadata["full_name"]),
            source_url=source_url,
            default_branch=request.branch or str(metadata.get("default_branch") or "main"),
            description=str(metadata["description"]) if metadata.get("description") else None,
        )
        self.session.add(repository)
        self.session.commit()
        self.session.refresh(repository)
        return GitHubImportResponse.model_validate(repository)
