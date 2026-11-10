function waitForGoogleIdentity() {
  if (window.google?.accounts?.id) return Promise.resolve();
  return new Promise((resolve, reject) => {
    const deadline = Date.now() + 10000;
    const check = () => {
      if (window.google?.accounts?.id) return resolve();
      if (Date.now() >= deadline) return reject(new Error("google-unavailable"));
      window.setTimeout(check, 50);
    };
    check();
  });
}

function showGoogleLoginMessage(mount, message) {
  const element = document.getElementById("googleLoginMessage");
  if (!element) return;
  element.textContent = message || mount.dataset.loginFailed || "";
  element.hidden = false;
}

async function initializeGoogleLogin(mount) {
  try {
    const configResponse = await fetch("/api/auth/google/config", { credentials: "same-origin" });
    const config = await configResponse.json();
    if (!configResponse.ok || !config.enabled || !config.client_id) {
      showGoogleLoginMessage(mount, mount.dataset.notConfigured);
      return;
    }
    await waitForGoogleIdentity();
    window.google.accounts.id.initialize({
      client_id: config.client_id,
      callback: async (googleResponse) => {
        try {
          if (!googleResponse?.credential) throw new Error(mount.dataset.loginFailed);
          const response = await fetch("/api/auth/google", {
            method: "POST",
            credentials: "same-origin",
            headers: { "Content-Type": "application/json" },
            body: JSON.stringify({ id_token: googleResponse.credential }),
          });
          const payload = await response.json().catch(() => ({}));
          if (!response.ok) throw new Error(payload.message || mount.dataset.loginFailed);
          window.location.assign("/");
        } catch (error) {
          showGoogleLoginMessage(mount, error.message);
        }
      },
    });
    window.google.accounts.id.renderButton(mount, {
      theme: "outline",
      size: "large",
      text: "signin_with",
      shape: "rectangular",
    });
  } catch (_error) {
    showGoogleLoginMessage(mount, mount.dataset.loginFailed);
  }
}

document.addEventListener("DOMContentLoaded", () => {
  document.querySelectorAll("time.local-time").forEach((element) => {
    const value = new Date(element.dateTime);
    if (!Number.isNaN(value.getTime())) element.textContent = value.toLocaleString("et-EE");
  });
  const browserDateTimeFormatter = new Intl.DateTimeFormat("et-EE", {
    day: "2-digit",
    month: "2-digit",
    year: "numeric",
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hourCycle: "h23",
  });
  document.querySelectorAll("time.browser-date-time").forEach((element) => {
    const value = new Date(element.dateTime);
    if (Number.isNaN(value.getTime())) return;
    const parts = Object.fromEntries(
      browserDateTimeFormatter.formatToParts(value).map((part) => [part.type, part.value]),
    );
    element.textContent = `${parts.day}.${parts.month}.${parts.year} ${parts.hour}:${parts.minute}:${parts.second}`;
  });
  document.querySelectorAll("[data-resolve-source]").forEach((source) => {
    const button = source.closest("form")?.querySelector("[data-resolve-button]");
    if (!button) return;
    const update = () => {
      button.disabled = !source.value.trim();
    };
    source.addEventListener(source.tagName === "SELECT" ? "change" : "input", update);
    update();
  });
  const googleLoginMount = document.getElementById("googleLoginMount");
  if (googleLoginMount) initializeGoogleLogin(googleLoginMount);
  document.querySelectorAll(".slide-file-input").forEach((input) => {
    input.addEventListener("change", () => {
      const filename = input.closest(".slide-upload")?.querySelector(".slide-file-name");
      if (filename) filename.textContent = input.files?.[0]?.name || "";
    });
  });
  const createSubmissionForm = document.getElementById("createSubmissionForm");
  const submitJobsButton = document.getElementById("submitJobsButton");
  const submissionProgress = document.getElementById("submissionProgress");
  if (createSubmissionForm && submitJobsButton && submissionProgress) {
    createSubmissionForm.addEventListener("submit", () => {
      submitJobsButton.disabled = true;
      submissionProgress.hidden = false;
    });
  }
  const transcriptViewer = document.getElementById("transcriptViewer");
  const openTranscriptViewer = document.getElementById("openTranscriptViewer");
  const closeTranscriptViewer = document.getElementById("closeTranscriptViewer");
  if (transcriptViewer && openTranscriptViewer && closeTranscriptViewer) {
    const videoContainer = document.getElementById("transcriptVideoContainer");
    const transcriptVideo = document.getElementById("transcriptVideo");
    const transcriptContent = document.getElementById("transcriptContent");
    const slideVersionSelect = document.getElementById("slideVersionSelect");
    const downloadSelectedVersion = document.getElementById("downloadSelectedVersion");
    const defaultSlideVersionOperationId = document.getElementById("defaultSlideVersionOperationId");
    const openDefaultSlideVersionDialog = document.getElementById("openDefaultSlideVersionDialog");
    const videoUrl = transcriptViewer.dataset.videoUrl;
    let pendingVideoStart = null;
    const hideVideo = () => {
      if (videoContainer) videoContainer.hidden = true;
    };
    const releaseVideo = () => {
      if (!transcriptVideo) return;
      transcriptVideo.pause();
      transcriptVideo.removeAttribute("src");
      transcriptVideo.load();
      pendingVideoStart = null;
      hideVideo();
    };
    if (videoContainer && transcriptVideo && videoUrl) {
      transcriptVideo.addEventListener("loadedmetadata", () => {
        if (pendingVideoStart !== null) {
          transcriptVideo.currentTime = pendingVideoStart;
          pendingVideoStart = null;
        }
      });
      transcriptVideo.addEventListener("pause", hideVideo);
      transcriptVideo.addEventListener("ended", hideVideo);
    }
    if (transcriptContent) {
      transcriptContent.addEventListener("click", (event) => {
        const timestampLink = event.target.closest('a[href^="#video-at-"]');
        if (timestampLink && videoContainer && transcriptVideo && videoUrl) {
          event.preventDefault();
          const seconds = Number.parseInt(timestampLink.getAttribute("href").slice("#video-at-".length), 10);
          if (!Number.isFinite(seconds)) return;
          videoContainer.hidden = false;
          if (!transcriptVideo.getAttribute("src")) {
            pendingVideoStart = seconds;
            transcriptVideo.src = videoUrl;
            transcriptVideo.load();
          } else if (transcriptVideo.readyState >= 1) {
            transcriptVideo.currentTime = seconds;
          } else {
            pendingVideoStart = seconds;
          }
          transcriptVideo.play().catch(hideVideo);
          return;
        }
        const image = event.target.closest("img");
        if (image) image.classList.toggle("is-expanded");
      });
      transcriptContent.addEventListener("keydown", (event) => {
        const image = event.target.closest("img");
        if (!image || (event.key !== "Enter" && event.key !== " ")) return;
        event.preventDefault();
        image.classList.toggle("is-expanded");
      });
      transcriptContent.querySelectorAll("img").forEach((image) => { image.tabIndex = 0; });
    }
    if (slideVersionSelect) {
      slideVersionSelect.addEventListener("change", async () => {
        const operationId = slideVersionSelect.value;
        const template = slideVersionSelect.dataset.urlTemplate;
        if (!operationId || !template || !transcriptContent) return;
        try {
          const response = await fetch(template.replace("__operation_id__", encodeURIComponent(operationId)), {
            credentials: "same-origin",
          });
          if (!response.ok) throw new Error("slide-version-unavailable");
          const payload = await response.json();
          releaseVideo();
          transcriptContent.innerHTML = payload.html;
          transcriptContent.querySelectorAll("img").forEach((image) => { image.tabIndex = 0; });
          if (downloadSelectedVersion) downloadSelectedVersion.href = payload.download_url;
          if (defaultSlideVersionOperationId) defaultSlideVersionOperationId.value = payload.operation_id === null ? "" : String(payload.operation_id);
          if (openDefaultSlideVersionDialog) openDefaultSlideVersionDialog.disabled = payload.is_original;
        } catch (_error) {
          window.location.reload();
        }
      });
    }
    openTranscriptViewer.addEventListener("click", () => {
      transcriptViewer.showModal();
      document.body.classList.add("modal-open");
    });
    const closeViewer = () => transcriptViewer.close();
    closeTranscriptViewer.addEventListener("click", closeViewer);
    transcriptViewer.addEventListener("click", (event) => {
      if (event.target === transcriptViewer) closeViewer();
    });
    transcriptViewer.addEventListener("close", () => {
      releaseVideo();
      document.body.classList.remove("modal-open");
      transcriptContent?.querySelectorAll("img.is-expanded").forEach((image) => image.classList.remove("is-expanded"));
    });
  }
  const bindConfirmDialog = (dialogId, openId, cancelId) => {
    const dialog = document.getElementById(dialogId);
    const open = document.getElementById(openId);
    const cancel = document.getElementById(cancelId);
    if (!dialog || !open || !cancel) return;
    open.addEventListener("click", () => dialog.showModal());
    cancel.addEventListener("click", () => dialog.close());
    dialog.addEventListener("click", (event) => {
      if (event.target === dialog) dialog.close();
    });
  };
  bindConfirmDialog("deleteLectureDialog", "openDeleteLectureDialog", "cancelDeleteLecture");
  bindConfirmDialog("reprocessSlidesDialog", "openReprocessSlidesDialog", "cancelReprocessSlides");
  bindConfirmDialog("defaultSlideVersionDialog", "openDefaultSlideVersionDialog", "cancelDefaultSlideVersion");
  const originalVideoDialog = document.getElementById("originalVideoDialog");
  const openOriginalVideoDialog = document.getElementById("openOriginalVideoDialog");
  const closeOriginalVideoDialog = document.getElementById("closeOriginalVideoDialog");
  const originalLectureVideo = document.getElementById("originalLectureVideo");
  if (originalVideoDialog && openOriginalVideoDialog && closeOriginalVideoDialog && originalLectureVideo) {
    const releaseOriginalVideo = () => {
      originalLectureVideo.pause();
      originalLectureVideo.removeAttribute("src");
      originalLectureVideo.load();
      document.body.classList.remove("modal-open");
    };
    openOriginalVideoDialog.addEventListener("click", () => {
      originalVideoDialog.showModal();
      document.body.classList.add("modal-open");
      if (!originalLectureVideo.getAttribute("src")) {
        originalLectureVideo.src = originalVideoDialog.dataset.videoUrl;
        originalLectureVideo.load();
      }
    });
    closeOriginalVideoDialog.addEventListener("click", () => originalVideoDialog.close());
    originalVideoDialog.addEventListener("click", (event) => {
      if (event.target === originalVideoDialog) originalVideoDialog.close();
    });
    originalVideoDialog.addEventListener("close", releaseOriginalVideo);
  }
  if (!document.querySelector("[data-auto-refresh='true']")) return;
  const seconds = Number.parseInt(document.body.dataset.pollInterval || "0", 10);
  if (Number.isFinite(seconds) && seconds > 0) {
    const refreshWhenNoDialogIsOpen = () => {
      if (document.querySelector("dialog[open]")) {
        window.setTimeout(refreshWhenNoDialogIsOpen, seconds * 1000);
        return;
      }
      window.location.reload();
    };
    window.setTimeout(refreshWhenNoDialogIsOpen, seconds * 1000);
  }
});
