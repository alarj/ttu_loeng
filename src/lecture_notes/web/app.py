from __future__ import annotations

import hashlib
import secrets
import logging
import re
import uuid
from contextlib import asynccontextmanager
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from urllib.parse import quote

import httpx
from fastapi import Depends, FastAPI, HTTPException, Request, status
from fastapi.responses import FileResponse, HTMLResponse, JSONResponse, RedirectResponse, Response, StreamingResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from markdown_it import MarkdownIt
from pydantic import BaseModel
from starlette.datastructures import UploadFile
from starlette.middleware.sessions import SessionMiddleware
from starlette.status import HTTP_303_SEE_OTHER
from starlette.concurrency import run_in_threadpool

from lecture_notes.web.database import OracleRepository
from lecture_notes.web.models import UploadInput, User
from lecture_notes.web.ords import OrdsClient
from lecture_notes.web.services import LectureService, ValidationError
from lecture_notes.web.settings import OrdsSettings, WebSettings
from lecture_notes.web.translations import translate


PACKAGE_ROOT = Path(__file__).resolve().parent
STATIC_VERSION = hashlib.sha256(
    b"".join(
        (PACKAGE_ROOT / "static" / filename).read_bytes()
        for filename in ("app.css", "app.js")
    )
).hexdigest()[:12]
TEMPLATES = Jinja2Templates(directory=str(PACKAGE_ROOT / "templates"))
LOGGER = logging.getLogger("lecture_notes.web")
GOOGLE_TOKENINFO_URL = "https://oauth2.googleapis.com/tokeninfo"
MARKDOWN = MarkdownIt("commonmark", {"html": False}).enable(["strikethrough", "table"])
TRANSCRIPT_TIME_RE = re.compile(r"\[(\d{2,}:\d{2}:\d{2})–(\d{2,}:\d{2}:\d{2})\]")
SLIDE_IMAGE_RE = re.compile(
    r"(!\[[^\]]*\]\()images/([A-Za-z0-9_.-]+\.(?:jpe?g|png|webp))(\s*(?:['\"][^)]*['\"])?\))",
    re.IGNORECASE,
)


class GoogleAuthRequest(BaseModel):
    id_token: str


def create_app(
    app_settings: WebSettings | None = None,
    repository: Any | None = None,
    ords_client: Any | None = None,
    echo_factory: Any | None = None,
) -> FastAPI:
    _configure_web_logging()
    settings = app_settings or WebSettings.from_env()
    owns_repository = repository is None

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        app.state.repository = repository or OracleRepository.from_env()
        app.state.ords = ords_client or OrdsClient(OrdsSettings.from_env())
        app.state.service = LectureService(
            app.state.repository,
            app.state.ords,
            settings.runtime_root,
            **({"echo_factory": echo_factory} if echo_factory else {}),
        )
        yield
        if owns_repository:
            app.state.repository.close()

    app = FastAPI(title="TTU loengutranskriptsioon", lifespan=lifespan)
    app.state.settings = settings
    app.add_middleware(
        SessionMiddleware,
        secret_key=settings.session_secret,
        session_cookie="ttu_loeng_session",
        same_site="lax",
        https_only=True,
        max_age=12 * 60 * 60,
    )
    app.mount("/static", StaticFiles(directory=str(PACKAGE_ROOT / "static")), name="static")

    async def current_user(request: Request) -> User:
        user_id = request.session.get("user_id")
        if not isinstance(user_id, int):
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, translate("login_required"))
        try:
            user = await run_in_threadpool(request.app.state.repository.get_user, user_id)
        except KeyError as exc:
            request.session.clear()
            raise HTTPException(status.HTTP_401_UNAUTHORIZED, translate("login_required")) from exc
        if not user.enabled:
            request.session.clear()
            raise HTTPException(status.HTTP_403_FORBIDDEN, translate("account_disabled"))
        return user

    async def admin_user(user: User = Depends(current_user)) -> User:
        if not user.is_admin:
            raise HTTPException(status.HTTP_403_FORBIDDEN, translate("forbidden"))
        return user

    def context(request: Request, user: User | None = None, **values: Any) -> dict[str, Any]:
        return {
            "request": request,
            "t": translate,
            "user": user,
            "csrf_token": _csrf_token(request),
            "poll_interval_seconds": settings.ui_status_poll_interval_seconds,
            "static_version": STATIC_VERSION,
            "utc_iso": _utc_iso,
            "date_only": _date_only,
            **values,
        }

    @app.exception_handler(HTTPException)
    async def http_error(request: Request, exc: HTTPException) -> Response:
        if exc.status_code == status.HTTP_401_UNAUTHORIZED:
            return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)
        return TEMPLATES.TemplateResponse(
            request,
            "error.html",
            context(request, message=str(exc.detail)),
            status_code=exc.status_code,
        )

    @app.get("/", response_class=HTMLResponse)
    async def index(request: Request) -> HTMLResponse:
        try:
            user = await current_user(request)
        except HTTPException as exc:
            if exc.status_code != status.HTTP_401_UNAUTHORIZED:
                raise
            return TEMPLATES.TemplateResponse(request, "login.html", context(request))
        courses = await run_in_threadpool(request.app.state.service.list_courses)
        return TEMPLATES.TemplateResponse(
            request,
            "index.html",
            context(request, user, courses=courses, message=request.query_params.get("message")),
        )

    @app.get("/courses/{canonical_section_id}", response_class=HTMLResponse)
    async def course_lectures(
        canonical_section_id: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> HTMLResponse:
        try:
            course = await run_in_threadpool(
                request.app.state.service.get_course,
                canonical_section_id,
            )
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        lectures = await run_in_threadpool(
            request.app.state.service.list_lectures,
            canonical_section_id,
        )
        return TEMPLATES.TemplateResponse(
            request,
            "course.html",
            context(request, user, course=course, lectures=lectures),
        )

    @app.get("/api/auth/google/config")
    async def google_config() -> dict[str, object]:
        return {"enabled": bool(settings.google_client_id), "client_id": settings.google_client_id}

    @app.post("/api/auth/google")
    async def google_login(body: GoogleAuthRequest, request: Request) -> JSONResponse:
        try:
            profile = await _verify_google_id_token(body.id_token, settings.google_client_id)
        except HTTPException as exc:
            return JSONResponse({"message": str(exc.detail)}, status_code=exc.status_code)
        subject = str(profile["sub"])
        email = str(profile["email"]).strip().lower()
        display_name = str(profile.get("name") or email)
        user = await run_in_threadpool(
            request.app.state.repository.get_or_create_google_user,
            subject,
            email,
            display_name,
        )
        if not user.enabled:
            return JSONResponse(
                {"message": translate("account_disabled")},
                status_code=status.HTTP_403_FORBIDDEN,
            )
        request.session.clear()
        request.session["user_id"] = user.user_id
        request.session["csrf_token"] = secrets.token_urlsafe(32)
        return JSONResponse({"ok": True})

    @app.post("/auth/logout")
    async def logout(request: Request, user: User = Depends(current_user)) -> RedirectResponse:
        del user
        await _verify_csrf(request)
        request.session.clear()
        return RedirectResponse("/", status_code=HTTP_303_SEE_OTHER)

    @app.get("/submissions/new", response_class=HTMLResponse)
    async def new_submission(request: Request, user: User = Depends(admin_user)) -> HTMLResponse:
        courses = await run_in_threadpool(request.app.state.service.list_courses)
        return TEMPLATES.TemplateResponse(
            request,
            "new_submission.html",
            context(request, user, courses=courses, resolver=None, submission_request_id=None),
        )

    @app.post("/submissions/resolve", response_class=HTMLResponse)
    async def resolve_submission(request: Request, user: User = Depends(admin_user)) -> HTMLResponse:
        form = await _verified_form(request)
        public_url = str(form.get("public_url") or "").strip()
        manual_public_url = public_url
        canonical_section_id = str(form.get("canonical_section_id") or "").strip()
        courses = await run_in_threadpool(request.app.state.service.list_courses)
        try:
            if canonical_section_id:
                selected_course = await run_in_threadpool(
                    request.app.state.service.get_course,
                    canonical_section_id,
                )
                public_url = str(selected_course.echo_public_url or "").strip()
            if not public_url:
                raise ValidationError("INVALID_COURSE", "Course URL is missing")
            resolver = await run_in_threadpool(request.app.state.service.resolve, public_url)
            submission_request_id = str(uuid.uuid4())
            message = None
        except (KeyError, ValidationError):
            resolver = None
            submission_request_id = None
            message = translate("resolve_failed")
        except Exception:
            LOGGER.exception("Echo360 resolution failed")
            resolver = None
            submission_request_id = None
            message = translate("resolve_failed")
        return TEMPLATES.TemplateResponse(
            request,
            "new_submission.html",
            context(
                request,
                user,
                courses=courses,
                resolver=resolver,
                public_url=public_url,
                manual_public_url=manual_public_url,
                selected_course_id=canonical_section_id,
                submission_request_id=submission_request_id,
                message=message,
            ),
            status_code=200 if resolver else 400,
        )

    @app.post("/submissions")
    async def create_submission_route(request: Request, user: User = Depends(admin_user)) -> Response:
        form = await _verified_form(request)
        public_url = str(form.get("public_url") or "").strip()
        submission_request_id = str(form.get("submission_request_id") or "").strip()
        selected = [str(value) for value in form.getlist("lesson_id")]
        upload_files: list[UploadFile] = []
        uploads: list[UploadInput] = []
        for lesson_id in selected:
            candidate = form.get(f"slides_{lesson_id}")
            if isinstance(candidate, UploadFile) and candidate.filename:
                upload_files.append(candidate)
                uploads.append(
                    UploadInput(
                        lesson_id=lesson_id,
                        filename=candidate.filename,
                        media_type=candidate.content_type or "application/octet-stream",
                        stream=candidate.file,
                    )
                )
        try:
            await run_in_threadpool(
                request.app.state.service.create_submission,
                user_id=user.user_id,
                submission_request_id=submission_request_id,
                public_url=public_url,
                selected_lesson_ids=selected,
                uploads=uploads,
            )
        except ValidationError as exc:
            courses = await run_in_threadpool(request.app.state.service.list_courses)
            if exc.code == "INVALID_SELECTION":
                message = translate("no_selection")
            elif exc.code == "INVALID_UPLOAD":
                message = translate("invalid_upload")
            else:
                message = translate("invalid_request")
            return TEMPLATES.TemplateResponse(
                request,
                "new_submission.html",
                context(
                    request,
                    user,
                    courses=courses,
                    resolver=None,
                    public_url=public_url,
                    manual_public_url=public_url,
                    submission_request_id=None,
                    message=message,
                ),
                status_code=400,
            )
        except Exception:
            LOGGER.exception("Submission creation failed")
            courses = await run_in_threadpool(request.app.state.service.list_courses)
            return TEMPLATES.TemplateResponse(
                request,
                "new_submission.html",
                context(
                    request,
                    user,
                    courses=courses,
                    resolver=None,
                    public_url=public_url,
                    manual_public_url=public_url,
                    submission_request_id=None,
                    message=translate("submission_failed"),
                ),
                status_code=500,
            )
        finally:
            for upload in upload_files:
                await upload.close()
        return RedirectResponse("/?message=submission_created", status_code=HTTP_303_SEE_OTHER)

    @app.get("/lectures/{lecture_id}", response_class=HTMLResponse)
    async def lecture_detail(
        lecture_id: int,
        request: Request,
        version: int | None = None,
        user: User = Depends(current_user),
    ) -> HTMLResponse:
        try:
            lecture = await run_in_threadpool(request.app.state.service.get_lecture, lecture_id)
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        selected_version = await run_in_threadpool(
            request.app.state.service.selected_slide_version,
            lecture,
            version,
        )
        if version is not None and selected_version is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request"))
        slide_versions = await run_in_threadpool(request.app.state.service.slide_versions, lecture)
        result_path = request.app.state.service.result_path(lecture, selected_version)
        result_text = (
            await run_in_threadpool(result_path.read_text, encoding="utf-8")
            if result_path is not None
            else None
        )
        result_html = (
            _render_markdown(
                result_text,
                lecture_id,
                selected_version.operation_id if selected_version is not None else None,
            )
            if result_text is not None
            else None
        )
        sharing_ready = request.app.state.service.publishable_result_path(lecture) is not None
        return TEMPLATES.TemplateResponse(
            request,
            "lecture.html",
            context(
                request,
                user,
                lecture=lecture,
                result_ready=result_path is not None,
                sharing_ready=sharing_ready,
                download_ready=sharing_ready,
                result_html=result_html,
                slide_versions=slide_versions,
                selected_version=selected_version,
                echo_url=f"https://echo360.org.uk/lesson/{quote(lecture.echo_lesson_id, safe='')}/classroom",
                base_url=settings.base_url,
            ),
        )

    @app.get("/lectures/{lecture_id}/versions/{operation_id}")
    async def lecture_version_content(
        lecture_id: int,
        operation_id: int,
        request: Request,
        user: User = Depends(current_user),
    ) -> JSONResponse:
        del user
        try:
            lecture = await run_in_threadpool(request.app.state.service.get_lecture, lecture_id)
            version = await run_in_threadpool(
                request.app.state.service.selected_slide_version,
                lecture,
                operation_id,
            )
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        if version is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request"))
        result_text = await run_in_threadpool(version.markdown_path.read_text, encoding="utf-8")
        return JSONResponse(
            {
                "operation_id": version.operation_id,
                "html": _render_markdown(result_text, lecture_id, version.operation_id),
                "download_url": f"/lectures/{lecture_id}/download?version={version.operation_id}",
            }
        )

    @app.get("/lectures/{lecture_id}/slides/{operation_id}/{filename}")
    async def lecture_version_slide(
        lecture_id: int,
        operation_id: int,
        filename: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> FileResponse:
        del user
        try:
            lecture = await run_in_threadpool(request.app.state.service.get_lecture, lecture_id)
            version = await run_in_threadpool(
                request.app.state.service.selected_slide_version,
                lecture,
                operation_id,
            )
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        path = request.app.state.service.slide_image_path(lecture, filename, version)
        if path is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request"))
        return FileResponse(path)

    @app.get("/lectures/{lecture_id}/slides/{filename}")
    async def lecture_slide(
        lecture_id: int,
        filename: str,
        request: Request,
        user: User = Depends(current_user),
    ) -> FileResponse:
        del user
        try:
            lecture = await run_in_threadpool(request.app.state.service.get_lecture, lecture_id)
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        path = request.app.state.service.slide_image_path(lecture, filename)
        if path is None:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request"))
        return FileResponse(path)

    @app.get("/lectures/{lecture_id}/video")
    async def lecture_video(
        lecture_id: int,
        request: Request,
        user: User = Depends(current_user),
    ) -> StreamingResponse:
        del user
        try:
            video = await run_in_threadpool(
                request.app.state.service.video_stream,
                lecture_id,
                request.headers.get("range"),
            )
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        except ValidationError as exc:
            code = (
                status.HTTP_416_REQUESTED_RANGE_NOT_SATISFIABLE
                if exc.code == "INVALID_VIDEO_RANGE"
                else status.HTTP_404_NOT_FOUND
            )
            raise HTTPException(code, exc.message) from exc
        except Exception as exc:
            LOGGER.exception("Echo360 video stream failed", extra={"lecture_id": lecture_id})
            raise HTTPException(status.HTTP_502_BAD_GATEWAY, "Echo360 video is unavailable") from exc
        return StreamingResponse(
            video.body,
            status_code=video.status_code,
            media_type=video.content_type,
            headers=video.headers,
        )

    @app.get("/lectures/{lecture_id}/download")
    async def download_result(
        lecture_id: int,
        request: Request,
        version: int | None = None,
        user: User = Depends(current_user),
    ) -> StreamingResponse:
        del user
        try:
            archive = await run_in_threadpool(request.app.state.service.download_archive, lecture_id, version)
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("not_ready"))
        except ValidationError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, translate("not_ready")) from exc
        return _archive_response(archive)

    @app.post("/lectures/{lecture_id}/slides/reprocess")
    async def reprocess_slides(
        lecture_id: int,
        request: Request,
        user: User = Depends(admin_user),
    ) -> RedirectResponse:
        del user
        form = await _verified_form(request)
        if str(form.get("confirmed") or "") != "1":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request"))
        try:
            sensitivity_level = int(str(form.get("sensitivity_level") or ""))
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request")) from exc
        try:
            await run_in_threadpool(request.app.state.service.reprocess_slides, lecture_id, sensitivity_level)
        except KeyError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, translate("slides_reprocess_unavailable")) from exc
        except ValidationError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request")) from exc
        return RedirectResponse(f"/lectures/{lecture_id}", status_code=HTTP_303_SEE_OTHER)

    @app.post("/lectures/{lecture_id}/slides/default")
    async def set_default_slide_version(
        lecture_id: int,
        request: Request,
        user: User = Depends(admin_user),
    ) -> RedirectResponse:
        del user
        form = await _verified_form(request)
        if str(form.get("confirmed") or "") != "1":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request"))
        try:
            operation_id = int(str(form.get("operation_id") or ""))
        except ValueError as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request")) from exc
        try:
            await run_in_threadpool(
                request.app.state.service.set_default_slide_version,
                lecture_id,
                operation_id,
            )
        except (KeyError, ValidationError) as exc:
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request")) from exc
        return RedirectResponse(f"/lectures/{lecture_id}?version={operation_id}", status_code=HTTP_303_SEE_OTHER)

    @app.post("/lectures/{lecture_id}/sharing")
    async def change_sharing(
        lecture_id: int,
        request: Request,
        user: User = Depends(admin_user),
    ) -> RedirectResponse:
        del user
        form = await _verified_form(request)
        enabled = str(form.get("enabled") or "") == "1"
        try:
            await run_in_threadpool(request.app.state.service.set_public_sharing, lecture_id, enabled)
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        except ValidationError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, translate("not_ready")) from exc
        return RedirectResponse(f"/lectures/{lecture_id}", status_code=HTTP_303_SEE_OTHER)

    @app.post("/lectures/{lecture_id}/delete")
    async def delete_lecture(
        lecture_id: int,
        request: Request,
        user: User = Depends(admin_user),
    ) -> RedirectResponse:
        del user
        form = await _verified_form(request)
        if str(form.get("confirmed") or "") != "1":
            raise HTTPException(status.HTTP_400_BAD_REQUEST, translate("invalid_request"))
        try:
            lecture = await run_in_threadpool(request.app.state.service.soft_delete_lecture, lecture_id)
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("invalid_request")) from exc
        return RedirectResponse(
            f"/courses/{quote(lecture.echo_canonical_section_id, safe='')}",
            status_code=HTTP_303_SEE_OTHER,
        )

    @app.get("/public/{public_id}/download")
    async def public_download(public_id: str, request: Request) -> StreamingResponse:
        try:
            archive = await run_in_threadpool(
                request.app.state.service.public_download_archive,
                public_id,
            )
        except KeyError as exc:
            raise HTTPException(status.HTTP_404_NOT_FOUND, translate("public_not_found")) from exc
        except ValidationError as exc:
            raise HTTPException(status.HTTP_409_CONFLICT, translate("not_ready")) from exc
        return _archive_response(archive)

    return app


def _configure_web_logging() -> None:
    """Route application logs through Uvicorn without changing worker logging."""
    uvicorn_handlers = logging.getLogger("uvicorn.error").handlers
    if not uvicorn_handlers:
        return
    LOGGER.handlers = list(uvicorn_handlers)
    LOGGER.setLevel(logging.INFO)
    LOGGER.propagate = False


def _archive_response(archive: Any) -> StreamingResponse:
    return StreamingResponse(
        archive.body,
        media_type="application/zip",
        headers={
            "Content-Disposition": f"attachment; filename*=UTF-8''{quote(archive.filename, safe='')}",
            "Cache-Control": "private, no-store",
        },
    )


def _csrf_token(request: Request) -> str:
    token = request.session.get("csrf_token")
    if not isinstance(token, str):
        token = secrets.token_urlsafe(32)
        request.session["csrf_token"] = token
    return token


async def _verify_csrf(request: Request) -> Any:
    form = await request.form()
    expected = request.session.get("csrf_token")
    supplied = form.get("csrf_token")
    if not isinstance(expected, str) or not isinstance(supplied, str) or not secrets.compare_digest(expected, supplied):
        raise HTTPException(status.HTTP_403_FORBIDDEN, translate("invalid_csrf"))
    return form


async def _verified_form(request: Request) -> Any:
    return await _verify_csrf(request)


def _utc_iso(value: object) -> str:
    if not isinstance(value, datetime):
        return str(value)
    if value.tzinfo is None:
        value = value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc).isoformat().replace("+00:00", "Z")


def _date_only(value: object) -> str:
    if isinstance(value, datetime):
        return value.strftime("%d.%m.%Y")
    return str(value)


def _render_markdown(value: str, lecture_id: int, operation_id: int | None = None) -> str:
    def replace_slide(match: re.Match[str]) -> str:
        filename = quote(match.group(2), safe="")
        if operation_id is None:
            path = f"/lectures/{lecture_id}/slides/{filename}"
        else:
            path = f"/lectures/{lecture_id}/slides/{operation_id}/{filename}"
        return f"{match.group(1)}{path}{match.group(3)}"

    def replace_time(match: re.Match[str]) -> str:
        hours, minutes, seconds = (int(part) for part in match.group(1).split(":"))
        start_seconds = hours * 3600 + minutes * 60 + seconds
        return f"[{match.group(1)}–{match.group(2)}](#video-at-{start_seconds})"

    with_slides = SLIDE_IMAGE_RE.sub(replace_slide, value)
    return MARKDOWN.render(TRANSCRIPT_TIME_RE.sub(replace_time, with_slides))


async def _verify_google_id_token(id_token: str, client_id: str) -> dict[str, Any]:
    try:
        async with httpx.AsyncClient(timeout=20) as client:
            response = await client.get(GOOGLE_TOKENINFO_URL, params={"id_token": id_token})
    except httpx.RequestError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, translate("google_unavailable")) from exc
    if response.status_code >= 400:
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, translate("google_login_failed"))
    try:
        profile = response.json()
    except ValueError as exc:
        raise HTTPException(status.HTTP_502_BAD_GATEWAY, translate("google_unavailable")) from exc
    return _validate_google_profile(profile, client_id)


def _validate_google_profile(profile: object, client_id: str) -> dict[str, Any]:
    if not isinstance(profile, dict):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, translate("google_login_failed"))
    subject = profile.get("sub")
    email = profile.get("email")
    email_verified = profile.get("email_verified")
    if (
        profile.get("aud") != client_id
        or email_verified not in (True, "true")
        or not isinstance(subject, str)
        or not subject.strip()
        or not isinstance(email, str)
        or not email.strip()
    ):
        raise HTTPException(status.HTTP_401_UNAUTHORIZED, translate("google_login_failed"))
    return profile
