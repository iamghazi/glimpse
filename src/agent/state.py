"""
Agent State Management
Handles persistence of agent sessions and projects
"""
import json
import logging
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime

from src.core.config import settings
from src.models.agent import AgentSession
from src.models.project import Project

logger = logging.getLogger(__name__)


class AgentStateManager:
    """Manages agent session and project state persistence"""

    def __init__(self):
        self.sessions_dir = settings.DATA_DIR / "agent_sessions"
        self.projects_dir = settings.DATA_DIR / "agent_projects"
        self._ensure_directories()

        # In-memory cache for active sessions
        self._sessions: Dict[str, AgentSession] = {}
        self._projects: Dict[str, Project] = {}

    def _ensure_directories(self):
        """Create storage directories if they don't exist"""
        self.sessions_dir.mkdir(parents=True, exist_ok=True)
        self.projects_dir.mkdir(parents=True, exist_ok=True)

    # Session Management

    def save_session(self, session: AgentSession) -> None:
        """Save a session to disk and cache"""
        self._sessions[session.id] = session

        session_path = self.sessions_dir / f"{session.id}.json"
        with open(session_path, "w") as f:
            json.dump(session.model_dump(mode="json"), f, indent=2, default=str)

        logger.debug(f"Saved session {session.id}")

    def get_session(self, session_id: str) -> Optional[AgentSession]:
        """Get a session by ID (from cache or disk)"""
        # Check cache first
        if session_id in self._sessions:
            return self._sessions[session_id]

        # Try loading from disk
        session_path = self.sessions_dir / f"{session_id}.json"
        if session_path.exists():
            with open(session_path, "r") as f:
                data = json.load(f)
                session = AgentSession(**data)
                self._sessions[session_id] = session
                return session

        return None

    def list_sessions(self) -> list[AgentSession]:
        """List all sessions"""
        sessions = []
        for session_path in self.sessions_dir.glob("*.json"):
            try:
                with open(session_path, "r") as f:
                    data = json.load(f)
                    sessions.append(AgentSession(**data))
            except Exception as e:
                logger.error(f"Failed to load session {session_path}: {e}")
        return sorted(sessions, key=lambda s: s.created_at, reverse=True)

    def delete_session(self, session_id: str) -> bool:
        """Delete a session"""
        # Remove from cache
        if session_id in self._sessions:
            del self._sessions[session_id]

        # Remove from disk
        session_path = self.sessions_dir / f"{session_id}.json"
        if session_path.exists():
            session_path.unlink()
            logger.info(f"Deleted session {session_id}")
            return True

        return False

    # Project Management

    def save_project(self, project: Project) -> None:
        """Save a project to disk and cache"""
        self._projects[project.id] = project

        project_path = self.projects_dir / f"{project.id}.json"
        with open(project_path, "w") as f:
            json.dump(project.model_dump(mode="json"), f, indent=2, default=str)

        logger.debug(f"Saved project {project.id}")

    def get_project(self, project_id: str) -> Optional[Project]:
        """Get a project by ID (from cache or disk)"""
        # Check cache first
        if project_id in self._projects:
            return self._projects[project_id]

        # Try loading from disk
        project_path = self.projects_dir / f"{project_id}.json"
        if project_path.exists():
            with open(project_path, "r") as f:
                data = json.load(f)
                project = Project(**data)
                self._projects[project_id] = project
                return project

        return None

    def list_projects(self) -> list[Project]:
        """List all projects"""
        projects = []
        for project_path in self.projects_dir.glob("*.json"):
            try:
                with open(project_path, "r") as f:
                    data = json.load(f)
                    projects.append(Project(**data))
            except Exception as e:
                logger.error(f"Failed to load project {project_path}: {e}")
        return sorted(projects, key=lambda p: p.updated_at, reverse=True)

    def delete_project(self, project_id: str) -> bool:
        """Delete a project"""
        # Remove from cache
        if project_id in self._projects:
            del self._projects[project_id]

        # Remove from disk
        project_path = self.projects_dir / f"{project_id}.json"
        if project_path.exists():
            project_path.unlink()
            logger.info(f"Deleted project {project_id}")
            return True

        return False


# Global state manager instance
state_manager = AgentStateManager()
